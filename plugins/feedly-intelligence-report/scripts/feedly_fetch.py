#!/usr/bin/env python3
"""
Feedly API から全未読記事を一括取得するスクリプト

Usage:
    # 全未読記事を取得（global.all使用、1 API call）
    python feedly_fetch.py --output /tmp/feedly_articles.json

    # 既読記事も含めて取得
    python feedly_fetch.py --include-read --output /tmp/feedly_articles.json

    # APIトークン確認
    python feedly_fetch.py --test

    # 取得した記事を既読にする
    python feedly_fetch.py --mark-read /tmp/feedly_articles.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

FEEDLY_API_BASE = "https://api.feedly.com/v3"


def expand_path(path: str) -> Path:
    """パスを展開（~ 対応）"""
    return Path(os.path.expanduser(path))


def load_token(token_file: str) -> str:
    """トークンファイルからトークンを読み込む"""
    path = expand_path(token_file)
    if not path.exists():
        raise FileNotFoundError(f"Token file not found: {path}")
    return path.read_text().strip()


def load_config(config_file: str) -> dict:
    """設定ファイルを読み込む"""
    path = expand_path(config_file)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    return json.loads(path.read_text())


def get_user_id(token: str) -> str:
    """ユーザーIDを取得"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{FEEDLY_API_BASE}/profile", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("id", "")


