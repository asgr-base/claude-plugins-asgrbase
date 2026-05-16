---
name: jp-kobunsho-xml-to-pdf
description: e-Gov 電子申請から返送される公文書 ZIP（XML + XSL スタイルシート）を、読みやすい PDF に変換する。ユーザーが「公文書 ZIP を PDF にして」「e-Gov の XML を PDF 化」「社会保険料額情報の PDF を作って」と言うと自動起動。1 つの ZIP に複数の XML が含まれる場合は個別 PDF を出力。XSL の固定 px width や table-layout: fixed、`<pre>` 内の長文など、A4 を超えるあらゆるケースを HTML 正規化 + aggressive CSS injection + 強制レスポンシブ化の多段フォールバックで A4 縦 1 ページに収める。日本の社労士・人事担当・小規模事業主が e-Gov から受け取った XML 公文書を保管・確認したい場面で使う。
version: 1.1.0
author: claude_code
createDate: 2026-05-16
updateDate: 2026-05-16
license: MIT
---

# e-Gov 公文書 XML → PDF 変換ツール

e-Gov 電子申請から返送される公文書 ZIP（XML + XSL）を、日本語フォント埋め込み・自動 fit-to-page で 1 ページに収まる PDF に変換します。

## When to Use

- e-Gov の被保険者通知・社会保険料額情報・雇用保険関連書類などを PDF 化したい
- 公文書 ZIP の中身を可読な形式で保管・関係者と共有したい
- 月次の電子申請後に届く XML を会計記録に紐づけて保存したい

## Quick Reference

| 特性 | 値 |
|------|-----|
| 入力 | e-Gov 公文書 ZIP（XML + XSL + 添付） |
| 出力 | PDF（XML ごとに 1 ファイル） |
| 自動 fit | 600px 超の固定幅 → auto 置換、大 margin → 5px に縮小、WeasyPrint 実測でページ収納 |
| 日本語フォント | IPAex Gothic/Mincho（同梱） |
| 処理速度 | ~2-5 秒/XML（PoC 実測） |

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
# プラグインのインストール先（バージョンは install 時のものに置き換え）
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | head -1)
echo "Plugin path: $PLUGIN"

# 専用 venv を作る（初回のみ）
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/pip" install -q -r "$PLUGIN/requirements.txt"

