# marketplace-plugin-manager

`asgr-base` マーケットプレイスへのプラグイン追加・更新・公開管理スキルです。

## インストール

```bash
claude plugin install marketplace-plugin-manager@asgr-base
```

## スキル

### marketplace-plugin-manager

プラグインの新規追加・バージョンアップ・整合性チェックを行います。

**使用タイミング**:

- 新しいプラグインをマーケットプレイスに追加したいとき
- プラグインを変更した後にバージョンアップ・公開したいとき
- `plugin.json` / `marketplace.json` / `README.md` のバージョン整合性を確認したいとき

**使用例**:

```
マーケットプレイスに新しいプラグインを追加して
mermaid-manager をバージョンアップして
全プラグインの整合性を確認して
```

> **注意**: 「スキルを作って」だけでは本スキルは起動しません（個人用ローカルスキル作成と区別するため）。マーケットプレイスへの追加・公開を明示してください。

## 機能

| 操作 | 説明 |
|------|------|
| **新規追加 [A]** | プラグインディレクトリ・plugin.json・SKILL.md・README.md を作成し、marketplace.json と README.md を更新して push |
| **更新 [U]** | plugin.json / marketplace.json / README.md × 2 の4ファイルを一括バージョンアップして push |
| **整合性検証 [V]** | 全プラグインのバージョン整合性をチェック |

## リファレンス

| ドキュメント | 内容 |
|-------------|------|
| [plugin-structure.md](./skills/marketplace-plugin-manager/references/plugin-structure.md) | マーケットプレイスリポジトリ全体構造・個別プラグイン構造・marketplace.json スキーマ・SKILL.md frontmatter・バージョニング規則 |

## 対応プラグインパターン

| パターン | 例 | 特徴 |
|---------|-----|------|
| シンプル | `atlassian-manager` | スキル1つ、`name:` frontmatter |
| マルチサブスキル | `pr-creator` | スキル複数、`skill:` frontmatter、`/plugin:subskill` で呼び分け |

## なぜこのスキルが必要か

プラグイン変更時に以下4ファイルの更新が漏れやすい:

1. `plugins/<name>/.claude-plugin/plugin.json`
2. `.claude-plugin/marketplace.json`
3. `plugins/<name>/README.md`
4. `README.md`（トップレベル）

このスキルはこれらを必ず一括更新することを保証します。
