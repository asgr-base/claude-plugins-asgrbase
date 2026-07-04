# Claude Code 設定例・コード例

## 完全な設定例

### Plugins（インストール済み）

通常4-5個のみ有効にする:

```markdown
ralph-wiggum@claude-code-plugins       # ループ自動化
frontend-design@claude-code-plugins    # UI/UXパターン
commit-commands@claude-code-plugins    # Gitワークフロー
security-guidance@claude-code-plugins  # セキュリティチェック
pr-review-toolkit@claude-code-plugins  # PR自動化
typescript-lsp@claude-plugins-official # TSインテリジェンス
hookify@claude-plugins-official        # フック作成
code-simplifier@claude-plugins-official
feature-dev@claude-code-plugins
explanatory-output-style@claude-code-plugins
code-review@claude-code-plugins
context7@claude-plugins-official       # ライブドキュメント
pyright-lsp@claude-plugins-official    # Python型
mgrep@Mixedbread-Grep                  # 改善された検索
```

---

## MCP Servers設定

### ユーザーレベル設定

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"]
    },
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest", "--project-ref=YOUR_PROJECT_REF"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "vercel": {
      "type": "http",
      "url": "https://mcp.vercel.com"
    },
    "railway": {
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"]
    },
    "cloudflare-docs": {
      "type": "http",
      "url": "https://docs.mcp.cloudflare.com/mcp"
    },
    "cloudflare-workers-bindings": {
      "type": "http",
      "url": "https://bindings.mcp.cloudflare.com/mcp"
    },
    "cloudflare-workers-builds": {
      "type": "http",
      "url": "https://builds.mcp.cloudflare.com/mcp"
    },
    "cloudflare-observability": {
      "type": "http",
      "url": "https://observability.mcp.cloudflare.com/mcp"
    },
    "clickhouse": {
      "type": "http",
      "url": "https://mcp.clickhouse.cloud/mcp"
    },
    "AbletonMCP": {
      "command": "uvx",
      "args": ["ableton-mcp"]
    },
    "magic": {
      "command": "npx",
      "args": ["-y", "@magicuidesign/mcp@latest"]
    }
  }
}
```

### プロジェクトごとの無効化（コンテキストウィンドウ管理）

`~/.claude.json`の`projects.[path].disabledMcpServers`に設定:

```json
{
  "disabledMcpServers": [
    "playwright",
    "cloudflare-workers-builds",
    "cloudflare-workers-bindings",
    "cloudflare-observability",
    "cloudflare-docs",
    "clickhouse",
    "AbletonMCP",
    "context7",
    "magic"
  ]
}
```

**ポイント**: 14個のMCPを設定しているが、プロジェクトごとに5-6個のみ有効化。コンテキストウィンドウを健全に保つ。

---

## Key Hooks設定

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "tool == \"Bash\" && tool_input.command matches \"(npm|pnpm|yarn|cargo|pytest)\"",
        "hooks": [{
          "type": "command",
          "command": "if [ -z \"$TMUX\" ]; then echo '[Hook] Consider tmux for long-running commands'; fi"
        }]
      },
      {
        "matcher": "tool == \"Write\" && tool_input.file_path matches \"\\.md$\" && !(tool_input.file_path matches \"(README|CLAUDE)\")",
        "hooks": [{
          "type": "command",
          "command": "echo '[Hook] Blocking unnecessary .md file creation'"
        }]
      },
      {
        "matcher": "tool == \"Bash\" && tool_input.command matches \"git push\"",
        "hooks": [{
          "type": "command",
          "command": "code --wait --diff HEAD~1 HEAD"
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\.(ts|tsx|js|jsx)$\"",
        "hooks": [{
          "type": "command",
          "command": "npx prettier --write \"$TOOL_INPUT_FILE_PATH\""
        }]
      },
      {
        "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\.(ts|tsx)$\"",
        "hooks": [{
          "type": "command",
          "command": "npx tsc --noEmit"
        }]
      },
      {
        "matcher": "tool == \"Edit\"",
        "hooks": [{
          "type": "command",
          "command": "grep -l 'console.log' \"$TOOL_INPUT_FILE_PATH\" && echo '[Hook] Warning: console.log found'"
        }]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [{
          "type": "command",
          "command": "git diff --name-only | xargs grep -l 'console.log' 2>/dev/null && echo '[Audit] console.log found in modified files'"
        }]
      }
    ]
  }
}
```

