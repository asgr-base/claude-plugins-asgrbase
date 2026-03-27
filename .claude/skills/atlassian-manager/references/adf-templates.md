# ADF基本構造（Building Blocks）

Confluence ページの ADF (Atlassian Document Format) 基本要素のリファレンス。

---

## 見出し

```json
{"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "見出し"}]}
```

## 段落

```json
{"type": "paragraph", "content": [{"type": "text", "text": "本文"}]}
```

## 箇条書き

```json
{
  "type": "bulletList",
  "content": [{
    "type": "listItem",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "項目"}]}]
  }]
}
```

## テーブル

```json
{
  "type": "table",
  "attrs": {"isNumberColumnEnabled": false, "layout": "default"},
  "content": [
    {
      "type": "tableRow",
      "content": [
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "ヘッダ"}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "ヘッダ"}]}]}
      ]
    },
    {
      "type": "tableRow",
      "content": [
        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "値"}]}]},
        {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "値"}]}]}
      ]
    }
  ]
}
```

## テキスト装飾（marks）

```json
{"type": "text", "text": "太字", "marks": [{"type": "strong"}]}
{"type": "text", "text": "斜体", "marks": [{"type": "em"}]}
{"type": "text", "text": "太字斜体", "marks": [{"type": "strong"}, {"type": "em"}]}
{"type": "text", "text": "色付き", "marks": [{"type": "textColor", "attrs": {"color": "#ff0000"}}]}
```
