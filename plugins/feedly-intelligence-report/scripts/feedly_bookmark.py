#!/usr/bin/env python3
"""
Feedlyレポートからチェック済み記事をRead Laterに保存するスクリプト

Usage:
    python feedly_bookmark.py --report Daily/2026-02/2026-02-03_feeds-report.md --mapping /tmp/url_to_entry_id.json
    python feedly_bookmark.py --report Daily/2026-02/2026-02-03_feeds-report.md --mapping /tmp/url_to_entry_id.json --dry-run
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

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


def load_mapping(mapping_file: str) -> dict:
    """URLとエントリーIDのマッピングを読み込む"""
    path = expand_path(mapping_file)
    if not path.exists():
        raise FileNotFoundError(f"Mapping file not found: {path}")
    return json.loads(path.read_text())


def get_user_id(token: str) -> str:
    """ユーザーIDを取得"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{FEEDLY_API_BASE}/profile", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json().get("id", "")


def parse_report_for_bookmarks(report_path: str) -> list[str]:
    """
    レポートファイルを解析して、「保存」列にチェックが入っている記事のURLを抽出

    Args:
        report_path: レポートファイルのパス

    Returns:
        チェック済み記事のURLリスト
    """
    path = expand_path(report_path)
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {path}")

    content = path.read_text()
    bookmarked_urls = []

    # テーブル行を解析
    # パターン: | # | [title](url) | ... | [ ] | [x] |
    # 最後の列が「保存」チェックボックス
    table_row_pattern = re.compile(
        r'\|\s*\d+\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|.*?\|\s*\[([x ])\]\s*\|\s*\[([x ])\]\s*\|'
    )

    for match in table_row_pattern.finditer(content):
        title = match.group(1)
        url = match.group(2)
        read_status = match.group(3)  # 読了
        save_status = match.group(4)  # 保存

        if save_status == 'x':
            bookmarked_urls.append(url)
            print(f"  → 保存対象: {title[:40]}...", file=sys.stderr)

    return bookmarked_urls


def save_to_read_later(token: str, user_id: str, entry_ids: list[str]) -> dict:
    """
    記事をRead Later（global.saved）に保存

    Args:
        token: Feedly API token
        user_id: Feedly user ID
        entry_ids: 保存する記事のエントリーIDリスト

    Returns:
        dict: {"success": bool, "saved_count": int, "error": str or None}
    """
    if not entry_ids:
        return {"success": True, "saved_count": 0, "error": None}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # global.savedタグID
    tag_id = f"user/{user_id}/tag/global.saved"
    encoded_tag_id = quote_plus(tag_id)

    total_saved = 0

    # 一度に複数のエントリーを保存
    payload = {"entryIds": entry_ids}

    try:
        resp = requests.put(
            f"{FEEDLY_API_BASE}/tags/{encoded_tag_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            total_saved = len(entry_ids)
        else:
            return {
                "success": False,
                "saved_count": 0,
                "error": f"API error: {resp.status_code} - {resp.text}"
            }
    except requests.RequestException as e:
        return {
            "success": False,
            "saved_count": 0,
            "error": f"Request error: {e}"
        }

    return {"success": True, "saved_count": total_saved, "error": None}


def main():
    parser = argparse.ArgumentParser(
        description="Save checked articles from Feedly report to Read Later"
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to the Feedly report markdown file"
    )
    parser.add_argument(
        "--mapping",
        required=True,
        help="Path to URL-to-EntryID mapping JSON file"
    )
    parser.add_argument(
        "--config",
        default="~/.feedly/config.json",
        help="Path to config file (default: ~/.feedly/config.json)"
    )
    parser.add_argument(
        "--token-file",
        default="~/.feedly/token",
        help="Path to token file (default: ~/.feedly/token)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be saved without actually saving"
    )

    args = parser.parse_args()

    # トークン読み込み
    try:
        config = load_config(args.config)
        token_file = config.get("token_file", args.token_file)
        token = load_token(token_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # マッピング読み込み
    try:
        url_to_entry_id = load_mapping(args.mapping)
        print(f"Loaded mapping: {len(url_to_entry_id)} URLs", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # レポート解析
    try:
        print(f"Parsing report: {args.report}", file=sys.stderr)
        bookmarked_urls = parse_report_for_bookmarks(args.report)
        print(f"Found {len(bookmarked_urls)} articles to save", file=sys.stderr)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not bookmarked_urls:
        print("No articles marked for saving.", file=sys.stderr)
        sys.exit(0)

    # URLをエントリーIDに変換
    entry_ids = []
    not_found = []
    for url in bookmarked_urls:
        entry_id = url_to_entry_id.get(url)
        if entry_id:
            entry_ids.append(entry_id)
        else:
            not_found.append(url)

    if not_found:
        print(f"Warning: {len(not_found)} URLs not found in mapping:", file=sys.stderr)
        for url in not_found[:5]:
            print(f"  - {url[:60]}...", file=sys.stderr)
        if len(not_found) > 5:
            print(f"  ... and {len(not_found) - 5} more", file=sys.stderr)

    if not entry_ids:
        print("No valid entry IDs found.", file=sys.stderr)
        sys.exit(1)

    # ドライラン
    if args.dry_run:
        print(f"\n[DRY RUN] Would save {len(entry_ids)} articles to Read Later", file=sys.stderr)
        for entry_id in entry_ids[:5]:
            print(f"  - {entry_id[:50]}...", file=sys.stderr)
        if len(entry_ids) > 5:
            print(f"  ... and {len(entry_ids) - 5} more", file=sys.stderr)
        sys.exit(0)

    # ユーザーID取得
    try:
        user_id = get_user_id(token)
        print(f"User ID: {user_id}", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Error getting user ID: {e}", file=sys.stderr)
        sys.exit(1)

    # Read Laterに保存
    print(f"Saving {len(entry_ids)} articles to Read Later...", file=sys.stderr)
    result = save_to_read_later(token, user_id, entry_ids)

    if result["success"]:
        print(f"✓ Saved {result['saved_count']} articles to Read Later", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"✗ Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
