# Claude Code 基礎編詳細

## Skills & Commands

### Skills

スキルはルールに似た機能で、特定のスコープやワークフローに制限される。特定のワークフローを実行する際のプロンプトのショートカット。

**活用例**:
- 長いコーディングセッション後に `/refactor-clean` でデッドコードと不要な.mdファイルを削除
- テストが必要なら `/tdd`, `/e2e`, `/test-coverage`
- 複数コマンドを1つのプロンプトでチェーン実行可能

**Codemapスキル**:
チェックポイントでcodemapを更新するスキルを作成可能。Claudeがコードベースを探索でコンテキストを消費せずに素早くナビゲートできる。

### Commands

コマンドはスラッシュコマンドで実行されるスキル。格納場所が異なる:
- **Skills**: `~/.claude/skills` - より広いワークフロー定義
- **Commands**: `~/.claude/commands` - 素早く実行可能なプロンプト

```bash
# スキル構造例
~/.claude/skills/
  pmx-guidelines.md      # プロジェクト固有パターン
  coding-standards.md    # 言語ベストプラクティス
  tdd-workflow/          # README.mdを含む複数ファイルスキル
  security-review/       # チェックリストベーススキル
```

---

## Hooks

フックはトリガーベースの自動化で、特定のイベントで発火する。スキルとは異なり、ツール呼び出しとライフサイクルイベントに制限される。

### Hook Types

| Type | 説明 | 用途 |
|------|------|------|
| **PreToolUse** | ツール実行前 | バリデーション、リマインダー |
| **PostToolUse** | ツール実行後 | フォーマット、フィードバックループ |
| **UserPromptSubmit** | メッセージ送信時 | 入力検証 |
| **Stop** | Claude応答完了時 | セッション終了処理、学習抽出 |
| **PreCompact** | コンテキスト圧縮前 | 重要な状態をファイルに保存 |
| **Notification** | 許可リクエスト時 | 通知カスタマイズ |

### 長時間コマンド前のtmuxリマインダー

```json
{
  "PreToolUse": [
    {
      "matcher": "tool == \"Bash\" && tool_input.command matches \"(npm|pnpm|yarn|cargo|pytest)\"",
      "hooks": [
        {
          "type": "command",
          "command": "if [ -z \"$TMUX\" ]; then echo '[Hook] Consider tmux for long-running commands'; fi"
        }
      ]
    }
  ]
}
```

### 戦略的コンパクト提案フック

```bash
#!/bin/bash
# Strategic Compact Suggester
# PreToolUseでEdit/Write操作時に実行

COUNTER_FILE="/tmp/claude-tool-count-$$"
THRESHOLD=${COMPACT_THRESHOLD:-50}

if [ -f "$COUNTER_FILE" ]; then
  count=$(cat "$COUNTER_FILE")
  count=$((count + 1))
  echo "$count" > "$COUNTER_FILE"
else
  echo "1" > "$COUNTER_FILE"
  count=1
fi

if [ "$count" -eq "$THRESHOLD" ]; then
  echo "[StrategicCompact] $THRESHOLD tool calls reached - consider /compact"
fi
```

### メモリ永続化フック

```json
{
  "hooks": {
    "PreCompact": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/pre-compact.sh"
      }]
    }],
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/session-start.sh"
      }]
    }],
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/memory-persistence/session-end.sh"
      }]
    }]
  }
}
```

**各スクリプトの役割**:
- `pre-compact.sh`: 圧縮イベントをログ、アクティブセッションファイルを更新
- `session-start.sh`: 最近のセッションファイル（7日以内）を確認、利用可能なコンテキストと学習済みスキルを通知
- `session-end.sh`: 日次セッションファイルをテンプレートで作成/更新、開始/終了時刻を追跡

**Pro tip**: `hookify`プラグインを使用すると、JSONを手動で書く代わりに会話形式でフックを作成できる。`/hookify`を実行して何が欲しいか説明するだけ。

---

## Subagents

サブエージェントは、オーケストレーター（メインClaude）がタスクを委譲できるプロセス。限定されたスコープを持ち、バックグラウンドまたはフォアグラウンドで実行可能。メインエージェントのコンテキストを解放する。

サブエージェントはスキルとうまく連携する。スキルのサブセットを実行できるサブエージェントにタスクを委譲し、それらのスキルを自律的に使用させることができる。また、特定のツール権限でサンドボックス化も可能。

```bash
# サブエージェント構造例
~/.claude/agents/
  planner.md            # 機能実装の計画
  architect.md          # システム設計の決定
  tdd-guide.md          # テスト駆動開発
  code-reviewer.md      # 品質/セキュリティレビュー
  security-reviewer.md  # 脆弱性分析
  build-error-resolver.md
  e2e-runner.md
  refactor-cleaner.md
```

**重要**: 適切なスコープ設定のため、サブエージェントごとに許可するツール、MCP、権限を設定する。

### モデル指定

```yaml
---
name: quick-search
description: Fast file search
tools: Glob, Grep
model: haiku  # 安価で高速
---
```

---

## Rules & Memory

`.rules`フォルダには、Claudeが**常に**従うべきベストプラクティスを記載した`.md`ファイルを配置。2つのアプローチがある:

1. **単一CLAUDE.md**: 全てを1ファイルに（ユーザーまたはプロジェクトレベル）
2. **Rulesフォルダ**: 関心事ごとにグループ化されたモジュラー`.md`ファイル

```bash
~/.claude/rules/
  security.md       # ハードコードされたシークレット禁止、入力検証
  coding-style.md   # 不変性、ファイル構成
  testing.md        # TDDワークフロー、80%カバレッジ
  git-workflow.md   # コミット形式、PRプロセス
  agents.md         # サブエージェントへの委譲タイミング
  performance.md    # モデル選択、コンテキスト管理
```

