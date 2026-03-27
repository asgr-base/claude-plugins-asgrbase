---
name: claude-code-guide
description: Claude Codeの機能・設定・ベストプラクティスを提供。Skills、Hooks、Subagents、MCPs、Plugins、コンテキスト管理、トークン最適化などClaude Code関連の質問時に使用。
version: 1.1.0
author: claude_code
createDate: 2026-01-25
updateDate: 2026-01-25
license: Apache-2.0
---

# Claude Code 完全ガイド

## 概要

Claude Codeは、Anthropicの公式CLI/エージェントツール。本ガイドは10ヶ月以上の実践経験に基づくベストプラクティスを網羅。

## コアコンポーネント

### 1. Skills & Commands

**Skills**: 再利用可能なワークフロー定義
- 配置: `~/.claude/skills/` または `.claude/skills/`
- 形式: SKILL.mdファイル（YAMLフロントマター必須）

**Commands**: スラッシュコマンドで実行可能なプロンプト
- 配置: `~/.claude/commands/`
- 実行: `/command-name`

```bash
# Skills構造例
~/.claude/skills/
  coding-standards.md    # コーディング規約
  tdd-workflow/          # 複数ファイルスキル
  security-review/       # チェックリスト型
```

**活用例**: `/refactor-clean` → `/tdd` → `/test-coverage` のチェーン実行

### 2. Hooks

トリガーベースの自動化。ツール呼び出しやライフサイクルイベントで発火。

| Hook Type | 発火タイミング | 用途例 |
|-----------|---------------|--------|
| PreToolUse | ツール実行前 | バリデーション、リマインダー |
| PostToolUse | ツール実行後 | フォーマット、フィードバック |
| UserPromptSubmit | メッセージ送信時 | 入力検証 |
| Stop | 応答完了時 | セッション終了処理 |
| PreCompact | コンテキスト圧縮前 | 状態保存 |
| Notification | 許可リクエスト時 | 通知カスタマイズ |

**設定例** (`~/.claude.json`):
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "tool == \"Bash\" && tool_input.command matches \"(npm|pnpm)\"",
      "hooks": [{
        "type": "command",
        "command": "if [ -z \"$TMUX\" ]; then echo '[Hook] Consider tmux'; fi"
      }]
    }]
  }
}
```

**詳細**: [BASICS.md](BASICS.md#hooks)

### 3. Subagents

メインエージェントがタスクを委譲できるプロセス。コンテキスト節約に有効。

```bash
~/.claude/agents/
  planner.md           # 機能実装計画
  architect.md         # システム設計
  tdd-guide.md         # TDD実行
  code-reviewer.md     # コードレビュー
  security-reviewer.md # 脆弱性分析
  build-error-resolver.md
```

**重要**: サブエージェントには限定されたツール/MCP権限を設定。

### 4. Rules & Memory

`.claude/rules/`フォルダにClaudeが常に従うべきルールを配置。

```bash
~/.claude/rules/
  security.md      # シークレット禁止、入力検証
  coding-style.md  # 不変性、ファイル構成
  testing.md       # TDD、80%カバレッジ
  git-workflow.md  # コミット形式
```

**または**: 単一の`CLAUDE.md`に全ルールを記載。

### 5. MCPs (Model Context Protocol)

外部サービスとの直接接続。APIのプロンプト駆動ラッパー。

**設定例**:
```json
{
  "mcpServers": {
    "github": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"] },
    "supabase": { "command": "npx", "args": ["-y", "@supabase/mcp-server-supabase@latest", "--project-ref=YOUR_REF"] }
  }
}
```

**重要**: コンテキストウィンドウ管理
- 200kのコンテキストがMCP過多で70kに減少する可能性
- **推奨**: 20-30個設定、10個以下有効、80ツール未満

### 6. Plugins

スキル+MCP+Hooks+ツールのバンドルパッケージ。

```bash
# マーケットプレイス追加
claude plugin marketplace add https://github.com/mixedbread-ai/mgrep

# /plugins で管理
```

**推奨プラグイン**:
- `typescript-lsp` / `pyright-lsp`: 型チェック
- `hookify`: フック作成支援
- `mgrep`: 高性能検索（grep/ripgrepより効率的）

## コンテキスト＆メモリ管理

### セッション間メモリ共有

`.claude/sessions/`に状態を保存し、次セッションで読み込み。

```
~/.claude/sessions/
  2026-01-25-feature-a.tmp
  2026-01-24-bugfix.tmp
```

**保存内容**:
- 成功したアプローチ（証拠付き）
- 試行したが失敗したアプローチ
- 未試行のアプローチ
- 残タスク

### 戦略的コンパクト

- 自動コンパクトを無効化し、論理的な区切りで手動実行
- 探索後・実行前、マイルストーン完了後にコンパクト

### 動的システムプロンプト注入

```bash
# 開発モード
alias claude-dev='claude --system-prompt "$(cat ~/.claude/contexts/dev.md)"'

