---
name: jp-kobunsho-xml-to-pdf
description: e-Gov 電子申請から返送される公文書 ZIP（XML + XSL スタイルシート）を、原本の見た目そのままの PDF または検索用 Markdown に変換する。ユーザーが「公文書 ZIP を PDF にして」「e-Gov の XML を PDF 化」「公文書を Markdown 化」「社会保険料額情報の PDF を作って」と言うと自動起動。v3.0.0 から PDF は XSL レイアウトを Chromium で忠実印刷する方式になり、未知様式も様式別実装なしで原本通りに出力される（用紙サイズ・縮小率は自動判定）。1 つの ZIP に複数の XML が含まれる場合は個別ファイルを出力。日本の社労士・人事担当・小規模事業主が e-Gov から受け取った XML 公文書を保管・確認・帳簿に貼り付けたい場面で使う。
version: 3.0.0
author: claude_code
createDate: 2026-05-16
updateDate: 2026-07-15
license: MIT
---

# e-Gov 公文書 XML → PDF / Markdown 変換ツール (v3.0.0)

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、**原本の見た目そのまま**の PDF と、検索・引用用の Markdown に変換します。

## When to Use

- e-Gov の被保険者通知・社会保険料額情報・口座振替開始通知・標準報酬決定通知などを PDF 化したい
- 公文書 ZIP の中身を可読な形式で保管・関係者と共有したい
- 月次の電子申請後に届く XML を会計記録に紐づけて保存したい
- **Markdown として** Obsidian / MoneyForward / 帳簿ファイルへ貼り付けたい
- 公文書を **grep / diff** したい (PDF テキスト抽出より高速)

## v3.0.0 の主な変更 (v2.x 比)

**PDF 生成を「意味抽出 + 再構築」から「XSL 忠実印刷」へ全面置換。**

v2 は WeasyPrint の border-collapse バグ回避のため意味データを抽出して CSS Grid で再配置していたが、未知様式が generic フォールバックに落ちると表データの**欠損・重複**が起きた（2026-07-15、標準報酬決定通知書 7130001 で実際に発生）。v3 はレンダラを Chromium に替え、XSL を唯一のレイアウト定義として扱う。

| 項目 | v2.x | v3.0.0 |
|------|------|--------|
| PDF レンダラ | WeasyPrint | **Chromium (playwright)** |
| PDF レイアウト | 意味抽出 → Jinja2 → CSS Grid | **XSLT 出力 HTML をそのまま印刷** |
| 未知様式の PDF | generic フォールバック（欠損・重複リスク） | **様式別実装不要で原本通り** |
| 用紙判定 | 様式ごとに固定定義 | コンテンツ幅実測 + scale 自動選択（A4縦/A4横/A3横） |
| 出力ファイル名 | XML 名 | **公文書の正式名称**（HTML `<title>`、重複は `_2` 付与） |
| Markdown | extractor + `*.md.j2` | **変更なし** |
| 依存 | lxml + weasyprint + jinja2 | lxml + jinja2 + **playwright** |

CLI 互換: フラグは v2 と同一。出力ファイル名は公文書の正式名称（HTML `<title>`）になった。呼び出し側（kobunsho-archiver 等）の変更は不要（出力一覧は戻り値/標準出力で返る）。

## Quick Reference

| 特性 | 値 |
|------|-----|
| 入力 | e-Gov 公文書 ZIP（XML + XSL + 添付） |
| 出力 | PDF / Markdown / 両方（XML ごとに 1 ファイル、`--format` で選択） |
| PDF パイプライン | XSLT (lxml) → 印刷調整 CSS 注入 → Chromium page.pdf() |
| MD パイプライン | extractor (lxml) → Jinja2 (`*.md.j2`) |
| 日本語フォント | IPAex Gothic/Mincho（同梱、@font-face 注入） |
| 処理速度 | ~2-5 秒/XML（Chromium は ZIP 単位で 1 プロセスを使い回し） |

## 前提条件

### Python 環境のセットアップ（推奨: 専用 venv）

```bash
# プラグインのインストール先
PLUGIN=~/.claude/plugins/marketplaces/asgr-base/plugins/jp-kobunsho-xml-to-pdf
echo "Plugin path: $PLUGIN"

# 専用 venv を作る（初回のみ）
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/pip" install -q -r "$PLUGIN/requirements.txt"

# Chromium を導入（初回のみ、~95MB。~/Library/Caches/ms-playwright に入る）
"$PLUGIN/.venv/bin/playwright" install chromium

# 動作確認
"$PLUGIN/.venv/bin/python" -c "import lxml, jinja2; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); print('OK')"
```

`requirements.txt` の中身:
- lxml >= 5.0
- jinja2 >= 3.0
- playwright >= 1.40

