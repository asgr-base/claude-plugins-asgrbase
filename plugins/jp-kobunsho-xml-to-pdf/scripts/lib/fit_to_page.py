"""HTML → PDF レンダリングと自動 fit-to-page。

XSL が画面表示用の固定 px width を持つため、A4 1 ページに収めるには:
1. HTML 正規化（html_normalizer で fix px width / 大 margin を緩和）
2. WeasyPrint で実レンダリング後、コンテンツ右端 X 座標を実測
3. 横はみ出しがあれば向きを切り替え、それでもダメなら追加 CSS で強制レスポンシブ化
4. 縦に長いコンテンツ（複数ページ）は正当として扱い、横はみ出しと区別する

注意: WeasyPrint の `html { zoom }` はレイアウト幅計算には反映されないため、
zoom ループでは横はみ出しを解消できない。代わりに CSS インジェクションで対処する。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from weasyprint import HTML, CSS

from . import html_normalizer


Orientation = Literal["portrait", "landscape"]


@dataclass
class FitOptions:
    """fit-to-page の挙動制御。"""
    force_orientation: Optional[Orientation] = None
    no_fit: bool = False
    manual_zoom: Optional[float] = None
    fonts_dir: Optional[Path] = None
    page_margin_mm: int = 5
    zoom_step: float = 0.05
    zoom_min: float = 0.20


@dataclass
class FitResult:
    """レンダリング結果と適用された設定。"""
    orientation: Orientation
    zoom: float
    page_count: int
    fits_horizontally: bool  # 横はみ出しなし
    fits: bool  # fits_horizontally AND page_count == 1（旧仕様互換）
    attempts: int = 0


# 横はみ出しを解消するための追加 CSS（強制レスポンシブ化）。
# 既存の固定 width 指定 / white-space: nowrap / pre を !important で打ち消し、
# テキストを必ず折り返させる。
_AGGRESSIVE_FIT_CSS = """
table { max-width: 100% !important; table-layout: auto !important; }
table, tr, td, th { word-break: break-word !important; overflow-wrap: anywhere !important; }
td, th, p, div, span { white-space: normal !important; }
pre { white-space: pre-wrap !important; word-break: break-word !important; max-width: 100% !important; }
div, p, h1, h2, h3, h4, h5, h6 { max-width: 100% !important; }
img { max-width: 100% !important; height: auto !important; }
"""


def _page_css(
    orientation: Orientation,
    margin_mm: int,
    zoom: float,
    fonts_dir: Optional[Path],
    aggressive: bool = False,
) -> str:
    """@page と html { zoom } を組み立てる。フォント @font-face は fonts_dir 指定時に追加。
    aggressive=True なら横はみ出し対策の追加 CSS をプリペンドする。
    """
    font_face = ""
    if fonts_dir:
        gothic = (fonts_dir / "ipaexg.ttf").resolve()
        mincho = (fonts_dir / "ipaexm.ttf").resolve()
        if gothic.exists():
            font_face += (
                f"@font-face {{ font-family: 'IPAex Gothic'; src: url('file://{gothic}'); }}\n"
            )
        if mincho.exists():
            font_face += (
                f"@font-face {{ font-family: 'IPAex Mincho'; src: url('file://{mincho}'); }}\n"
            )
        font_face += "body { font-family: 'IPAex Gothic', sans-serif; }\n"
    aggressive_css = _AGGRESSIVE_FIT_CSS if aggressive else ""
    return (
        f"{font_face}"
        f"@page {{ size: A4 {orientation}; margin: {margin_mm}mm; }}\n"
        f"html {{ zoom: {zoom}; }}\n"
        f"{aggressive_css}"
    )


def _max_content_right(page) -> float:
    """ページ内のレイアウトボックスを走査し、最も右の X 座標（CSS px）を返す。"""
    max_right = 0.0

    def walk(box):
        nonlocal max_right
        px = getattr(box, "position_x", None)
        pw = getattr(box, "width", None)
        if isinstance(px, (int, float)) and isinstance(pw, (int, float)):
            right = px + pw
            if right > max_right:
                max_right = right
        for child in getattr(box, "children", ()) or ():
            walk(child)

    walk(page._page_box)
    return max_right


def _render(
    html_str: str,
    base_url: str,
    orientation: Orientation,
    zoom: float,
    opts: FitOptions,
    aggressive: bool = False,
):
    css = CSS(string=_page_css(orientation, opts.page_margin_mm, zoom, opts.fonts_dir, aggressive))
    return HTML(string=html_str, base_url=base_url).render(stylesheets=[css])


def _fits_horizontally(doc) -> bool:
    """全ページでコンテンツ右端 <= ページ幅なら True。"""
    if not doc.pages:
        return False
    for page in doc.pages:
        if _max_content_right(page) > page.width + 1.0:
            return False
    return True


def _fits(doc) -> bool:
    """1 ページかつ横はみ出しなしなら True（旧仕様互換）。"""
    return len(doc.pages) == 1 and _fits_horizontally(doc)


def _make_result(orient: Orientation, zoom: float, doc, attempts: int) -> FitResult:
    fh = _fits_horizontally(doc)
    return FitResult(
        orientation=orient,
        zoom=zoom,
        page_count=len(doc.pages),
        fits_horizontally=fh,
        fits=fh and len(doc.pages) == 1,
        attempts=attempts,
    )


def render(html_str: str, base_url: str, opts: FitOptions) -> tuple[bytes, FitResult]:
    """HTML を PDF bytes に変換し、fit 結果も返す。

    縦に長いコンテンツは複数ページに正当に分割されるため、`fits_horizontally`
    で「横はみ出し」のみを判定する。`fits` は旧仕様互換で「1 ページ完全収納」。
    """
    # 1. HTML 正規化（no_fit でない場合のみ）
    src = html_str if opts.no_fit else html_normalizer.normalize_all(html_str)

    # 2. 手動 zoom が指定されていれば 1 回だけレンダリングして返す
    if opts.manual_zoom is not None:
        orient = opts.force_orientation or "portrait"
        doc = _render(src, base_url, orient, opts.manual_zoom, opts)
        return doc.write_pdf(), _make_result(orient, opts.manual_zoom, doc, 1)

    # 3. no_fit: 縦 zoom=1.0 で固定（force_orientation あれば反映）
    if opts.no_fit:
        orient = opts.force_orientation or "portrait"
        doc = _render(src, base_url, orient, 1.0, opts)
        return doc.write_pdf(), _make_result(orient, 1.0, doc, 1)

    # 4. 自動 fit: 「横はみ出しなし」を目指す。縦に長いコンテンツは複数ページ OK。
    orients: tuple[Orientation, ...] = (
        (opts.force_orientation,) if opts.force_orientation else ("portrait", "landscape")
    )
    return _orient_search(src, base_url, opts, orients)


def _orient_search(
    src: str,
    base_url: str,
    opts: FitOptions,
    orientations: tuple[Orientation, ...],
) -> tuple[bytes, FitResult]:
    """1) 各向きで通常レンダリング → 横はみ出しなしなら採用。
    2) すべて横はみ出しなら、aggressive CSS injection で再試行。
    3) それでもダメなら最後の試行を返す（PDF は出力するが fits_horizontally=False）。
    """
    attempts = 0
    candidates: list[tuple[Orientation, "Document"]] = []  # noqa: F821

    # Pass 1: 通常レンダリング
    for orient in orientations:
        attempts += 1
        doc = _render(src, base_url, orient, 1.0, opts, aggressive=False)
        candidates.append((orient, doc))
        if _fits_horizontally(doc):
            return doc.write_pdf(), _make_result(orient, 1.0, doc, attempts)

    # Pass 2: aggressive CSS injection（横はみ出し強制レスポンシブ）
    for orient in orientations:
        attempts += 1
        doc = _render(src, base_url, orient, 1.0, opts, aggressive=True)
        candidates.append((orient, doc))
        if _fits_horizontally(doc):
            return doc.write_pdf(), _make_result(orient, 1.0, doc, attempts)

    # Pass 3: 最終手段 — 全 width 指定を 100% に強制して A4 縦で再レンダリング。
    # XSL の固定幅レイアウトを完全に無視するため、表のバランスは崩れる可能性があるが
    # 「全テキストが折り返されて A4 縦の用紙に収まる」を最優先する。
    forced = html_normalizer.force_all_widths_relative(src)
    for orient in orientations:
        attempts += 1
        doc = _render(forced, base_url, orient, 1.0, opts, aggressive=True)
        if _fits_horizontally(doc):
            return doc.write_pdf(), _make_result(orient, 1.0, doc, attempts)

    # Pass 4: それでもダメなら、長尺紙（実コンテンツ幅に合わせたカスタムページ）で出力。
    attempts += 1
    custom_doc = _render_custom_size(forced, base_url, opts)
    return custom_doc.write_pdf(), _make_result(
        opts.force_orientation or "portrait", 1.0, custom_doc, attempts
    )


def _render_custom_size(src: str, base_url: str, opts: FitOptions):
    """A4 では絶対に収まらないコンテンツ向け。実コンテンツ幅に合わせた PDF を出力する。

    1. 一旦巨大なページサイズ (2000×3000mm) でレンダリングし、実コンテンツ右端を計測
    2. その幅 + 余白 = 必要ページ幅 mm、高さは auto（コンテンツに合わせる）で再レンダリング

    注意: WeasyPrint の `@page size` は **mm/cm/in 等の物理単位のみサポート**（px は無視されて
    A4 にフォールバックする）ため、px → mm 変換が必須。
    """
    PX_PER_MM = 96 / 25.4  # CSS px (96dpi) → mm

    # Step 1: A4 portrait で一旦測る（コンテンツの自然な実幅を得る）
    measure_css = CSS(
        string=_page_css("portrait", 0, 1.0, opts.fonts_dir, aggressive=True)
    )
    measure_doc = HTML(string=src, base_url=base_url).render(stylesheets=[measure_css])
    if not measure_doc.pages:
        return measure_doc
    # 横はみ出した実コンテンツ右端を全ページで取得（A4 では複数ページに分かれることがある）
    content_right_px = max(_max_content_right(p) for p in measure_doc.pages)
    content_height_px = sum(_max_content_bottom(p) for p in measure_doc.pages)

    # Step 2: 実コンテンツに合わせたカスタムページ作成（mm 単位、両軸明示）
    margin_mm = opts.page_margin_mm
    needed_width_mm = int(content_right_px / PX_PER_MM + margin_mm * 2 + 5)
    needed_height_mm = int(content_height_px / PX_PER_MM + margin_mm * 2 + 5)
    # 上限ガード（極端に巨大な PDF を避ける）
    needed_width_mm = min(needed_width_mm, 2000)
    needed_height_mm = min(max(needed_height_mm, 297), 3000)
    final_css = CSS(
        string=_page_css(
            "portrait", margin_mm, 1.0, opts.fonts_dir, aggressive=True
        ).replace("size: A4 portrait", f"size: {needed_width_mm}mm {needed_height_mm}mm")
    )
    return HTML(string=src, base_url=base_url).render(stylesheets=[final_css])


def _max_content_bottom(page) -> float:
    """ページ内のすべてのレイアウトボックスを走査し、最も下の Y 座標（CSS px）を返す。"""
    max_bottom = 0.0

    def walk(box):
        nonlocal max_bottom
        py = getattr(box, "position_y", None)
        ph = getattr(box, "height", None)
        if isinstance(py, (int, float)) and isinstance(ph, (int, float)):
            bottom = py + ph
            if bottom > max_bottom:
                max_bottom = bottom
        for child in getattr(box, "children", ()) or ():
            walk(child)

    walk(page._page_box)
    return max_bottom