# レビューモード
alias claude-review='claude --system-prompt "$(cat ~/.claude/contexts/review.md)"'
```

**詳細**: [ADVANCED.md](ADVANCED.md#context-management)

## トークン最適化

### モデル選択指針

| タスク種別 | モデル | 理由 |
|-----------|--------|------|
| 探索/検索 | Haiku | 高速・低コスト |
| 単純編集 | Haiku | 明確な指示なら十分 |
| 複数ファイル実装 | Sonnet | コーディングに最適バランス |
| 複雑なアーキテクチャ | Opus | 深い推論が必要 |
| PRレビュー | Sonnet | コンテキスト理解 |
| セキュリティ分析 | Opus | 脆弱性見落とし不可 |
| デバッグ（複雑） | Opus | システム全体の把握が必要 |

**コスト比較** (per MTok):
- Opus 4.5: $5入力 / $25出力
- Sonnet 4.5: $3入力 / $15出力
- Haiku: $1入力 / $5出力

### その他の最適化

- **mgrep使用**: grep比で約50%トークン削減
- **tmux活用**: バックグラウンドプロセスをClaude外で実行
- **モジュラーコードベース**: 数百行/ファイルで維持

**詳細**: [ADVANCED.md](ADVANCED.md#token-optimization)

## 並列化

### /fork

会話をフォークして非重複タスクを並列実行。

### Git Worktrees

重複する並列作業でコンフリクトを回避。

```bash
git worktree add ../project-feature-a feature-a
git worktree add ../project-feature-b feature-b
# 各worktreeで別々のClaudeインスタンスを実行
```

### 推奨パターン

- メインチャット: コード変更
- フォーク: コードベースの質問、ドキュメント調査、外部サービス検索

**注意**: 初心者は並列化を避け、単一インスタンスの習熟を優先。

## 検証ループ＆評価

### チェックポイントベース

線形ワークフロー向け。各マイルストーンで検証→失敗なら修正→次へ。

### 継続的評価

長時間セッション向け。N分毎またはメジャー変更後にテストスイート実行。

### サブエージェントコンテキスト問題

サブエージェントは要約を返すが、オーケストレータの意図を把握していない。

**対策**: 反復的取得パターン
1. サブエージェントが要約を返す
2. オーケストレータが評価
3. 不十分なら追加質問
4. 最大3サイクルまで繰り返し

**詳細**: [ADVANCED.md](ADVANCED.md#verification)

## キーボードショートカット

| ショートカット | 機能 |
|---------------|------|
| `Ctrl+U` | 行全体削除 |
| `!` | Bashコマンドプレフィックス |
| `@` | ファイル検索 |
| `/` | スラッシュコマンド |
| `Shift+Enter` | 複数行入力 |
| `Tab` | thinking表示切替 |
| `Esc Esc` | 中断/コード復元 |

## 便利なコマンド

| コマンド | 機能 |
|---------|------|
| `/rewind` | 以前の状態に戻る |
| `/statusline` | ステータスラインカスタマイズ |
| `/checkpoints` | ファイルレベルのundoポイント |
| `/compact` | 手動コンテキスト圧縮 |
| `/fork` | 会話フォーク |
| `/rename` | チャット名変更 |
| `/plugins` | プラグイン管理 |
| `/mcp` | MCP管理 |

## エディタ連携

### Zed（推奨）

- Rust製で高速・軽量
- Agent Panel統合でリアルタイムファイル追跡
- `CMD+Shift+R`: コマンドパレット
- Vimモード対応

### VSCode / Cursor

- `\ide`でLSP機能有効化
- 拡張機能でUI統合

## 設定例

**詳細な設定例**: [EXAMPLES.md](EXAMPLES.md)

## ベストプラクティス

### Tier 1: 即効性あり（使いやすい）
- **サブエージェント**: コンテキスト腐敗防止、アドホック特化
- **メタプロンプティング**: 3分のプロンプト作成で20分のタスクを安定化
- **序盤での質問**: 仮定の確認

### Tier 2: 高スキル床（習熟が必要）
- **長時間エージェント**: 15分 vs 1.5時間 vs 4時間タスクの最適化
- **並列マルチエージェント**: 高分散、複雑/セグメント化されたタスク向け
- **Computer Use**: 非常に早期のパラダイム

**詳細パターン**: [PATTERNS.md](PATTERNS.md)

## 関連専門スキル

特定のトピックについて詳細が必要な場合は、以下の専門スキルを参照してください。

| スキル | 用途 | トリガーワード |
|--------|------|----------------|
| [claude-md-guide](../claude-md-guide/SKILL.md) | CLAUDE.md作成・最適化 | CLAUDE.md、/init、メモリ設定 |
| [claude-skill-creation-guide](../claude-skill-creation-guide/SKILL.md) | Agent Skills作成 | スキル作成、SKILL.md、Progressive Disclosure |

**使い分け**:
- **本ガイド**: Claude Code全般の機能・設定・ベストプラクティス
- **claude-md-guide**: CLAUDE.mdファイルの書き方、60行ルール、構成パターン
- **claude-skill-creation-guide**: スキルの設計・実装・評価・反復開発

## 詳細リファレンス

| ファイル | 内容 |
|----------|------|
| [BASICS.md](BASICS.md) | Skills, Hooks, Subagents, MCPs, Plugins詳細 |
| [ADVANCED.md](ADVANCED.md) | コンテキスト管理、トークン最適化、検証ループ |
| [EXAMPLES.md](EXAMPLES.md) | 設定例、コード例 |
| [PATTERNS.md](PATTERNS.md) | ベストプラクティスパターン |

## 公式リソース

- [Claude Code Docs](https://code.claude.com/docs)
- [Plugins Reference](https://code.claude.com/docs/en/plugins)
- [Hooks Documentation](https://code.claude.com/docs/en/hooks)
- [MCP Overview](https://code.claude.com/docs/en/mcp)

---

**Version**: 1.1.0
**Last Updated**: 2026-01-25
**Source**: @affaanmustafa's Shorthand/Longform Guides (Anthropic Hackathon Winner)

**更新履歴**:
- v1.1.0: 関連専門スキル（claude-md-guide、claude-skill-creation-guide）セクション追加
- v1.0.0: 初版作成