> v2 で必要だった pango/cairo (WeasyPrint) は不要になりました。

### パス確認

```bash
PLUGIN=~/.claude/plugins/marketplaces/asgr-base/plugins/jp-kobunsho-xml-to-pdf
CONVERT="$PLUGIN/scripts/convert.py"
PYTHON="$PLUGIN/.venv/bin/python"
ls -la "$CONVERT" "$PYTHON"
```

## 変換手順

### Step 1: ZIP のパス確認

ユーザーから受領した e-Gov 公文書 ZIP のローカルパスを確認します（通常はメール添付やダウンロードフォルダ）。

### Step 2: CLI で変換

```bash
# 基本 (PDF のみ)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip

# 出力先指定
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --output-dir /tmp/out

# Markdown のみ
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --format md

# PDF + Markdown 両方
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --format both

# 中間 HTML / MD をダンプ (デバッグ用)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --debug-dir /tmp/dbg

# 詳細ログ (stderr に出力)
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --verbose
```

### Step 3: 結果確認

ZIP 内の各 XML について、**公文書の正式名称**（HTML `<title>`）をファイル名にした `.pdf`（/`.md`）が出力されます。`<title>` が無い XML は XML 名にフォールバックし、同一 ZIP 内で名称が重複する場合は `_2` を付与します。

```bash
ls -la out/
# 例（ファイル名は公文書の正式名称 = HTML <title> 由来）:
# 日本年金機構からのお知らせ.pdf
# 社会保険料額情報.pdf
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

## v3.0.0 PDF パイプライン

```
ZIP 展開
  ↓
XML 列挙 (.xml のみ)
  ↓
XSLT 変換 (lxml.etree.XSLT) → XSL レイアウトの HTML
  ↓
印刷調整 CSS を注入 (scripts/lib/render_v3.py)
  - IPAex フォント @font-face（環境差の吸収）
  - pre { white-space: pre-wrap }（IE quirk 互換: IE は word-wrap で <pre> も折り返していた）
  - XSL 自身の transform:scale() を無効化（e-Gov 申請アプリ系 XSL は設計幅フォームを
    画面幅に縮めて表示するため、印刷では二重縮小になる）
  ↓
Chromium で用紙自動判定
  - 狭ビューポート(400px)で自然コンテンツ幅、自然幅ビューポートで高さを実測
  - 縦長コンテンツ（W<=H）→ A4縦 + 幅フィット縮小
  - 横長コンテンツ（W>H）→ A4横 → A3横 の順に scale >= 0.65 で収まる最小用紙
  - 高さが 1.25 ページ以内の溢れなら scale 縮小で 1 ページに収める
  ↓
page.pdf() で出力（余白 10mm、Chromium は ZIP 単位で 1 プロセスを使い回し）
```

Markdown は v2 の意味抽出経路（form_detector → extractor → `*.md.j2`）を維持。既知様式（yoshiki_04 / 26 / 29 / kagami_only）は構造化された表になる。

### 既知の制限

- **未知様式の Markdown** は generic フォールバックのため表構造が崩れたり重複することがある。**PDF は常に正**なので、PDF を一次成果物として扱うこと。Markdown の品質が必要になったら extractor を追加する（`scripts/lib/extractors/` + `templates/yoshiki_NN.md.j2`）

## CLI 引数リファレンス

| フラグ | 既定値 | 説明 |
|-------|-------|------|
| `<zip_path>` (位置引数) | 必須 | 入力 ZIP |
| `--output-dir DIR` | カレント | 出力先 |
| `--format {pdf,md,both}` | `pdf` | 出力形式。`md` は Markdown のみ、`both` は同 stem で両方 |
| `--debug-dir DIR` | 無し | 中間 HTML / MD をダンプ |
| `-v`, `--verbose` | False | 詳細ログを stderr に出力 |

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `playwright / Chromium が見つかりません` | `"$PLUGIN/.venv/bin/pip" install -r requirements.txt` → `"$PLUGIN/.venv/bin/playwright" install chromium` |
| `ModuleNotFoundError: jinja2` 等 | venv 消失（プラグイン更新で `.venv` が消えることがある）。上記セットアップで venv を再作成 |
| Chromium 起動失敗 (SSH/headless 環境) | headless モードは GUI 不要。sandbox エラーが出る場合のみ環境を確認 |
| `xml-stylesheet 指示が見つかりません` | ZIP 内の XML が `<?xml-stylesheet?>` を含まない異常データ |
| PDF に豆腐（□）が表示される | フォント参照が壊れている。`fonts/ipaexg.ttf` の存在を確認 |
| 未知様式の Markdown が崩れる | 既知の制限（PDF は正しく出る）。PDF を正とし、必要なら extractor を追加 |

## ライセンス

- 本ツール: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](../../fonts/LICENSE_ipaex.txt)
