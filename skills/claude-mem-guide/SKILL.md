---
name: claude-mem-guide
description: claude-mem plugin guide for persistent memory across Claude Code sessions. Setup, troubleshooting, search usage, worker management. Use when user mentions claude-mem, persistent memory, session memory, or memory search.
version: 1.0.0
author: asgr-base
createDate: 2026-02-05
updateDate: 2026-02-12
license: Apache-2.0
---

# claude-mem ガイド

## 概要

claude-memはClaude Codeの永続メモリプラグイン。セッション間でコンテキストを自動保持し、過去の作業履歴を検索可能にする。

## クイックリファレンス

| 問題 | 解決策 |
|------|--------|
| localhost:37777にアクセスできない | ワーカー未起動 → `worker-cli.js start` |
| "Bun is required" エラー | Bunインストール後、PATH設定を確認 |
| MCPツールがエラー | ワーカー起動後、Claude Code再起動 |
| メモリが記録されない | プラグイン再インストール、ワーカー再起動 |
| **hooksが二重実行される** | **`~/.claude/settings.json`から手動hooks設定を削除（enabledPluginsで自動hook）** |
| **FOREIGN KEY constraint failed** | **DBリセット：`rm ~/.claude-mem/claude-mem.db*`後ワーカー再起動** |
| hookでbunが見つからない | `~/.zshenv`にPATH設定を追加 |
| **memorySessionId not yet captured** | **claudeプロバイダーに切り替え（推奨）、またはワークアラウンド適用** |
| Gemini 429 quota exceeded | 別モデルに切り替え、またはclaudeプロバイダーを使用 |
| **Unknown event type: session-complete** | **hooks.jsonから該当行を削除後、Claude Code再起動（v9.0.17ビルドバグ）** |

## インストール

```bash
# 1. プラグイン追加
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem  # user scope推奨

# 2. Bun インストール（未インストールの場合）
curl -fsSL https://bun.sh/install | bash

# 3. PATH設定（重要：非対話シェルでも読み込まれるよう ~/.zshenv に追加）
echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.zshenv
echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.zshenv

# 4. ワーカー起動
source ~/.zshenv
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | head -1)
node ${PLUGIN_DIR}scripts/worker-cli.js start

# 5. Claude Code再起動
```

## LLM API設定（必須）

IMPORTANT: Summary/Observationの生成にはLLM APIが必要。

### 推奨：claudeプロバイダー（Claude Max/APIキー）

**IMPORTANT**: Gemini/OpenRouterプロバイダーには`memorySessionId not yet captured`バグ（Issue #623）があります。**claudeプロバイダーを推奨**。

claudeプロバイダーはClaude Code CLI + Agent SDK経由で動作し、以下のいずれかで認証：
- **Claude Maxサブスクリプション**（追加料金なし）
- **Anthropic APIキー**（従量課金）

```json
{
  "CLAUDE_MEM_PROVIDER": "claude",
  "CLAUDE_MEM_MODEL": "claude-sonnet-4-5"
}
```

### 代替：Gemini API（バグあり・非推奨）

**WARNING**: Gemini/OpenRouterはstatelessプロバイダーのため、`memorySessionId`をキャプチャできず、無限クラッシュリカバリーループが発生する可能性があります（Issue #623）。PR #615がマージされるまで非推奨。

