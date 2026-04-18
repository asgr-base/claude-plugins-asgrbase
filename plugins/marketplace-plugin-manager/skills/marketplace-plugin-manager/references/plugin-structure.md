# プラグイン構造リファレンス

asgr-base マーケットプレイスのプラグイン構造仕様。

## マーケットプレイスリポジトリ全体構造

```
claude-plugins-asgrbase/          ← リポジトリルート
├── .claude-plugin/
│   └── marketplace.json               ← マーケットプレイス定義（プラグイン一覧）
├── README.md                          ← トップレベル説明・プラグイン一覧表
└── plugins/
    ├── claude-md-team-rules/          ← 各プラグインディレクトリ
    ├── atlassian-manager/
    ├── slack-manager/
    ├── mermaid-manager/
    ├── prd-manager/
    ├── notebooklm-manager/
    ├── miro2mermaid/
    ├── pr-creator/
    ├── claude-rules-sync/
    ├── marketplace-plugin-manager/
    └── example-plugin/               ← 構造サンプル（最後に配置）
```

### marketplace.json の構造

```json
{
  "name": "asgr-base",
  "owner": { "name": "asgr-base" },
  "metadata": {
    "description": "ASGR Base Claude Code Plugins マーケットプレイス",
    "version": "1.0.0",
    "homepage": "https://github.com/asgr-base/claude-plugins-asgrbase",
    "repository": "https://github.com/asgr-base/claude-plugins-asgrbase"
  },
  "plugins": [
    // ... プラグインエントリーの配列
    // example-plugin は常に最後
  ]
}
```

新規プラグイン追加時は `example-plugin` の直前に挿入すること。

### トップレベル README.md のカテゴリ表

| カテゴリ | 対象プラグイン例 |
|---------|----------------|
| 設定・共通 | claude-md-team-rules, claude-rules-sync, marketplace-plugin-manager |
| ツール統合系 | atlassian-manager, slack-manager, mermaid-manager |
| タスク実行系 | prd-manager, pr-creator |

## 個別プラグインのディレクトリ構造

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json          # プラグインメタデータ（必須）
├── README.md                 # プラグイン説明（必須）
└── skills/
    ├── <name>/               # シンプルパターン（スキル1つ）
    │   ├── SKILL.md
    │   ├── references/       # 参照ドキュメント（任意）
    │   ├── scripts/          # 実行スクリプト（任意）
    │   └── assets/           # テンプレート等（任意）
    ├── <subskill1>/          # マルチパターン（サブスキル複数）
    │   └── SKILL.md
    └── <subskill2>/
        └── SKILL.md
```

その他の資産タイプ（必要に応じて）:
```
plugins/<name>/
├── hooks/                    # フック定義
├── commands/                 # スラッシュコマンド
├── agents/                   # サブエージェント定義
├── .mcp.json                 # MCPサーバー設定
└── CLAUDE.md                 # チーム共通指示
```

## plugin.json

```json
{
  "name": "plugin-name",           // kebab-case（必須）
  "version": "1.0.0",              // semver（必須）
  "description": "説明",           // 日本語可（必須）
  "author": { "name": "Liquid-dev" },
  "license": "ELEMENTS, Inc.",
  "keywords": ["tag1", "tag2"]     // marketplace 検索用タグ
}
```

## marketplace.json エントリー

`.claude-plugin/marketplace.json` の `plugins` 配列に追加する:

```json
{
  "name": "plugin-name",
  "description": "説明",
  "source": "./plugins/plugin-name",
  "version": "1.0.0",
  "author": { "name": "Liquid-dev" },
  "license": "ELEMENTS, Inc.",
  "tags": ["tag1", "tag2"]
}
```

注意: `example-plugin` エントリーの直前に追加すること（リストの最後から2番目）。

## SKILL.md フロントマター

### シンプルパターン（スキル1つ）

frontmatter キーは `name:`:

```yaml
---
name: plugin-name
description: スキルの説明。いつ使うか・何をするかを含める。
version: 1.0.0
author: claude_code
createDate: YYYY-MM-DD
updateDate: YYYY-MM-DD
---
```

### マルチパターン（サブスキル複数）

frontmatter キーは `skill:`（`name:` ではない）:

```yaml
---
skill: subskill-name
description: このサブスキルの説明
version: 1.0.0
author: claude_code
createDate: YYYY-MM-DD
argument-hint: [引数ヒント]
---
```

呼び出し方: `/plugin-name:subskill-name`

## バージョニング規則（semver）

| 変更内容 | バンプ種別 | 例 |
|---------|-----------|-----|
| 誤字・表記修正、軽微なバグ修正 | PATCH | `1.0.0 → 1.0.1` |
| 機能追加、テスト追加、ドキュメント充実 | MINOR | `1.0.0 → 1.1.0` |
| 破壊的変更、大規模リファクタ | MAJOR | `1.0.0 → 2.0.0` |

## 4ファイル更新チェックリスト

プラグインを変更したら必ず以下4ファイルを更新すること:

- [ ] `plugins/<name>/.claude-plugin/plugin.json` — `version` フィールド
- [ ] `.claude-plugin/marketplace.json` — 該当プラグインの `version` フィールド
- [ ] `plugins/<name>/README.md` — 変更内容を反映
- [ ] `README.md`（トップレベル） — バージョン欄

## インストールコマンド（参考）

```bash
# マーケットプレイス追加
claude plugin marketplace add Liquid-dev/liquid-ekyc-planning-plugins

# プラグインインストール
claude plugin install <name>@liquid-ekyc-planning-plugins

# プラグイン更新
claude plugin update <name>
```

