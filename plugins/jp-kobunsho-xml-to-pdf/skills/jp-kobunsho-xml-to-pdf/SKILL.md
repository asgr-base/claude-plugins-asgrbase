---
name: jp-kobunsho-xml-to-pdf
description: e-Gov 電子申請から返送される公文書 ZIP（XML + XSL スタイルシート）を、読みやすい PDF または Markdown に変換する。ユーザーが「公文書 ZIP を PDF にして」「e-Gov の XML を PDF 化」「公文書を Markdown 化」「社会保険料額情報の PDF を作って」と言うと自動起動。1 つの ZIP に複数の XML が含まれる場合は個別ファイルを出力。XSL の table 入れ子に依存せず、意味データを抽出して CSS Grid で再配置する真のレスポンシブパイプラインで、罫線完全制御・1 ページ収納・全データ表示を保証する。v2.1.0 から同じ意味データから Markdown も同時生成可能 (--format pdf/md/both)。日本の社労士・人事担当・小規模事業主が e-Gov から受け取った XML 公文書を保管・確認・帳簿に貼り付けたい場面で使う。
version: 2.1.0
author: claude_code
createDate: 2026-05-16
updateDate: 2026-05-24
license: MIT
---

# e-Gov 公文書 XML → PDF / Markdown 変換ツール (v2.1.0)

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、**真のレスポンシブレイアウト**で 1 ページに収まる PDF または Markdown に変換します。

## When to Use

- e-Gov の被保険者通知・社会保険料額情報・口座振替開始通知などを PDF 化したい
- 公文書 ZIP の中身を可読な形式で保管・関係者と共有したい
- 月次の電子申請後に届く XML を会計記録に紐づけて保存したい
- **Markdown として** Obsidian / MoneyForward / 帳簿ファイルへ貼り付けたい (v2.1.0)
- 公文書を **grep / diff** したい (PDF テキスト抽出より高速)

## v2.1.0 の新機能

- **`--format {pdf,md,both}` フラグ追加**: 同じ extractor → Document データから、PDF と Markdown を選択 / 同時出力可能
  - `--format pdf` (default): v2.0.x と同等の PDF 出力のみ (後方互換)
  - `--format md`: Markdown のみ出力 (`.md` 拡張子、PDF と同 stem)
  - `--format both`: PDF + Markdown を同ディレクトリに対で出力
- Markdown は YAML frontmatter (form_id / paper / title) 付き
- 5 様式すべて Markdown 対応 (yoshiki_29 / yoshiki_04 / yoshiki_26 / kagami_only / generic)

```bash
# Markdown のみ
"$PY" "$CONVERT" /path/to/kobunsho.zip --format md

# PDF + Markdown 同時
"$PY" "$CONVERT" /path/to/kobunsho.zip --format both
```

## v2.0.0 の主な改善 (v1.x 比)

| 項目 | v1.x | v2.0.0 |
|------|------|--------|
| アーキテクチャ | XSL 出力 HTML に CSS 注入で fit | XSL を読み捨てて意味データ抽出 → Jinja2 + CSS Grid で再構築 |
| 罫線品質 | WeasyPrint の border-collapse バグで一部抜け・二重 | `<div>` + flex / Grid ベースで完全制御、抜けゼロ・太さ均一 |
| レスポンシブ | 固定 px width のまま zoom 探索 | `grid-template-areas` で紙サイズに応じて意味ブロックを再配置 |
| 改行・折り返し | `<pre>` 長文がはみ出し | tr 境界で自動分割、長文は `pre-wrap` で折り返し |
| 未知様式対応 | エラー | generic フォールバックで共通 class を自動検出 |

## 対応様式 (v2.0.0)

| 様式 | 文書名 | デフォルト紙 |
|------|-------|---------|
| `yoshiki_29` | 保険料納入告知額・領収済額通知書 | A3 横 |
| `yoshiki_04` | 社会保険料額情報 | A4 横 |
| `yoshiki_26` | 健康保険・厚生年金保険口座振替開始通知書 | A4 縦 |
| `kagami_only` | 表紙のみ (DTA 付き等) | A4 縦 |
| `generic` | 未知様式 (フォールバック) | A4 縦 |

## Quick Reference

| 特性 | 値 |
|------|-----|
| 入力 | e-Gov 公文書 ZIP（XML + XSL + 添付） |
| 出力 | PDF / Markdown / 両方（XML ごとに 1 ファイル、`--format` で選択） |
| パイプライン | extractor (lxml) → Jinja2 → CSS Grid → WeasyPrint (PDF) or Markdown |
| 日本語フォント | IPAex Gothic/Mincho（同梱） |
| 処理速度 | ~2-5 秒/XML |

## 前提条件

### 1. システム依存ライブラリ

WeasyPrint は pango / cairo / gdk-pixbuf を必要とします。

```bash
# macOS
brew install pango

# Linux (Debian/Ubuntu)
apt-get install -y libpango-1.0-0 libpangoft2-1.0-0
```

### 2. Python 環境のセットアップ（推奨: 専用 venv）

システム Python に直接 weasyprint を入れると他プロジェクトと衝突するため、**プラグイン専用の venv を作る**のを推奨します。

