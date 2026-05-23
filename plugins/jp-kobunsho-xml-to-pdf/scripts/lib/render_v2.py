"""Phase 9 以降の新パイプライン: extractor → Jinja2 テンプレート → WeasyPrint。"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

from .extractors import get_extractor, Document
from .form_detector import FormSpec

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
_TEMPLATES_DIR = _SCRIPTS_DIR / "templates"
_CSS_DIR = _SCRIPTS_DIR / "css"
# スキル同梱フォント (scripts/.. = plugin root の fonts/)
_DEFAULT_FONTS_DIR = _SCRIPTS_DIR.parent / "fonts"


def _build_css(form_id: str, paper: str, fonts_dir: Path) -> str:
    """grid_v2.css をベースに、フォントパスを置換し @page を追加。"""
    css = (_CSS_DIR / "grid_v2.css").read_text(encoding="utf-8")
    gothic = (fonts_dir / "ipaexg.ttf").resolve()
    mincho = (fonts_dir / "ipaexm.ttf").resolve()
    css = css.replace("FONT_PATH_GOTHIC", f"file://{gothic}")
    css = css.replace("FONT_PATH_MINCHO", f"file://{mincho}")

    paper_map = {
        "a4-portrait":  "A4 portrait",
        "a4-landscape": "A4 landscape",
        "a3-landscape": "A3 landscape",
        "auto":         "A4 portrait",
    }
    page_decl = f"@page {{ size: {paper_map.get(paper, 'A4 portrait')}; margin: 10mm; }}\n"
    return css + "\n" + page_decl


def _render_html(doc: Document) -> str:
    """Jinja2 テンプレートで HTML を生成。"""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(['html']),
    )
    template_name = f"{doc.form_id}.html.j2"
    template = env.get_template(template_name)
    return template.render(doc=doc)


def render_v2(
    xml_html: str,
    form_spec: FormSpec,
    base_url: str = "",
    fonts_dir: Path | None = None,
    debug_dir: Path | None = None,
) -> bytes:
    """XSLT 出力 HTML + form 情報 → PDF bytes (新パイプライン)。"""
    if fonts_dir is None:
        fonts_dir = _DEFAULT_FONTS_DIR

    extractor = get_extractor(form_spec.form_id)
    if extractor is None:
        raise RuntimeError(f"no extractor for form_id={form_spec.form_id}")

    # 1. データ抽出
    doc = extractor.extract(xml_html)
    # form_spec の paper が override されていれば反映
    if form_spec.paper and form_spec.paper != "auto":
        doc.paper = form_spec.paper

    # 2. Jinja2 で HTML 生成
    rendered_html = _render_html(doc)

    # 3. CSS 構築
    css_str = _build_css(doc.form_id, doc.paper, fonts_dir)

    # 4. debug ダンプ
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / f"{doc.form_id}.v2.html").write_text(rendered_html, encoding="utf-8")
        (debug_dir / f"{doc.form_id}.v2.css").write_text(css_str, encoding="utf-8")

    # 5. PDF 生成
    pdf = HTML(string=rendered_html, base_url=base_url).write_pdf(
        stylesheets=[CSS(string=css_str)]
    )
    return pdf
