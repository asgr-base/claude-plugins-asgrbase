# mf-cli — MoneyForward Cloud Accounting CLI

MoneyForward Cloud Accounting をコマンドラインから操作するプラグイン。仕訳の登録・取得、試算表・帳票の取得、マスター情報の参照ができます。OAuth 2.0 認証によるセキュアな API 操作に対応。

**完全性**: エンドポイント 20/20 (100%) | テスト合格率 100% | OpenAPI 仕様準拠

---

## 機能

- **仕訳管理**: 仕訳の作成・取得・更新・削除
- **財務報告**: 試算表（PL/BS）、推移表の取得
- **マスター情報**: 勘定科目、部門、税区分、補助科目、取引先などを参照
- **バッチ処理**: 複数仕訳の一括削除・CSV エクスポート
- **セキュア認証**: OAuth 2.0 による安全な API アクセス
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

---

## ドキュメント

| ドキュメント | 説明 |
|------------|------|
| **[SKILL.md](./SKILL.md)** | 全コマンド・フラグのリファレンス、セットアップガイド |
| **[CLAUDE.md](./CLAUDE.md)** | 開発者向けガイドライン、OpenAPI 仕様参照ルール |
| **[references/](./references/)** | 詳細ドキュメント（エラー対応、最適化、パターン） |

### 詳細リファレンス

- **[references/ERROR_CODES_REFERENCE.md](./references/ERROR_CODES_REFERENCE.md)** — HTTP エラーコード・トラブルシューティング
- **[references/PERFORMANCE_OPTIMIZATION.md](./references/PERFORMANCE_OPTIMIZATION.md)** — キャッシング、バッチ処理、実行時間最適化
- **[references/ADVANCED_PATTERNS.md](./references/ADVANCED_PATTERNS.md)** — Python スクリプティング、自動化パターン

---

## 環境変数

認証情報と動作設定は環境変数で制御します：

| 変数 | 説明 | 例 |
|-----|------|-----|
| `MF_CLIENT_ID` | OAuth Client ID | `your_client_id` |
| `MF_CLIENT_SECRET` | OAuth Client Secret | `your_client_secret` |
| `MF_CACHE_TTL` | キャッシュ有効期限（秒） | `300` |
| `MF_NO_CACHE` | キャッシュ無効化 | `1` |
| `MF_CLI_DEBUG` | デバッグ出力 | `1` |
| `MF_CLI_LANG` | 言語（ja/en） | `ja` |

詳細は [SKILL.md](./SKILL.md) の「Configuration & Environment Variables」を参照。

---

## テスト

テストカバレッジ: **100% (16/16 テストケース合格)**

---

## トラブルシューティング

### 認証エラー（401）

```bash
# トークンを再取得
python3 scripts/mf.py auth login
```

### API レート制限エラー（429）

```bash
# 自動リトライが動作します（指数バックオフ）
# リトライ回数を増やす場合:
export MF_CLI_RETRY=5
```

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

**v1.2.0** — 2026-03-30

### 変更履歴

- **v1.2.0**: MEDIUM/LOW 優先度機能の実装、ドキュメント改善
- **v1.1.0**: HIGH 優先度エンドポイント実装
- **v1.0.0**: 初版リリース