---

## Rules構造

```bash
~/.claude/rules/
  security.md       # 必須セキュリティチェック
  coding-style.md   # 不変性、ファイルサイズ制限
  testing.md        # TDD、80%カバレッジ
  git-workflow.md   # Conventional commits
  agents.md         # サブエージェント委譲ルール
  patterns.md       # APIレスポンスフォーマット
  performance.md    # モデル選択（Haiku vs Sonnet vs Opus）
  hooks.md          # フックドキュメント
```

### security.md 例

```markdown
# セキュリティルール

## 禁止事項
- ハードコードされたシークレット、API キー、パスワード
- `.env`ファイルの内容をコードに直接記載
- SQLインジェクションを可能にするクエリ構築

## 必須事項
- ユーザー入力は必ずサニタイズ
- 機密データはログに出力しない
- OWASP Top 10を意識した実装
```

### coding-style.md 例

```markdown
# コーディングスタイル

## ファイル構成
- 1ファイル500行以下を推奨
- 関連する機能はモジュールにまとめる
- テストファイルは対象と同じ階層に配置

## TypeScript
- 明示的な型定義を優先（`any`禁止）
- イミュータブルな操作を優先
- 副作用は関数の末尾にまとめる
```

---

## Subagents構造

```bash
~/.claude/agents/
  planner.md            # 機能をブレークダウン
  architect.md          # システム設計
  tdd-guide.md          # テスト駆動開発
  code-reviewer.md      # 品質レビュー
  security-reviewer.md  # 脆弱性スキャン
  build-error-resolver.md
  e2e-runner.md         # Playwrightテスト
  refactor-cleaner.md   # デッドコード削除
  doc-updater.md        # ドキュメント同期
```

### planner.md 例

```yaml
---
name: planner
description: Break down features into implementation tasks
tools: Read, Glob, Grep
model: sonnet
---

# Feature Planner

## 役割
機能要件を実装タスクに分解する

## プロセス
1. 要件を理解するために関連コードを読む
2. 既存のパターンと規約を特定
3. 実装ステップをタスクリストとして出力

## 出力形式
- Markdown チェックリスト
- 各タスクに推定難易度（S/M/L）を付与
```

### code-reviewer.md 例

```yaml
---
name: code-reviewer
description: Review code for quality and security issues
tools: Read, Glob, Grep
model: sonnet
---

# Code Reviewer

## チェック項目
- [ ] エラーハンドリングが適切か
- [ ] テストカバレッジは十分か
- [ ] パフォーマンス問題はないか
- [ ] セキュリティ脆弱性はないか
- [ ] コーディング規約に従っているか

## レビューフォーマット
```markdown
## Summary
[1-2文の概要]

## Issues Found
- [Critical/Warning/Info] 説明

## Suggestions
- 改善提案
```
```

---

## セッションログテンプレート

`~/.claude/sessions/YYYY-MM-DD-topic.tmp`:

```markdown
# Session: [トピック名]
Date: YYYY-MM-DD
Start: HH:MM
End: HH:MM

## Current State
- 現在の作業状態

## Completed
- [x] 完了したタスク1
- [x] 完了したタスク2

## In Progress
- [ ] 進行中タスク

## Blockers
- ブロッカーがあれば記載

## Key Decisions
- 重要な決定事項

## What Worked
- 成功したアプローチ（証拠付き）

## What Didn't Work
- 失敗したアプローチ

## Not Attempted
- 未試行のアプローチ

## Context for Next Session
- 次回セッションに必要なコンテキスト
```

---

## コンテキストファイル例

### dev.md（開発モード）

```markdown
# Development Context

## Focus
- 機能実装に集中
- 品質よりスピードを優先（後でレビュー）
- テストは基本的なケースのみ

## Constraints
- 既存パターンに従う
- 大規模リファクタリングは避ける
```

