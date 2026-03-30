#!/usr/bin/env python3
"""
mf-cli: マネーフォワード クラウド会計 CLI

マネーフォワード APIを使用して、仕訳・帳票・マスター情報を取得・操作します。
OAuth 2.0認可コードフロー + リフレッシュトークン自動管理に対応。

使用方法:
    python3 mf.py auth setup              # OAuth認証設定
    python3 mf.py auth login              # ログイン（トークン取得）
    python3 mf.py auth status             # 認証状態確認
    python3 mf.py tenant info             # 事業者情報取得
    python3 mf.py journal list            # 仕訳一覧
    python3 mf.py journal get <id>        # 仕訳取得
    python3 mf.py journal create          # 仕訳作成
    python3 mf.py journal update <id>     # 仕訳更新（全置換）
    python3 mf.py report trial-balance    # 残高試算表（累計値）
    python3 mf.py report transition       # 推移表（単月値）
    python3 mf.py master accounts         # 勘定科目
    python3 mf.py master sub-accounts     # 補助科目
    python3 mf.py master taxes            # 税区分
    python3 mf.py master departments      # 部門
    python3 mf.py master partners         # 取引先
"""

import sys
import json
import os
import time
import base64
import webbrowser
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import argparse

# マネーフォワード API設定
MF_AUTH_BASE = "https://api.biz.moneyforward.com"          # 認証API
MF_ACCOUNTING_API = "https://api-accounting.moneyforward.com/api/v3"  # 会計API

SCOPES = "mfc/accounting/offices.read mfc/accounting/journal.read mfc/accounting/journal.write mfc/accounting/accounts.read mfc/accounting/departments.read mfc/accounting/taxes.read mfc/accounting/report.read mfc/accounting/trade_partners.read mfc/accounting/trade_partners.write mfc/accounting/voucher.write mfc/accounting/transaction.write mfc/accounting/connected_account.read"
LOCAL_REDIRECT_URI = "http://localhost:8080/callback"
CONFIG_DIR = os.path.expanduser("~/.mf-cli")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TOKENS_FILE = os.path.join(CONFIG_DIR, "tokens.json")

# グローバル：認可コード取得用
_auth_code = None
_auth_error = None

# 多言語対応：エラーメッセージマッピング
MESSAGES = {
    "ja": {
        "auth_failed": "認証に失敗しました",
        "token_expired": "トークンが期限切れです",
        "permission_denied": "権限がありません",
        "not_found": "リソースが見つかりません",
        "rate_limit": "APIレート制限に達しました",
        "server_error": "サーバーエラーが発生しました",
        "invalid_request": "リクエストが不正です",
        "retry_after": "しばらく待ってから再試行してください",
        "delete_success": "削除に成功しました",
        "export_success": "エクスポートに成功しました",
    },
    "en": {
        "auth_failed": "Authentication failed",
        "token_expired": "Token expired",
        "permission_denied": "Permission denied",
        "not_found": "Resource not found",
        "rate_limit": "API rate limit exceeded",
        "server_error": "Server error occurred",
        "invalid_request": "Invalid request",
        "retry_after": "Please wait before retrying",
        "delete_success": "Deleted successfully",
        "export_success": "Exported successfully",
    }
}

# デフォルト言語（環境変数で上書き可能）
LANGUAGE = os.environ.get("MF_CLI_LANG", "ja")