def test_connection(token: str) -> bool:
    """API接続テスト"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(f"{FEEDLY_API_BASE}/profile", headers=headers, timeout=10)
        if resp.status_code == 200:
            profile = resp.json()
            print(f"✓ Connected as: {profile.get('email', 'unknown')}")
            return True
        else:
            print(f"✗ Connection failed: {resp.status_code} - {resp.text}", file=sys.stderr)
            return False
    except requests.RequestException as e:
        print(f"✗ Request error: {e}", file=sys.stderr)
        return False


def fetch_stream_contents(
    token: str,
    stream_id: str,
    count: int = 100,
    newer_than: int = None,
    unread_only: bool = True,
    fetch_all: bool = True
) -> list[dict]:
    """
    指定されたストリームから記事を取得

    Args:
        token: Feedly API token
        stream_id: Feedly stream ID
        count: 1回のリクエストで取得する記事数（最大1000）
        newer_than: この時刻（Unix timestamp ms）より新しい記事のみ取得
        unread_only: Trueの場合、未読記事のみを取得（デフォルト: True）
        fetch_all: Trueの場合、continuationトークンを使って全件取得（デフォルト: True）

    Returns:
        記事リスト
    """
    headers = {"Authorization": f"Bearer {token}"}
    all_articles = []
    continuation = None
    page = 1

    while True:
        params = {
            "streamId": stream_id,
            "count": min(count, 1000),  # API上限
            "unreadOnly": "true" if unread_only else "false",
        }
        if newer_than:
            params["newerThan"] = newer_than
        if continuation:
            params["continuation"] = continuation

        try:
            resp = requests.get(
                f"{FEEDLY_API_BASE}/streams/contents",
                headers=headers,
                params=params,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            all_articles.extend(items)

            if page > 1:
                print(f"    page {page}: +{len(items)} articles (total: {len(all_articles)})", file=sys.stderr)

            # 全件取得モードでない場合、または続きがない場合は終了
            if not fetch_all:
                break

            continuation = data.get("continuation")
            if not continuation:
                break

            page += 1

        except requests.RequestException as e:
            print(f"Error fetching stream {stream_id}: {e}", file=sys.stderr)
            break

    return all_articles


def extract_article_url(article: dict) -> str:
    """
    記事URLを取得（優先順位: canonicalUrl > alternate[0].href > originId）

    はてなブックマーク等の集約サイト経由の場合、canonicalUrlがnullになることがあり、
    その場合はoriginIdに元記事のURLが含まれている。
    """
    # 1. canonicalUrl（最優先）
    if article.get("canonicalUrl"):
        return article["canonicalUrl"]

    # 2. alternate配列の最初のhref
    alternate = article.get("alternate", [])
    if alternate and isinstance(alternate, list) and len(alternate) > 0:
        href = alternate[0].get("href")
        if href:
            return href

    # 3. originId（フォールバック）
    return article.get("originId", "")


def extract_article_data(article: dict) -> dict:
    """
    記事データから必要な情報を抽出

    Args:
        article: Feedly API レスポンスの記事オブジェクト

    Returns:
        正規化された記事データ
    """
    # 本文取得（content または summary）
    content = ""
    if "content" in article and article["content"]:
        content = article["content"].get("content", "")
    elif "summary" in article and article["summary"]:
        content = article["summary"].get("content", "")

    # ソース情報
    origin = article.get("origin", {})

    return {
        "id": article.get("id", ""),
        "title": article.get("title", "No Title"),
        "url": extract_article_url(article),
        "published": article.get("published", 0),
        "crawled": article.get("crawled", 0),  # Feedlyがクロールした時刻
        "updated": article.get("updated", 0),
        "author": article.get("author", ""),
        "content": content,
        "engagement": article.get("engagement", 0),
        "engagement_rate": article.get("engagementRate", 0.0),
        "source": {
            "title": origin.get("title", ""),
            "url": origin.get("htmlUrl", ""),
            "stream_id": origin.get("streamId", ""),
        },
        "keywords": article.get("keywords", []),
        "entities": [e.get("label", "") for e in article.get("entities", [])],
        "visual": article.get("visual", {}).get("url", ""),
    }


def mark_entries_as_read(token: str, entry_ids: list[str]) -> dict:
    """
    記事を既読にマークする

    Args:
        token: Feedly API token
        entry_ids: 既読にする記事IDリスト

    Returns:
        dict: {"success": bool, "marked_count": int, "error": str or None}
    """
    if not entry_ids:
        return {"success": True, "marked_count": 0, "error": None}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Feedly APIは1リクエストあたり1000件まで
    batch_size = 1000
    total_marked = 0

    for i in range(0, len(entry_ids), batch_size):
        batch = entry_ids[i:i + batch_size]
        payload = {
            "action": "markAsRead",
            "type": "entries",
            "entryIds": batch
        }

        try:
            resp = requests.post(
                f"{FEEDLY_API_BASE}/markers",
                headers=headers,
                json=payload,
                timeout=30
            )
            if resp.status_code == 200:
                total_marked += len(batch)
            else:
                return {
                    "success": False,
                    "marked_count": total_marked,
                    "error": f"API error: {resp.status_code} - {resp.text}"
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "marked_count": total_marked,
                "error": f"Request error: {e}"
            }

    return {"success": True, "marked_count": total_marked, "error": None}


def extract_entry_ids_from_json(json_file: str) -> list[str]:
    """
    取得済みJSONファイルから記事IDを抽出

    Args:
        json_file: feedly_fetch.pyの出力JSONファイル

    Returns:
        記事IDリスト
    """
    path = expand_path(json_file)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    data = json.loads(path.read_text())
    entry_ids = []

    for category in data.get("categories", {}).values():
        for article in category.get("articles", []):
            article_id = article.get("id", "")
            if article_id:
                entry_ids.append(article_id)

    return entry_ids


def fetch_global_all(config: dict, token: str, include_read: bool = False) -> dict:
    """
    global.allストリームから全記事を一括取得し、カテゴリごとにグループ化

    Args:
        config: 設定辞書
        token: API token
        include_read: Trueの場合、既読記事も含める（デフォルト: False = 未読のみ）

    Returns:
        カテゴリ別の記事辞書
    """
    fetch_count = config.get("fetch_count", 1000)  # global.allでは多めに
    unread_only = config.get("unread_only", True)
    if include_read:
        unread_only = False

    # ユーザーIDを取得
    user_id = get_user_id(token)
    global_all_id = f"user/{user_id}/category/global.all"

    mode_str = "未読のみ" if unread_only else "全記事（既読含む）"
    print(f"取得モード: {mode_str} (global.all)", file=sys.stderr)
    print(f"Fetching all articles...", file=sys.stderr)

    raw_articles = fetch_stream_contents(
        token=token,
        stream_id=global_all_id,
        count=fetch_count,
        newer_than=None,  # 時間制限なし
        unread_only=unread_only
    )

    print(f"  → {len(raw_articles)} articles", file=sys.stderr)

    # カテゴリごとにグループ化
    results = {}
    config_categories = {cat.get("name"): cat for cat in config.get("categories", [])}

    for article in raw_articles:
        article_data = extract_article_data(article)

        # 記事のカテゴリ情報を取得
        categories = article.get("categories", [])
        if not categories:
            # カテゴリなしの場合は "uncategorized" に分類
            cat_label = "uncategorized"
            cat_slug = "uncategorized"
        else:
            # 最初のカテゴリを使用
            cat_label = categories[0].get("label", "unknown")
            # 設定ファイルのカテゴリ名からslugを取得
            if cat_label in config_categories:
                cat_slug = config_categories[cat_label].get("slug", cat_label.lower())
            else:
                cat_slug = cat_label.lower().replace(" ", "-")

        if cat_slug not in results:
            # 設定ファイルからキーワード等を取得
            cat_config = config_categories.get(cat_label, {})
            results[cat_slug] = {
                "name": cat_label,
                "slug": cat_slug,
                "stream_id": f"user/{user_id}/category/{cat_label}",
                "keywords": cat_config.get("keywords", []),
                "trusted_sources": cat_config.get("trusted_sources", {}),
                "articles": [],
                "fetched_at": datetime.now().isoformat(),
                "count": 0,
            }

        results[cat_slug]["articles"].append(article_data)
        results[cat_slug]["count"] += 1

    # カテゴリ別の件数を表示
    for slug, data in sorted(results.items(), key=lambda x: -x[1]["count"]):
        print(f"  - {data['name']}: {data['count']}件", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch articles from Feedly API")
    parser.add_argument(
        "--config",
        default="~/.feedly/config.json",
        help="Path to config file (default: ~/.feedly/config.json)"
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test API connection only"
    )
    parser.add_argument(
        "--token-file",
        default="~/.feedly/token",
        help="Path to token file (default: ~/.feedly/token)"
    )
    parser.add_argument(
        "--mark-read",
        metavar="JSON_FILE",
        help="Mark all articles in the specified JSON file as read"
    )
    parser.add_argument(
        "--include-read",
        action="store_true",
        help="Include already-read articles (default: unread only)"
    )

    args = parser.parse_args()

    # トークン読み込み
    try:
        # 設定ファイルからトークンファイルパスを取得（存在すれば）
        if args.test:
            token_file = args.token_file
        else:
            config = load_config(args.config)
            token_file = config.get("token_file", args.token_file)

        token = load_token(token_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Please run setup first. See SETUP.md", file=sys.stderr)
        sys.exit(1)

    # テストモード
    if args.test:
        success = test_connection(token)
        sys.exit(0 if success else 1)

    # 既読マークモード
    if args.mark_read:
        try:
            entry_ids = extract_entry_ids_from_json(args.mark_read)
            print(f"Marking {len(entry_ids)} articles as read...", file=sys.stderr)
            result = mark_entries_as_read(token, entry_ids)
            if result["success"]:
                print(f"✓ Marked {result['marked_count']} articles as read", file=sys.stderr)
                sys.exit(0)
            else:
                print(f"✗ Error: {result['error']}", file=sys.stderr)
                print(f"  Partially marked: {result['marked_count']} articles", file=sys.stderr)
                sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # 記事取得（global.allから一括取得）
    config = load_config(args.config)
    results = fetch_global_all(config, token, include_read=args.include_read)

    # メタデータ追加
    unread_only = config.get("unread_only", True) and not args.include_read
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_articles": sum(cat["count"] for cat in results.values()),
            "categories_count": len(results),
            "unread_only": unread_only,
        },
        "categories": results,
    }

    # URL → エントリーIDマッピングを生成
    url_to_entry_id = {}
    for category in results.values():
        for article in category.get("articles", []):
            url = article.get("url", "")
            entry_id = article.get("id", "")
            if url and entry_id:
                url_to_entry_id[url] = entry_id

    # 出力
    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(output_json)
    else:
        output_path = expand_path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json)
        print(f"Output written to: {output_path}", file=sys.stderr)

        # マッピングファイルを出力（同じディレクトリに配置）
        mapping_path = output_path.parent / "url_to_entry_id.json"
        mapping_path.write_text(json.dumps(url_to_entry_id, ensure_ascii=False, indent=2))
        print(f"Mapping file written to: {mapping_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
