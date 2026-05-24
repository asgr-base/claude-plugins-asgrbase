"""Phase 9 以降の新パイプライン: extractor → Jinja2 テンプレート → WeasyPrint/Markdown。"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

from . import md_filters
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


def _render_markdown(doc: Document) -> str:
    """Jinja2 テンプレートで Markdown を生成 (autoescape 無効、custom filter 有効)。"""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    md_filters.register(env)
    template_name = f"{doc.form_id}.md.j2"
    template = env.get_template(template_name)
    rendered = template.render(doc=doc)
    # 連続する空行を 2 行までに正規化 (テンプレートのループで余白が膨らみがちなため)
    lines = rendered.splitlines()
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run <= 1:
                out.append(line)
        else:
            blank_run = 0
            out.append(line.rstrip())
    return "\n".join(out).rstrip() + "\n"


def _extract_document(xml_html: str, form_spec: FormSpec) -> Document:
    """XSLT 出力 HTML から Document を抽出し、form_spec の paper override を反映。"""
    extractor = get_extractor(form_spec.form_id)
    if extractor is None:
        raise RuntimeError(f"no extractor for form_id={form_spec.form_id}")
    doc = extractor.extract(xml_html)
    if form_spec.paper and form_spec.paper != "auto":
        doc.paper = form_spec.paper
    return doc


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

    doc = _extract_document(xml_html, form_spec)
    rendered_html = _render_html(doc)
    css_str = _build_css(doc.form_id, doc.paper, fonts_dir)

    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / f"{doc.form_id}.v2.html").write_text(rendered_html, encoding="utf-8")
        (debug_dir / f"{doc.form_id}.v2.css").write_text(css_str, encoding="utf-8")

    pdf = HTML(string=rendered_html, base_url=base_url).write_pdf(
        stylesheets=[CSS(string=css_str)]
    )
    return pdf


def render_v2_markdown(
    xml_html: str,
    form_spec: FormSpec,
    debug_dir: Path | None = None,
) -> str:
    """XSLT 出力 HTML + form 情報 → Markdown 文字列 (v2.1.0 新規)。

    PDF とは独立して呼べる。同じ extractor / Document を使うため、
    PDF と Markdown は同一データから生成される。
    """
    doc = _extract_document(xml_html, form_spec)
    rendered_md = _render_markdown(doc)

    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / f"{doc.form_id}.v2.md").write_text(rendered_md, encoding="utf-8")

    return rendered_md
