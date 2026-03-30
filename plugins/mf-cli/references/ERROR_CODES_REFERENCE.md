# mf-cli エラーコード リファレンス

**対象**: MoneyForward Cloud Accounting REST API v3
**最終更新**: 2026-03-30

---

## 概要

このドキュメントは、mf-cli コマンド実行時に発生する可能性があるエラーコードと、その解決方法を体系化した参考資料です。

---

## HTTP ステータスコード別リファレンス

### 4xx クライアントエラー

#### 400 Bad Request

**原因**: リクエストのパラメータ形式が不正

**メッセージ例**:
```
400 Bad Request: Invalid parameter format
Bad request: journals.0.transaction_date is required
```

**解決方法**:
1. **日付フォーマト確認**: `--from`, `--to` は `YYYY-MM-DD` 形式か確認
   ```bash
   # ❌ 間違い
   python3 scripts/mf.py journal list --from 2026/03/30

   # ✅ 正しい
   python3 scripts/mf.py journal list --from 2026-03-30
   ```

2. **JSON データ形式確認**: `--data` の JSON は有効か確認
   ```bash
   # ❌ JSON が不正
   python3 scripts/mf.py journal create --data '{invalid json}'

   # ✅ JSON validator で確認
   echo '{"transaction_date": "2026-03-30"}' | jq .
   ```

3. **必須パラメータ確認**: エラーメッセージで指定されたフィールドが含まれているか確認

---

#### 401 Unauthorized

**原因**: 認証トークンが無効または期限切れ

**メッセージ例**:
```
401 Unauthorized: Invalid access token
Invalid access token or insufficient scopes
```

**解決方法**:

**Step 1**: トークン更新を試す
```bash
python3 scripts/mf.py auth login
# ブラウザで再度認可
```

**Step 2**: トークンファイルの確認
```bash
ls -la ~/.mf-cli/tokens.json
# 存在しない場合は認証設定から開始
python3 scripts/mf.py auth setup
```

**Step 3**: 環境変数確認
```bash
# 以下が設定されているか確認
echo $MF_CLIENT_ID
echo $MF_CLIENT_SECRET
```

**Step 4**: トークンリフレッシュが失敗している場合
```bash
# トークンキャッシュをクリア
rm ~/.mf-cli/tokens.json

# 再度ログイン
python3 scripts/mf.py auth login
```

**多発する場合**:
- **セキュリティ**: クライアントシークレットが外部に漏洩していないか確認
- **スコープ不足**: App Portal でユーザー権限が有効化されているか確認（`アプリ連携`, `事業者情報`, `クラウド会計・確定申告`）
- **環境**: CI/CD パイプラインではトークンの自動リフレッシュが無効化されている可能性あり

---

#### 403 Forbidden

**原因**: ユーザーまたは事業者に対する権限不足

**メッセージ例**:
```
403 Forbidden: The office being accessed does not have sufficient permissions
insufficient_permissions: This account does not have permission to access accounting API
```

**解決方法**:

| シナリオ | 確認項目 | 対応 |
|--------|--------|------|
| **すべてのAPI呼び出しが 403** | MoneyForward プラン | SKILL.md に「Plus プラン以上」と明記。プランアップグレード検討 |
| 特定の操作（`journal delete` など）が 403 | OAuth スコープ | `mfc/accounting/journal.write` スコープが有効か App Portal で確認 |
| 取引先・証憑作成が 403 | OAuth スコープ + 権限 | `mfc/accounting/trade_partners.write`, `mfc/accounting/voucher.write` を確認 |
| 新しいトークンでも 403 | キャッシュ | `MF_NO_CACHE=1 python3 scripts/mf.py <コマンド>` で再試行 |

**詳細チェックリスト**:
```bash
# 1. 認証状態確認
python3 scripts/mf.py auth status

# 2. 事業者情報取得テスト
python3 scripts/mf.py tenant info --json

# 3. 特定エンドポイントテスト
python3 scripts/mf.py journal list --limit 1 --json

# 4. キャッシュ無効で再試行
MF_NO_CACHE=1 python3 scripts/mf.py journal list --limit 1 --json
```

---

#### 404 Not Found

**原因**: 指定したリソース ID が見つからない

**メッセージ例**:
```
404 Not Found: Journal with id 'abc123xyz' not found
```

**解決方法**:

1. **ID が正しいか確認**
   ```bash
   # 仕訳一覧から ID を確認
   python3 scripts/mf.py journal list --json | jq -r '.journals[] | .id' | head -5

   # その ID で取得テスト
   python3 scripts/mf.py journal get <id> --json
   ```

2. **ID がすでに削除されていないか確認**
   ```bash
   # 仕訳一覧で対象期間を確認
   python3 scripts/mf.py journal list --from 2026-03-01 --to 2026-03-31 --json | jq '.journals[] | select(.id == "<id>")'
   ```

3. **ワイルドカード検索**
   ```bash
   # IDの一部で検索（jqで）
   python3 scripts/mf.py journal list --json | jq '.journals[] | select(.id | contains("部分ID"))'
   ```

---

#### 429 Too Many Requests

**原因**: API レート制限に達した

**メッセージ例**:
```
429 Too Many Requests: Rate limit exceeded
Retry-After: 60
```

**解決方法**:

**自動リトライ** (mf-cli は指数バックオフで自動処理):
```python
# 内部実装: 1秒 → 2秒 → 4秒で自動リトライ
# 環境変数で最大リトライ回数を変更可能
export MF_CLI_RETRY=5
python3 scripts/mf.py journal list --limit 1000
```

**手動回避**:
```bash
# 遅延を入れてバッチ処理
python3 scripts/mf.py journal list --limit 50 --json | \
  jq -r '.journals[].id' | while read id; do
  python3 scripts/mf.py journal delete "$id"
  sleep 2  # 2秒待機
done
```

**API レート制限ポリシー**:
- **一般的な制限**: 1分あたり 1,000 リクエスト
- **バッチ処理**: 1秒あたり 10 リクエスト以下を推奨
- **超過時の対応**: 指数バックオフまたはセマフォで調整

---

### 5xx サーバーエラー

#### 500 Internal Server Error

**原因**: MoneyForward API サーバー側のエラー

**メッセージ例**:
```
500 Internal Server Error: An unexpected error occurred
```

**解決方法**:

1. **一時的なエラーの可能性**: 数分待機して再実行
   ```bash
   sleep 60
   python3 scripts/mf.py journal list --limit 1
   ```

2. **ステータスページ確認**: MoneyForward 開発者ポータルでサービス状態を確認
   - https://developers.biz.moneyforward.com/

3. **特定データ関連の問題**: 異なるパラメータで試行
   ```bash
   # 日付範囲を狭める
   python3 scripts/mf.py journal list --from 2026-03-30 --to 2026-03-30 --json
   ```

4. **Support に報告**: 再現手順を含めて MoneyForward サポートに報告

---

#### 503 Service Unavailable

**原因**: サーバーがメンテナンス中またはオーバーロード

**メッセージ例**:
```
503 Service Unavailable: Service temporarily unavailable
Retry-After: 300
```

**解決方法**:

1. **待機**: `Retry-After` ヘッダーで指定された時間待機
   ```bash
   # 300秒（5分）待機
   sleep 300
   python3 scripts/mf.py journal list
   ```

2. **ステータスページ確認**: メンテナンス情報を確認

3. **リトライスケジューリング**: 定期ジョブの場合は遅延実行
   ```bash
   # crontab で遅延実行
   # * * * * * sleep 600 && python3 /path/to/backup.sh
   ```

---

## カテゴリ別トラブルシューティング

### 認証関連

| エラー | 原因 | 解決 |
|--------|------|------|
| `No authentication config found` | 認証が未設定 | `python3 scripts/mf.py auth setup` を実行 |
| `InvalidClientId` | Client ID が誤り | `python3 scripts/mf.py auth setup` で再入力 |
| `unauthorized` | トークン期限切れ | `python3 scripts/mf.py auth login` で再ログイン |
| Browser が起動しない | システム設定 | macOS: セキュリティ設定確認 / Linux: `BROWSER=firefox` 設定 |

### API 呼び出し関連

| エラー | 原因 | 解決 |
|--------|------|------|
| `bad_request` | パラメータ形式不正 | JSON フォーマット、日付形式を確認 |
| `not_found` | リソース ID が無い | ID が正しいか再確認 |
| `rate_limit_exceeded` | API レート制限 | 自動リトライ（待機）またはバッチ処理遅延 |
| `insufficient_permissions` | 権限不足 | プラン確認、スコープ確認、新トークン取得 |

