---
name: atlassian-manager
description: Manage Atlassian Confluence and Jira via MCP tools. Resolve Confluence Tiny Links (/wiki/x/XXXXX) to page IDs, set up MCP server connections, search pages with CQL/JQL, edit pages with ADF format, and troubleshoot common issues. Use when working with Atlassian, Confluence, Jira, MCP setup, tiny links, short URLs, page ID resolution, ADF editing, or page updates.
---

# Atlassian Manager

Atlassian MCP Server を使用した Confluence / Jira 操作の統合ガイド。Tiny Link 解決、MCP セットアップ、ツールリファレンス、トラブルシューティングを提供。

## Confluence Tiny Link 解決

Confluence の短縮URL（Tiny Link）は `/wiki/x/{code}` 形式。MCP ツールはページIDを必要とするため、Tiny Link からの変換が必要。

### デコード方法

Tiny Link のエンコードは Perl の `pack("L", $pageId)` + Base64 + 文字置換（`+`→`_`, `/`→`-`）。デコードはこの逆操作を行う。

**Bash ワンライナー**:

```bash
CODE="YOUR_CODE_HERE" python3 -c "
import base64,struct,os;c=os.environ['CODE']
s=c.replace('_','+').replace('-','/')
s=s+'A'*(6-len(s))+'=='
print(struct.unpack('<I',base64.b64decode(s)[:4])[0])
"
```

`YOUR_CODE_HERE` を Tiny Link のコード部分に置換（例: `/wiki/x/CoA_y` なら `CoA_y`）。

**Python 関数**:

```python
import base64
import struct

def decode_tiny_link(code: str) -> int:
    """Decode Confluence Tiny Link code to numeric page ID.

    Algorithm (reverse of Perl pack/encode):
      1. Reverse character substitution: _ -> +, - -> /
      2. Pad with 'A' to 6 chars (pack('L') = 4 bytes = 6 base64 chars)
      3. Add '=' padding for standard base64
      4. base64 decode
      5. Unpack as little-endian unsigned 32-bit (Perl's unpack('L'))

    Args:
        code: The encoded portion from /wiki/x/{code}

    Returns:
        Numeric page ID for use with MCP tools
    """
    s = code.replace('_', '+').replace('-', '/')
    while len(s) < 6:
        s += 'A'
    padding = (4 - len(s) % 4) % 4
    s += '=' * padding
    return struct.unpack('<I', base64.b64decode(s)[:4])[0]
```

**URL からの抽出**:

```python
import re

def resolve_confluence_url(url: str) -> int | None:
    """Extract page ID from any Confluence URL format.

    Supports:
      - Tiny Link: https://example.atlassian.net/wiki/x/CoA_y
      - Full URL:  https://example.atlassian.net/wiki/spaces/SPACE/pages/12345/Title
      - Edit URL:  https://example.atlassian.net/wiki/spaces/SPACE/pages/edit-v2/12345
    """
    # Tiny Link format
    m = re.search(r'/wiki/x/([A-Za-z0-9_-]+)', url)
    if m:
        return decode_tiny_link(m.group(1))

    # Full/Edit URL format
    m = re.search(r'/pages/(?:edit-v2/)?(\d+)', url)
    if m:
        return int(m.group(1))

    return None
```

詳細は [references/tiny-link.md](references/tiny-link.md) を参照。

### MCP Server 側の対応状況

