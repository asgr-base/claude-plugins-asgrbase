---
name: pdf2md-docling
description: Convert PDF files to Markdown using Docling with TableFormer for high-accuracy table extraction. Exports images as separate PNG files. Handles complex documents with APDU tables, cryptographic protocols, MRZ examples, ASN.1 syntax. Use when converting technical specifications, passport standards (ICAO Doc 9303), smart card documentation, or documents requiring precise table structure preservation. Includes 12-step post-processing pipeline for production-grade output.
version: 3.20.0
author: claude_code
createDate: 2025-12-27
updateDate: 2026-01-26
license: Apache-2.0
---

# PDF to Markdown Converter (Docling Edition)

PDFファイルをDoclingでMarkdownに変換。TableFormerによる高精度テーブル抽出、画像は外部PNGファイルとして出力。

## When to Use

- 複雑なテーブルや図を含むPDFの変換
- 画像を別ファイル（PNG）として出力したい場合
- RAGやドキュメンテーション用の高品質変換

## Quick Reference

| 特性 | 値 |
|------|-----|
| 変換速度 | ~1秒/ページ（50ページで約50秒） |
| 出力形式 | Markdown + 外部PNG画像 |
| テーブル | TableFormer（高精度） |

## 変換手順

### Step 0: Doclingパス確認

Doclingのインストール場所は環境により異なるため、最初にパスを確認：

```bash
# パス確認（いずれかでヒット）
which docling 2>/dev/null || \
  find ~/Library/Python -name docling 2>/dev/null | head -1 || \
  pip show docling 2>/dev/null | grep Location
```

**一般的なインストール場所:**
- グローバル: `docling`（PATHに含まれる場合）
- macOS Python: `~/Library/Python/3.x/bin/docling`
- pipx: `~/.local/bin/docling`
- venv: `.venv/bin/docling`

以降のコマンドでは、確認したパスを使用してください。

### Step 1: Docling実行

```bash
docling "path/to/input.pdf" \
  --to md \
  --output "output_directory" \
  --image-export-mode referenced \
  --table-mode accurate \
  -v
```

**必須オプション:**
- `--image-export-mode referenced`: 画像をPNGファイルとして出力
- `--table-mode accurate`: TableFormerで高精度テーブル抽出

### Step 2: ファイル整理

Doclingは深いディレクトリ構造を作成するため、以下のように整理：

```
変換前（Docling出力）:
output_directory/
└── Users/USERNAME/.../filename_artifacts/
    └── image_*.png

変換後（整理済み）:
output_directory/
├── filename_docling.md
└── assets/
    └── filename_docling/
        └── image_*.png
```

### Step 3: 後処理（全て必須・順序厳守）

**以下の12ステップの後処理を順序通りに実行すること:**

| Phase | # | 処理 | 目的 |
|-------|---|------|------|
| **A. ファイル整理** | 1 | 画像移動 | `assets/{basename}_docling/`に整理 |
| **B. クリーンアップ** | 2 | Unicode除去 | Private Use Area文字（U+E000-F8FF）削除 |
| | 3 | パス更新 | 絶対パス→相対パスに変換 |
| | 4 | JSON整形 | 単一行JSON→インデント付きに変換 |
| **C. 構造再構築** | 5 | ヘッダー削除 | 繰り返しヘッダー・ページ番号を削除（コードブロック・テーブル保護） |
| | 6 | 孤立コードフェンス削除 | Doclingが誤挿入した単独「```」を削除 |
| | 7 | 長いコード行整形 | 改行なしXML/WSDL（2000文字超）・ASN.1（1000文字超）をコードブロック化 |
| | 8 | テーブルヘッダー補完 | セパレータなしテーブルにヘッダー+セパレータ追加 |
| | 9 | 定義リスト再構成 | 罫線なしテーブルをMarkdownテーブルに変換 |
| | 10 | テーブル統合 | 改ページで分断されたテーブルを結合 |
| **D. 最終整形** | 11 | テーブル最適化 | 余分なスペース・ハイフン削除 |
| | 12 | セル内改行 | 番号付き/箇条書き・文の境界に`<br>`タグ追加 |

**順序の根拠:**
- Phase B: 問題文字を除去してから構造認識（誤認識防止）
- Phase C: 不要行削除→孤立記号削除→長いコード整形→ヘッダー補完→構造再構築→統合（正確な構造認識）
- Phase D: 統合後に整形（最終品質向上）

**詳細な実装コードは [IMPLEMENTATION.md](IMPLEMENTATION.md) を参照。**

### Step 4: 検証

```bash
# ファイルサイズ確認（KBであるべき、MBは異常）
ls -lh output_directory/filename_docling.md

# 画像カウント
ls output_directory/assets/filename_docling/ | wc -l

# Private Use Area文字チェック
python3 -c "
with open('output_directory/filename_docling.md', 'r') as f:
    pua = [c for c in f.read() if 0xE000 <= ord(c) <= 0xF8FF]
    print(f'PUA chars: {len(pua)}' if pua else '✅ Clean')
"
```

## 出力ファイル命名規則

```
{basename}_docling.md          # Markdownファイル
assets/{basename}_docling/     # 画像ディレクトリ
```

複数PDF変換時の画像混在を防止。

## 品質チェックリスト

- [ ] Markdownサイズが適切（KB単位、MBは異常）
- [ ] 画像パスが相対パス（`assets/...`で始まる）
- [ ] Private Use Area文字がない
- [ ] JSONが整形済み（複数行）
- [ ] テーブルが最適化済み（`|---|`形式）
- [ ] テーブルセル内の改行が`<br>`で表現されている（番号付き・箇条書き・文の境界）
- [ ] 繰り返しヘッダー（ページ番号、文書タイトル等）が削除されている
- [ ] 改ページで分断されたテーブルが統合されている
- [ ] 罫線なしテーブル（定義リスト）がMarkdownテーブルに変換されている
- [ ] 縦結合セルが正しく分割されている（`grep "| P[12] [A-Z]"`で検出）
- [ ] ASN.1構文が適切に整形されている（`grep "::=" | awk 'length > 100'`で長い定義を検出）
- [ ] 結合セルが空欄で表現されている（Command/Response/Status Bytes等で同一値の繰り返しがない）
- [ ] 番号付きリストが連続している（`grep "<br>[0-9]<br>"`で断絶を検出）

## 比較: pdf2md vs pdf2md-docling

| 特性 | pdf2md (Read) | pdf2md-docling |
|------|---------------|----------------|
| テーブル品質 | Good | Excellent |
| 画像 | Base64埋め込み | 外部PNG |
| 速度 | ~10秒 | ~50秒 |
| ファイルサイズ | 大（MB） | 小（KB）+画像 |
| 用途 | 簡易変換 | 本番/RAG |

## 関連ファイル

| ファイル | 内容 |
|----------|------|
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | 後処理の詳細Pythonコード |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | エラー対応、FAQ |
| [CHANGELOG.md](CHANGELOG.md) | 全バージョン変更履歴 |

---
**Version**: 3.20.0 | **Updated**: 2026-01-26
