# jp-kobunsho-xml-to-pdf

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、1 ページに収まる読みやすい PDF に変換するスキル + CLI ツール。

## 特徴

- **オフライン処理**: 個人情報を含む公文書を第三者サーバーに送らず手元で完結
- **自動 fit-to-page**: XSL が固定 px width（例: 1400px）を指定していても、HTML 正規化と実測ベースの自動縮小で A4 1 ページに収納
- **複数 XML 対応**: 1 つの ZIP に複数の XML が含まれる場合、それぞれを個別 PDF 化
- **日本語フォント同梱**: IPAex Gothic / Mincho を同梱し、環境差で豆腐化しない
- **CLI 単独動作**: Claude Code から呼ぶだけでなく、シェルから直接実行可能

## インストール

```bash
claude plugin install jp-kobunsho-xml-to-pdf@asgr-base
```

### システム依存ライブラリ

WeasyPrint の依存（pango/cairo）が必要です。

```bash
# macOS
brew install pango

# Linux (Debian/Ubuntu)
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0
```

### Python パッケージ

```bash
pip3 install -r ~/.claude/plugins/cache/asgr-base/*/plugins/jp-kobunsho-xml-to-pdf/requirements.txt
```

## 使い方

### Claude Code から

```
e-Gov の公文書 ZIP を PDF にして: /path/to/kobunsho.zip
```

スキルが自動起動し、PDF を ZIP と同じディレクトリに出力します。

### CLI から直接

```bash
PLUGIN=~/.claude/plugins/cache/asgr-base/*/plugins/jp-kobunsho-xml-to-pdf
python3 $PLUGIN/scripts/convert.py /path/to/kobunsho.zip

# オプション
python3 $PLUGIN/scripts/convert.py /path/to/kobunsho.zip \
  --output-dir /tmp/out \
  --landscape \
  --verbose
```

## 入出力例

**入力**: `1381260511705101_20260516161013.zip`

中身:
```
1381260511705101/
├── kagami.xsl
├── yoshiki_04_shakai_003.xsl
├── 202605160534016314.xml
├── 社会保険料額情報_令和8年4月分(202605160534016314).xml
└── 社会保険料額情報_令和8年4月分_明細(...).csv
```

**出力**: 同ディレクトリに 2 つの PDF
- `202605160534016314.pdf`（表紙）
- `社会保険料額情報_令和8年4月分(202605160534016314).pdf`（社会保険料額表、A4 縦 1 ページ）

## 対応様式

実機で動作確認した様式:

| 様式 | XSL | 結果 |
|------|-----|------|
| 被保険者通知書（kagami） | `kagami.xsl` | A4 縦 1 ページ |
| 社会保険料額情報 | `yoshiki_04_shakai_003.xsl` + `kagami.xsl` | A4 縦 1 ページ（自動 fit 適用） |

XML 冒頭の `<?xml-stylesheet href="..."?>` 指示があるすべての e-Gov 公文書で動作するはずですが、未確認様式は実 ZIP を使ってご報告ください。

## CLI フラグ

| フラグ | 既定 | 説明 |
|-------|-----|------|
| `<zip_path>` | 必須 | 入力 ZIP |
| `--output-dir DIR` | ZIP 同階層 | 出力先 |
| `--portrait` / `--landscape` | (自動) | 向き強制 |
| `--no-fit` | False | 自動 fit を無効化（元 XSL の見た目を保つ） |
| `--zoom FLOAT` | (自動) | 手動 zoom |
| `--verbose` | False | 詳細ログ |

## 競合認識

2026 年に e-Gov 公式の「公文書表示」機能が登場済みです。本ツールは以下の点で差別化します:

- **オフライン**: 公式 Web ツールは XML をアップロードするが、本ツールは手元で完結
- **CLI / 自動化**: スクリプトから一括処理が可能
- **Claude Code 連携**: 月次会計フロー等に組み込み可能

## 関連プラグイン

- [pdf2md-docling](../pdf2md-docling/) — 生成された PDF を Markdown 化したい時に
- [jp-aoiro-accounting](../jp-aoiro-accounting/) — 青色申告帳簿との連携

## ライセンス

- 本プラグイン: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](fonts/LICENSE_ipaex.txt)