### review.md（レビューモード）

```markdown
# Review Context

## Focus
- コード品質とセキュリティ
- エッジケースの考慮
- パフォーマンス影響の評価

## Checklist
- セキュリティ脆弱性
- エラーハンドリング
- テストカバレッジ
- ドキュメント
```

### research.md（リサーチモード）

```markdown
# Research Context

## Focus
- 行動前に徹底的に調査
- 複数のアプローチを比較
- トレードオフを文書化

## Output
- 選択肢のリスト
- 各選択肢のPros/Cons
- 推奨事項と理由
```

---

## ステータスライン設定例

ユーザー、ディレクトリ、gitブランチ（dirty インジケータ付き）、残りコンテキスト%、モデル、時刻、todo数を表示:

```
affoon:~ ctx:65% Opus 4.5 19:52
■ plan mode on (shift+tab to cycle)
```

---

## tmux設定例

### 開発サーバー用セッション作成

```bash
#!/bin/bash
# start-dev.sh

# フロントエンドセッション
tmux new-session -d -s frontend
tmux send-keys -t frontend 'cd ~/project && npm run dev' C-m

# バックエンドセッション
tmux new-session -d -s backend
tmux send-keys -t backend 'cd ~/project && npm run server' C-m

echo "Development servers started in tmux sessions"
echo "Use 'tmux attach -t frontend' or 'tmux attach -t backend' to view"
```

### Claude用tmuxレイアウト

```bash
# 2ペインレイアウト（左: Claude, 右: ログ）
tmux new-session -d -s claude-dev
tmux split-window -h -t claude-dev
tmux send-keys -t claude-dev:0.0 'claude' C-m
tmux send-keys -t claude-dev:0.1 'tail -f ~/.claude/logs/latest.log' C-m
tmux attach -t claude-dev
```

---

## Git Worktree設定例

```bash
# メインリポジトリにいる状態で

# Feature A用worktree作成
git worktree add ../project-feature-a -b feature-a

# Feature B用worktree作成
git worktree add ../project-feature-b -b feature-b

# Refactor用worktree作成
git worktree add ../project-refactor -b refactor-cleanup

# 各worktreeで別々のClaudeセッションを起動
# Terminal 1:
cd ../project-feature-a && claude

# Terminal 2:
cd ../project-feature-b && claude

# Terminal 3:
cd ../project-refactor && claude
```

### Worktree管理コマンド

```bash
# worktree一覧
git worktree list

# worktree削除（ブランチマージ後）
git worktree remove ../project-feature-a

# 全worktreeをプルーン（削除済みのものをクリーンアップ）
git worktree prune
```

---

## 継続学習スキル設定

### evaluate-session.sh

```bash
#!/bin/bash
# ~/.claude/skills/continuous-learning/evaluate-session.sh

SESSION_DIR="$HOME/.claude/sessions"
LEARNED_DIR="$HOME/.claude/skills/learned"
TODAY=$(date +%Y-%m-%d)

# 今日のセッションファイルを検索
SESSION_FILE=$(find "$SESSION_DIR" -name "${TODAY}*.tmp" -type f | head -1)

if [ -z "$SESSION_FILE" ]; then
  exit 0
fi

# パターン抽出のためのマーカーを検索
if grep -q "PATTERN_WORTH_SAVING" "$SESSION_FILE"; then
  mkdir -p "$LEARNED_DIR"

  # パターンを新しいスキルファイルとして抽出
  PATTERN_NAME=$(grep "PATTERN_NAME:" "$SESSION_FILE" | cut -d: -f2 | tr -d ' ')
  if [ -n "$PATTERN_NAME" ]; then
    grep -A 100 "PATTERN_START" "$SESSION_FILE" | grep -B 100 "PATTERN_END" > "$LEARNED_DIR/${PATTERN_NAME}.md"
    echo "[ContinuousLearning] Saved new pattern: $PATTERN_NAME"
  fi
fi
```

### フック設定

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/skills/continuous-learning/evaluate-session.sh"
          }
        ]
      }
    ]
  }
}
```