使用する場合：
1. [Google AI Studio](https://aistudio.google.com/apikey)でAPIキーを取得
2. `~/.claude-mem/settings.json`を編集：
   ```json
   {
     "CLAUDE_MEM_PROVIDER": "gemini",
     "CLAUDE_MEM_GEMINI_API_KEY": "AIza...",
     "CLAUDE_MEM_GEMINI_MODEL": "gemini-2.0-flash"
   }
   ```
3. ワーカー再起動：`node ${PLUGIN_DIR}scripts/worker-cli.js restart`

**注意**: 無料枠を超えると429エラー（quota exceeded）が発生。異なるモデルは異なるクォータを持つ。

### プロバイダー比較

| プロバイダー | 設定 | memorySessionId | 推奨度 |
|-------------|------|-----------------|--------|
| **claude** | `"CLAUDE_MEM_PROVIDER": "claude"` | ✓ 正常動作 | **推奨** |
| gemini | `"CLAUDE_MEM_PROVIDER": "gemini"` | ✗ バグあり | 非推奨 |
| openrouter | `"CLAUDE_MEM_PROVIDER": "openrouter"` | ✗ バグあり | 非推奨 |

## Hooks

プラグインインストール時に`enabledPlugins`経由で自動でhooksが設定される。手動設定は不要。

**WARNING**: `~/.claude/settings.json`にclaude-memのhooksを手動で追加しないこと。`enabledPlugins`による自動hookと二重実行になり、全てのobservation/summaryが2回ずつ処理される。手動hooks設定がある場合は削除すること。

### 各hookの役割

| Hook | 機能 |
|------|------|
| `SessionStart` | コンテキスト生成、ユーザーメッセージ準備 |
| `UserPromptSubmit` | セッション初期化（session_id取得） |
| `PostToolUse` | ツール使用後にobservation記録 |
| `Stop` | セッション終了時にサマリー生成 |

## ディレクトリ構成

| パス | 内容 |
|------|------|
| `~/.claude-mem/` | データディレクトリ |
| `~/.claude-mem/settings.json` | claude-mem設定ファイル |
| `~/.claude-mem/logs/` | ログファイル |
| `~/.claude-mem/claude-mem.db` | SQLiteデータベース |
| `~/.claude/plugins/cache/thedotmack/claude-mem/` | プラグイン本体 |

## ワーカー管理

```bash
# プラグインディレクトリを取得
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | head -1)

# ワーカーコマンド
node ${PLUGIN_DIR}scripts/worker-cli.js start    # 起動
node ${PLUGIN_DIR}scripts/worker-cli.js stop     # 停止
node ${PLUGIN_DIR}scripts/worker-cli.js restart  # 再起動
node ${PLUGIN_DIR}scripts/worker-cli.js status   # 状態確認

# ポート確認
lsof -i :37777
```

## 動作確認

### 1. ワーカー確認

```bash
curl -s http://localhost:37777/api/health
# 期待出力: {"status":"ok",...}
```

### 2. 統計確認

```bash
curl -s http://localhost:37777/api/stats
# 期待出力: {"worker":{...},"database":{"observations":N,"sessions":N,...}}
```

### 3. ログでhook動作確認

```bash
cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log | grep -E "HOOK|INIT_COMPLETE"
# 期待出力: [HOOK ] → PostToolUse: ... / INIT_COMPLETE | sessionDbId=...
```

### 正常動作の指標

| 項目 | 確認方法 |
|------|---------|
| ワーカー起動 | `lsof -i :37777` でbunプロセスが表示 |
| セッション初期化 | ログに`INIT_COMPLETE`が記録 |
| observation記録 | `api/stats`で`observations`が増加 |
| hook実行 | ログに`[HOOK ]`エントリが記録 |

## MCPツール（3層検索）

IMPORTANT: トークン節約のため、必ず3層ワークフローに従うこと。

### 1. search（インデックス検索）

```
mcp__plugin_claude-mem_mcp-search__search
パラメータ: query, limit, project, type, obs_type, dateStart, dateEnd
```

軽量なインデックスを返す（~50-100トークン/結果）。まずこれで候補を絞る。

### 2. timeline（コンテキスト取得）

```
mcp__plugin_claude-mem_mcp-search__timeline
パラメータ: anchor (observation ID) または query, depth_before, depth_after
```

特定の観察の前後コンテキストを取得。

### 3. get_observations（詳細取得）

```
mcp__plugin_claude-mem_mcp-search__get_observations
パラメータ: ids (配列、必須)
```

フィルタ済みIDの完全な詳細を取得。最後に使用。

## 設定（~/.claude-mem/settings.json）

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `CLAUDE_MEM_MODEL` | claude-sonnet-4-5 | 圧縮用モデル |
| `CLAUDE_MEM_WORKER_PORT` | 37777 | ワーカーポート |
| `CLAUDE_MEM_DATA_DIR` | ~/.claude-mem | データ保存先 |
| `CLAUDE_MEM_LOG_LEVEL` | INFO | ログレベル |
| `CLAUDE_MEM_SKIP_TOOLS` | (複数) | 記録除外ツール |

## Webインターフェース

http://localhost:37777 でリアルタイムメモリを確認可能。

## セッション再開

### 自動コンテキスト注入（推奨）

IMPORTANT: 新しいセッションを開始するだけで、過去のコンテキストが自動注入される。特別な操作は不要。

SessionStartフックが以下を自動注入：

| 注入データ | デフォルト設定 |
|-----------|--------------|
| 最近のobservations | 50件 (`CLAUDE_MEM_CONTEXT_OBSERVATIONS`) |
| 過去のセッションサマリー | 10件 (`CLAUDE_MEM_CONTEXT_SESSION_COUNT`) |

キーワードを含めて依頼するだけでOK：

```
前回のclaude-mem設定作業の続きをお願いします。
```

### 3層Progressive Disclosure

| 層 | 内容 | アクセス方法 |
|----|------|-------------|
| 第1層 | observationのタイトル、トークンコスト推定 | 自動表示 |
| 第2層 | 詳細検索（概念、ファイル、タイプ、キーワード） | 質問するとMCPツールで自動検索 |
| 第3層 | 完全な履歴・ソースコード | 直接アクセス |

### /clearコマンド

`/clear`を使用してもセッションは継続。コンテキストが再注入され、observationキャプチャも継続。

### 手動でSession Summaryを参照

1. http://localhost:37777 でWebインターフェースを開く
2. 再開したいセッションのSummaryをコピー
3. 新しいセッションで貼り付けて依頼

### コンテキスト注入設定（~/.claude-mem/settings.json）

| 設定 | デフォルト | 説明 |
|------|-----------|------|
| `CLAUDE_MEM_CONTEXT_OBSERVATIONS` | 50 | 参照observations最大数 |
| `CLAUDE_MEM_CONTEXT_FULL_COUNT` | 5 | 詳細narrative取得数 |
| `CLAUDE_MEM_CONTEXT_SESSION_COUNT` | 10 | 参照セッション数 |
| `CLAUDE_MEM_CONTEXT_SHOW_LAST_SUMMARY` | true | 最後のsummary表示 |

### データ構造

| データ | 内容 | 用途 |
|--------|------|------|
| **Session Summary** | INVESTIGATED/LEARNED/COMPLETED/NEXT_STEPS | セッション全体の要約 |
| **Observations** | 各ツール使用の詳細（facts, narrative, concepts） | 詳細なコンテキスト |

Session Summaryは要約、Observationsに詳細が残る。詳細が必要な場合は`search` → `get_observations`で取得。

## トラブルシューティング

### bunがPATHで見つからない

非対話シェル（hooks実行環境）では`~/.zshrc`が読み込まれない。`~/.zshenv`にPATH設定を追加：

```bash
# ~/.zshenv に追加
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
```

### ワーカーが起動しない

```bash
# ログ確認
cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log | tail -50

# Bunパス確認
which bun || echo "Bunがインストールされていない"

# フルパスで確認
$HOME/.bun/bin/bun --version
```

### hooksが動作しない

1. `enabledPlugins`でclaude-memが有効か確認（`~/.claude/settings.json`）
2. bunのPATHが`~/.zshenv`に設定されているか確認
3. ワーカーが起動しているか確認（`curl -s http://localhost:37777/api/health`）
4. Claude Codeを再起動

### observationsが記録されない

1. ログで`INIT_COMPLETE`が記録されているか確認
2. ログで`[HOOK ]`エントリが記録されているか確認
3. LLM APIキーが設定されているか確認（上記「LLM API設定」参照）
4. FOREIGN KEYエラーが出ていないか確認（出ていればDBリセット）

### Generator exited unexpectedly エラー

LLM APIキーが未設定または無効。`~/.claude-mem/settings.json`でプロバイダーとAPIキーを確認：

```bash
# ログでエラー確認
cat ~/.claude-mem/logs/claude-mem-$(date +%Y-%m-%d).log | grep -i "error"
```

### memorySessionId not yet captured エラー（Issue #623）

**症状**:
- `Cannot store observations: memorySessionId not yet captured`エラーが繰り返し発生
- 無限のクラッシュリカバリーループ
- キューが蓄積（queueDepth増加）
- observationsが記録されない

**原因**: Gemini/OpenRouterはstatelessプロバイダーで、`memorySessionId`を返さないため発生。

**推奨解決策**: claudeプロバイダーに切り替え

```json
{
  "CLAUDE_MEM_PROVIDER": "claude"
}
```

**一時的ワークアラウンド**（Gemini/OpenRouterを使い続ける場合）:

```bash
# 1. ワーカー停止
pkill -f "worker-service"

# 2. stuck queueをクリア
sqlite3 ~/.claude-mem/claude-mem.db "DELETE FROM pending_messages;"

# 3. 壊れたセッションをfailedにマーク
sqlite3 ~/.claude-mem/claude-mem.db "UPDATE sdk_sessions SET status = 'failed' WHERE memory_session_id IS NULL OR memory_session_id = '';"

# 4. ワーカー再起動
source ~/.zshenv && node ${PLUGIN_DIR}scripts/worker-cli.js start
```

**関連Issue**: [#623 - Crash-recovery loop when memory_session_id is not captured](https://github.com/thedotmack/claude-mem/issues/623)

**修正予定**: PR #615（generate memorySessionId for stateless providers）がマージされれば解消

### hooks二重実行

**症状**:
- ログで全てのhookエントリが2回ずつ記録される
- observation/summaryが重複処理される
- 処理負荷が倍増

**原因**: `enabledPlugins`によるプラグイン自動hookと、`~/.claude/settings.json`内の手動hooks設定が共存

**解決策**: `~/.claude/settings.json`からclaude-memのhooks設定（SessionStart, UserPromptSubmit, PostToolUse, Stop）を削除。`enabledPlugins`のみで動作する。

### FOREIGN KEY constraint failed エラー

**症状**:
- `FOREIGN KEY constraint failed`エラーでGeneratorが停止
- `Generator exited unexpectedly`が続く
- observationsが記録されない

**原因**: ワーカー再起動時にセッションIDが変わり、古いセッションデータとの参照関係が壊れる。頻発する（92回/2日間の実績あり）。ワーカー再起動のたびに発生する可能性が高い

**解決策**: DBリセット

```bash
# 1. DBファイルを削除（observations/summariesは失われる）
rm ~/.claude-mem/claude-mem.db ~/.claude-mem/claude-mem.db-wal ~/.claude-mem/claude-mem.db-shm 2>/dev/null

# 2. ワーカーが自動で新DBを作成（health checkで確認）
curl -s http://localhost:37777/api/health
```

**関連**: ワーカー再起動時にIssue #817（stale memory_session_id）の警告が出ることがある。これ自体は自動処理されるが、FOREIGN KEYエラーを伴う場合はDBリセットが必要。

### Gemini 429 quota exceeded エラー

**症状**: `Quota exceeded for metric: generate_content_paid_tier_input_token_count`

**原因**: Gemini APIの無料枠を超過

**解決策**:
1. 30秒待ってリトライ（クォータがリセットされる）
2. 別のモデルに切り替え（異なるモデルは異なるクォータ）
3. claudeプロバイダーに切り替え（推奨）

### Unknown event type: session-complete エラー

**症状**: Stopフック実行時に`Unknown event type: session-complete`エラーが毎回表示される

**原因**: v9.0.17のビルドバグ。`hooks.json`が`session-complete`イベントを送信するが、`worker-service.cjs`にハンドラが未バンドル

**解決策**:

```bash
# hooks.jsonからsession-complete行を削除
PLUGIN_DIR=$(ls -d ~/.claude/plugins/cache/thedotmack/claude-mem/*/ | sort -V | tail -1)
# ${PLUGIN_DIR}hooks/hooks.json のStop内から session-complete のブロックを削除
# その後 Claude Codeを再起動（現セッション中はhooksがメモリにキャッシュされているため）
```

**注意**: プラグイン更新時にhooks.jsonが上書きされ再発する可能性あり。再発した場合は同じ修正を再適用。

### MCPツールがタイムアウト

1. ワーカー起動確認: `lsof -i :37777`
2. 起動していなければ: `worker-cli.js start`
3. Claude Code再起動

### プライバシー制御

機密情報を記録から除外するには `<private>` タグを使用：

```
<private>
この内容は記録されない
</private>
```

## オブザーバーパターンの運用指針

### デュアルエージェント方式は非推奨

プライマリセッションと並行してオブザーバーエージェントを実行するデュアルエージェントパターンは、**成功率が低い**（Insight分析: 12セッション中、大半が「一部達成」「やや有用」評価）。

**主な問題**:
- オブザーバーがプライマリセッションの活動に対する可視性が限定的
- 最小限の観察しか生成できずにセッションが終了する
- デュアルセッションのオーバーヘッドが出力品質に見合わない

### 推奨: セッション終了時サマリー方式

重要なセッションの終了時に、以下のプロンプトを実行して主要な発見事項を一度にキャプチャする:

```
このセッションの主要な発見事項を構造化されたobservationsとしてまとめてください:
- 調査で判明したこと
- 解決した問題と解決策
- 未解決の課題と次のステップ
- 学んだ教訓（今後のセッションで再利用可能なもの）
```

この方式により、オブザーバーエージェントのオーバーヘッドなしに、より質の高いメモリレコードを生成できる。

## スキル

| スキル | 説明 |
|--------|------|
| `claude-mem:make-plan` | 実装計画作成 |
| `claude-mem:do` | サブエージェントで計画実行 |

## 関連リソース

- [GitHub - thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
- ログ: `~/.claude-mem/logs/`
- 設定: `~/.claude-mem/settings.json`

---

**Version**: 1.8.0
**Last Updated**: 2026-02-12

**更新履歴**:
- v1.8.0 (2026-02-12): オブザーバーパターン運用指針を追加（Insight分析結果に基づく）。セッション終了時サマリー方式を推奨。
- v1.7.0 (2026-02-06): session-completeビルドバグ（v9.0.17）の対処を追加。
- v1.6.0 (2026-02-06): hooks二重実行の問題と対処を追加。FOREIGN KEY constraintエラーの対処を追加。enabledPluginsによる自動hook登録の注意事項を明記。
- v1.5.0 (2026-02-05): プロバイダー比較を追加。claudeプロバイダーを推奨に変更。Issue #623（memorySessionId not yet captured）のワークアラウンドを追加。Gemini 429エラー対処を追加。
