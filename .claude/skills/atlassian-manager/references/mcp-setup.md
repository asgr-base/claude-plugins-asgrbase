# Atlassian MCP Server - セットアップガイド

## 概要

Atlassian MCP（Model Context Protocol）サーバーを使用すると、AI ツール（Claude Code, Cursor IDE 等）から Confluence と Jira を操作できる。

## 基本情報

| 項目 | 値 |
|------|-----|
| サーバー名 | `atlassian` |
| サーバーURL | `https://mcp.atlassian.com/v1/sse` |
| トランスポート | SSE (Server-Sent Events) |
| 認証方式 | OAuth 2.0 |

## セットアップ

### Claude Code CLI

```bash
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse
```

確認:

```bash
claude mcp list
# 期待される出力:
# atlassian: https://mcp.atlassian.com/v1/sse (SSE) - ✓ Connected
```

手動設定（`~/.claude.json`）:

```json
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "atlassian": {
          "type": "sse",
          "url": "https://mcp.atlassian.com/v1/sse"
        }
      }
    }
  }
}
```

### Cursor IDE

設定ファイル: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
    }
  }
}
```

### 汎用 MCP 対応ツール

SSE 方式:

```json
{
  "mcpServers": {
    "atlassian": {
      "type": "sse",
      "url": "https://mcp.atlassian.com/v1/sse"
    }
  }
}
```

npx 経由:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
    }
  }
}
```

## OAuth 認証フロー

### 初回接続

1. AI ツールが MCP サーバーに接続を試みる
2. ブラウザが自動的に開き、Atlassian 認証ページが表示される
3. Atlassian アカウントでログイン
4. アクセス許可のスコープ（Confluence, Jira 等）を確認して承認
5. トークンがローカルに保存され、接続完了

### トークンの保存場所

| OS | 保存先 |
|----|--------|
| macOS | Keychain |
| Linux | libsecret |
| Windows | Credential Manager |

OAuth トークンは自動更新される。通常、手動での再認証は不要。

## Cloud ID の取得

すべてのツール呼び出しに Cloud ID が必要。以下の方法で取得:

### 方法 1: MCP ツール

```javascript
getAccessibleAtlassianResources()
```

レスポンス例:

```json
[
  {
    "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "url": "https://example.atlassian.net",
    "name": "example",
    "scopes": ["read:confluence-content.all", "write:confluence-content"]
  }
]
```

`id` フィールドが Cloud ID。

### 方法 2: URL から推定

`https://example.atlassian.net` の `example` 部分をサイト識別に使用できる場合がある（MCP ツールが自動変換に対応している場合）。確実ではないため、方法 1 を推奨。

## トラブルシューティング

### 認証エラー（Invalid refresh token）

OAuth トークンの有効期限切れまたは破損。

```bash
claude mcp remove atlassian
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse
# ブラウザで再認証
```

### 接続タイムアウト

確認項目:

1. ネットワーク接続
2. プロキシ設定（`HTTP_PROXY`, `HTTPS_PROXY` 環境変数）
3. ファイアウォール設定

### ツールが見つからない

MCP サーバーが接続されていない可能性がある。

```bash
claude mcp list
```

Hosted MCP（Claude AI 経由）と Local MCP（`claude mcp add`）で prefix が異なる:

| 環境 | Prefix 例 |
|------|-----------|
| Hosted MCP | `mcp__claude_ai_Atlassian__getConfluencePage` |
| Local MCP | `mcp__atlassian__getConfluencePage` |

## 参考資料

- [Atlassian Rovo MCP Server - Getting Started](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Code MCP Documentation](https://docs.claude.com/en/docs/claude-code/mcp)
