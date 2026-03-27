# jp-legal-amendment-pdf2md

Japanese legal amendment PDF (縦書き・新旧対照表) to Markdown converter.

## What It Does

縦書き・新旧対照表形式の日本語法令改正PDFをMarkdownに変換します。5段階のワークフローで、Doclingによる画像抽出、Claude直接読み取りによる構造化、変更箇所のマークアップを行います。

## Key Features

- **縦書き→横書き変換** — 法令特有のレイアウトを処理
- **新旧対照表構造** — 改正前/改正後を正確に保持
- **変更マークアップ** — 太字（修正箇所）、`[新設]`、`［号の細分を削る。］`
- **特殊表記処理** — `［同上］`（変更なし）、条番号繰り下げ、脚注
- **14項目品質チェックリスト** — 構文検証、画像配置、内容保持

## Usage

```
/jp-legal-amendment-pdf2md
```

法令改正PDF、新旧対照表のMarkdown変換時に使用。

## Workflow

1. Docling基本変換（画像抽出）
2. ファイル整理（画像移動、中間ファイル削除）
3. PDF直接読み取り + Markdown手動作成
4. 最終ファイル保存
5. 品質チェックリスト検証

## File Structure

```
jp-legal-amendment-pdf2md/
└── SKILL.md          # Full workflow and checklist
```

## Requirements

- Docling CLI（画像抽出用）
- Claude Code CLI

## License

Apache 2.0