```bash
# プラグインのインストール先
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | tail -1)
echo "Plugin path: $PLUGIN"

# 専用 venv を作る（初回のみ）
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/pip" install -q -r "$PLUGIN/requirements.txt"

# 動作確認
"$PLUGIN/.venv/bin/python" -c "import lxml, weasyprint, jinja2; print('OK', lxml.__version__, weasyprint.__version__, jinja2.__version__)"
```

`requirements.txt` の中身:
- lxml >= 5.0
- weasyprint >= 65
- jinja2 >= 3.0

### 3. パス確認

```bash
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | tail -1)
CONVERT="$PLUGIN/scripts/convert.py"
PYTHON="$PLUGIN/.venv/bin/python"
ls -la "$CONVERT" "$PYTHON"
```

## 変換手順

### Step 1: ZIP のパス確認

ユーザーから受領した e-Gov 公文書 ZIP のローカルパスを確認します（通常はメール添付やダウンロードフォルダ）。

### Step 2: CLI で変換

```bash
# 基本 (PDF のみ、v2.0 と後方互換)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip

# 出力先指定
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --output-dir /tmp/out

# Markdown のみ (v2.1.0)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --format md

# PDF + Markdown 両方 (v2.1.0)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --format both

# 中間 HTML / CSS / MD をダンプ (デバッグ用)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --debug-dir /tmp/dbg

# 詳細ログ (form 判定や fit 結果を stderr に出力)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --verbose
```

### Step 3: 結果確認

ZIP 内の各 XML について同名 `.pdf` が出力されます。

```bash
ls -la out/
# 例:
# 202605160534016314.pdf
# 社会保険料額情報_令和8年4月分(202605160534016314).pdf
```

## ZIP 構造（参考）

```
<受付番号>.zip
└── <受付番号>/
    ├── kagami.xsl                          # 共通表紙 XSL
    ├── yoshiki_<NN>_<area>_<NNN>.xsl       # 様式別本文 XSL（あれば）
    ├── <受付番号>.xml                      # kagami 経由の XML
    ├── <文書名>(<受付番号>).xml            # 様式別の本体 XML
    ├── <添付>.csv                          # 明細 (Shift_JIS テキスト)
    └── SHFD<NNNN>.DTA                      # 磁気媒体届書バイナリ (一部の通知書)
```

各 XML の冒頭 `<?xml-stylesheet type="text/xsl" href="..." ?>` 指示で参照される XSL が同 ZIP 内に同梱されています。`.xml` 以外のファイル (CSV / DTA / その他) は自動的にスキップされます。

## v2.0.0 パイプライン

```
ZIP 展開
  ↓
XML 列挙 (.xml のみ)
  ↓
XSLT 変換 (lxml.etree.XSLT)
  ↓
form_detector で様式判定 (XSL 名 → HTML 指紋 → generic)
  ↓
extractor で意味データ抽出 (lxml + XPath)
  - oshirase / title / appeal / payment / address / detail 等を Block 化
  ↓
Jinja2 テンプレートで HTML を新規生成 (div ベース)
  ↓
CSS Grid (grid_v2.css) で紙サイズに応じて意味ブロックを配置
  ↓
WeasyPrint で PDF 化 (border-collapse は使わない)
```

### 様式追加の拡張ポイント

新様式 `yoshiki_NN` に対応する手順:

1. `scripts/lib/extractors/yoshiki_NN.py` を作成し、`BaseExtractor` を継承して `extract(html) -> Document` を実装
2. `scripts/lib/extractors/__init__.py` の `EXTRACTORS` 辞書に登録
3. `scripts/lib/form_detector.py` の `_FORM_DEFAULTS` に紙サイズを登録
4. `scripts/templates/yoshiki_NN.html.j2` を作成 (`{% extends "base.html.j2" %}` から）
5. `scripts/css/grid_v2.css` に `[data-form="yoshiki_NN"]` セクションを追加

未対応の様式は `generic` extractor にフォールバックし、e-Gov 共通 class (`oshirase` / `title` / `caption` / `jgshName` / `jimusho` / `detail` / `pre.normal` 等) を自動検出して最低限の表示を保証します。

## CLI 引数リファレンス

| フラグ | 既定値 | 説明 |
|-------|-------|------|
| `<zip_path>` (位置引数) | 必須 | 入力 ZIP |
| `--output-dir DIR` | カレント | 出力先 |
| `--format {pdf,md,both}` | `pdf` | 出力形式 (v2.1.0)。`md` は Markdown のみ、`both` は同 stem で両方 |
| `--debug-dir DIR` | 無し | 中間 HTML / CSS / MD をダンプ |
| `-v`, `--verbose` | False | 詳細ログを stderr に出力 |

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `cannot load library 'libpango...'` | `brew install pango` (macOS) / `apt-get install libpango-1.0-0` (Linux) |
| `ModuleNotFoundError: jinja2` | `pip install -r requirements.txt` (v2.0.0 で追加された依存) |
| 未知の様式で罫線が崩れる | generic フォールバックは最低限の表示のみ。新 extractor の追加を検討 |
| `xml-stylesheet 指示が見つかりません` | ZIP 内の XML が `<?xml-stylesheet?>` を含まない異常データ |
| PDF に豆腐（□）が表示される | フォント参照が壊れている。`fonts/ipaexg.ttf` の存在を確認 |

## ライセンス

- 本ツール: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](../../fonts/LICENSE_ipaex.txt)