### 出力関連

| エラー | 原因 | 解決 |
|--------|------|------|
| `JSON parse error` | `--json` で JSON 以外が出力 | エラー前のメッセージを確認 |
| CSV エクスポート失敗 | ファイル書き込み権限 | `-o` で指定したディレクトリの権限確認 |
| 文字化け | 文字コード不一致 | `--json` で JSON 出力、jq で処理 |

---

## デバッグモード

### 詳細ログ有効化

```bash
# デバッグ出力の有効化
export MF_CLI_DEBUG=1
python3 scripts/mf.py journal list --limit 1 --json

# 詳細エラーメッセージ
export MF_CLI_VERBOSE=1
python3 scripts/mf.py auth login
```

### トークンの確認

```bash
# トークンファイルの内容確認
cat ~/.mf-cli/tokens.json | jq .

# トークンの有効期限確認
python3 scripts/mf.py auth status --json | jq '.expires_in'
```

### キャッシュの確認・クリア

```bash
# キャッシュなしで実行（検証用）
MF_NO_CACHE=1 python3 scripts/mf.py journal list --limit 1

# キャッシュ TTL の変更
export MF_CACHE_TTL=0  # キャッシュ無効
python3 scripts/mf.py journal list
```

---

## FAQ: よくある質問

### Q1: 「insufficient_permissions」が出続ける

**A**: 以下の順で確認：
1. MoneyForward プラン（Plus 以上が必須）
2. App Portal の user permission（`アプリ連携` をチェック）
3. `python3 scripts/mf.py auth login` で新しいトークン取得
4. 効かない場合は MoneyForward Support に確認

### Q2: 特定の仕訳だけ削除できない（404）

**A**:
- 仕訳一覧から存在確認: `python3 scripts/mf.py journal list --json | jq '.journals[] | select(.id == "...")'`
- 期日経過で削除不可になっていないか確認
- 同期中の仕訳でないか確認

### Q3: バッチ削除が途中で止まる

**A**:
- ネットワーク接続確認
- 個別削除でどれが失敗するか特定: `python3 scripts/mf.py journal delete <id>` で1つずつ試行
- `MF_CLI_RETRY` を増やす: `export MF_CLI_RETRY=5`

### Q4: CSV/JSON エクスポートが文字化けする

**A**:
- CSV 出力はデフォルトで UTF-8（Excel で開く時は「Unicode (UTF-8)」を指定）
- JSON は `--json` + `jq` での処理を推奨
- PowerShell (Windows) の場合: `chcp 65001` で UTF-8 コードページに変更

---

## トラブルシューティングツール

### ワンライナーテスト

```bash
# 認証テスト
python3 scripts/mf.py auth status && echo "✅ Auth OK"

# API 接続テスト
python3 scripts/mf.py journal list --limit 1 && echo "✅ API OK"

# パーミッションテスト（write）
python3 scripts/mf.py journal list --limit 1 | head -1 && echo "✅ Read OK"

# キャッシュテスト
time python3 scripts/mf.py journal list --limit 1 > /dev/null  # 1回目（キャッシュなし）
time python3 scripts/mf.py journal list --limit 1 > /dev/null  # 2回目（キャッシュ命中）
```

### 完全診断スクリプト

```bash
#!/bin/bash
echo "🔍 mf-cli 診断開始"
echo "---"

echo "1. 認証状態"
python3 scripts/mf.py auth status --json | jq '.status'

echo "2. 事業者情報"
python3 scripts/mf.py tenant info --json 2>&1 | head -3

echo "3. 環境変数"
echo "  CLIENT_ID: ${MF_CLIENT_ID:0:10}***"
echo "  DEBUG: ${MF_CLI_DEBUG:-off}"
echo "  CACHE_TTL: ${MF_CACHE_TTL:-300}"

echo "4. トークンファイル"
ls -lh ~/.mf-cli/tokens.json 2>/dev/null || echo "  トークンファイルなし（再ログインが必要）"

echo "---"
echo "診断完了"
```

---

## 参考資料

- **SKILL.md Troubleshooting**: SKILL.md の Troubleshooting セクション参照
- **公式 API 仕様**: https://developers.api-accounting.moneyforward.com/
- **MoneyForward Support**: https://support.moneyforward.com/