# 動作確認
"$PLUGIN/.venv/bin/python" -c "import lxml, weasyprint; print('OK', lxml.__version__, weasyprint.__version__)"
```

`requirements.txt` の中身:
- lxml >= 5.0
- weasyprint >= 65

### 3. パス確認

Claude Code のプラグインキャッシュ構造により、`convert.py` は次の場所にあります:

```bash
# 標準的なインストール先
PLUGIN=$(ls -d ~/.claude/plugins/cache/asgr-base/jp-kobunsho-xml-to-pdf/*/ | head -1)
CONVERT="$PLUGIN/scripts/convert.py"
PYTHON="$PLUGIN/.venv/bin/python"  # 上で作った venv

# 動作確認
ls -la "$CONVERT" "$PYTHON"
```

## 変換手順

### Step 1: ZIP のパス確認

ユーザーから受領した e-Gov 公文書 ZIP のローカルパスを確認します（通常はメール添付やダウンロードフォルダ）。

### Step 2: CLI で変換

```bash
# 基本（前提条件 3 で設定した $PYTHON, $CONVERT を使用）
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip

# 出力先指定
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --output-dir /tmp/out

# 向き手動指定
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --landscape

# 自動 fit を切る（XSL 元の見た目を尊重する場合）
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --no-fit

# zoom 手動指定
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --zoom 0.7

# 詳細ログ
"$PYTHON" "$CONVERT" /path/to/kobunsho.zip --verbose
```

### Step 3: 結果確認

ZIP 内の各 XML について同名 `.pdf` が出力されます。

```bash
ls -la /tmp/out/
# 例:
# 202605160534016314.pdf
# 社会保険料額情報_令和8年4月分(202605160534016314).pdf
```

## ZIP 構造（参考）

e-Gov 公文書 ZIP は以下のような構造が典型です:

```
<受付番号>.zip
└── <受付番号>/
    ├── kagami.xsl                          # 共通表紙 XSL
    ├── yoshiki_<NN>_<area>_<NNN>.xsl       # 様式別本文 XSL（あれば）
    ├── <文書ID>.xml                        # メイン公文書 XML
    ├── <別文書名>.xml                      # 追加文書（あれば）
    ├── <添付>.csv                          # 明細（実体は Shift_JIS テキスト）
    └── SHFD<NNNN>.DTA                      # バイナリ（一部の通知書）
```

各 XML の冒頭 `<?xml-stylesheet type="text/xsl" href="..." ?>` 指示で参照される XSL が同 ZIP 内に同梱されています。

## 自動 fit-to-page アルゴリズム (v1.1.0)

XSL は画面表示用に固定 px（例: `width: 1400px`）や `table-layout: fixed`、`<pre>` 内の長文を持つことが多く、A4 縦では収まらないケースが頻発します。本スキルは以下の 4 段階フォールバックで A4 縦 1 ページ収納を目指します:

| Pass | 処理 | 対応するケース |
|------|------|--------------|
| **1. 通常レンダリング** | HTML 正規化（600px 超 width → auto、30px 超 margin → 5px、table-layout: fixed → auto、cellpadding="20px" → "20"）→ A4 縦／横で render | 多くの一般的な公文書 |
| **2. Aggressive CSS** | `table { max-width: 100% !important }` / `pre { white-space: pre-wrap !important }` / `td { white-space: normal !important }` 等を強制注入 | `<pre>` 内の長文や `white-space: nowrap` が原因のはみ出し |
| **3. 全 width 強制 100%** | HTML 内のすべての width 指定（CSS + 属性）を `100%` に置換、`table-layout: auto` 強制 | 複雑な CSS class 階層で width が深く埋め込まれているケース |
| **4. 長尺紙フォールバック** | A4 をあきらめ、コンテンツ実幅に合わせた規格外サイズの PDF を生成 | どうしても折り返せない極端なコンテンツ |

横はみ出しは WeasyPrint Document API で **実コンテンツ右端 X 座標** を測って判定します（縦に長い→複数ページは正当として扱う）。

`--no-fit` フラグで正規化と fit の両方をスキップできます（元 XSL の見た目を保ったまま、収まらない場合はクリップされた PDF が出ます）。

## CLI 引数リファレンス

| フラグ | 既定値 | 説明 |
|-------|-------|------|
| `<zip_path>` (位置引数) | 必須 | 入力 ZIP |
| `--output-dir DIR` | ZIP と同じディレクトリ | 出力先 |
| `--portrait` | (自動) | A4 縦を強制 |
| `--landscape` | (自動) | A4 横を強制 |
| `--no-fit` | False | 自動 fit を無効化 |
| `--zoom FLOAT` | (自動) | 手動 zoom（fit より優先） |
| `--verbose` | False | 各 XML の処理ログを stderr に出力 |

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `cannot load library 'libpango...'` | `brew install pango` (macOS) / `apt-get install libpango-1.0-0` (Linux) |
| `xml-stylesheet 指示が見つかりません` | ZIP 内の XML が `<?xml-stylesheet?>` を含まない異常データ。XSL を `--xsl` で明示指定（将来拡張予定） |
| `参照されている XSL が ZIP 内にありません` | ZIP の構造異常。ZIP を unzip して中身を確認 |
| PDF に豆腐（□）が表示される | フォント参照が壊れている。`fonts/ipaexg.ttf` の存在を確認 |
| 自動 fit でレイアウトが崩れる | `--no-fit --landscape` で fit を切って横向き出力 |

## ライセンス

- 本ツール: MIT
- 同梱 IPAex フォント: [IPA フォントライセンス v1.0](fonts/LICENSE_ipaex.txt)
