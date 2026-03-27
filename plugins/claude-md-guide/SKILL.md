---
name: claude-md-guide
description: CLAUDE.mdファイルの作成・最適化ガイド。プロジェクト固有のコンテキスト設定、性能最大化のためのベストプラクティスを提供。CLAUDE.md作成、/init後の改善、メモリ設定関連の質問時に使用。
version: 2.1.0
author: claude_code
createDate: 2026-01-12
updateDate: 2026-01-25
license: Apache-2.0
---

# CLAUDE.md 作成・最適化ガイド

## 概要

CLAUDE.mdはClaude Codeが**毎回の会話で自動読み込み**するファイル。プロジェクトの「脳」として機能し、性能を決定する最高レバレッジポイント。

## コア原則

### 1. 60行以下を目指す

| 行数 | 効果 |
|------|------|
| **60行以下** | 最適（各指示が確実に適用） |
| **100行未満** | 良好 |
| **300行以上** | 性能低下（重要指示が埋もれる） |

**IMPORTANT**: システムプロンプトで約50の指示を消費。CLAUDE.mdは**普遍的に適用可能な指示のみ**に限定。

### 2. WHY / WHAT / HOW 構成

```markdown
# Project Name
## WHY - プロジェクトの目的、対象ユーザー
## WHAT - 技術スタック、主要ディレクトリ構造
## HOW - 開発コマンド（build, test, lint）、環境変数
```

### 3. Progressive Disclosure（段階的開示）

詳細は別ファイルに分割し、標準Markdown記法で参照:

| 記法 | 推奨 | 理由 |
|------|------|------|
| `[表示名](相対パス)` | ✅ | 標準Markdown |
| `@path/to/file` | ❌ | Claude Code独自 |
| `[[ファイル名]]` | ❌ | Obsidian固有 |

## 配置場所と階層

| 配置場所 | 用途 | スコープ |
|----------|------|----------|
| `./CLAUDE.md` | プロジェクト共有 | チーム |
| `./CLAUDE.local.md` | 個人設定（.gitignore） | 個人 |
| `~/.claude/CLAUDE.md` | 全プロジェクト共通 | 個人 |
| `./.claude/rules/*.md` | モジュール分割 | チーム |

## 含める / 含めない

| 含める | 含めない |
|--------|----------|
| 開発コマンド（build, test, lint） | コードフォーマット規則（リンターの仕事） |
| 重要なアーキテクチャパターン | 網羅的なエッジケース |
| 命名規則 | 変更頻度の高い情報 |
| 予期しない動作の警告 | 自明な指示 |

**IMPORTANT**: "Never send an LLM to do a linter's job"

## クイックリファレンス

| 問題 | 解決策 |
|------|--------|
| 指示が無視される | 強調表現（IMPORTANT, YOU MUST）を使用 |
| CLAUDE.mdが長すぎる | 詳細を別ファイルに分離、60行以下に |
| 頻繁に更新が必要 | 変更頻度の高い情報は別ファイルに |
| フォーマットが崩れる | リンター/Hooksに任せる |
| 曖昧で効果がない | 具体的な指示に書き換え |

## 関連機能との連携

### Hooksとの組み合わせ

PostToolUseフックでフォーマット自動化 → CLAUDE.mdにフォーマット規則不要

```json
{
  "PostToolUse": [{
    "matcher": "Edit && .ts/.tsx",
    "hooks": [{ "command": "npx prettier --write" }]
  }]
}
```

### .claude/rules/ モジュール分割

```
.claude/
├── CLAUDE.md           # メイン（60行以下）
└── rules/
    ├── code-style.md   # コードスタイル
    └── security.md     # セキュリティ要件
```

パス固有ルール（YAMLフロントマター）:
```yaml
---
paths:
  - "src/api/**/*.ts"
---
```

### 動的システムプロンプト注入

```bash
alias claude-dev='claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"'
```

**詳細**: [claude-code-guide](../claude-code-guide/SKILL.md)

## 反復的改善

1. `/init`で生成 → 汎用的すぎる内容を削除
2. プロジェクト固有の重要事項を追加
3. 60行以下に圧縮
4. `#`キーで作業中に気づいた点を即座に追記
5. 定期的にレビュー（遵守されていない指示は表現を調整）

## 詳細リファレンス

| ファイル | 内容 |
|----------|------|
| [TEMPLATES.md](TEMPLATES.md) | テンプレート集（最小/中規模/大規模） |
| [EXAMPLES.md](EXAMPLES.md) | 良い例/悪い例の比較、効果的な表現 |
| [CHECKLIST.md](CHECKLIST.md) | 作成/レビュー時チェックリスト |

## 関連スキル

| スキル | 用途 |
|--------|------|
| [claude-code-guide](../claude-code-guide/SKILL.md) | Claude Code全般の機能・設定 |
| [claude-skill-creation-guide](../claude-skill-creation-guide/SKILL.md) | Agent Skills作成 |

## 参考リソース

- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Manage Claude's Memory](https://code.claude.com/docs/en/memory)

---

**Version**: 2.1.0
**Last Updated**: 2026-01-25

**更新履歴**:
- v2.1.0 (2026-01-25): 関連スキルセクション追加（claude-code-guide、claude-skill-creation-guide）
- v2.0.0: Progressive Disclosure徹底（TEMPLATES/EXAMPLES/CHECKLIST分離）、クイックリファレンス追加、claude-code-guide連携追加
- v1.1.0: ファイル参照の記法ルールを追加
- v1.0.0: 初版作成
