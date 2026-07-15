"""v3 PDF パイプライン: XSLT 出力 HTML を Chromium でそのまま印刷する。

v2（意味抽出 + CSS Grid 再構築 + WeasyPrint）が未知様式で表崩れ・データ欠損を
起こした反省から、v3 は XSL を唯一のレイアウト定義として扱い、忠実に再現する。
WeasyPrint の border-collapse バグは Chromium 採用により構造的に消滅する。

方式:
1. HTML に最小の印刷調整 CSS を注入（IPAex フォント / pre の折り返し互換）
2. 狭ビューポートで自然コンテンツ幅を実測 → A4縦/A4横/A3横 + scale を自動選択
3. わずかな高さ溢れ（〜1.25 ページ）は scale 縮小で 1 ページに収める
4. page.pdf() で出力

依存: playwright（+ `playwright install chromium`）。
"""
from __future__ import annotations

from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
_DEFAULT_FONTS_DIR = _SCRIPTS_DIR.parent / "fonts"

# CSS px (96dpi) での用紙サイズ。printable = 用紙幅/高さ − 余白 10mm×2 (≒76px)
_MARGIN_MM = 10
_MARGIN_PX = 76
_PAPERS = [
    # (format, landscape, printable_width_px, printable_height_px)
    ("A4", False, 794 - _MARGIN_PX, 1123 - _MARGIN_PX),
    ("A4", True, 1123 - _MARGIN_PX, 794 - _MARGIN_PX),
    ("A3", True, 1587 - _MARGIN_PX, 1123 - _MARGIN_PX),
]

# これ未満に縮めないと収まらない場合は、より大きい用紙候補へ進む
_MIN_SCALE = 0.65
# 高さがこの倍率以内の溢れなら scale 縮小で 1 ページに収める
# （明らかな複数ページ文書まで縮めてしまわないための閾値）
_HEIGHT_FIT_MAX_RATIO = 1.25
# コンテンツ幅実測用の狭ビューポート
_MEASURE_VIEWPORT = {"width": 400, "height": 800}

_SETUP_HINT = (
    "playwright / Chromium が見つかりません。プラグイン venv でセットアップしてください:\n"
    "  <plugin>/.venv/bin/pip install -r <plugin>/requirements.txt\n"
    "  <plugin>/.venv/bin/playwright install chromium"
)


def _inject_css(fonts_dir: Path) -> str:
    gothic = (fonts_dir / "ipaexg.ttf").resolve()
    mincho = (fonts_dir / "ipaexm.ttf").resolve()
    return f"""
@font-face {{ font-family: 'IPAexGothic'; src: url('file://{gothic}'); }}
@font-face {{ font-family: 'IPAexMincho'; src: url('file://{mincho}'); }}
html {{ font-family: 'IPAexGothic', sans-serif; }}
/* XSL 中の Windows フォント指定を同梱フォントへフォールバック */
body, table, td, th, div, span, p, pre {{ font-family: 'IPAexGothic', sans-serif; }}
/* IE quirk 互換: IE は word-wrap:break-word で <pre> も折り返していた。
   現代ブラウザは white-space:pre のまま溢れるので pre-wrap にする */
pre {{ white-space: pre-wrap; }}
/* e-Gov 申請アプリ系 XSL は設計幅のフォームを transform:scale() で画面幅に
   縮めて表示する（例: scale(0.64)）。印刷では二重縮小になるため無効化し、
   自然幅で測定 → こちらの用紙判定・scale に一元化する */
[style*="transform:scale"], [style*="transform: scale"] {{ transform: none !important; }}
"""


def _with_print_css(html: str, fonts_dir: Path) -> str:
    style = f"<style>{_inject_css(fonts_dir)}</style>"
    if "</head>" in html:
        return html.replace("</head>", style + "</head>", 1)
    return style + html


