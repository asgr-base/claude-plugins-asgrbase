---
name: m365-ai-bridge-manager
description: Manage Microsoft Teams integration via M365 AI Bridge Chrome Extension and MCP tools. Read channel/DM messages, queue replies, download attachments, check connection status, and troubleshoot setup. Use when user mentions Teams messages, Teams reading, Teams reply, Teams attachments, teams_read_messages, teams_queue_reply, teams_download_file, M365 bridge, or wants to interact with Microsoft Teams from Claude Code.
version: 1.0.0
author: asgr-base
createDate: 2026-03-03
updateDate: 2026-03-03
license: Apache-2.0
disable-model-invocation: true
---

# M365 AI Bridge Manager

M365 AI Bridge Chrome Extension と MCP ツールを使って Microsoft Teams のメッセージ読取・返信・添付ファイルダウンロードを行うスキル。

## 前提条件

- Chrome Extension がインストール済み（`chrome://extensions` → デベロッパーモード → Extension フォルダを読み込み）
- `.mcp.json` に MCP サーバーが登録済み
- Chrome で Teams（`teams.microsoft.com` または `teams.cloud.microsoft`）を開いている

## MCP ツール一覧

| ツール | 引数 | 用途 |
|--------|------|------|
| `mcp__teams__teams_read_messages` | `limit?` (number) | チャンネル/チャットのメッセージ取得 |
| `mcp__teams__teams_queue_reply` | `text` (string, 必須) | 返信フォームにテキスト挿入 |
| `mcp__teams__teams_get_status` | なし | 接続状態・バッファ確認 |
| `mcp__teams__teams_download_file` | `filename` (string, 必須), `groupId?`, `chatType?`, `downloadDir?` | 添付ファイルを Graph API 経由でダウンロード |

## 基本操作フロー

### メッセージ読取

```
1. teams_get_status で接続確認
2. messageBuffer が null → ユーザーに「Teamsタブを開いてください」と案内
3. messageBuffer あり → teams_read_messages で取得
```

Extension は 15 秒ごとに自動プッシュするため、Teams タブが開いていれば基本的にデータは存在する。手動で即時取得したい場合は、Extension ポップアップの「メッセージを読み取る」ボタン。

### 返信

```
1. teams_read_messages でメッセージ確認
2. ユーザーと返信内容を確認
3. teams_queue_reply(text="返信文") でフォームに挿入
4. ユーザーに「送信ボタンを押してください」と案内
```

IMPORTANT: AI は送信ボタンを押さない。必ずユーザーが手動で送信する設計。返信キュー後は「Teamsの返信フォームにテキストが挿入されています。内容を確認して送信してください」と案内すること。

### 添付ファイルダウンロード

```
1. teams_read_messages でメッセージ取得 → attachments フィールドを確認
2. teams_download_file(filename="report.xlsx") でダウンロード
3. chatType: "channel"（デフォルト）または "dm" を指定
4. groupId: チャンネルファイルの場合、status の groupId を指定
```

ダウンロードファイルは Extension の `downloads/` フォルダに保存される。`downloadDir` で任意のパスを指定可能。

## メッセージデータ構造

各メッセージには以下の情報が含まれる:

| フィールド | 説明 |
|-----------|------|
| `sender` | 送信者名 |
| `body` | メッセージ本文 |
| `timestamp` | 送信日時（ISO 8601） |
| `messageId` | メッセージ ID |
| `deepLink` | Teams メッセージへの直接リンク URL |
| `mentions.to` | TO メンション（名前の配列） |
| `mentions.cc` | CC メンション（名前の配列） |
| `replyCount` | 返信数（チャンネルメッセージのみ） |
| `replySenders` | 返信者名の配列（チャンネルメッセージのみ） |
| `attachments` | 添付ファイル名の配列（存在する場合のみ） |

## トラブルシューティング

### 「メッセージがありません」エラー

原因と対処:

1. **Teams タブが開いていない** → Chrome で Teams を開く
2. **Extension が無効** → `chrome://extensions` で有効化
3. **MCP サーバー未起動** → Claude Code を再起動（起動時に自動開始）
4. **自動プッシュ未実行** → Teams タブをリロード（Ctrl+R）して 3 秒待つ

### teams_get_status の確認ポイント

```
messageBuffer: null       → Extension からデータ未受信
messageBuffer.messageCount: 0 → メッセージ0件のページ
graphToken.hasToken: false → Graph API トークン未取得（ファイルDLに必要）
```

### Extension 更新後の反映手順

コード修正後は以下の両方が必要:
1. `chrome://extensions` → M365 AI Bridge の「更新」ボタン
2. Teams タブをリロード（Ctrl+R）— Content Script を再注入

### ポート競合

MCP サーバーは `localhost:3765` を使用。テスト実行（`npm test`）がサーバープロセスを kill することがある。Claude Code を再起動すれば MCP サーバーが自動復旧する。

### Graph API トークンがない

`teams_download_file` には Graph API トークンが必要。Teams ページを開くと Extension が自動的に MSAL キャッシュからトークンを取得・送信する。トークンは Teams のログインセッションに依存するため、Teams からログアウトすると無効になる。

## セットアップ手順

### 新規インストール

```bash
# 1. リポジトリ取得
git clone https://github.com/asgr-base/m365-ai-bridge-extension.git

# 2. 依存関係インストール
cd m365-ai-bridge-extension && npm install

# 3. Chrome Extension インストール
# chrome://extensions → デベロッパーモード ON → 「パッケージ化されていない拡張機能を読み込む」→ このフォルダを選択

# 4. .mcp.json に登録
# プロジェクトの .mcp.json または ~/.claude/.mcp.json に以下を追加:
```

```json
{
  "mcpServers": {
    "teams": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/m365-ai-bridge-extension/native/mcp-server.js"]
    }
  }
}
```

```bash
# 5. Claude Code を再起動 → MCP サーバーが自動起動

# 6. Chrome で Teams を開く（teams.microsoft.com または teams.cloud.microsoft）
```

### テスト実行

```bash
cd m365-ai-bridge-extension
npm test    # Playwright テスト（59件）
```

注意: テスト実行時にポート 3765 が使用される。テスト後に Claude Code の MCP サーバーを再起動する必要がある場合がある。
