"""HTML → PDF レンダリングと自動 fit-to-page。

XSL が画面表示用の固定 px width を持つため、A4 1 ページに収めるには:
1. HTML 正規化（html_normalizer で fix px width / 大 margin を緩和）
2. WeasyPrint で実レンダリング後、コンテンツ右端 X 座標を実測
3. ページ幅を超えていれば向きを切り替え、それでもダメなら zoom を段階的に下げる
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
    fits: bool
    attempts: int = 0


def _page_css(orientation: Orientation, margin_mm: int, zoom: float, fonts_dir: Optional[Path]) -> str:
    """@page と html { zoom } を組み立てる。フォント @font-face は fonts_dir 指定時に追加。"""
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
    return (
        f"{font_face}"
        f"@page {{ size: A4 {orientation}; margin: {margin_mm}mm; }}\n"
        f"html {{ zoom: {zoom}; }}\n"
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


def _render(html_str: str, base_url: str, orientation: Orientation, zoom: float, opts: FitOptions):
    css = CSS(string=_page_css(orientation, opts.page_margin_mm, zoom, opts.fonts_dir))
    return HTML(string=html_str, base_url=base_url).render(stylesheets=[css])


def _fits(doc) -> bool:
    """1 ページかつコンテンツ右端 <= ページ幅なら True。"""
    if not doc.pages or len(doc.pages) != 1:
        return False
    page = doc.pages[0]
    return _max_content_right(page) <= page.width + 1.0


def render(html_str: str, base_url: str, opts: FitOptions) -> tuple[bytes, FitResult]:
    """HTML を PDF bytes に変換し、fit 結果も返す。"""
    # 1. HTML 正規化（no_fit でない場合のみ）
    src = html_str if opts.no_fit else html_normalizer.normalize_margins(
        html_normalizer.normalize_widths(html_str)
    )

    # 2. 手動 zoom が指定されていれば 1 回だけレンダリングして返す
    if opts.manual_zoom is not None:
        orient = opts.force_orientation or "portrait"
        doc = _render(src, base_url, orient, opts.manual_zoom, opts)
        return doc.write_pdf(), FitResult(orient, opts.manual_zoom, len(doc.pages), _fits(doc), 1)

    # 3. no_fit: 縦 zoom=1.0 で固定（force_orientation あれば反映）
    if opts.no_fit:
        orient = opts.force_orientation or "portrait"
        doc = _render(src, base_url, orient, 1.0, opts)
        return doc.write_pdf(), FitResult(orient, 1.0, len(doc.pages), _fits(doc), 1)

    # 4. force_orientation 指定があれば、その向きで zoom 探索
    if opts.force_orientation:
        return _zoom_search(src, base_url, opts, (opts.force_orientation,))

    # 5. 自動: 縦→横の順で zoom=1.0 を試し、ダメなら zoom 探索
    return _zoom_search(src, base_url, opts, ("portrait", "landscape"))


def _zoom_search(
    src: str,
    base_url: str,
    opts: FitOptions,
    orientations: tuple[Orientation, ...],
) -> tuple[bytes, FitResult]:
    attempts = 0
    last_doc = None
    last_orient: Orientation = orientations[0]
    last_zoom = 1.0

    # まず zoom=1.0 で各 orientation を試す
    for orient in orientations:
        attempts += 1
        doc = _render(src, base_url, orient, 1.0, opts)
        last_doc, last_orient, last_zoom = doc, orient, 1.0
        if _fits(doc):
            return doc.write_pdf(), FitResult(orient, 1.0, len(doc.pages), True, attempts)

    # zoom を段階的に下げる（横向き優先）
    zoom = 1.0 - opts.zoom_step
    search_orients = ("landscape", "portrait") if "landscape" in orientations else orientations
    while zoom >= opts.zoom_min:
        for orient in search_orients:
            attempts += 1
            doc = _render(src, base_url, orient, zoom, opts)
            last_doc, last_orient, last_zoom = doc, orient, zoom
            if _fits(doc):
                return doc.write_pdf(), FitResult(orient, zoom, len(doc.pages), True, attempts)
        zoom = round(zoom - opts.zoom_step, 3)

    # 諦め: 最後の試行結果を返す
    return last_doc.write_pdf(), FitResult(last_orient, last_zoom, len(last_doc.pages), False, attempts)
