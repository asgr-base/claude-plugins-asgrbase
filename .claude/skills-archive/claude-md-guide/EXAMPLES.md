# CLAUDE.md 良い例・悪い例

## 効果的な表現パターン

### 強調表現の使い分け

| 表現 | 効果 | 使用場面 |
|------|------|----------|
| `IMPORTANT:` | 高 | 必ず守るべきルール |
| `YOU MUST` | 最高 | 絶対に違反不可のルール |
| `NEVER` | 最高 | 絶対禁止事項 |
| `Note:` | 中 | 補足情報 |
| 通常文 | 低 | 一般的な情報 |

**例**:
```markdown
IMPORTANT: 本番環境へのデプロイ前に必ずテストを実行すること

YOU MUST use TypeScript strict mode in all new files

NEVER commit API keys or secrets to the repository
```

---

## 良い例 vs 悪い例

### 1. 開発コマンド

❌ **悪い例**（冗長）:
```markdown
## 開発環境のセットアップと実行方法

このプロジェクトを開発環境で実行するには、まずNode.js v18以上が
インストールされていることを確認してください。その後、以下の
コマンドを順番に実行してください。最初に依存関係をインストールし、
次に開発サーバーを起動します。

依存関係のインストール:
npm install

開発サーバーの起動:
npm run dev
```

✅ **良い例**（簡潔）:
```markdown
## コマンド
- dev: `npm run dev`
- build: `npm run build`
- test: `npm test`
```

### 2. コーディング規則

❌ **悪い例**（リンターの仕事）:
```markdown
## コードフォーマット規則
- インデントは2スペース
- 行末にセミコロンを付ける
- 文字列はシングルクォートを使用
- 1行は80文字以下
- 関数の後に空行を入れる
```

✅ **良い例**（本質的なルールのみ）:
```markdown
## 命名規則
- コンポーネント: PascalCase
- hooks: use + PascalCase（例: useAuth）
- 定数: UPPER_SNAKE_CASE
```

### 3. アーキテクチャ説明

❌ **悪い例**（詳細すぎ）:
```markdown
## アーキテクチャ

このプロジェクトはクリーンアーキテクチャを採用しています。
ドメイン層には純粋なビジネスロジックを配置し、外部依存を
持ちません。アプリケーション層ではユースケースを定義し、
ドメイン層のエンティティを操作します。インフラ層では...
（以下20行続く）
```

✅ **良い例**（概要 + 参照）:
```markdown
## アーキテクチャ
クリーンアーキテクチャ採用。詳細は[ARCHITECTURE.md](docs/ARCHITECTURE.md)参照。

重要: 依存の方向は常に外→内（Infra→App→Domain）
```

### 4. 注意事項

❌ **悪い例**（曖昧）:
```markdown
## 注意
- パフォーマンスに気をつけてください
- セキュリティを考慮してください
- テストを書いてください
```

✅ **良い例**（具体的）:
```markdown
## 注意
- IMPORTANT: N+1クエリを避ける（必ずeager loadingを使用）
- NEVER: ユーザー入力をサニタイズせずにSQLに渡さない
- 新機能には最低1つのテストを追加
```

### 5. 環境変数

❌ **悪い例**（値を記載）:
```markdown
## 環境変数
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
API_KEY=sk-xxxxxxxxxxxxx
SECRET_KEY=my-secret-key-123
```

✅ **良い例**（説明のみ）:
```markdown
## 環境変数
`.env.example`を`.env`にコピーして設定:
- `DATABASE_URL`: PostgreSQL接続文字列
- `API_KEY`: 外部API認証キー
- `SECRET_KEY`: JWT署名用シークレット
```

---

## アンチパターン

### 1. 全てを詰め込む

```markdown
# 悪い例: 300行以上のCLAUDE.md

## プロジェクト概要
（10行）

## 技術スタック
（20行）

## ディレクトリ構造
（30行）

## コマンド
（15行）

## コーディング規則
（50行）

## API仕様
（80行）

## デプロイ手順
（40行）

## トラブルシューティング
（50行）
...
```

→ **解決策**: 60行以下に圧縮し、詳細は別ファイルに分離

### 2. 自明な指示

```markdown
# 悪い例
- 変数には意味のある名前を付けてください
- コードは読みやすく書いてください
- バグがないようにしてください
```

→ **解決策**: 自明な指示は削除

### 3. 変更頻度の高い情報

```markdown
# 悪い例
## 現在のバージョン
v1.2.3

## 最新のリリースノート
- 2024-01-15: 機能Aを追加
- 2024-01-10: バグBを修正
...
```

→ **解決策**: 変更頻度の高い情報は別ファイルに

### 4. プロジェクト固有でない内容

```markdown
# 悪い例
## Gitの使い方
git add . でファイルをステージング
git commit -m "message" でコミット
git push でプッシュ
```

→ **解決策**: 一般的な知識は含めない

---

## 効果的な構成例

### Before（150行）→ After（45行）

**Before**:
```markdown
# My Project

## はじめに
このプロジェクトは...（説明10行）

## セットアップ
まず、Node.jsをインストールして...（説明15行）

## ディレクトリ構造
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.styles.ts
│   │   └── Button.test.tsx
│   ├── Input/
...（30行続く）

## コーディング規則
### 命名規則
...（20行）
### フォーマット
...（15行）

## API仕様
### ユーザーAPI
...（40行）
```

**After**:
```markdown
# My Project

## WHY
ユーザー管理システム。管理者向けダッシュボード提供。

## WHAT
- Frontend: React + TypeScript
- Backend: Node.js + Express
- DB: PostgreSQL

## HOW
| コマンド | 説明 |
|----------|------|
| `npm run dev` | 開発サーバー |
| `npm test` | テスト |
| `npm run build` | ビルド |

## 命名規則
- Components: PascalCase
- Functions: camelCase
- Constants: UPPER_SNAKE_CASE

## IMPORTANT
- N+1クエリ禁止（eager loading必須）
- 新機能にはテスト必須

## 詳細
- [アーキテクチャ](docs/ARCHITECTURE.md)
- [API仕様](docs/API.md)
- [コードスタイル](.claude/rules/code-style.md)
```

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
