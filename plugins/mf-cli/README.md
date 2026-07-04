# mf-cli — MoneyForward Cloud Accounting CLI

MoneyForward Cloud Accounting をコマンドラインから操作するプラグイン。仕訳の登録・取得、試算表・帳票の取得、マスター情報の参照ができます。OAuth 2.0 認証によるセキュアな API 操作に対応。

**完全性**: エンドポイント 20/20 (100%) | テスト合格率 100% | OpenAPI 仕様準拠

---

## 機能

- **仕訳管理**: 仕訳の作成・取得・更新・削除
- **財務報告**: 試算表（PL/BS）、推移表の取得
- **マスター情報**: 勘定科目、部門、税区分、補助科目、取引先などを参照・作成
- **明細・証憑**: 明細の作成（自動仕訳生成の入力）、仕訳への証憑添付・解除
- **会計年度**: 会計年度設定の取得（期間・税方式・端数処理）
- **バッチ処理**: 複数仕訳の一括削除・CSV エクスポート
- **セキュア認証**: OAuth 2.0 による安全な API アクセス（無人再認証ヘルパー付き）
- **多言語対応**: 日本語・英語をサポート

---

## クイックスタート

### 前提条件

- Python 3.8 以上
- MoneyForward Cloud Accounting アカウント（Plus プラン以上）
- アプリケーション登録済み（Client ID・Secret 保有）

### セットアップ手順

1. **このプラグインをインストール**

2. **初期設定を実行**
   ```bash
   python3 scripts/mf.py auth setup
   ```

3. **ブラウザで認可**
   - 自動的にブラウザが開きます
   - MoneyForward でログイン・認可を完了

4. **認証確認**
   ```bash
   python3 scripts/mf.py auth status
   ```

5. **（任意）トークンの定期リフレッシュ**
   ```bash
   # launchd/cron での定期更新用。アクセストークン期限前の予防更新
   python3 scripts/mf.py auth refresh
   ```

---

## 使用例

### 事業者情報の取得

```bash
python3 scripts/mf.py tenant info --json
```

### 仕訳一覧の取得

```bash
# 3月の仕訳をJSON形式で取得
python3 scripts/mf.py journal list \
  --from 2026-03-01 --to 2026-03-31 --json
```

### 試算表（PL）の取得

```bash
python3 scripts/mf.py report trial-balance --type pl
```

### CSV エクスポート

```bash
python3 scripts/mf.py journal export \
  --from 2026-01-01 --to 2026-12-31 \
  --format csv --output journals.csv
```

### 会計年度設定・取引先作成・明細・証憑（v1.4.0〜）

```bash
# 会計年度設定一覧（開始日の降順）
python3 scripts/mf.py tenant terms --json

# 取引先を作成
python3 scripts/mf.py master partners create --data '{"name": "株式会社サンプル"}'

# 明細を作成（自動仕訳生成の入力。connected_account_id は master connected-accounts で取得）
python3 scripts/mf.py txn create --data @/tmp/transactions.json

# 仕訳に証憑を添付 / 解除
python3 scripts/mf.py voucher create --journal-id <仕訳ID> --file /path/to/receipt.pdf
python3 scripts/mf.py voucher delete --journal-id <仕訳ID> --voucher-file-id <証憑ID>
```

---

## オプション機能: 無人再認証（macOS + Chrome）

refresh_token 失効（`invalid_grant`）時、通常は `auth login` でブラウザ承認が必要ですが、Chrome で moneyforward.com にログイン済みなら `auth_auto.py` で OAuth フローを無人完走できます（cron / エージェント運用向け）：

```bash
# 依存: pip3 install browser-cookie3（mf.py 本体は標準ライブラリのみのまま）
python3 scripts/auth_auto.py           # tokens.json を再生成
python3 scripts/auth_auto.py --check   # refresh_token が有効なら何もしない
```

新しい権限付与はなし（App Portal 登録済みアプリの再認可のみ）。Chrome 側のセッションが切れている場合は明示エラーで終了します。

---

## ドキュメント

| ドキュメント | 説明 |
|------------|------|
| **[SKILL.md](./SKILL.md)** | 全コマンド・フラグのリファレンス、セットアップガイド |
| **[CLAUDE.md](./CLAUDE.md)** | 開発者向けガイドライン、OpenAPI 仕様参照ルール |
| **[references/](./references/)** | 詳細ドキュメント（エラー対応、最適化、パターン） |

### 詳細リファレンス

- **[references/ERROR_CODES_REFERENCE.md](./references/ERROR_CODES_REFERENCE.md)** — HTTP エラーコード・トラブルシューティング
- **[references/PERFORMANCE_OPTIMIZATION.md](./references/PERFORMANCE_OPTIMIZATION.md)** — バッチ処理、リクエスト最適化、実行時間短縮
- **[references/ADVANCED_PATTERNS.md](./references/ADVANCED_PATTERNS.md)** — Python スクリプティング、自動化パターン

---

## 環境変数

認証情報と動作設定は環境変数で制御します：

| 変数 | 説明 | 例 |
|-----|------|-----|
| `MF_CLIENT_ID` | OAuth Client ID | `your_client_id` |
| `MF_CLIENT_SECRET` | OAuth Client Secret | `your_client_secret` |
| `MF_CLI_LANG` | 言語（ja/en） | `ja` |
| `MF_CLI_DEBUG` | デバッグ出力 | `1` |

詳細は [SKILL.md](./SKILL.md) の「Configuration & Environment Variables」を参照。

---

## テスト

オフラインテストを同梱（API 非接続・全モック）：

```bash
python3 -m unittest discover tests
```

18 テストケース全合格（リクエスト組み立て・`{"journal": {...}}` ラップ・401/429 リトライ・新コマンドの CLI ディスパッチ）。

---

## トラブルシューティング

### 認証エラー（401）

```bash
# トークンを再取得
python3 scripts/mf.py auth login
```

### API レート制限エラー（429）

自動リトライ3回（指数バックオフ、固定）が動作します。それでも失敗する場合は数秒待機して再実行してください。

その他のエラーについては [references/ERROR_CODES_REFERENCE.md](./references/ERROR_CODES_REFERENCE.md) を参照。

---

## ライセンス

MIT License - 詳細は [LICENSE](./LICENSE) を参照

---

## サポート

- **公式ドキュメント**: https://developers.api-accounting.moneyforward.com/
- **開発者ポータル**: https://developers.biz.moneyforward.com/

---

## バージョン

**v1.4.0** — 2026-07-04

### 変更履歴

- **v1.4.0**: 新コマンド5種（`tenant terms` / `master partners create` / `txn create` / `voucher create` / `voucher delete`）、無人再認証ヘルパー `auth_auto.py`、オフラインテスト同梱（tests/、18件）、キャッシュデッドコード削除とドキュメント整合性修正、openapi.yaml 最新化（term_settings 追加）
- **v1.3.0**: 仕訳作成の `{"journal": {...}}` 自動ラップ、`--data @file` 入力、`--resolve-names` 名前自動解決、`master resolve`
- **v1.2.0**: MEDIUM/LOW 優先度機能の実装、ドキュメント改善
- **v1.1.0**: HIGH 優先度エンドポイント実装
- **v1.0.0**: 初版リリース
