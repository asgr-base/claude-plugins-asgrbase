# Confluence Tiny Link 解決 - 詳細リファレンス

## 概要

Confluence はページごとに短縮URL（Tiny Link）を生成する。形式は `/wiki/x/{code}` で、`{code}` はページIDを Perl の `pack("L")` + Base64 + 文字置換でエンコードしたもの。

MCP ツール（`getConfluencePage` 等）はページID（数値）を必要とするが、Tiny Link からは直接ページIDがわからない。本ドキュメントでは、Tiny Link をデコードしてページIDを取得する方法を解説する。

## URL 形式の比較

Confluence は3種類のURL形式を使用する:

| 形式 | URL例 | ページID抽出 |
|------|-------|-------------|
| Display URL | `https://example.atlassian.net/wiki/spaces/SPACE/pages/12345/Title` | URL から直接抽出可能 |
| Tiny Link | `https://example.atlassian.net/wiki/x/CoA_y` | デコードが必要 |
| Edit URL | `https://example.atlassian.net/wiki/spaces/SPACE/pages/edit-v2/12345` | URL から直接抽出可能 |

## デコードアルゴリズム

### エンコード仕様（Perl 公式アルゴリズム）

1. ページID（整数）を `pack("L", $pageId)` でリトルエンディアン 4バイトに変換
2. 標準 Base64 エンコード
3. 文字置換: `+` → `_`, `/` → `-`
4. パディング `=` と末尾の `A`（ゼロバイト由来）を除去

### デコード手順

1. 文字置換を逆転: `_` → `+`, `-` → `/`
2. `A` を追加して6文字にパディング（`pack("L")` = 4バイト = 6 base64文字）
3. `=` パディングを追加して標準 Base64 デコード
4. リトルエンディアン unsigned 32-bit integer としてアンパック

## 実装

### Python 関数

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
        Numeric page ID

    Examples:
        >>> decode_tiny_link("CoA_y")
        3359539210
        >>> decode_tiny_link("DoAz")
        3375118
        >>> decode_tiny_link("bgBQ")
        5242990
    """
    s = code.replace('_', '+').replace('-', '/')
    while len(s) < 6:
        s += 'A'
    padding = (4 - len(s) % 4) % 4
    s += '=' * padding
    return struct.unpack('<I', base64.b64decode(s)[:4])[0]
```

### Bash ワンライナー

```bash
# 使い方: CODE= の値を変更して実行
CODE="CoA_y" python3 -c "
import base64,struct,os;c=os.environ['CODE']
s=c.replace('_','+').replace('-','/')
s=s+'A'*(6-len(s))+'=='
print(struct.unpack('<I',base64.b64decode(s)[:4])[0])
"
```

### URL パーサー（フル URL 対応）

```python
import re

def resolve_confluence_url(url: str) -> int | None:
    """Extract page ID from any Confluence URL format.

    Supports:
      - Tiny Link: https://example.atlassian.net/wiki/x/CoA_y
      - Display:   https://example.atlassian.net/wiki/spaces/SPACE/pages/12345/Title
      - Edit:      https://example.atlassian.net/wiki/spaces/SPACE/pages/edit-v2/12345

    Returns None if URL format is unrecognized.
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

## 公式ドキュメント

### Atlassian KB

- [Differences between URL formats for a Confluence page](https://support.atlassian.com/confluence/kb/the-differences-between-various-url-formats-for-a-confluence-page/) — 3種のURL形式を説明
- [How to programmatically generate the Tiny link](https://support.atlassian.com/confluence/kb/how-to-programmatically-generate-the-tiny-link-of-a-confluence-page/) — エンコードアルゴリズム（Perl実装、AS-IS提供）

### MCP Server 対応状況

- [GitHub Issue #27: Support resolving Confluence short URLs](https://github.com/atlassian/atlassian-mcp-server/issues/27) — MCP Server側での Tiny Link 対応リクエスト。提案されている解決策:
  - Option A: `fetch` ツールで短縮URL を直接受付
  - Option B: 専用 `resolveConfluenceShortUrl` ツール追加
  - Option C: `getConfluencePage` で tinyui コード受付

現時点では**いずれも未実装**。クライアント側でのデコードが唯一の方法。

### REST API の制約

Confluence REST API にも Tiny Link を解決する専用エンドポイントは存在しない。ただし、ページ取得レスポンスの `_links.tinyui` フィールドに Tiny Link パスが含まれる:

```json
{
  "id": "12345",
  "_links": {
    "webui": "/spaces/SPACE/pages/12345/Title",
    "tinyui": "/x/AbCdE",
    "self": "https://example.atlassian.net/wiki/rest/api/content/12345"
  }
}
```

## 注意事項

- 公式KBのエンコードアルゴリズムは「AS-IS, not officially supported」と明記されている
- Confluence の文字置換（`+`→`_`, `/`→`-`）は標準 URL-safe Base64（`+`→`-`, `/`→`_`）と**逆**であることに注意
- `pack("L")` はリトルエンディアンであり、ビッグエンディアンではない
- 非常に大きなページID（32bit超）の場合、バイト長が変わる可能性がある
- アルゴリズムの正確性は実際の Confluence インスタンスで検証すること
