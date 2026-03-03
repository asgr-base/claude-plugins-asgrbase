# ADF編集パターン・検証・ノード仕様

Confluence ページを安全に編集するための ADF (Atlassian Document Format) 操作リファレンス。

## 目次

- 編集パターン（テキスト置換、太字追加、テーブル行追加、補足テキスト追加）
- 変更検証（SmartLink数・セル結合数の一致確認）
- ADF構造の重要ノード
- 大きなページの更新: mcp-remote stdio パイプ方式

---

## 編集パターン

### パターン1: テキスト置換

`type: "text"` ノードの `text` フィールドを変更。既存の `marks`（annotation, textColor, strong等）と `attrs` は常に保持。

```python
import json, copy

def replace_text(node, old_text, new_text, edits):
    if 'content' not in node:
        return
    new_content = []
    for child in node['content']:
        if child.get('type') == 'text' and old_text in child.get('text', ''):
            child = copy.deepcopy(child)
            child['text'] = child['text'].replace(old_text, new_text)
            edits.append(f"Replaced: {old_text}")
        new_content.append(child)
        replace_text(child, old_text, new_text, edits)
    node['content'] = new_content
```

### パターン2: 太字追加（ノード分割）

テキストノードを分割し、太字部分に `marks: [{"type": "strong"}]` を追加。

```python
existing_marks = child.get('marks', [])
# "AはBである" → "Aは" + "**B**" + "である"
new_content.append({
    "type": "text", "text": "Aは",
    "marks": copy.deepcopy(existing_marks)
})
new_content.append({
    "type": "text", "text": "B",
    "marks": copy.deepcopy(existing_marks) + [{"type": "strong"}]
})
new_content.append({
    "type": "text", "text": "である",
    "marks": copy.deepcopy(existing_marks)
})
```

### パターン3: テーブル行追加

`tableRow` を作成して `table` の `content` に挿入。

```python
def create_table_cell(text, marks=None, attrs=None):
    cell = {
        "type": "tableCell",
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": text, "marks": marks or []}]
        }]
    }
    if attrs:
        cell["attrs"] = attrs
    return cell

new_row = {
    "type": "tableRow",
    "content": [
        create_table_cell("セルA"),
        create_table_cell("セルB"),
        create_table_cell("セルC")
    ]
}
# table['content'].insert(index, new_row)
```

### パターン4: 補足テキスト追加

既存ノードの後に改行＋テキストを追加。

```python
new_content.append(child)  # 既存ノードを保持
new_content.append({"type": "hardBreak"})
new_content.append({
    "type": "text", "text": "補足: ...",
    "marks": copy.deepcopy(existing_marks)
})
```

## 変更検証

更新前にSmartLink数・セル結合数が変更前後で一致することを検証:

```python
def count_structure(adf):
    smart_links, merged_cells = 0, 0
    def traverse(node):
        nonlocal smart_links, merged_cells
        if node.get('type') == 'inlineCard':
            smart_links += 1
        if node.get('type') == 'tableCell':
            attrs = node.get('attrs', {})
            if attrs.get('colspan', 1) > 1 or attrs.get('rowspan', 1) > 1:
                merged_cells += 1
        for child in node.get('content', []):
            traverse(child)
    traverse(adf)
    return smart_links, merged_cells

before_sl, before_mc = count_structure(original_adf)
after_sl, after_mc = count_structure(modified_adf)
assert before_sl == after_sl, f"SmartLink: {before_sl} → {after_sl}"
assert before_mc == after_mc, f"Merged cells: {before_mc} → {after_mc}"
```

## ADF構造の重要ノード

| ノードタイプ | 説明 | 保持ルール |
|-------------|------|-----------|
| `text` | テキストノード | `marks` を常に保持 |
| `inlineCard` | SmartLink | 絶対に変更しない |
| `tableCell` | テーブルセル | `attrs`（colspan, rowspan, colwidth）を保持 |
| `extension` | マクロ（目次等） | 絶対に変更しない |
| `hardBreak` | 改行 | そのまま保持 |
| `annotation` | インラインコメント | marksとして保持 |

## 大きなページの更新: mcp-remote stdio パイプ方式

ADF JSONが大きい（100KB超）場合、MCPツールのパラメータとして直接渡すと出力トークン制限を超える。
`mcp-remote` の stdio にJSON-RPCメッセージを直接パイプして回避する。

### 手順

1. **Python で修正済みADF を JSON-RPC リクエストに変換**

```python
import json

with open('/tmp/modified-adf.json') as f:
    adf = json.load(f)

request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "updateConfluencePage",
        "arguments": {
            "cloudId": "YOUR-CLOUD-ID",
            "pageId": "TARGET-PAGE-ID",
            "title": "ページタイトル",
            "contentFormat": "adf",
            "body": json.dumps(adf, ensure_ascii=False, separators=(',', ':')),
            "versionMessage": "更新メッセージ"
        }
    },
    "id": 1
}

with open('/tmp/mcp-request.json', 'w') as f:
    json.dump(request, f, ensure_ascii=False)
```

2. **mcp-remote にパイプ送信**

```bash
INIT='{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"adf-updater","version":"1.0.0"}},"id":0}'
CALL=$(cat /tmp/mcp-request.json)

{
  echo "$INIT"
  sleep 2
  echo "$CALL"
  sleep 5
} | npx -y mcp-remote https://mcp.atlassian.com/v1/sse 2>/tmp/mcp-stderr.txt | tee /tmp/mcp-stdout.txt
```

3. **レスポンス確認**

```python
import json
with open('/tmp/mcp-stdout.txt') as f:
    for line in f:
        data = json.loads(line.strip())
        if data.get('id') == 1:
            page = json.loads(data['result']['content'][0]['text'])
            print(f"Version: {page['version']['number']}")
            print(f"Status: {page['status']}")
```

### 注意事項

- `mcp-remote` は `~/.mcp-auth/` にOAuthトークンをキャッシュ。期限切れ時はブラウザ認証が走る
- `sleep 2` / `sleep 5` はサーバー初期化・処理待ち。短すぎるとレスポンス未受信で終了する
- macOS では `timeout` コマンドが未インストールの場合がある（`gtimeout` or 省略）
