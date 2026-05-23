# jp-kobunsho-xml-to-pdf

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、**真のレスポンシブレイアウト**で 1 ページに収まる読みやすい PDF に変換するスキル + CLI ツール。

## 特徴

- **オフライン処理**: 個人情報を含む公文書を第三者サーバーに送らず手元で完結
- **真のレスポンシブパイプライン (v2.0.0)**: XSL の table 入れ子に依存せず、意味データを抽出して CSS Grid で再配置。罫線完全制御・1 ページ収納・全データ表示を保証
- **複数 XML 対応**: 1 つの ZIP に複数の XML が含まれる場合、それぞれを個別 PDF 化
- **日本語フォント同梱**: IPAex Gothic / Mincho を同梱し、環境差で豆腐化しない
- **CLI 単独動作**: Claude Code から呼ぶだけでなく、シェルから直接実行可能
- **拡張可能**: 新様式は `extractors/yoshiki_NN.py` + テンプレ + CSS の 3 ファイル追加で対応

## v2.0.0 の主な変更点 (v1.x からの移行)

| 項目 | v1.x | v2.0.0 |
|------|------|--------|
| アーキテクチャ | XSL 出力 HTML への CSS 注入 + zoom 探索 | extractor で意味データ抽出 → Jinja2 で HTML 再構築 → CSS Grid 配置 |
| 罫線 | WeasyPrint バグで一部抜け・二重 | `<div>` + flex / Grid で完全制御 |
| レスポンシブ | 固定 px width のまま | `grid-template-areas` で紙サイズに応じて再配置 |
| 改行 | `<pre>` 長文がはみ出し | tr 境界分割 + `pre-wrap` で確実に折り返し |
| 未知様式 | エラー or 崩れ | `generic` フォールバックで最低限の表示を保証 |
| 依存 | lxml + weasyprint | lxml + weasyprint + **jinja2** |

CLI フラグは整理されました。`--portrait` / `--landscape` / `--no-fit` / `--zoom` などの v1 フラグは廃止 (extractor + Grid が紙サイズを自動判定)。

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

### Python 環境（推奨: 専用 venv）

```bash
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | tail -1)

# 専用 venv を作る（初回のみ）
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/pip" install -q -r "$PLUGIN/requirements.txt"
```

`requirements.txt` の中身:
- lxml >= 5.0
- weasyprint >= 65
- jinja2 >= 3.0

## 使い方

### Claude Code から

```
e-Gov の公文書 ZIP を PDF にして: /path/to/kobunsho.zip
```

スキルが自動起動し、PDF を出力します。

### CLI から直接

```bash
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | tail -1)
PY="$PLUGIN/.venv/bin/python"
CONVERT="$PLUGIN/scripts/convert.py"

# 基本
"$PY" "$CONVERT" /path/to/kobunsho.zip

# 出力先指定 + 詳細ログ + 中間 HTML ダンプ
"$PY" "$CONVERT" /path/to/kobunsho.zip --output-dir /tmp/out --debug-dir /tmp/dbg -v
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
- `202605160534016314.pdf`（表紙、A4 縦）
- `社会保険料額情報_令和8年4月分(202605160534016314).pdf`（社会保険料額表、A4 横 1 ページ）

## 対応様式 (v2.0.0)

| 様式 | XSL | デフォルト紙 |
|------|-----|---------|
| 表紙のみ (kagami_only) | `kagami.xsl` 単体 | A4 縦 |
| 健康保険・厚生年金保険口座振替開始通知書 | `yoshiki_26_*` | A4 縦 |
| 社会保険料額情報 | `yoshiki_04_*` | A4 横 |
| 保険料納入告知額・領収済額通知書 | `yoshiki_29_*` | A3 横 |
| **未知様式** | 任意 | A4 縦 (generic フォールバックで共通 class を自動検出) |

新様式の対応は extractor (Python) + Jinja2 テンプレート + CSS の 3 ファイル追加で可能。詳細は [`skills/jp-kobunsho-xml-to-pdf/SKILL.md`](skills/jp-kobunsho-xml-to-pdf/SKILL.md) の「様式追加の拡張ポイント」セクションを参照。

## CLI フラグ

| フラグ | 既定 | 説明 |
|-------|-----|------|
| `<zip_path>` | 必須 | 入力 ZIP |
| `--output-dir DIR` | カレント | PDF 出力先 |
| `--debug-dir DIR` | 無し | 中間 HTML / CSS / 注入 PDF のダンプ先 (デバッグ用) |
| `-v`, `--verbose` | False | 詳細ログを stderr に出力 |

## 競合認識

2026 年に e-Gov 公式の「公文書表示」機能が登場済みです。本ツールは以下の点で差別化します:

- **オフライン**: 公式 Web ツールは XML をアップロードするが、本ツールは手元で完結
- **CLI / 自動化**: スクリプトから一括処理が可能
- **Claude Code 連携**: 月次会計フロー等に組み込み可能
- **真のレスポンシブ**: 紙サイズに応じて意味ブロックを再配置 (v2.0.0)

## 関連プラグイン

- [pdf2md-docling](../pdf2md-docling/) — 生成された PDF を Markdown 化したい時に
- [jp-aoiro-accounting](../jp-aoiro-accounting/) — 青色申告帳簿との連携

## ライセンス

- 本プラグイン: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](fonts/LICENSE_ipaex.txt)
