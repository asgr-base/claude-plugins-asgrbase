---
name: mf-cli
description: マネーフォワード クラウド会計をCLIで操作する。仕訳の登録・取得、試算表・帳票の取得、マスター情報の参照ができます。OAuth認証によるセキュアなAPI操作に対応。アプリ登録から初回ログイン、日常操作まで、マネーフォワード会計APIとの統合が必要な場面で使用してください。
version: 1.4.0
author: claude_code
createDate: 2026-03-27
updateDate: 2026-07-04
license: MIT
---

# mf-cli — マネーフォワード クラウド会計 CLI

マネーフォワード クラウド会計のAPIをコマンドラインから操作するスキル。OAuth 2.0認証でセキュアに仕訳・帳票・マスター情報を取得・操作できます。

**完全性**: エンドポイント 20/20 (100%) | テスト合格率 100% | OpenAPI 仕様準拠

---

## Prerequisites（前提条件）

- **Python 3.8以上**
- **マネーフォワード クラウド会計アカウント** (Plus プラン以上)
- **アプリ登録済み** (Client ID・Secret 保有)
- **OAuth認可完了** (`python3 scripts/mf.py auth status` で確認)

⚠️ **初回セットアップ**: [初期セットアップガイド](#初期セットアップガイド) を参照

---

## Quick Reference

### Global Flags（全コマンド共通オプション）

| フラグ | 説明 | 使用例 |
|--------|------|--------|
| `--json` | JSON形式で出力 | `journal list --json` |
| `--from DATE` | 開始日付（YYYY-MM-DD） | `--from 2026-01-01` |
| `--to DATE` | 終了日付（YYYY-MM-DD） | `--to 2026-12-31` |
| `--limit N` | 件数上限 | `--limit 100` |
| `--help` | ヘルプ表示 | `journal --help` |

### Output Formats（出力形式）

| 形式 | コマンド | 用途 | 例 |
|-----|---------|------|-----|
| **テーブル形式** | デフォルト | 対話的な確認 | `journal list` |
| **JSON** | `--json` | パイプ処理・外部連携 | `journal list --json \| jq` |
| **CSV** | `journal export --format csv` | スプレッドシート等 | `-o journals.csv` |
| **バッチ処理** | `--ids id1,id2` | 複数リソース操作 | `batch-delete --ids id1,id2` |

---

## Common Patterns（実践的な使用例）

### 1. JSON 出力を jq でフィルタリング
```bash
# 2026年3月以降の仕訳を抽出
python3 scripts/mf.py journal list --json | \
  jq '.journals[] | select(.transaction_date > "2026-03-01")'

# 勘定科目 ID を一覧化
python3 scripts/mf.py master accounts --json | jq -r '.[] | .id'
```

### 2. 全仕訳を CSV エクスポート＆Excelで開く
```bash
python3 scripts/mf.py journal export --from 2026-01-01 --to 2026-12-31 \
  --format csv -o journals.csv

# macOS でそのまま開く
open journals.csv
```

### 3. Bash ループで複数仕訳を処理
```bash
# 全仕訳を取得してループ処理
python3 scripts/mf.py journal list-all --json | \
  jq -r '.[] | .id' | while read id; do
  echo "Processing $id..."
  python3 scripts/mf.py journal delete "$id"
done
```

### 4. 月別試算表を一括取得
```bash
# 2026年1月～12月の試算表を別ファイルに保存
for month in {1..12}; do
  python3 scripts/mf.py report trial-balance --type pl \
    --month $month --json > "tb_pl_2026_$month.json"
  echo "Generated: tb_pl_2026_$month.json"
done
```

### 5. 複数仕訳をファイルから削除
```bash
# ids.txt 作成（1行1ID）
cat > ids.txt << EOF
id1_here
id2_here
id3_here
EOF

# バッチ削除
python3 scripts/mf.py journal batch-delete --from-file ids.txt
```

### 6. 定期実行：毎月末に試算表をバックアップ
```bash
#!/bin/bash
# backup_monthly_reports.sh
BACKUP_DIR="~/mf-cli-backups/$(date +%Y-%m)"
mkdir -p "$BACKUP_DIR"

python3 scripts/mf.py report trial-balance --type pl --json > \
  "$BACKUP_DIR/trial_balance_pl.json"
python3 scripts/mf.py report trial-balance --type bs --json > \
  "$BACKUP_DIR/trial_balance_bs.json"

echo "✅ Backed up to $BACKUP_DIR"
```

---

## Commands by Category

### 認証コマンド

```bash
# 認証情報を設定
python3 scripts/mf.py auth setup

# ブラウザで OAuth 認可
python3 scripts/mf.py auth login

# 認証状態を確認
python3 scripts/mf.py auth status

# トークンを強制リフレッシュ（launchd/cron での定期更新用。アクセストークン期限前の予防更新）
python3 scripts/mf.py auth refresh
```

### 事業者コマンド

```bash
# 事業者情報を取得
python3 scripts/mf.py tenant info
python3 scripts/mf.py tenant info --json

# 会計年度設定一覧（開始日の降順。期間・都道府県・税方式・端数処理を返す）
python3 scripts/mf.py tenant terms --json
```

### 仕訳コマンド

| コマンド | 説明 | オプション |
|---------|------|----------|
| `journal list` | 仕訳一覧（フィルタ付き） | `--from` `--to` `--account-id` `--is-realized` `--limit` `--json` |
| `journal get <id>` | 仕訳取得（ID指定） | `--json` |
| `journal create` | 仕訳作成 | `--data <JSON>` `--json` |
| `journal update <id>` | 仕訳更新（全置換） | `--data <JSON>` `--resolve-names` `--json` |
| `journal delete <id>` | 仕訳削除 | `--json` |
| `journal list-all` | 全仕訳取得（自動ページネーション） | `--from` `--to` `--json` |
| `journal export` | CSV/JSON エクスポート | `--from` `--to` `--format csv/json` `-o FILE` |
| `journal batch-delete` | バッチ削除 | `--ids id1,id2` または `--from-file FILE` |

#### journal update / journal create の --data フォーマット

**必須フィールド**:

```json
{
  "transaction_date": "2026-03-31",
  "journal_type": "journal_entry",
  "branches": [
    {
      "debitor": {
        "account_id": "<科目ID>",
        "value": 10000
      },
      "creditor": {
        "account_id": "<科目ID>",
        "value": 10000
      },
      "remark": "行の摘要（省略可）"
    }
  ],
  "memo": "仕訳全体の摘要（省略可）"
}
```

> **⚠️ 注意事項**
> - `journal_type` は必須。`"journal_entry"`（通常仕訳）または `"adjusting_entry"`（決算整理仕訳）を指定
> - `invoice_kind` は**免税事業者には指定不可**（省略すること）
> - 複合仕訳で借方が存在しない行は、`"debitor"` キーごと省略すること（`null` を渡すと `--resolve-names` でエラー）
> - `journal update` は**全置換（PUT）**のため、変更しない行も含めて全行を渡すこと
> - 科目 ID が不明な場合は `--resolve-names` フラグで科目名・取引先名から自動解決できる

**`--resolve-names` を使った例（科目名で指定）**:

```bash
python3 scripts/mf.py journal update <id> --resolve-names --data '{
  "transaction_date": "2026-03-31",
  "journal_type": "journal_entry",
  "branches": [
    {
      "debitor": {
        "account_name": "地代家賃",
        "sub_account_name": "本社事務所",
        "trade_partner_name": "サンプル不動産",
        "value": 10000
      },
      "creditor": {
        "account_name": "普通預金",
        "sub_account_name": "サンプル銀行本店",
        "value": 10000
      },
      "remark": "地代家賃 2026年03月分"
    }
  ]
}'
```

### 帳票コマンド

```bash
# 試算表（PL）：2026年1月～3月、補助科目を含む
python3 scripts/mf.py report trial-balance --type pl --year 2026 \
  --start-month 1 --month 3 --with-sub-accounts --json

# 試算表（BS）：期首からの累計
python3 scripts/mf.py report trial-balance --type bs --json

# 推移表（月別単月値）
python3 scripts/mf.py report transition --type pl --json
```

### マスター情報コマンド

```bash
python3 scripts/mf.py master accounts            # 勘定科目
python3 scripts/mf.py master sub-accounts        # 補助科目
python3 scripts/mf.py master departments         # 部門
python3 scripts/mf.py master taxes               # 税区分
python3 scripts/mf.py master partners            # 取引先
python3 scripts/mf.py master connected-accounts  # 連携サービス

# JSON 形式で取得
python3 scripts/mf.py master accounts --json

# 取引先を作成（単一オブジェクト・リスト・{"trade_partners": [...]} ラップ済みのいずれも可）
python3 scripts/mf.py master partners create --data '{"name": "株式会社サンプル"}'
python3 scripts/mf.py master partners create --data @/tmp/partners.json
```

### 明細コマンド（自動仕訳生成の入力）

連携サービス口座に明細データを投入し、自動仕訳の入力にする（POST /transactions）。

```bash
# connected_account_id は master connected-accounts で取得
python3 scripts/mf.py txn create --data '{
  "connected_account_id": "<連携サービスID>",
  "transactions": [
    {"date": "2026-06-30", "value": 100, "side": "EXPENSE", "content": "内容", "memo": "備考"}
  ]
}'
```

- `side` は `INCOME` / `EXPENSE`
- `transactions` は最大 1000 件
- `connected_account_id` と `transactions` が無い場合は API 送信前に検証エラーになる

### 証憑コマンド

仕訳に証憑ファイル（領収書 PDF 等）を添付・添付解除する。電子帳簿保存法対応の証跡管理に使用。

```bash
# 仕訳に証憑を添付（ファイルは自動で base64 変換。--file は複数指定可）
python3 scripts/mf.py voucher create --journal-id <仕訳ID> --file /path/to/receipt.pdf

# JSON を直接指定する場合（--file と排他）
python3 scripts/mf.py voucher create --data '{"journal_id": "<仕訳ID>", "voucher_files": [{"file_name": "receipt.pdf", "file_data": "<base64>"}]}'

# 仕訳と証憑の関連付けを解除
python3 scripts/mf.py voucher delete --journal-id <仕訳ID> --voucher-file-id <証憑ID>
```

---

## Advanced Usage

### Python スクリプトから直接利用

```python
import sys
sys.path.insert(0, 'scripts')
from mf import MFClient

client = MFClient()
client.login()

# 仕訳全件取得（自動ページネーション）
journals = client.get_all_journals(from_date='2026-01-01')
print(f"Total journals: {len(journals)}")

# フィルタ付き取得
filtered = client.list_journals(limit=10, is_realized=True)

# バッチ削除
success, failure, errors = client.delete_journals_batch(['id1', 'id2', 'id3'])
print(f"Deleted: {success}, Failed: {failure}")

# エクスポート
client.to_csv(journals, output_file='journals.csv')
client.to_json_export(journals, output_file='journals.json')
```

---

## Configuration & Environment Variables

### 環境変数一覧

| 変数 | 説明 | 例 |
|-----|------|-----|
| `MF_CLIENT_ID` | OAuth Client ID | `your_client_id` |
| `MF_CLIENT_SECRET` | OAuth Client Secret | `your_client_secret` |
| `MF_CLI_LANG` | 言語（ja/en、デフォルト: ja） | `en` |
| `MF_CLI_DEBUG` | デバッグ出力を有効化 | `1` |

### 認証設定

```bash
# 方法A: 環境変数で自動設定（推奨）
export MF_CLIENT_ID="your_client_id"
export MF_CLIENT_SECRET="your_client_secret"
python3 scripts/mf.py auth setup

# 方法B: インタラクティブ入力
python3 scripts/mf.py auth setup
```

### 出力形式・言語

```bash
# 言語切り替え（デフォルト: ja）
export MF_CLI_LANG=en
python3 scripts/mf.py auth status  # 英語出力
```

### デバッグ

```bash
# デバッグ出力を有効化
export MF_CLI_DEBUG=1
python3 scripts/mf.py journal list
```

### 設定ファイル

認証情報は以下に保存されます：
- **トークン**: `~/.mf-cli/tokens.json` （権限: 600）
- **設定**: `~/.mf-cli/config.json` （権限: 600）

---

## Troubleshooting

### 認証エラー

| エラー | 原因 | 解決方法 |
|--------|------|--------|
| `InvalidClientId` | Client ID が誤っている | `python3 scripts/mf.py auth setup` で再入力 |
| `unauthorized` / 401 | トークン期限切れ | `python3 scripts/mf.py auth login` で再ログイン |
| `No authentication config found` | 未セットアップ | `python3 scripts/mf.py auth setup` を実行 |
| `Error: トークン更新失敗` | refresh_token が失効または未取得 | `MF_CLI_DEBUG=1` で原因確認 → `auth login` で再ログイン |

### トークン自動更新について

mf-cli は API リクエスト前にトークンの有効期限を自動チェックし、期限切れの場合は **refresh_token を使って自動更新**します。

ただし、以下の場合は `auth login`（ブラウザ認証）が再び必要になります：
- **初回セットアップ時**（必ず1回は必要）
- **refresh_token が失効した場合**（MoneyForward のポリシー上、長期間使用しないと失効）
- **refresh_token が返されなかった場合**（ネットワークエラー等）

再認証が必要な頻度が高い場合は、以下でデバッグできます：

```bash
MF_CLI_DEBUG=1 python3 scripts/mf.py journal list
```

**無人再認証（macOS + Chrome 限定・オプション）**: refresh_token 失効（`invalid_grant`）時、Chrome で moneyforward.com にログイン済みであれば、`auth login` の代わりに `auth_auto.py` で OAuth フローを無人完走できます（cron / エージェント運用向け）：

```bash
# 依存: pip3 install browser-cookie3（mf.py 本体は標準ライブラリのみのまま）
python3 scripts/auth_auto.py           # tokens.json を再生成
python3 scripts/auth_auto.py --check   # refresh_token が有効なら何もしない（cron 向け）
```

新しい権限を付与するものではなく、App Portal 登録済みアプリの再認可のみを行います。Chrome 側の MF セッションが切れている場合は明示エラーで終了します。

### API エラー

| エラー | 原因 | 解決方法 |
|--------|------|--------|
| `RATE_LIMIT_EXCEEDED` / 429 | API呼び出しが多すぎる | 自動リトライ3回（指数バックオフ、固定）。それでも失敗する場合は数秒待機して再実行 |
| `BAD_REQUEST` / 400 | リクエストデータが不正 | `--data` の JSON フォーマットを確認 |
| `免税事業者にインボイス区分を登録できません` | `invoice_kind` を指定している | `invoice_kind` フィールドを削除する |
| `journal_type` が必須 | `journal_type` フィールドが未指定 | `"journal_type": "journal_entry"` を追加する |
| `insufficient_permissions` / 403 | 権限不足 | 1. プランが Plus 以上か確認<br/>2. `python3 scripts/mf.py auth login` で再ログイン<br/>3. App Portal でユーザー権限を確認 |
| `NOT_FOUND` / 404 | リソースが見つからない | ID が正しいか確認 |

### ブラウザが開かない

**問題**: `auth login` でブラウザが起動しない

**解決**:
- **macOS**: Spotlight で「セキュリティとプライバシー」を開き、ブラウザを確認
- **Linux**: `export BROWSER=firefox` を設定してから実行
- **手動対応**: ターミナルに表示された URL をブラウザにコピー&ペースト

---

## References（詳細ドキュメント）

### 実装ドキュメント

| ドキュメント | 対象 |
|------------|------|
| **IMPLEMENTATION_SUMMARY.md** | v1.1.0 実装内容（HIGH優先度エンドポイント） |
| **MEDIUM_LOW_GAPS_IMPLEMENTATION.md** | v1.2.0 実装内容（ユーティリティ・国際化） |
| **FINAL_IMPLEMENTATION_REPORT.md** | 完全実装レポート＆テスト結果 |
| **TEST_PLAN.md** | テストケース一覧（TC1-TC17） |
| **openapi.yaml** | MoneyForward CA REST API v3 公式仕様書 |
| **SKILL_IMPROVEMENT_PROPOSAL.md** | ドキュメント改善提案 |

### 詳細リファレンス（references/）

| ドキュメント | 説明 |
|------------|------|
| **ERROR_CODES_REFERENCE.md** | HTTP エラーコード別対応・トラブルシューティング |
| **PERFORMANCE_OPTIMIZATION.md** | バッチ処理・リクエスト最適化・実行時間短縮 |
| **ADVANCED_PATTERNS.md** | Python スクリプティング・複雑な CLI パターン・運用自動化 |

### 公式リソース

- **開発者ポータル**: https://developers.biz.moneyforward.com/
- **会計API仕様**: https://developers.api-accounting.moneyforward.com/
- **App Portal**: https://app-portal.moneyforward.com/

---

## 初期セットアップガイド

### STEP 1: アプリケーション登録

マネーフォワード App Portal (https://app-portal.moneyforward.com/authorized_apps/) で:

1. 左サイドバー **「アプリ開発【開発者向け】」** をクリック
2. **「アプリ新規登録」** をクリック
3. 以下を入力：
   - **アプリ名**: `mf-cli` （任意）
   - **リダイレクト URI**: `http://localhost:8080/callback`
   - **クライアント認証方式**: `CLIENT_SECRET_BASIC` （推奨）
4. **「利用規約に同意する」** をチェック
5. **「登録」** をクリック
6. **Client ID** と **Client Secret** をコピー保存

### STEP 2: 環境変数を設定

```bash
export MF_CLIENT_ID="your_client_id_here"
export MF_CLIENT_SECRET="your_client_secret_here"
```

### STEP 3: ユーザー権限を設定

App Portal → **「ユーザー」** → あなたのアカウント → **「編集」**

**「アプリ連携」** セクションで以下をチェック ✅:
- `アプリ連携` （必須）
- `事業者情報` （必須）
- `クラウド会計・確定申告` （会計API使用時）

**「保存」** をクリック

### STEP 4: CLI認証設定

```bash
python3 scripts/mf.py auth setup
```

### STEP 5: ログイン

```bash
python3 scripts/mf.py auth login
# ブラウザが開き、マネーフォワード認可画面に遷移
# 「承認する」をクリック
```

### STEP 6: 確認

```bash
python3 scripts/mf.py auth status
# Status: Authenticated → 完了 ✅
```

---

## Version History

| バージョン | リリース日 | 変更内容 |
|-----------|---------|--------|
| **1.4.0** | 2026-07-04 | 新コマンド5種（`tenant terms` / `master partners create` / `txn create` / `voucher create` / `voucher delete`）+ 無人再認証ヘルパー `auth_auto.py` + オフラインテスト同梱（tests/、18件）+ キャッシュデッドコード削除・ドキュメント整合性修正 + openapi.yaml 最新化（term_settings） |
| **1.3.0** | 2026-03-31 | バグ修正：仕訳作成時の自動ラッピング + 3新機能（JSON @file入力、名前自動解決、master resolve） |
| **1.2.0** | 2026-03-30 | ドキュメント完全改善＆全ユーティリティ実装（20/20 エンドポイント、100% テスト合格） |
| 1.1.0 | 2026-03-30 | HIGH優先度エンドポイント＆パラメータ拡張 |
| 1.0.0 | 2026-03-27 | 初版リリース |
