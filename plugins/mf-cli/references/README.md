# mf-cli 詳細リファレンス

**作成日**: 2026-03-30
**バージョン**: v1.2.0

このディレクトリは、mf-cli の詳細なリファレンスドキュメントをまとめています。

---

## 📚 ドキュメント一覧

### 1. ERROR_CODES_REFERENCE.md
**エラーハンドリング・トラブルシューティングの完全ガイド**

**内容**:
- HTTP ステータスコード別の原因分析（4xx, 5xx）
- 401/403/404/429/500/503 エラーの詳細な解決方法
- カテゴリ別トラブルシューティング（認証、API、出力）
- よくある質問（FAQ）
- デバッグツール・診断スクリプト

**対象者**: エラーが発生した時に読む

**例**:
```bash
# 403 insufficient_permissions エラーが出た
→ ERROR_CODES_REFERENCE.md の "403 Forbidden" セクション参照
```

---

### 2. PERFORMANCE_OPTIMIZATION.md
**パフォーマンス最適化の完全ガイド**

**内容**:
- CLI 外部でのキャッシュ戦略（取得結果のファイル保存・再利用）
- リクエスト最適化（ページネーション、フィルタ）
- バッチ処理の最適化
- jq での効率的なフィルタリング
- 定期実行の効率化
- ベストプラクティス
- パフォーマンストラブルシューティング

**対象者**: 実行時間を改善したい、API レート制限エラーが出ている

**例**:
```bash
# 仕訳一覧取得が遅い
→ PERFORMANCE_OPTIMIZATION.md の "リクエスト最適化" セクション参照

# API レート制限エラー
→ PERFORMANCE_OPTIMIZATION.md の "429 Too Many Requests" または "バッチ処理の最適化" 参照
```

**実感できる高速化**:
- マスター情報の反復参照: **大幅高速化**（ファイル保存 + jq 再利用）
- バッチ削除: **80%削減**（バッチ処理）
- CSV エクスポート: **65%削減**（直接出力）

---

### 3. ADVANCED_PATTERNS.md
**複雑なスクリプティング・運用自動化の実装パターン集**

**内容**:
- Python スクリプティング（基本～エラーハンドリング）
- バッチ処理の実装例
- マスター情報の同期
- 複雑な jq フィルタリング
- 月別集計、期間比較分析
- 自動化パターン（毎月末バックアップ、週次レポート、差分同期）
- Slack 通知、Google Drive 連携
- デバッグ・プロファイリング方法

**対象者**: スクリプトを書きたい、自動化を構築したい

**例**:
```bash
# 月別売上を集計したい
→ ADVANCED_PATTERNS.md の "月別集計" セクション参照

# 毎月末に試算表をバックアップしたい
→ ADVANCED_PATTERNS.md の "毎月末の自動バックアップ" セクション参照
```

---

## 🗺️ 読む順序（ユースケース別）

### 🔴 エラーが出た場合
```
1. SKILL.md → Troubleshooting セクション（まず簡単な対応）
2. ERROR_CODES_REFERENCE.md → 詳細な解決方法
```

### ⚡ 実行が遅い場合
```
1. PERFORMANCE_OPTIMIZATION.md → リクエスト最適化・CLI 外部でのキャッシュ戦略
2. PERFORMANCE_OPTIMIZATION.md → 最適化方法の選択
```

### 🤖 スクリプトを書きたい場合
```
1. SKILL.md → Advanced Usage（Python 基本例）
2. ADVANCED_PATTERNS.md → 詳細な実装パターン
3. ERROR_CODES_REFERENCE.md → エラーハンドリング
```

### 📊 自動化を構築したい場合
```
1. ADVANCED_PATTERNS.md → "運用自動化パターン" セクション
2. PERFORMANCE_OPTIMIZATION.md → "定期実行の最適化" セクション
3. ERROR_CODES_REFERENCE.md → トラブルシューティング
```

---

## 🎯 クイックアクセス

### よくあるエラー・質問

| 質問 | 参照先 |
|-----|--------|
| 401/403 エラーが出た | ERROR_CODES_REFERENCE.md → 4xx クライアントエラー |
| API レート制限に達した | PERFORMANCE_OPTIMIZATION.md → バッチ処理・リクエスト最適化 |
| 実行時間が長い | PERFORMANCE_OPTIMIZATION.md → リクエスト最適化 |
| Python スクリプトを書きたい | ADVANCED_PATTERNS.md → Python スクリプティング |
| 毎月末にバックアップしたい | ADVANCED_PATTERNS.md → 毎月末の自動バックアップ |
| メモリ使用量が多い | PERFORMANCE_OPTIMIZATION.md → ディスク I/O 最適化 |

---

## 📖 ドキュメント構成

```
references/
├── README.md                           ← このファイル（ナビゲーション）
├── ERROR_CODES_REFERENCE.md            （HTTP エラー・トラブルシューティング）
├── PERFORMANCE_OPTIMIZATION.md         （パフォーマンス最適化）
└── ADVANCED_PATTERNS.md                （スクリプティング・自動化）

_docs/
├── IMPLEMENTATION_SUMMARY.md           （v1.1.0 実装内容）
├── MEDIUM_LOW_GAPS_IMPLEMENTATION.md   （v1.2.0 実装内容）
├── FINAL_IMPLEMENTATION_REPORT.md      （完全実装レポート）
├── TEST_PLAN.md                        （テスト計画・テストケース）
├── SKILL_IMPROVEMENT_PROPOSAL.md       （ドキュメント改善提案）
└── openapi.yaml                        （MoneyForward API 仕様書）
```

---

## 🔗 参考リンク

- **SKILL.md**: 基本的な使用方法・Quick Reference
- **公式 API 仕様**: https://developers.api-accounting.moneyforward.com/
- **MoneyForward サポート**: https://support.moneyforward.com/

---

## 💡 Tips

### 複数ドキュメントを検索する

```bash
# ディレクトリ内で特定キーワードを検索
grep -r "バッチ" references/

# エラーコードで検索
grep -r "429" references/
```

### プリント・PDF化

```bash
# Markdown を PDF に変換（pandoc 利用）
pandoc references/ERROR_CODES_REFERENCE.md -o error_codes.pdf

# ブラウザのプリント機能で HTML → PDF
```

---

## 📝 ドキュメントのバージョン

| ファイル | 更新日 | バージョン |
|---------|--------|-----------|
| ERROR_CODES_REFERENCE.md | 2026-03-30 | v1.0 |
| PERFORMANCE_OPTIMIZATION.md | 2026-03-30 | v1.0 |
| ADVANCED_PATTERNS.md | 2026-03-30 | v1.0 |

---

**質問・フィードバック**: SKILL.md の Troubleshooting セクションまたは公式サポートチャネルを参照