def get_message(key):
    """国際化メッセージを取得"""
    lang = MESSAGES.get(LANGUAGE, MESSAGES["ja"])
    return lang.get(key, f"[{key}]")


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuth認可後のコールバックハンドラ"""

    def do_GET(self):
        global _auth_code, _auth_error

        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if "code" in query_params:
            _auth_code = query_params["code"][0]
            response = b"<html><body><h1>Success!</h1><p>You can close this window.</p></body></html>"
            self.send_response(200)
        elif "error" in query_params:
            _auth_error = query_params.get("error_description", ["Unknown error"])[0]
            response = f"<html><body><h1>Error</h1><p>{_auth_error}</p></body></html>".encode()
            self.send_response(400)
        else:
            response = b"<html><body><h1>Invalid Request</h1></body></html>"
            self.send_response(400)

        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        pass


class MFClient:
    """マネーフォワード クラウド会計 API クライアント"""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.config = self._load_config()
        self.tokens = self._load_tokens()
        self._office_cache = None
        self._response_cache = {}  # 応答キャッシュ（get_cache_key で管理）
        self._cache_ttl = 300  # キャッシュ有効期限（秒）

    # -------------------------
    # キャッシング・応答処理
    # -------------------------

    def _get_cache_key(self, method, endpoint):
        """キャッシュキー生成"""
        return f"{method}:{endpoint}"

    def _get_cached(self, method, endpoint):
        """キャッシュから取得"""
        key = self._get_cache_key(method, endpoint)
        if key in self._response_cache:
            cached, timestamp = self._response_cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return cached
            else:
                del self._response_cache[key]
        return None

    def _set_cached(self, method, endpoint, response):
        """キャッシュに保存"""
        key = self._get_cache_key(method, endpoint)
        self._response_cache[key] = (response, time.time())
        return response

    def _normalize_response(self, response):
        """複雑な応答を正規化（ネスト構造の抽出）"""
        if not isinstance(response, dict):
            return response

        # よくあるパターンを検出して正規化
        if "journals" in response:
            return response.get("journals", response)
        elif "rows" in response:
            return response.get("rows", response)
        elif "items" in response:
            return response.get("items", response)
        elif "accounts" in response:
            return response.get("accounts", response)
        elif "data" in response and isinstance(response["data"], list):
            return response.get("data", response)

        return response

    def _handle_error(self, code, message, details=None):
        """エラーハンドリング（詳細情報表示）"""
        error_messages = {
            400: "リクエストのパラメータが不正です",
            401: "認証が失敗しました（トークン有効期限切れなど）",
            403: "事業者に対する権限がありません",
            404: "リクエストされたリソースが見つかりません",
            429: "APIレート制限に達しました。しばらく待ってから再試行してください",
            500: "サーバーエラーが発生しました",
        }

        error_msg = error_messages.get(code, f"エラーが発生しました（{code}）")
        print(f"❌ {error_msg}", file=sys.stderr)
        if message:
            print(f"   詳細: {message}", file=sys.stderr)
        if details:
            print(f"   {details}", file=sys.stderr)
        return None

    # -------------------------
    # 設定・トークン管理
    # -------------------------

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return {}
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)

    def _load_tokens(self):
        if not os.path.exists(TOKENS_FILE):
            return {}
        try:
            with open(TOKENS_FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_tokens(self):
        with open(TOKENS_FILE, "w") as f:
            json.dump(self.tokens, f, indent=2)
        os.chmod(TOKENS_FILE, 0o600)

    def _basic_auth_header(self):
        """CLIENT_SECRET_BASIC 方式の Authorization ヘッダーを生成"""
        client_id = self.config["client_id"]
        client_secret = self.config["client_secret"]
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        return f"Basic {credentials}"

    def _encode_id(self, id_str):
        """API から返ってきた Base64 エンコード ID を REST API パス用に二重エンコード。
        %2F（スラッシュ）がパス区切りと混同されないようにする。
        """
        return urllib.parse.quote(id_str, safe="")

    # -------------------------
    # 認証コマンド
    # -------------------------

    def setup(self):
        """OAuth設定（Client ID / Secret入力または環境変数から取得）"""
        print("=== mf-cli 認証設定 ===\n")

        client_id = os.environ.get("MF_CLIENT_ID", "").strip()
        client_secret = os.environ.get("MF_CLIENT_SECRET", "").strip()

        if not client_id:
            print("アプリポータル → アプリ開発 → mf-cli の Client ID を入力してください")
            print("URL: https://app-portal.moneyforward.com/authorized_apps/\n")
            client_id = input("Client ID: ").strip()

        if not client_secret:
            client_secret = input("Client Secret: ").strip()

        if not client_id or not client_secret:
            print("Error: Client ID と Client Secret は必須です", file=sys.stderr)
            return False

        self.config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": LOCAL_REDIRECT_URI
        }
        self._save_config()
        print(f"✓ 設定を保存しました（{CONFIG_FILE}）")
        return True

    def login(self):
        """OAuth 認可コードフローでアクセストークン取得"""
        global _auth_code, _auth_error
        _auth_code = None
        _auth_error = None

        if "client_id" not in self.config:
            print("Error: 先に `mf auth setup` を実行してください", file=sys.stderr)
            return False

        auth_url = f"{MF_AUTH_BASE}/authorize?" + urllib.parse.urlencode({
            "response_type": "code",
            "client_id": self.config["client_id"],
            "scope": SCOPES,
            "redirect_uri": self.config["redirect_uri"]
        })

        print("=== OAuth認可フロー開始 ===\n")
        server = HTTPServer(("localhost", 8080), AuthCallbackHandler)
        server_thread = Thread(target=server.handle_request)
        server_thread.daemon = True
        server_thread.start()

        time.sleep(0.5)
        webbrowser.open(auth_url)
        print(f"ブラウザが開きます...\n手動で開く場合: {auth_url}\n")
        print("認可を待機中...", end="", flush=True)

        start = time.time()
        while _auth_code is None and _auth_error is None:
            if time.time() - start > 120:
                print("\nTimeout", file=sys.stderr)
                return False
            time.sleep(0.1)
            print(".", end="", flush=True)

        print()
        server.server_close()

        if _auth_error:
            print(f"Error: {_auth_error}", file=sys.stderr)
            return False

        return self._exchange_code_for_token(_auth_code)

    def _exchange_code_for_token(self, code):
        """認可コード → アクセストークン交換（CLIENT_SECRET_BASIC）"""
        data = urllib.parse.urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config["redirect_uri"]
        }).encode()

        try:
            req = urllib.request.Request(f"{MF_AUTH_BASE}/token", data=data, method="POST")
            req.add_header("Authorization", self._basic_auth_header())
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                self.tokens = {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token"),
                    "expires_at": time.time() + result["expires_in"]
                }
                self._save_tokens()
                print("✓ ログイン成功。トークンを保存しました")
                return True
        except urllib.error.HTTPError as e:
            body = json.loads(e.read().decode())
            print(f"Error: {body.get('error_description', body)}", file=sys.stderr)
            return False

    def _refresh_access_token(self):
        """リフレッシュトークンでアクセストークンを更新（CLIENT_SECRET_BASIC）"""
        if not self.tokens.get("refresh_token"):
            return False

        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"]
        }).encode()

        try:
            req = urllib.request.Request(f"{MF_AUTH_BASE}/token", data=data, method="POST")
            req.add_header("Authorization", self._basic_auth_header())
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())
                self.tokens["access_token"] = result["access_token"]
                self.tokens["expires_at"] = time.time() + result["expires_in"]
                self._save_tokens()
                return True
        except urllib.error.HTTPError:
            return False

    def _ensure_valid_token(self):
        if not self.tokens.get("access_token"):
            print("Error: `mf auth login` を先に実行してください", file=sys.stderr)
            return False
        if time.time() >= self.tokens.get("expires_at", 0):
            print("トークン期限切れ。更新中...", file=sys.stderr)
            if not self._refresh_access_token():
                print("Error: トークン更新失敗。`mf auth login` を再実行してください", file=sys.stderr)
                return False
        return True

    def status(self):
        if not self.tokens.get("access_token"):
            print("Status: Not authenticated")
            return
        expires_in = max(0, int(self.tokens.get("expires_at", 0) - time.time()))
        print(f"Status: Authenticated")
        print(f"Expires in: {expires_in} seconds")

    # -------------------------
    # API 共通ヘルパー
    # -------------------------

    def _api_request(self, method, endpoint, data=None, _retry=0):
        """会計API呼び出し。429 は指数バックオフでリトライ、401 は自動リフレッシュ。"""
        if not self._ensure_valid_token():
            return None

        url = f"{MF_ACCOUNTING_API}{endpoint}"
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.tokens['access_token']}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and _retry < 3:
                wait = 2 ** _retry
                print(f"Rate limit. {wait}秒後にリトライ...", file=sys.stderr)
                time.sleep(wait)
                return self._api_request(method, endpoint, data, _retry + 1)
            if e.code == 401 and _retry == 0:
                if self._refresh_access_token():
                    return self._api_request(method, endpoint, data, 1)
            try:
                err = json.loads(e.read().decode())
                msg = err.get("errors", [{}])[0].get("message") or err.get("error_description") or str(err)
            except Exception:
                msg = f"HTTP {e.code}"
            print(f"Error: {msg}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None

    # -------------------------
    # 事業者
    # -------------------------

    def get_office(self):
        """事業者情報取得（キャッシュあり）"""
        if not self._office_cache:
            self._office_cache = self._api_request("GET", "/offices")
        return self._office_cache

    # -------------------------
    # 仕訳
    # 注意: 取得時の value は税抜金額。税込 = value + tax_value
    #       登録・更新時の value は税込金額を指定（APIが自動分解）
    # -------------------------

    def list_journals(self, limit=50, from_date=None, to_date=None, page=1, account_id=None, is_realized=None):
        """仕訳一覧取得。

        account_id: 指定された勘定科目を借方貸方のいずれかに持つ仕訳のみ
        is_realized: 未実現の仕訳であるかを指定（True=実現, False=未実現）
        """
        params = {"per_page": limit, "page": page}
        if from_date:
            params["start_date"] = from_date
        if to_date:
            params["end_date"] = to_date
        if account_id:
            params["account_id"] = account_id
        if is_realized is not None:
            params["is_realized"] = str(is_realized).lower()
        qs = urllib.parse.urlencode(params)
        return self._api_request("GET", f"/journals?{qs}")

    def get_journal(self, journal_id):
        """仕訳取得（ID指定）。ID は API から返ってきた値をそのまま渡す。"""
        encoded = self._encode_id(journal_id)
        return self._api_request("GET", f"/journals/{encoded}")

    def create_journal(self, data):
        """仕訳新規作成。

        data 形式:
          {
            "transaction_date": "2026-03-29",  # 必須
            "journal_type": "journal_entry",   # 必須: "journal_entry" or "adjusting_entry"
            "branches": [                       # 必須（最大300行）
              {
                "debitor": {
                  "account_id": "<勘定科目ID>",  # 必須
                  "value": 11000,               # 必須: 税込金額
                  "tax_id": "<税区分ID>"         # 省略可
                },
                "creditor": { ... }             # 同構造
              }
            ],
            "memo": "摘要"                      # 省略可
          }
        """
        return self._api_request("POST", "/journals", data)

    def update_journal(self, journal_id, data):
        """仕訳更新（全置換 PUT API）。

        ⚠️ 全置換のため、未指定フィールドは削除されます。
        必ず事前に get_journal() で既存データを取得し、全フィールドを含めて送信してください。
        """
        encoded = self._encode_id(journal_id)
        return self._api_request("PUT", f"/journals/{encoded}", data)

    def delete_journal(self, journal_id):
        """仕訳削除。"""
        encoded = self._encode_id(journal_id)
        return self._api_request("DELETE", f"/journals/{encoded}")

    # -------------------------
    # 帳票
    # -------------------------

    def get_trial_balance(self, fiscal_year=None, start_month=None, end_month=None, start_date=None, end_date=None,
                         with_sub_accounts=None, include_tax=None, journal_types=None, report_type="pl"):
        """残高試算表取得（期首からの累計値）。

        report_type: "pl"（損益計算書）または "bs"（貸借対照表）
        fiscal_year: 会計年度
        start_month: 集計開始月（1-12、fiscal_year と組み合わせて使用）
        end_month: 集計終了月（1-12）
        start_date: 対象期間の開始日（YYYY-MM-DD形式、end_month/start_month より優先）
        end_date: 対象期間の終了日（YYYY-MM-DD形式）
        with_sub_accounts: 補助科目の金額を取得するか（True/False）
        include_tax: 税込で算出するか（True/False、「税抜（内税）」の場合のみ指定可能）
        journal_types: 対象の仕訳種別（"adjusting_entry" で決算整理仕訳を含める）
        """
        params = {}
        if fiscal_year:
            params["fiscal_year"] = fiscal_year
        if start_month:
            params["start_month"] = start_month
        if end_month:
            params["end_month"] = end_month
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if with_sub_accounts is not None:
            params["with_sub_accounts"] = str(with_sub_accounts).lower()
        if include_tax is not None:
            params["include_tax"] = str(include_tax).lower()
        if journal_types:
            params["journal_types"] = journal_types
        qs = urllib.parse.urlencode(params)
        endpoint = f"/reports/trial_balance_{report_type}"
        if qs:
            endpoint += f"?{qs}"
        return self._api_request("GET", endpoint)

    def get_transition(self, fiscal_year=None, start_month=None, end_month=None,
                      with_sub_accounts=None, include_tax=None, report_type="pl"):
        """推移表取得（各月の単月値）。

        試算表との違い:
          試算表 = 期首からの累計（決算書向け）
          推移表 = 各月の単月値（月別推移分析向け）

        report_type: "pl"（損益計算書）または "bs"（貸借対照表）
        fiscal_year: 会計年度
        start_month: 集計開始月（1-12、fiscal_year と組み合わせて使用）
        end_month: 集計終了月（1-12）
        with_sub_accounts: 補助科目の金額を取得するか（True/False）
        include_tax: 税込で算出するか（True/False）
        """
        params = {"type": "monthly"}  # 必須パラメータ
        if fiscal_year:
            params["fiscal_year"] = fiscal_year
        if start_month:
            params["start_month"] = start_month
        if end_month:
            params["end_month"] = end_month
        if with_sub_accounts is not None:
            params["with_sub_accounts"] = str(with_sub_accounts).lower()
        if include_tax is not None:
            params["include_tax"] = str(include_tax).lower()
        qs = urllib.parse.urlencode(params)
        endpoint = f"/reports/transition_{report_type}"
        if qs:
            endpoint += f"?{qs}"
        return self._api_request("GET", endpoint)

    # -------------------------
    # マスター情報
    # -------------------------

    def get_accounts(self, available_only=True):
        """勘定科目一覧"""
        qs = urllib.parse.urlencode({"available": str(available_only).lower()})
        return self._api_request("GET", f"/accounts?{qs}")

    def get_sub_accounts(self, account_id=None):
        """補助科目一覧。account_id を指定すると特定科目の補助科目のみ返す。"""
        qs = urllib.parse.urlencode({"account_id": account_id}) if account_id else ""
        return self._api_request("GET", f"/sub_accounts?{qs}" if qs else "/sub_accounts")

    def get_taxes(self, available_only=True):
        """税区分一覧"""
        qs = urllib.parse.urlencode({"available": str(available_only).lower()})
        return self._api_request("GET", f"/taxes?{qs}")

    def get_departments(self):
        """部門一覧"""
        return self._api_request("GET", "/departments")

    def get_partners(self, available_only=True):
        """取引先一覧"""
        qs = urllib.parse.urlencode({"available": str(available_only).lower()})
        return self._api_request("GET", f"/trade_partners?{qs}")

    def create_partner(self, data):
        """取引先作成。

        data形式:
          {
            "name": "取引先名",           # 必須
            "search_key": "検索キー",      # 省略可
            "company_id": "<会社ID>",      # 省略可
            "memo": "備考"                 # 省略可
          }
        """
        return self._api_request("POST", "/trade_partners", data)

    def get_connected_accounts(self):
        """連携サービス一覧取得"""
        return self._api_request("GET", "/connected_accounts")

    def create_transaction(self, data):
        """取引作成（自動仕訳生成）。

        data形式は OpenAPI 仕様を参照してください。
        POST /transactions エンドポイント参照。
        """
        return self._api_request("POST", "/transactions", data)

    def create_voucher(self, data):
        """証憑作成。

        data形式は OpenAPI 仕様を参照してください。
        POST /vouchers エンドポイント参照。
        """
        return self._api_request("POST", "/vouchers", data)

    def delete_voucher(self, voucher_id):
        """証憑削除。

        data形式は OpenAPI 仕様を参照してください。
        DELETE /vouchers エンドポイント参照。
        """
        return self._api_request("DELETE", "/vouchers", {"id": voucher_id})

    # -------------------------
    # ユーティリティ（自動フェッチ・バッチ・エクスポート）
    # -------------------------

    def get_all_journals(self, from_date=None, to_date=None, account_id=None, is_realized=None, limit=100):
        """仕訳を全件取得（ページネーション自動処理）。

        **参考**: 大量データ取得時は時間がかかります。利用に注意。
        """
        all_journals = []
        page = 1
        while True:
            result = self.list_journals(
                limit=limit, from_date=from_date, to_date=to_date,
                page=page, account_id=account_id, is_realized=is_realized
            )
            if not result:
                break
            journals = result if isinstance(result, list) else result.get("journals", [])
            all_journals.extend(journals)

            # ページネーション確認
            if isinstance(result, dict) and "pagination" in result:
                pagination = result["pagination"]
                total = pagination.get("total_count", 0)
                if len(all_journals) >= total:
                    break
            else:
                break
            page += 1

        return all_journals

    def delete_journals_batch(self, journal_ids):
        """仕訳をバッチ削除（複数仕訳を順次削除）。

        Returns: (成功数, 失敗数, エラー詳細)
        """
        success_count = 0
        failure_count = 0
        errors = []

        for jid in journal_ids:
            try:
                result = self.delete_journal(jid)
                if result is not None:
                    success_count += 1
                else:
                    failure_count += 1
                    errors.append(f"{jid}: 削除失敗")
            except Exception as e:
                failure_count += 1
                errors.append(f"{jid}: {str(e)}")

        return success_count, failure_count, errors

    def to_csv(self, data, output_file=None):
        """データを CSV 形式でエクスポート。

        Args:
            data: 辞書のリスト（仕訳一覧など）
            output_file: 出力ファイルパス（None の場合はコンソール出力）
        """
        if not data or not isinstance(data, list) or not data[0]:
            print("Error: CSV エクスポート対象データが空です", file=sys.stderr)
            return None

        import csv
        from io import StringIO

        keys = data[0].keys() if isinstance(data[0], dict) else []
        if not keys:
            print("Error: データの構造が不正です", file=sys.stderr)
            return None

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())
            print(f"✅ CSV エクスポート: {output_file}")
        else:
            print(output.getvalue())

        return output.getvalue()

    def to_json_export(self, data, output_file=None, pretty=True):
        """データを JSON 形式でエクスポート。"""
        json_str = json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"✅ JSON エクスポート: {output_file}")
        else:
            print(json_str)

        return json_str


# -------------------------
# 表示ヘルパー
# -------------------------

def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_table(data, keys):
    if not isinstance(data, list) or not data:
        print("(No data)")
        return
    widths = [max(len(k), max((len(str(item.get(k, ""))) for item in data), default=0)) for k in keys]
    header = " | ".join(k.ljust(w) for k, w in zip(keys, widths))
    print(header)
    print("-" * len(header))
    for item in data:
        print(" | ".join(str(item.get(k, "")).ljust(w) for k, w in zip(keys, widths)))


# -------------------------
# CLI エントリーポイント
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="mf-cli: マネーフォワード クラウド会計 CLI",
        prog="python3 mf.py"
    )
    sub = parser.add_subparsers(dest="command")

    # auth
    auth_p = sub.add_parser("auth", help="認証コマンド")
    auth_s = auth_p.add_subparsers(dest="auth_cmd")
    auth_s.add_parser("setup", help="Client ID / Secret を設定")
    auth_s.add_parser("login", help="OAuth ログイン")
    auth_s.add_parser("status", help="認証状態確認")

    # tenant
    tenant_p = sub.add_parser("tenant", help="事業者コマンド")
    tenant_s = tenant_p.add_subparsers(dest="tenant_cmd")
    info_t = tenant_s.add_parser("info", help="事業者情報取得")
    info_t.add_argument("--json", action="store_true", help="JSON形式で出力")

    # journal
    journal_p = sub.add_parser("journal", help="仕訳コマンド")
    journal_s = journal_p.add_subparsers(dest="journal_cmd")
    list_j = journal_s.add_parser("list", help="仕訳一覧")
    list_j.add_argument("--limit", type=int, default=50)
    list_j.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    list_j.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    list_j.add_argument("--page", type=int, default=1)
    list_j.add_argument("--account-id", dest="account_id", help="勘定科目ID でフィルタ")
    list_j.add_argument("--is-realized", dest="is_realized", choices=["true", "false"], help="実現/未実現フィルタ")
    list_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    get_j = journal_s.add_parser("get", help="仕訳取得")
    get_j.add_argument("id", help="仕訳ID")
    get_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    create_j = journal_s.add_parser("create", help="仕訳作成")
    create_j.add_argument("--data", help="JSON データ（文字列）")
    create_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    update_j = journal_s.add_parser("update", help="仕訳更新（全置換）")
    update_j.add_argument("id", help="仕訳ID")
    update_j.add_argument("--data", help="JSON データ（文字列）")
    update_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    delete_j = journal_s.add_parser("delete", help="仕訳削除")
    delete_j.add_argument("id", help="仕訳ID")
    delete_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    list_all_j = journal_s.add_parser("list-all", help="仕訳全件取得（ページネーション自動処理）")
    list_all_j.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    list_all_j.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    list_all_j.add_argument("--json", action="store_true", help="JSON形式で出力")
    export_j = journal_s.add_parser("export", help="仕訳エクスポート（CSV/JSON）")
    export_j.add_argument("--from", dest="from_date", metavar="YYYY-MM-DD")
    export_j.add_argument("--to", dest="to_date", metavar="YYYY-MM-DD")
    export_j.add_argument("--format", choices=["csv", "json"], default="json", help="エクスポート形式")
    export_j.add_argument("--output", "-o", metavar="FILE", help="出力ファイル")
    batch_delete_j = journal_s.add_parser("batch-delete", help="仕訳バッチ削除")
    batch_delete_j.add_argument("--ids", help="削除対象のID（カンマ区切り）")
    batch_delete_j.add_argument("--from-file", help="ID リストファイル（1行1ID）")

    # report
    report_p = sub.add_parser("report", help="帳票コマンド")
    report_s = report_p.add_subparsers(dest="report_cmd")
    tb = report_s.add_parser("trial-balance", help="残高試算表（累計）")
    tb.add_argument("--type", dest="report_type", default="pl", choices=["pl", "bs"])
    tb.add_argument("--year", type=int)
    tb.add_argument("--start-month", type=int, help="集計開始月（1-12）")
    tb.add_argument("--month", type=int, help="集計終了月（1-12）")
    tb.add_argument("--start-date", metavar="YYYY-MM-DD", help="対象期間の開始日")
    tb.add_argument("--end-date", metavar="YYYY-MM-DD", help="対象期間の終了日")
    tb.add_argument("--with-sub-accounts", dest="with_sub_accounts", action="store_true", help="補助科目を含める")
    tb.add_argument("--include-tax", dest="include_tax", action="store_true", help="税込で算出")
    tb.add_argument("--journal-types", help="仕訳種別（adjusting_entry で決算整理含む）")
    tb.add_argument("--json", action="store_true", help="JSON形式で出力")
    tr = report_s.add_parser("transition", help="推移表（単月）")
    tr.add_argument("--type", dest="report_type", default="pl", choices=["pl", "bs"])
    tr.add_argument("--year", type=int)
    tr.add_argument("--start-month", type=int, help="集計開始月（1-12）")
    tr.add_argument("--month", type=int, help="集計終了月（1-12）")
    tr.add_argument("--with-sub-accounts", dest="with_sub_accounts", action="store_true", help="補助科目を含める")
    tr.add_argument("--include-tax", dest="include_tax", action="store_true", help="税込で算出")
    tr.add_argument("--json", action="store_true", help="JSON形式で出力")

    # master
    master_p = sub.add_parser("master", help="マスター情報コマンド")
    master_s = master_p.add_subparsers(dest="master_cmd")
    for master_cmd in [
        master_s.add_parser("accounts", help="勘定科目"),
        master_s.add_parser("sub-accounts", help="補助科目"),
        master_s.add_parser("taxes", help="税区分"),
        master_s.add_parser("departments", help="部門"),
        master_s.add_parser("partners", help="取引先"),
        master_s.add_parser("connected-accounts", help="連携サービス"),
    ]:
        master_cmd.add_argument("--json", action="store_true", help="JSON形式で出力")

    # グローバルオプション（master コマンドのみ - 他はsubcommandで個別追加）
    for p in [parser, master_p]:
        p.add_argument("--json", action="store_true", help="JSON形式で出力")

    args = parser.parse_args()
    client = MFClient()

    if args.command == "auth":
        if args.auth_cmd == "setup":
            client.setup()
        elif args.auth_cmd == "login":
            client.login()
        elif args.auth_cmd == "status":
            client.status()
        else:
            auth_p.print_help()

    elif args.command == "tenant":
        if args.tenant_cmd == "info":
            result = client.get_office()
            if result:
                if args.json:
                    print_json(result)
                else:
                    print(f"Name:    {result.get('name')}")
                    print(f"ID:      {result.get('id')}")
                    periods = result.get("accounting_periods", [])
                    if periods:
                        p = periods[0]
                        print(f"FY:      {p.get('fiscal_year')} ({p.get('start_date')} ~ {p.get('end_date')})")
        else:
            tenant_p.print_help()

    elif args.command == "journal":
        if args.journal_cmd == "list":
            is_realized = None
            if args.is_realized:
                is_realized = args.is_realized.lower() == "true"
            result = client.list_journals(
                limit=args.limit,
                from_date=args.from_date,
                to_date=args.to_date,
                page=args.page,
                account_id=args.account_id,
                is_realized=is_realized
            )
            if result:
                journals = result.get("journals", result) if isinstance(result, dict) else result
                if args.json:
                    print_json(result)
                else:
                    print_table(journals, ["id", "transaction_date", "memo"])
                    if isinstance(result, dict) and "pagination" in result:
                        pg = result["pagination"]
                        print(f"\n{pg.get('page')}/{-(-pg.get('total_count', 0) // args.limit)} ページ "
                              f"（全{pg.get('total_count')}件）")
        elif args.journal_cmd == "get":
            result = client.get_journal(args.id)
            if result:
                print_json(result)
        elif args.journal_cmd == "create":
            if not args.data:
                print("Error: --data に JSON データを指定してください", file=sys.stderr)
                sys.exit(1)
            data = json.loads(args.data)
            result = client.create_journal(data)
            if result:
                print_json(result)
        elif args.journal_cmd == "update":
            if not args.data:
                print("Error: --data に JSON データを指定してください", file=sys.stderr)
                sys.exit(1)
            data = json.loads(args.data)
            result = client.update_journal(args.id, data)
            if result:
                print_json(result)
        elif args.journal_cmd == "delete":
            result = client.delete_journal(args.id)
            if result:
                print_json(result) if args.json else print(get_message("delete_success"))
        elif args.journal_cmd == "list-all":
            print("⏳ 全仕訳を取得中（時間がかかる可能性があります）...", file=sys.stderr)
            result = client.get_all_journals(from_date=args.from_date, to_date=args.to_date)
            if result:
                print(f"✅ {len(result)}件取得", file=sys.stderr)
                if args.json:
                    print_json(result)
                else:
                    print_table(result, ["id", "transaction_date", "memo"])
        elif args.journal_cmd == "export":
            print("⏳ 仕訳を取得中...", file=sys.stderr)
            result = client.get_all_journals(from_date=args.from_date, to_date=args.to_date)
            if result:
                if args.format == "csv":
                    client.to_csv(result, output_file=args.output)
                else:
                    client.to_json_export(result, output_file=args.output)
        elif args.journal_cmd == "batch-delete":
            ids = []
            if args.ids:
                ids = [id.strip() for id in args.ids.split(",")]
            elif args.from_file:
                with open(args.from_file, 'r') as f:
                    ids = [line.strip() for line in f if line.strip()]
            if not ids:
                print("Error: --ids または --from-file を指定してください", file=sys.stderr)
                sys.exit(1)
            success, failure, errors = client.delete_journals_batch(ids)
            print(f"結果: 成功 {success}件, 失敗 {failure}件")
            if errors:
                print("エラー詳細:")
                for err in errors:
                    print(f"  - {err}")
        else:
            journal_p.print_help()

    elif args.command == "report":
        if args.report_cmd == "trial-balance":
            result = client.get_trial_balance(
                fiscal_year=args.year,
                start_month=args.start_month,
                end_month=args.month,
                start_date=args.start_date,
                end_date=args.end_date,
                with_sub_accounts=args.with_sub_accounts if args.with_sub_accounts else None,
                include_tax=args.include_tax if args.include_tax else None,
                journal_types=args.journal_types,
                report_type=args.report_type
            )
            if result:
                if args.json:
                    print_json(result)
                else:
                    rows = result.get("rows", [])
                    print_table(rows, ["account_name", "fs_type"])
        elif args.report_cmd == "transition":
            result = client.get_transition(
                fiscal_year=args.year,
                start_month=args.start_month,
                end_month=args.month,
                with_sub_accounts=args.with_sub_accounts if args.with_sub_accounts else None,
                include_tax=args.include_tax if args.include_tax else None,
                report_type=args.report_type
            )
            if result:
                if args.json:
                    print_json(result)
                else:
                    rows = result.get("rows", [])
                    print_table(rows, ["account_name", "fs_type"])
        else:
            report_p.print_help()

    elif args.command == "master":
        result = None
        keys = ["id", "name"]
        if args.master_cmd == "accounts":
            result = client.get_accounts()
        elif args.master_cmd == "sub-accounts":
            result = client.get_sub_accounts()
        elif args.master_cmd == "taxes":
            result = client.get_taxes()
        elif args.master_cmd == "departments":
            result = client.get_departments()
        elif args.master_cmd == "partners":
            result = client.get_partners()
            keys = ["id", "name", "search_key"]
        elif args.master_cmd == "connected-accounts":
            result = client.get_connected_accounts()
            keys = ["id", "name"]
        else:
            master_p.print_help()
            return

        if result is not None:
            items = result if isinstance(result, list) else result.get("data", result.get("items", [result]))
            if args.json:
                print_json(result)
            else:
                print_table(items if isinstance(items, list) else [], keys)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