Atlassian MCP Server は現時点で Tiny Link の直接解決を**サポートしていない**。[GitHub Issue #27](https://github.com/atlassian/atlassian-mcp-server/issues/27) で対応がリクエストされている。上記のクライアント側デコードが現在の唯一の方法。

## MCP ツール一覧

### MCP Tool Prefix

環境により prefix が異なる:

| 環境 | Prefix |
|------|--------|
| Hosted MCP (Claude AI) | `mcp__claude_ai_Atlassian__` |
| Local MCP (claude mcp add) | `mcp__atlassian__` |

### Confluence ツール

| ツール | 機能 |
|--------|------|
| `getConfluencePage` | ページ取得（pageId 指定） |
| `getConfluenceSpaces` | スペース一覧取得 |
| `getPagesInConfluenceSpace` | スペース内ページ一覧 |
| `getConfluencePageDescendants` | 子孫ページ取得 |
| `createConfluencePage` | 新規ページ作成 |
| `updateConfluencePage` | ページ更新 |
| `searchConfluenceUsingCql` | CQL 検索 |
| `getConfluencePageFooterComments` | フッターコメント取得 |
| `getConfluencePageInlineComments` | インラインコメント取得 |
| `createConfluenceFooterComment` | フッターコメント作成 |
| `createConfluenceInlineComment` | インラインコメント作成 |

### Jira ツール

| ツール | 機能 |
|--------|------|
| `getJiraIssue` | 課題取得 |
| `editJiraIssue` | 課題更新 |
| `createJiraIssue` | 課題作成 |
| `searchJiraIssuesUsingJql` | JQL 検索 |
| `getTransitionsForJiraIssue` | ステータス遷移取得 |
| `transitionJiraIssue` | ステータス変更 |
| `addCommentToJiraIssue` | コメント追加 |
| `lookupJiraAccountId` | アカウントID検索 |
| `getVisibleJiraProjects` | プロジェクト一覧 |
| `getJiraProjectIssueTypesMetadata` | 課題タイプメタデータ |
| `getJiraIssueTypeMetaWithFields` | フィールドメタデータ |
| `getJiraIssueRemoteIssueLinks` | リモートリンク取得 |

### 共通ツール

| ツール | 機能 |
|--------|------|
| `atlassianUserInfo` | 現在のユーザー情報 |
| `getAccessibleAtlassianResources` | アクセス可能なリソース（Cloud ID 等） |
| `search` | Rovo Search（横断検索） |
| `fetch` | ARI でコンテンツ取得 |

## よくある操作パターン

### Cloud ID の取得

```javascript
// 最初に Cloud ID を取得
getAccessibleAtlassianResources()
// → [{ "id": "your-cloud-id", "url": "https://example.atlassian.net", ... }]
```

Cloud ID はすべてのツール呼び出しに必要。一度取得すればセッション内で再利用可能。

### ページ取得

```javascript
getConfluencePage({
  cloudId: "YOUR-CLOUD-ID",
  pageId: "12345"
})
```

### CQL 検索

```javascript
searchConfluenceUsingCql({
  cloudId: "YOUR-CLOUD-ID",
  cql: "space = MYSPACE AND title ~ 'keyword' AND type = page",
  limit: 50
})
```

### ページ作成

```javascript
createConfluencePage({
  cloudId: "YOUR-CLOUD-ID",
  spaceId: "YOUR-SPACE-ID",
  title: "New Page Title",
  body: "# Heading\n\nBody in Markdown format"
})
```

## ADF（Atlassian Document Format）編集

Confluence ページを更新する際は ADF 形式を使用する。Markdown 形式で更新すると SmartLink、セル結合、マクロが失われる。

### 編集ワークフロー

1. **ADF取得**: `getConfluencePage(contentFormat: "adf")` で ADF JSON を取得
2. **Python編集**: ADF JSON ツリーを直接操作
3. **検証**: SmartLink数・セル結合数が変更前後で一致することを確認
4. **更新**: `updateConfluencePage(contentFormat: "adf")` で反映

### リファレンス

- 編集パターン・検証ロジック・mcp-remote パイプ方式: [references/adf-editing.md](references/adf-editing.md)
- ADF 基本構造（見出し、テーブル、テキスト装飾等）: [references/adf-templates.md](references/adf-templates.md)

## トラブルシューティング

### 認証エラー（Invalid refresh token）

OAuth トークンの有効期限切れ。MCP サーバーを再登録して再認証:

```bash
claude mcp remove atlassian
claude mcp add --transport sse atlassian https://mcp.atlassian.com/v1/sse
```

### 接続タイムアウト

ネットワーク接続、プロキシ設定（`HTTP_PROXY`, `HTTPS_PROXY`）、ファイアウォールを確認。

### ツールが見つからない

MCP サーバーが正しく接続されていない。`claude mcp list` で接続状態を確認。Hosted MCP と Local MCP で prefix が異なる点にも注意。

### Tiny Link のデコードエラー

Tiny Link コードに無効な文字が含まれている場合、デコードは失敗する。有効な文字は `A-Z`, `a-z`, `0-9`, `-`, `_` のみ。URL からコード部分を正確に抽出しているか確認。

## セットアップ

初回セットアップの詳細手順は [references/mcp-setup.md](references/mcp-setup.md) を参照。

## 参考資料

- [Atlassian Rovo MCP Server](https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/)
- [Confluence Tiny Link Generation (Atlassian KB)](https://support.atlassian.com/confluence/kb/how-to-programmatically-generate-the-tiny-link-of-a-confluence-page/)
- [MCP Server Tiny Link Support Request (GitHub Issue #27)](https://github.com/atlassian/atlassian-mcp-server/issues/27)
- [Model Context Protocol](https://modelcontextprotocol.io/)
