#!/usr/bin/env python3
"""mf-cli オフラインテスト（API 非接続）

urllib.request.urlopen / MFClient._api_request をモックし、
リクエスト組み立て・ラップ処理・リトライ・新コマンドの挙動を検証する。

実行:
  cd plugins/mf-cli && python3 -m unittest discover tests -v
"""
import base64
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "scripts"))
import mf  # noqa: E402


def make_client():
    """認証済み状態のクライアントをディスクに触れず生成"""
    with mock.patch.object(mf.MFClient, "_load_config", return_value={"client_id": "cid", "client_secret": "sec"}), \
         mock.patch.object(mf.MFClient, "_load_tokens", return_value={"access_token": "tok", "refresh_token": "ref", "expires_at": 9999999999}), \
         mock.patch("os.makedirs"):
        return mf.MFClient()


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestApiRequest(unittest.TestCase):
    """_api_request のリクエスト組み立てとエラー処理"""

    def test_get_builds_bearer_request(self):
        client = make_client()
        captured = {}

        def fake_urlopen(req):
            captured["url"] = req.full_url
            captured["auth"] = req.get_header("Authorization")
            captured["method"] = req.get_method()
            return FakeResponse(b'{"ok": true}')

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            result = client._api_request("GET", "/accounts?available=true")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(captured["url"], f"{mf.MF_ACCOUNTING_API}/accounts?available=true")
        self.assertEqual(captured["auth"], "Bearer tok")
        self.assertEqual(captured["method"], "GET")

    def test_429_retries_three_times_then_gives_up(self):
        client = make_client()
        calls = []

        def fake_urlopen(req):
            calls.append(1)
            raise mf.urllib.error.HTTPError(req.full_url, 429, "Too Many", {}, io.BytesIO(b"{}"))

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             mock.patch("time.sleep"):
            result = client._api_request("GET", "/accounts")
        self.assertIsNone(result)
        self.assertEqual(len(calls), 4)  # 初回 + リトライ3回

    def test_401_triggers_refresh_and_retry_once(self):
        client = make_client()
        calls = []

        def fake_urlopen(req):
            calls.append(1)
            if len(calls) == 1:
                raise mf.urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"{}"))
            return FakeResponse(b'{"ok": true}')

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
             mock.patch.object(client, "_refresh_access_token", return_value=True):
            result = client._api_request("GET", "/accounts")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(calls), 2)


class TestJournalWrap(unittest.TestCase):
    """仕訳 create/update の {"journal": {...}} 自動ラップ（v1.3.0 の中核仕様）"""

    def test_create_wraps_bare_journal(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={"journal": {"id": "x"}}) as api:
            client.create_journal({"transaction_date": "2026-06-30", "branches": []})
        api.assert_called_once_with(
            "POST", "/journals",
            {"journal": {"transaction_date": "2026-06-30", "branches": []}})

    def test_create_keeps_existing_wrap(self):
        client = make_client()
        data = {"journal": {"transaction_date": "2026-06-30"}}
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.create_journal(data)
        api.assert_called_once_with("POST", "/journals", data)

    def test_update_wraps_and_encodes_id(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.update_journal("abc/+=", {"memo": "m"})
        method, endpoint, payload = api.call_args[0]
        self.assertEqual(method, "PUT")
        self.assertTrue(endpoint.startswith("/journals/"))
        self.assertNotIn("/journals/abc/+=", endpoint)  # ID は URL エンコードされる
        self.assertEqual(payload, {"journal": {"memo": "m"}})


class TestPartnerCreate(unittest.TestCase):
    """取引先作成: {"trade_partners": [...]} への自動ラップ"""

    def test_single_object_is_wrapped_into_list(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.create_partner({"name": "テスト商事"})
        api.assert_called_once_with(
            "POST", "/trade_partners", {"trade_partners": [{"name": "テスト商事"}]})

    def test_list_is_wrapped(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.create_partner([{"name": "A"}, {"name": "B"}])
        api.assert_called_once_with(
            "POST", "/trade_partners", {"trade_partners": [{"name": "A"}, {"name": "B"}]})

    def test_existing_wrap_passthrough(self):
        client = make_client()
        data = {"trade_partners": [{"name": "A"}]}
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.create_partner(data)
        api.assert_called_once_with("POST", "/trade_partners", data)


class TestTransactionCreate(unittest.TestCase):
    """明細（取引）作成: 必須キーの事前検証"""

    def test_valid_data_passthrough(self):
        client = make_client()
        data = {"connected_account_id": "ca1", "transactions": [
            {"date": "2026-06-30", "value": 100, "side": "EXPENSE", "content": "c"}]}
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.create_transaction(data)
        api.assert_called_once_with("POST", "/transactions", data)

    def test_missing_required_keys_raises(self):
        client = make_client()
        with self.assertRaises(ValueError):
            client.create_transaction({"transactions": []})
        with self.assertRaises(ValueError):
            client.create_transaction({"connected_account_id": "ca1"})


class TestVoucher(unittest.TestCase):
    """証憑の添付・関連付け解除"""

    def test_create_from_files_encodes_base64(self):
        client = make_client()
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-fake")
            path = f.name
        try:
            with mock.patch.object(client, "_api_request", return_value={}) as api:
                client.create_voucher_from_files("j1", [path])
            method, endpoint, payload = api.call_args[0]
            self.assertEqual((method, endpoint), ("POST", "/vouchers"))
            self.assertEqual(payload["journal_id"], "j1")
            vf = payload["voucher_files"][0]
            self.assertEqual(vf["file_name"], os.path.basename(path))
            self.assertEqual(base64.b64decode(vf["file_data"]), b"%PDF-fake")
        finally:
            os.unlink(path)

    def test_delete_requires_both_ids(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={}) as api:
            client.delete_voucher("j1", "vf1")
        api.assert_called_once_with(
            "DELETE", "/vouchers", {"journal_id": "j1", "voucher_file_id": "vf1"})


class TestTermSettings(unittest.TestCase):
    """会計年度設定の取得（2026 追加の新エンドポイント）"""

    def test_get_term_settings(self):
        client = make_client()
        with mock.patch.object(client, "_api_request", return_value={"term_settings": []}) as api:
            result = client.get_term_settings()
        api.assert_called_once_with("GET", "/term_settings")
        self.assertEqual(result, {"term_settings": []})


class TestCli(unittest.TestCase):
    """CLI ディスパッチ（argparse → メソッド呼び出し）"""

    def _run(self, argv, method_name, return_value=None):
        with mock.patch.object(mf.MFClient, "__init__", return_value=None), \
             mock.patch.object(mf.MFClient, method_name, return_value=return_value or {"ok": True}) as m, \
             mock.patch.object(sys, "argv", ["mf.py"] + argv), \
             mock.patch("sys.stdout", new_callable=io.StringIO):
            mf.main()
        return m

    def test_partner_create_cli(self):
        m = self._run(["master", "partners", "create", "--data", '{"name": "X"}'], "create_partner")
        m.assert_called_once_with({"name": "X"})

    def test_txn_create_cli(self):
        data = '{"connected_account_id": "c", "transactions": []}'
        m = self._run(["txn", "create", "--data", data], "create_transaction")
        m.assert_called_once_with(json.loads(data))

    def test_voucher_delete_cli(self):
        m = self._run(["voucher", "delete", "--journal-id", "j1", "--voucher-file-id", "v1"], "delete_voucher")
        m.assert_called_once_with("j1", "v1")

    def test_tenant_terms_cli(self):
        m = self._run(["tenant", "terms", "--json"], "get_term_settings",
                      return_value={"term_settings": []})
        m.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
