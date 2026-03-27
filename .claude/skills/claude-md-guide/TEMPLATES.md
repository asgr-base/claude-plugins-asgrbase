# CLAUDE.md テンプレート集

## 最小テンプレート（〜20行）

個人プロジェクト・小規模向け:

```markdown
# Project Name

## 概要
[1-2文でプロジェクトの目的]

## コマンド
- build: `npm run build`
- test: `npm test`
- lint: `npm run lint`

## 重要事項
- [プロジェクト固有の注意点]
```

---

## 中規模テンプレート（〜60行）

チーム開発・中規模向け:

```markdown
# Project Name

## WHY - プロジェクトの目的
[対象ユーザー、解決する課題]

## WHAT - 技術スタック
- フロントエンド: [React/Vue/etc]
- バックエンド: [Node/Python/etc]
- データベース: [PostgreSQL/etc]

## ディレクトリ構造
```
src/
├── components/   # UIコンポーネント
├── services/     # ビジネスロジック
└── utils/        # ユーティリティ
```

## HOW - 開発コマンド
| コマンド | 説明 |
|----------|------|
| `npm run dev` | 開発サーバー起動 |
| `npm run build` | 本番ビルド |
| `npm test` | テスト実行 |
| `npm run lint` | リント実行 |

## 命名規則
- コンポーネント: PascalCase
- 関数: camelCase
- 定数: UPPER_SNAKE_CASE

## 重要事項
- IMPORTANT: [必ず守るべきルール]
- [予期しない動作の警告]

## 詳細リファレンス
- [アーキテクチャ詳細](docs/ARCHITECTURE.md)
- [API仕様](docs/API.md)
```

---

## 大規模テンプレート（メイン + モジュール分割）

### メインファイル（CLAUDE.md）

```markdown
# Project Name

## WHY
[プロジェクトの目的・背景]

## WHAT
- 技術スタック: [概要のみ]
- アーキテクチャ: [概要のみ]

## HOW
| コマンド | 説明 |
|----------|------|
| `npm run dev` | 開発サーバー |
| `npm test` | テスト |
| `npm run build` | ビルド |

## IMPORTANT
- [最重要ルール1]
- [最重要ルール2]

## 詳細リファレンス
| ファイル | 内容 |
|----------|------|
| [コードスタイル](.claude/rules/code-style.md) | 命名規則、フォーマット |
| [セキュリティ](.claude/rules/security.md) | セキュリティ要件 |
| [テスト](.claude/rules/testing.md) | テスト方針 |
| [API設計](docs/api-design.md) | API規約 |
```

### モジュールファイル例

**.claude/rules/code-style.md**:
```markdown
# コードスタイル

## 命名規則
- コンポーネント: PascalCase（例: `UserProfile`）
- 関数: camelCase（例: `getUserById`）
- 型定義: PascalCase + 接尾辞（例: `UserResponse`）

## ファイル構成
- 1ファイル500行以下
- 1関数50行以下
- ネスト3レベル以下
```

**.claude/rules/security.md**:
```markdown
# セキュリティ要件

## 禁止事項
- ハードコードされたシークレット
- SQLインジェクション可能なクエリ
- 未検証のユーザー入力

## 必須事項
- 入力値のサニタイズ
- 機密データのログ出力禁止
```

**.claude/rules/testing.md**:
```markdown
# テスト方針

## カバレッジ目標
- ユニットテスト: 80%以上
- 重要パス: 100%

## テスト命名
- `describe`: 対象の説明
- `it`: 期待される動作（should〜）
```

---

## 特殊用途テンプレート

### ライブラリ/パッケージ向け

```markdown
# Library Name

## 概要
[ライブラリの目的]

## 公開API
- `functionA()`: [説明]
- `functionB()`: [説明]

## コマンド
- `npm run build`: ビルド
- `npm test`: テスト
- `npm run docs`: ドキュメント生成

## 破壊的変更に関する注意
- IMPORTANT: 公開APIの変更は必ずCHANGELOGに記載
```

### モノレポ向け

```markdown
# Monorepo Name

## パッケージ構成
| パッケージ | 説明 |
|------------|------|
| `packages/core` | コア機能 |
| `packages/ui` | UIコンポーネント |
| `apps/web` | Webアプリ |

## コマンド
- `pnpm dev`: 全パッケージ開発モード
- `pnpm build`: 全パッケージビルド
- `pnpm test`: 全テスト実行

## 依存関係
- `core` → 依存なし
- `ui` → `core`
- `web` → `core`, `ui`
```

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
