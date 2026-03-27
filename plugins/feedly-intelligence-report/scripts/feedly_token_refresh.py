#!/usr/bin/env python3
"""
Feedly Web Access Token を取得するスクリプト

ブラウザを開いてFeedlyにアクセスし、localStorageからトークンを取得して保存します。
ログイン済みであれば自動的にトークンを取得、未ログインならログイン画面が表示されます。

Usage:
    # Chromiumインストール（初回のみ）
    uv run --with playwright python -m playwright install chromium

    # トークン取得
    uv run --with playwright --with requests python feedly_token_refresh.py

    # 有効性確認
    uv run --with playwright --with requests python feedly_token_refresh.py --check

    # 強制更新
    uv run --with playwright --with requests python feedly_token_refresh.py --force
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Error: playwright not installed.", file=sys.stderr)
    print("Run: pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None  # --check オプション使用時のみ必要

DEFAULT_TOKEN_FILE = "~/.feedly/token"
FEEDLY_URL = "https://feedly.com"
USER_DATA_DIR = "~/.feedly/browser_data"


def expand_path(path: str) -> Path:
    """パスを展開（~ 対応）"""
    return Path(os.path.expanduser(path))


def check_token_validity(token: str) -> dict:
    """トークンの有効性を確認"""
    if requests is None:
        return {"valid": False, "error": "requests not installed"}

    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(
            "https://api.feedly.com/v3/profile",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            profile = resp.json()
            return {
                "valid": True,
                "email": profile.get("email", "unknown"),
                "id": profile.get("id", ""),
            }
        elif resp.status_code == 401:
            return {"valid": False, "error": "Token expired or invalid"}
        else:
            return {"valid": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def load_existing_token(token_file: str) -> str | None:
    """既存のトークンを読み込む"""
    path = expand_path(token_file)
    if path.exists():
        return path.read_text().strip()
    return None


def save_token(token: str, token_file: str) -> None:
    """トークンを保存"""
    path = expand_path(token_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token)
    os.chmod(path, 0o600)
    print(f"✓ Token saved to: {path}", file=sys.stderr)


def get_token_from_browser(headless: bool = False, timeout: int = 120) -> str | None:
    """
    ブラウザを開いてFeedlyからトークンを取得

    Args:
        headless: ヘッドレスモードで実行するか（Falseの場合ブラウザが表示される）
        timeout: ログイン待機のタイムアウト（秒）

    Returns:
        取得したトークン、または取得できなかった場合はNone
    """
    user_data_dir = expand_path(USER_DATA_DIR)
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # 永続的なブラウザコンテキストを使用（ログイン状態を保持）
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("Opening Feedly...", file=sys.stderr)
        page.goto(FEEDLY_URL)

        # localStorageからトークンを取得する関数
        def try_get_token() -> str | None:
            try:
                session_data = page.evaluate("""
                    () => {
                        const session = localStorage.getItem('feedly.session');
                        if (session) {
                            try {
                                return JSON.parse(session);
                            } catch (e) {
                                return null;
                            }
                        }
                        return null;
                    }
                """)
                if session_data and session_data.get("feedlyToken"):
                    return session_data["feedlyToken"]
            except Exception:
                pass
            return None

        # 最初にトークンを確認（すでにログイン済みの場合）
        time.sleep(2)
        token = try_get_token()

        if token:
            print("✓ Already logged in, token retrieved.", file=sys.stderr)
            browser.close()
            return token

        # ログインが必要な場合
        print(f"Please log in to Feedly in the browser window.", file=sys.stderr)
        print(f"Waiting up to {timeout} seconds for login...", file=sys.stderr)

        start_time = time.time()
        while time.time() - start_time < timeout:
            token = try_get_token()
            if token:
                print("✓ Login detected, token retrieved.", file=sys.stderr)
                browser.close()
                return token
            time.sleep(2)

        print("✗ Timeout waiting for login.", file=sys.stderr)
        browser.close()
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve Feedly Web Access Token from browser"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check validity of existing token without opening browser"
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_TOKEN_FILE,
        help=f"Output file path (default: {DEFAULT_TOKEN_FILE})"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (not recommended for login)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for login (default: 120)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh even if existing token is valid"
    )

    args = parser.parse_args()

    # --check モード: 既存トークンの確認のみ
    if args.check:
        token = load_existing_token(args.output)
        if not token:
            print(f"✗ No token found at {args.output}", file=sys.stderr)
            sys.exit(1)

        result = check_token_validity(token)
        if result["valid"]:
            print(f"✓ Token is valid", file=sys.stderr)
            print(f"  Email: {result['email']}", file=sys.stderr)
            sys.exit(0)
        else:
            print(f"✗ Token is invalid: {result['error']}", file=sys.stderr)
            sys.exit(1)

    # 既存トークンが有効なら何もしない（--force指定時を除く）
    if not args.force:
        existing_token = load_existing_token(args.output)
        if existing_token:
            result = check_token_validity(existing_token)
            if result["valid"]:
                print(f"✓ Existing token is still valid", file=sys.stderr)
                print(f"  Email: {result['email']}", file=sys.stderr)
                print(f"  Use --force to refresh anyway", file=sys.stderr)
                sys.exit(0)
            else:
                print(f"Existing token is invalid: {result['error']}", file=sys.stderr)
                print("Refreshing token...", file=sys.stderr)

    # ブラウザからトークンを取得
    token = get_token_from_browser(
        headless=args.headless,
        timeout=args.timeout
    )

    if not token:
        print("✗ Failed to retrieve token", file=sys.stderr)
        sys.exit(1)

    # トークンの有効性を確認
    result = check_token_validity(token)
    if not result["valid"]:
        print(f"✗ Retrieved token is invalid: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"  Email: {result['email']}", file=sys.stderr)

    # トークンを保存
    save_token(token, args.output)

    print("✓ Token refresh complete!", file=sys.stderr)


if __name__ == "__main__":
    main()
