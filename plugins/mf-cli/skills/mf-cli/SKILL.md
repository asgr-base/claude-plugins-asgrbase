---
name: mf-cli
description: マネーフォワード クラウド会計をCLIで操作する。仕訳の登録・取得、試算表・帳票の取得、マスター情報の参照ができます。OAuth認証によるセキュアなAPI操作に対応。アプリ登録から初回ログイン、日常操作まで、マネーフォワード会計APIとの統合が必要な場面で使用してください。
version: 1.2.0
author: claude_code
createDate: 2026-03-27
updateDate: 2026-03-30
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
```

### 事業者コマンド

```bash
# 事業者情報を取得
python3 scripts/mf.py tenant info
python3 scripts/mf.py tenant info --json
```

### 仕訳コマンド

| コマンド | 説明 | オプション |
|---------|------|----------|
| `journal list` | 仕訳一覧（フィルタ付き） | `--from` `--to` `--account-id` `--is-realized` `--limit` `--json` |
| `journal get <id>` | 仕訳取得（ID指定） | `--json` |
| `journal create` | 仕訳作成 | `--data <JSON>` `--json` |
| `journal update <id>` | 仕訳更新（全置換） | `--data <JSON>` `--json` |
| `journal delete <id>` | 仕訳削除 | `--json` |
| `journal list-all` | 全仕訳取得（自動ページネーション） | `--from` `--to` `--json` |
| `journal export` | CSV/JSON エクスポート | `--from` `--to` `--format csv/json` `-o FILE` |
| `journal batch-delete` | バッチ削除 | `--ids id1,id2` または `--from-file FILE` |

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

### キャッシング活用

```python
# GET リクエストは自動キャッシュ（TTL: 300秒）
accounts1 = client.get_accounts()  # API呼び出し
accounts2 = client.get_accounts()  # キャッシュから取得（高速）

# 環境変数でキャッシュを無効化
export MF_NO_CACHE=1
python3 scripts/mf.py journal list  # 常に API を呼び出す
```

---

## Configuration & Environment Variables

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

# JSON 出力を圧縮
export MF_JSON_PRETTY=0
python3 scripts/mf.py journal list --json
```

### パフォーマンス・キャッシング

```bash
# キャッシュ TTL を変更（デフォルト: 300秒）
export MF_CACHE_TTL=600
python3 scripts/mf.py master accounts  # 長時間キャッシュ

# キャッシング無効化
export MF_NO_CACHE=1

# リトライ回数を増やす（デフォルト: 3）
export MF_CLI_RETRY=5
```

### デバッグ

```bash
# デバッグ出力を有効化
export MF_CLI_DEBUG=1
python3 scripts/mf.py journal list

# 詳細エラーメッセージ
export MF_CLI_VERBOSE=1
python3 scripts/mf.py auth login
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

### API エラー

| エラー | 原因 | 解決方法 |
|--------|------|--------|
| `RATE_LIMIT_EXCEEDED` / 429 | API呼び出しが多すぎる | 数秒待機（自動リトライ対応） |
| `BAD_REQUEST` / 400 | リクエストデータが不正 | `--data` の JSON フォーマットを確認 |
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

### 詳細リファレンス（_docs/references/）

| ドキュメント | 説明 |
|------------|------|
| **ERROR_CODES_REFERENCE.md** | HTTP エラーコード別対応・トラブルシューティング |
| **PERFORMANCE_OPTIMIZATION.md** | キャッシング戦略・バッチ処理・実行時間最適化 |
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
| **1.3.0** | 2026-03-31 | バグ修正：仕訳作成時の自動ラッピング + 3新機能（JSON @file入力、名前自動解決、master resolve） |
| **1.2.0** | 2026-03-30 | ドキュメント完全改善＆全ユーティリティ実装（20/20 エンドポイント、100% テスト合格） |
| 1.1.0 | 2026-03-30 | HIGH優先度エンドポイント＆パラメータ拡張 |
| 1.0.0 | 2026-03-27 | 初版リリース |