**ルール例**:
- コードベースに絵文字を使用しない
- フロントエンドで紫系の色を避ける
- デプロイ前に必ずコードをテスト
- メガファイルよりモジュラーコードを優先
- console.logをコミットしない

---

## MCPs (Model Context Protocol)

MCPはClaudeを外部サービスに直接接続する。APIの代替ではなく、より柔軟な情報ナビゲーションを可能にするプロンプト駆動のラッパー。

**例**: Supabase MCPを使うと、Claudeがコピー&ペーストなしで特定のデータを取得したり、アップストリームで直接SQLを実行できる。データベース、デプロイメントプラットフォームなども同様。

**Chrome in Claude**: Claudeが自律的にブラウザを制御できる組み込みプラグインMCP。

### コンテキストウィンドウ管理が重要

MCPは選択的に使用すること。全MCPをユーザー設定に保持しつつ、**未使用のものは全て無効化**。`/plugins`に移動してスクロールするか、`/mcp`を実行。

圧縮前の200kコンテキストウィンドウが、有効なツールが多すぎると70kしか残らない可能性がある。パフォーマンスが著しく低下する。

**経験則**: 設定に20-30個のMCPを持ち、有効は10個未満/アクティブツールは80未満に保つ。

### MCP vs CLI + Skills

MCPをCLI + Skillsに変換することでコンテキストを節約できる:
- GitHub MCP → `/gh-pr`コマンド（`gh pr create`をラップ）
- Supabase MCP → Supabase CLIを使用するスキル

**Lazy Loading**: 最近のClaude Codeはlazy loadingによりMCPが最初からコンテキストを消費しなくなった。ただしトークン使用量とコストはCLI + Skillsアプローチで最適化可能。

---

## Plugins

プラグインは、面倒な手動セットアップの代わりに簡単にインストールできるツールをパッケージ化したもの。プラグインはスキル+MCPの組み合わせ、またはフック/ツールのバンドルにできる。

### インストール

```bash
# マーケットプレイスを追加
claude plugin marketplace add https://github.com/mixedbread-ai/mgrep

# Claudeを開き、/pluginsを実行、新しいマーケットプレイスを見つけてインストール
```

### LSPプラグイン

エディタ外でClaude Codeを頻繁に実行する場合に特に有用。Language Server Protocolにより、IDEを開かずにリアルタイムの型チェック、定義へのジャンプ、インテリジェントな補完が可能。

```bash
# 有効なプラグイン例
typescript-lsp@claude-plugins-official  # TypeScriptインテリジェンス
pyright-lsp@claude-plugins-official     # Python型チェック
hookify@claude-plugins-official         # フック作成を会話形式で
mgrep@Mixedbread-Grep                   # ripgrepより優れた検索
```

**MCPと同じ警告**: コンテキストウィンドウに注意。

---

## tmux活用

長時間実行コマンド用。Claudeが実行するログ/bashプロセスをストリーミングして監視。

```bash
tmux new -s dev
# Claudeがここでコマンドを実行、デタッチして再アタッチ可能
tmux attach -t dev
```

**ログ確認**:
```bash
# フロントエンドログ
tmux attach -t pmx-frontend

# バックエンドログ
tmux attach -t pmx-backend
```

**tmuxショートカット（アタッチ後）**:
- `Ctrl+b d`: デタッチ（実行継続）
- `Ctrl+b [`: スクロールモード（矢印で移動、qで終了）
- `Ctrl+c`: サーバー停止

---

## mgrep

`mgrep`はripgrep/grepから大幅に改善されたツール。様々なタスクで従来のgrepやripgrep（Claudeがデフォルトで使用）と比較して平均約半分のトークン削減効果がある。

```bash
mgrep "function handleSubmit"  # ローカル検索
mgrep --web "Next.js 15 app router changes"  # Web検索
```

プラグインマーケットプレイス経由でインストールし、`/mgrep`スキルを使用。

---

## エディタ連携

エディタは必須ではないが、Claude Codeワークフローにプラス・マイナス両方の影響を与える可能性がある。Claude Codeはどのターミナルからでも動作するが、有能なエディタと組み合わせることでリアルタイムのファイル追跡、素早いナビゲーション、統合コマンド実行が可能になる。

### Zed（推奨）

軽量、高速、高度にカスタマイズ可能なRustベースエディタ。

**Claude Codeとの相性が良い理由**:
- **Agent Panel統合**: Claudeが編集するファイル変更をリアルタイムで追跡。Claudeが参照するファイル間を素早くジャンプ
- **パフォーマンス**: Rust製、即座に起動、大規模コードベースでもラグなし
- **CMD+Shift+Rコマンドパレット**: 全カスタムスラッシュコマンド、デバッガー、ツールに検索可能なUIで素早くアクセス
- **最小限のリソース使用**: 重い操作中にClaudeとシステムリソースを競合しない
- **Vimモード**: 完全なvimキーバインディング対応

**ベストプラクティス**:
1. 画面分割 - 片側にClaude Code付きターミナル、もう片側にエディタ
2. `Ctrl+G` - Claudeが現在作業中のファイルをZedで素早く開く
3. 自動保存 - Claudeのファイル読み込みが常に最新になるよう有効化
4. Git統合 - エディタのgit機能でコミット前にClaudeの変更をレビュー
5. ファイルウォッチャー - ほとんどのエディタは変更されたファイルを自動リロード、有効確認

### VSCode / Cursor

ターミナル形式で使用可能（`\ide`でLSP機能有効化、プラグインでやや冗長に）。または、エディタとより統合されマッチするUIを持つ拡張機能を選択可能。