def _pick_paper(content_width: int, content_height: int) -> tuple[str, bool, float, int, int]:
    """コンテンツの縦横比に合う向きの用紙を選び、幅に合わせた scale を決める。

    - 縦長コンテンツ（W <= H）: A4縦一択。横向きにしても幅は増えるが高さ予算が
      減るだけなので、幅フィット縮小（fit-to-width）する。
    - 横長コンテンツ（W > H）: A4横 → A3横 の順に scale >= _MIN_SCALE で収まる
      最小用紙。収まらなければ A3横 + fit 縮小。

    Returns: (format, landscape, scale, printable_w, printable_h)
    """
    content_width = max(content_width, 1)
    if content_width <= max(content_height, 1):
        fmt, landscape, pw, ph = _PAPERS[0]  # A4 縦
        return fmt, landscape, round(min(1.0, pw / content_width), 3), pw, ph

    for fmt, landscape, pw, ph in _PAPERS[1:]:  # A4横 → A3横
        scale = min(1.0, pw / content_width)
        if scale >= _MIN_SCALE:
            return fmt, landscape, round(scale, 3), pw, ph
    fmt, landscape, pw, ph = _PAPERS[-1]
    return fmt, landscape, round(max(0.1, pw / content_width), 3), pw, ph


class ChromiumRenderer:
    """Chromium を 1 プロセスで使い回す PDF レンダラ。

    with ChromiumRenderer() as r:
        pdf_bytes = r.render_pdf(html)
    """

    def __init__(self, fonts_dir: Path | None = None) -> None:
        self._fonts_dir = fonts_dir or _DEFAULT_FONTS_DIR
        self._pw = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "ChromiumRenderer":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise RuntimeError(_SETUP_HINT) from e
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch()
        except Exception as e:
            self._pw.stop()
            self._pw = None
            raise RuntimeError(f"Chromium の起動に失敗しました: {e}\n{_SETUP_HINT}") from e
        self._page = self._browser.new_page(viewport=dict(_MEASURE_VIEWPORT))
        return self

    def __exit__(self, *exc) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._pw is not None:
            self._pw.stop()
            self._pw = None
        self._page = None

    def render_pdf(self, xml_html: str, debug_dir: Path | None = None,
                   debug_stem: str = "document") -> bytes:
        """XSLT 出力 HTML → PDF bytes。"""
        if self._page is None:
            raise RuntimeError("ChromiumRenderer は with 文の中で使ってください")
        page = self._page
        html = _with_print_css(xml_html, self._fonts_dir)
        if debug_dir is not None:
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / f"{debug_stem}.v3.html").write_text(html, encoding="utf-8")

        # 1) 狭ビューポートで自然コンテンツ幅を実測し、
        #    次に自然幅のビューポートで高さを実測（縦横比で用紙の向きを決める）
        page.set_viewport_size(dict(_MEASURE_VIEWPORT))
        page.set_content(html, wait_until="load")
        content_width = page.evaluate("document.scrollingElement.scrollWidth")
        page.set_viewport_size({
            "width": max(content_width, _MEASURE_VIEWPORT["width"]),
            "height": _MEASURE_VIEWPORT["height"],
        })
        content_height = page.evaluate("document.scrollingElement.scrollHeight")
        fmt, landscape, scale, pw, ph = _pick_paper(content_width, content_height)

        # 2) 印刷時のレイアウト幅でコンテンツ高さを再実測し、軽微な溢れは縮小で吸収
        layout_width = max(int(pw / scale), _MEASURE_VIEWPORT["width"])
        page.set_viewport_size({"width": layout_width, "height": _MEASURE_VIEWPORT["height"]})
        content_height = page.evaluate("document.scrollingElement.scrollHeight")
        height_ratio = (content_height * scale) / ph
        if 1.0 < height_ratio <= _HEIGHT_FIT_MAX_RATIO:
            scale = round(max(0.1, ph / content_height), 3)

        return page.pdf(
            format=fmt,
            landscape=landscape,
            scale=scale,
            margin={
                "top": f"{_MARGIN_MM}mm", "bottom": f"{_MARGIN_MM}mm",
                "left": f"{_MARGIN_MM}mm", "right": f"{_MARGIN_MM}mm",
            },
            print_background=True,
        )
