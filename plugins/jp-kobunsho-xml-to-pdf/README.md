# jp-kobunsho-xml-to-pdf

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、**原本の見た目そのまま**の **PDF** と、検索・引用に便利な **Markdown** に変換するスキル + CLI ツール。

## 特徴

- **忠実印刷パイプライン (v3.0.0)**: XSL レイアウトを Chromium でそのまま印刷。**未知様式も様式別実装ゼロで原本通り**に出力
- **オフライン処理**: 個人情報を含む公文書を第三者サーバーに送らず手元で完結
- **用紙自動判定**: コンテンツ幅を実測して A4 縦 / A4 横 / A3 横 + 縮小率を自動選択。軽微な高さ溢れは縮小して 1 ページに収める
- **PDF / Markdown 同時出力**: `--format pdf/md/both`。Markdown は YAML frontmatter 付きで Obsidian / 帳簿への貼り付けに便利
- **複数 XML 対応**: 1 つの ZIP に複数の XML が含まれる場合、それぞれを個別ファイル化
- **日本語フォント同梱**: IPAex Gothic / Mincho を同梱し、環境差で豆腐化しない
- **CLI 単独動作**: Claude Code から呼ぶだけでなく、シェルから直接実行可能

## v3.0.0 の主な変更点 (v2.x からの移行)

**PDF 生成を「意味抽出 + 再構築」から「XSL 忠実印刷」へ全面置換。**

v2 は WeasyPrint の border-collapse バグを回避するため、XSL を捨てて意味データを抽出し CSS Grid で再配置していた。しかし未知様式が generic フォールバックに落ちると**表データの欠損・重複出力**が起きることが実運用で判明（2026-07-15、標準報酬決定通知書で標準報酬月額が PDF から消失）。v3 はレンダラを Chromium に替えることで問題の根本（WeasyPrint）を除去し、XSL を唯一のレイアウト定義として扱う。

| 項目 | v2.x | v3.0.0 |
|------|------|--------|
| PDF レンダラ | WeasyPrint | **Chromium (playwright)** |
| PDF レイアウト | extractor で意味抽出 → Jinja2 再構築 → CSS Grid | **XSLT 出力 HTML をそのまま印刷** |
| 未知様式の PDF | generic フォールバック（欠損・重複リスク） | **様式別実装不要で原本通り** |
| 用紙判定 | 様式ごとに固定定義 | コンテンツ幅実測 + scale 自動選択 |
| IE 互換 | — | `pre` の折り返し quirk を CSS 注入で補正 |
| 出力ファイル名 | XML 名 | **公文書の正式名称**（HTML `<title>`、重複は `_2` 付与） |
| Markdown | extractor + `*.md.j2` | **変更なし**（同経路を維持） |
| 依存 | lxml + weasyprint + jinja2 | lxml + jinja2 + **playwright** |

CLI 互換: フラグは v2 と同一。出力ファイル名は公文書の正式名称（HTML `<title>`）になった。呼び出し側の変更は不要（出力一覧は戻り値/標準出力で返る）。

## インストール

```bash
claude plugin install jp-kobunsho-xml-to-pdf@asgr-base
```

### Python 環境（推奨: 専用 venv）

```bash
PLUGIN=~/.claude/plugins/marketplaces/asgr-base/plugins/jp-kobunsho-xml-to-pdf

# 専用 venv を作る（初回のみ）
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/pip" install -q -r "$PLUGIN/requirements.txt"

# Chromium を導入（初回のみ、~95MB）
"$PLUGIN/.venv/bin/playwright" install chromium

# 動作確認
"$PLUGIN/.venv/bin/python" -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); print('OK')"
```

`requirements.txt` の中身:
- lxml >= 5.0
- jinja2 >= 3.0
- playwright >= 1.40

> v2 で必要だった pango/cairo (WeasyPrint 依存) は不要になりました。

## 使い方

### Claude Code から

```
e-Gov の公文書 ZIP を PDF にして: /path/to/kobunsho.zip
```

スキルが自動起動し、PDF を出力します。

### CLI から直接

```bash
PLUGIN=~/.claude/plugins/marketplaces/asgr-base/plugins/jp-kobunsho-xml-to-pdf
PY="$PLUGIN/.venv/bin/python"
CONVERT="$PLUGIN/scripts/convert.py"

# 基本 (PDF のみ)
"$PY" "$CONVERT" /path/to/kobunsho.zip

# Markdown のみ
"$PY" "$CONVERT" /path/to/kobunsho.zip --format md

# PDF + Markdown 同時
"$PY" "$CONVERT" /path/to/kobunsho.zip --format both

# 出力先指定 + 詳細ログ + 中間 HTML/MD ダンプ
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

**出力**: 同ディレクトリに 2 つの PDF（ファイル名は HTML `<title>` の公文書正式名称。無い場合は XML 名、同名は `_2` 付与）
- `日本年金機構からのお知らせ.pdf`（表紙、A4 縦）
- `社会保険料額情報.pdf`（社会保険料額表、A4 横 1 ページ）

## 対応様式

**PDF はすべての様式に対応**（XSL がレイアウトを定義するため様式別実装が不要）。

Markdown は意味抽出ベースのため、既知様式（yoshiki_04 / yoshiki_26 / yoshiki_29 / kagami_only）は構造化された表になり、未知様式は generic フォールバック（テキスト保証のみ、表構造が崩れる場合あり）になる。

## CLI フラグ

| フラグ | 既定 | 説明 |
|-------|-----|------|
| `<zip_path>` | 必須 | 入力 ZIP |
| `--output-dir DIR` | カレント | 出力先 |
| `--format {pdf,md,both}` | `pdf` | 出力形式 |
| `--debug-dir DIR` | 無し | 中間 HTML / MD のダンプ先 (デバッグ用) |
| `-v`, `--verbose` | False | 詳細ログを stderr に出力 |

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `playwright / Chromium が見つかりません` | 上記セットアップの `pip install -r requirements.txt` + `playwright install chromium` を実行 |
| `ModuleNotFoundError: jinja2` 等 | venv 消失（プラグイン更新で `.venv` が消えることがある）。venv を再作成 |
| PDF の文字が豆腐になる | 同梱 `fonts/ipaexg.ttf` の存在を確認（プラグイン再インストールで復旧） |
| 未知様式の Markdown が崩れる | 既知の制限（PDF は正しく出る）。PDF を正とし、必要なら extractor を追加 |

## 競合認識

2026 年に e-Gov 公式の「公文書表示」機能、社労士向け Web 変換ツール等が存在します。本ツールは以下の点で差別化します:

- **オフライン**: Web ツールは個人情報入り XML をアップロードするが、本ツールは手元で完結
- **CLI / 自動化**: スクリプトから一括処理が可能
- **Claude Code 連携**: 月次会計フロー等に組み込み可能

## 関連プラグイン

- [pdf2md-docling](../pdf2md-docling/) — 生成された PDF を Markdown 化したい時に
- [jp-aoiro-accounting](../jp-aoiro-accounting/) — 青色申告帳簿との連携

## ライセンス

- 本プラグイン: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](fonts/LICENSE_ipaex.txt)
