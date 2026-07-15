"""Markdown パイプライン: extractor → Jinja2 テンプレート (*.md.j2)。

v3.0.0 で PDF 生成は render_v3 (Chromium 忠実印刷) に移行した。
本モジュールは Markdown 出力（検索・引用用のテキスト表現）専用。
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from . import md_filters
from .extractors import get_extractor, Document
from .form_detector import FormSpec

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/
_TEMPLATES_DIR = _SCRIPTS_DIR / "templates"


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
