#!/usr/bin/env python3
"""mf-cli トークンの無人再取得（macOS + Chrome 専用のオプション機能）

リフレッシュトークンが失効（invalid_grant）した場合、通常は `mf.py auth login` で
ブラウザを開いて人間が承認する必要がある。本スクリプトは Chrome の Cookie DB から
マネーフォワード ID の SSO セッションを直読みし、OAuth Authorization Code フローを
HTTP のみで自動完走して ~/.mf-cli/tokens.json を再生成する。

前提:
  - macOS で Chrome にログイン済み（biz.moneyforward.com / id.moneyforward.com の
    セッションが有効であること）
  - pip3 install browser-cookie3（mf.py 本体とは異なり外部依存あり。
    ModuleNotFoundError の場合は browser_cookie3 が入った Python で実行する）
  - ~/.mf-cli/config.json に client_id / client_secret が設定済み

使い方:
  python3 auth_auto.py            # トークン再取得して tokens.json を上書き
  python3 auth_auto.py --check    # 現在のトークンが有効なら何もしない（cron 向け）

セキュリティ上の注意:
  - 新しい権限を付与するものではない（App Portal で登録済みアプリの再認可のみ）
  - SSO authorize の乱発は MF ID セッション Cookie のローテーションを誘発し
    Chrome 側のログインを無効化しうるため、認可フローは 1 回だけ実行する
"""
import argparse
import base64
import http.cookiejar
import json
import os
import re
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CONFIG_FILE = os.path.expanduser("~/.mf-cli/config.json")
TOKENS_FILE = os.path.expanduser("~/.mf-cli/tokens.json")
CHROME_COOKIE_DB = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Cookies")
AUTH_BASE = "https://api.biz.moneyforward.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
SCOPES = (
    "mfc/accounting/offices.read mfc/accounting/journal.read mfc/accounting/journal.write "
    "mfc/accounting/accounts.read mfc/accounting/departments.read mfc/accounting/taxes.read "
    "mfc/accounting/report.read mfc/accounting/trade_partners.read mfc/accounting/trade_partners.write "
    "mfc/accounting/voucher.write mfc/accounting/transaction.write mfc/accounting/connected_account.read"
)


class _StopAtLocalhost(urllib.request.HTTPRedirectHandler):
    """localhost コールバックへのリダイレクトを HTTPError として捕捉し、認可コードを取り出す"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if newurl.startswith("http://localhost"):
            raise urllib.error.HTTPError(newurl, code, "callback", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _extract_code(err):
    url = str(err.filename or "")
    if url.startswith("http://localhost"):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return q.get("code", [None])[0]
    raise err


def reauthorize():
    import browser_cookie3  # 遅延 import（依存を本体に波及させない）

    config = json.load(open(CONFIG_FILE))
    redirect_uri = config.get("redirect_uri", "http://localhost:8080/callback")

    jar = http.cookiejar.CookieJar()
    for c in browser_cookie3.chrome(cookie_file=CHROME_COOKIE_DB, domain_name="moneyforward.com"):
        jar.set_cookie(c)
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), _StopAtLocalhost())
    opener.addheaders = [("User-Agent", UA), ("Accept", "text/html")]

    params = {
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": secrets.token_urlsafe(16),
    }
    code = None
    try:
        r = opener.open(f"{AUTH_BASE}/authorize?" + urllib.parse.urlencode(params), timeout=30)
        body = r.read().decode("utf-8", "ignore")

        # Step 1: MF ID の SSO（アカウント選択）を追従
        if "id.moneyforward" in r.url:
            m = re.search(r'gon\.authorizationParamsQueryString="(.*?)";', body)
            if not m:
                raise RuntimeError("MF ID セッションが無効です。Chrome で moneyforward.com にログインしてください")
            qs = m.group(1).replace("\\u0026", "&")
            try:
                r = opener.open("https://id.moneyforward.com/oauth/authorize?" + qs, timeout=30)
                body = r.read().decode("utf-8", "ignore")
            except urllib.error.HTTPError as e:
                code = _extract_code(e)

        # Step 2: 事業者（テナント）選択
        if code is None and "/tenants" in r.url:
            m = re.search(r'"identification_code":"([^"]+)"', body)
            if not m:
                raise RuntimeError("事業者一覧を取得できませんでした")
            try:
                r = opener.open(f"{AUTH_BASE}/tenants/select?identification_code={m.group(1)}", timeout=30)
                body = r.read().decode("utf-8", "ignore")
            except urllib.error.HTTPError as e:
                code = _extract_code(e)

        # Step 3: 同意画面で「許可」を POST
        if code is None and "/oauth" in r.url:
            try:
                req = urllib.request.Request(f"{AUTH_BASE}/oauth/allow", data=b"", headers={"Referer": r.url})
                opener.open(req, timeout=30)
                raise RuntimeError("認可コードのコールバックに到達しませんでした")
            except urllib.error.HTTPError as e:
                code = _extract_code(e)
    except urllib.error.HTTPError as e:
        code = _extract_code(e)

    if not code:
        raise RuntimeError("認可コードを取得できませんでした（SSO セッション切れの可能性）")

    # Step 4: トークン交換（CLIENT_SECRET_BASIC）
    basic = base64.b64encode(f"{config['client_id']}:{config['client_secret']}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri,
    }).encode()
    req = urllib.request.Request(f"{AUTH_BASE}/token", data=data, headers={
        "Authorization": "Basic " + basic,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    tok = json.loads(urllib.request.urlopen(req, timeout=30).read())
    tokens = {
        "access_token": tok["access_token"],
        "refresh_token": tok.get("refresh_token"),
        "expires_at": time.time() + tok.get("expires_in", 3600),
    }
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKENS_FILE, 0o600)
    return tokens


def main():
    ap = argparse.ArgumentParser(description="mf-cli トークンの無人再取得（Chrome Cookie 利用）")
    ap.add_argument("--check", action="store_true",
                    help="リフレッシュトークンで更新を試み、成功したら再認可をスキップ")
    args = ap.parse_args()

    if args.check:
        # mf.py の auth refresh 相当を試し、生きていれば何もしない
        script_dir = os.path.dirname(os.path.abspath(__file__))
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(script_dir, "mf.py"), "auth", "refresh"],
                           capture_output=True, text=True)
        if r.returncode == 0 and "失敗" not in (r.stdout + r.stderr):
            print("refresh token は有効です（再認可不要）")
            return

    tokens = reauthorize()
    print(f"tokens.json を再生成しました（expires_at: {time.strftime('%H:%M:%S', time.localtime(tokens['expires_at']))}）")


if __name__ == "__main__":
    main()
