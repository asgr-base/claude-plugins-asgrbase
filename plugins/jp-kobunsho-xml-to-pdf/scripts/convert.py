"""convert.py — e-Gov 公文書 ZIP → PDF / Markdown 変換 (v3.0.0)。

PDF: XSLT 出力 HTML を Chromium (playwright) でそのまま印刷する忠実再現パイプライン。
     XSL が唯一のレイアウト定義のため、未知様式も様式別実装なしで原本通りに出る。
MD:  extractors/ (lxml で意味データ抽出) → templates/*.md.j2 (Jinja2) の v2 経路を維持。
     検索・引用用のテキスト表現という位置づけ。

v3.0.0: PDF を WeasyPrint + 意味抽出から Chromium 忠実印刷へ全面置換。
"""
from __future__ import annotations

import argparse
import contextlib
import re
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import zip_handler, xslt_transformer  # noqa: E402
from lib.form_detector import detect_form  # noqa: E402
from lib.render_v2 import render_v2_markdown  # noqa: E402
from lib.render_v3 import ChromiumRenderer  # noqa: E402


def _log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg, file=sys.stderr)


_STEM_LEN_MAX = 80


def _derive_stem(html: str, fallback: str, used: dict[str, int]) -> str:
    """XSLT 出力 HTML の <title>（公文書の正式名称）を出力ファイル名にする。

    <title> が無い/空なら fallback（XML の stem）。同一 ZIP 内で名称が重複する
    場合は _2, _3... を付与する。
    """
    stem = fallback
    try:
        from lxml import html as lhtml
        title = (lhtml.fromstring(html).findtext(".//title") or "").strip()
        title = re.sub(r"\s+", " ", title)
        title = re.sub(r'[\\/:*?"<>|]', "_", title)
        if title:
            stem = title[:_STEM_LEN_MAX]
    except Exception:
        pass
    n = used.get(stem, 0) + 1
    used[stem] = n
    return stem if n == 1 else f"{stem}_{n}"


def convert_zip(
    zip_path: Path,
    output_dir: Path,
    *,
    debug_dir: Path | None = None,
    verbose: bool = False,
    output_format: str = "pdf",
) -> list[Path]:
    """ZIP 内の XML を PDF / Markdown / 両方 に変換する。

    Args:
        output_format: "pdf" | "md" | "both"。default "pdf" は v2.0.x と後方互換。

    Returns:
        生成されたファイルのパスリスト (PDF + Markdown が混在しうる)。
    """
    if output_format not in ("pdf", "md", "both"):
        raise ValueError(f"invalid output_format: {output_format!r}")

    output_dir.mkdir(parents=True, exist_ok=True)
    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="kobunsho_") as tmp:
        work = Path(tmp)
        inner = zip_handler.extract_zip(zip_path, work)

        for p in zip_handler.find_non_xml_files(inner):
            _log(f"SKIP non-XML: {p.name}", verbose)

        xmls = zip_handler.find_xml_files(inner)
        if not xmls:
            raise RuntimeError(f"no .xml files in {zip_path}")

        used_stems: dict[str, int] = {}
        with contextlib.ExitStack() as stack:
            renderer: ChromiumRenderer | None = None
            if output_format in ("pdf", "both"):
                # Chromium は 1 プロセスを全 XML で使い回す
                renderer = stack.enter_context(ChromiumRenderer())

            for xml_path in xmls:
                xsl_href = zip_handler.parse_xml_stylesheet(xml_path)
                if not xsl_href:
                    _log(f"SKIP {xml_path.name}: no xml-stylesheet", verbose)
                    continue
                xsl_path = xml_path.parent / xsl_href
                if not xsl_path.exists():
                    _log(f"SKIP {xml_path.name}: xsl not found ({xsl_href})", verbose)
                    continue

                try:
                    html = xslt_transformer.transform(xml_path, xsl_path)
                except xslt_transformer.XSLTError as e:
                    _log(f"XSLT ERROR {xml_path.name}: {e}", verbose)
                    continue

                if debug_dir is not None:
                    (debug_dir / f"{xml_path.stem}.raw.html").write_text(html, encoding="utf-8")

                out_stem = _derive_stem(html, xml_path.stem, used_stems)

                if renderer is not None:
                    try:
                        pdf_bytes = renderer.render_pdf(
                            html, debug_dir=debug_dir, debug_stem=xml_path.stem,
                        )
                    except Exception as e:
                        _log(f"PDF RENDER ERROR {xml_path.name}: {e}", verbose)
                    else:
                        out_path = output_dir / (out_stem + ".pdf")
                        out_path.write_bytes(pdf_bytes)
                        outputs.append(out_path)
                        _log(f"OK [pdf] {xml_path.name} -> {out_path.name}", verbose)

                if output_format in ("md", "both"):
                    spec = detect_form(xml_path, xsl_path, html)
                    _log(f"  → form={spec.form_id} (md) conf={spec.confidence:.2f}", verbose)
                    try:
                        md_str = render_v2_markdown(
                            xml_html=html,
                            form_spec=spec,
                            debug_dir=debug_dir,
                        )
                    except Exception as e:
                        _log(f"MD RENDER ERROR {xml_path.name}: {e}", verbose)
                    else:
                        out_path = output_dir / (out_stem + ".md")
                        out_path.write_text(md_str, encoding="utf-8")
                        outputs.append(out_path)
                        _log(f"OK [md] {xml_path.name} -> {out_path.name}", verbose)

    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="e-Gov 公文書 ZIP (XML+XSL) を 1 ページに収まる PDF / Markdown に変換"
    )
    parser.add_argument("zip_path", type=Path, help="入力 ZIP のパス")
    parser.add_argument(
        "--output-dir", type=Path, default=Path.cwd(),
        help="出力先 (デフォルト: カレントディレクトリ)",
    )
    parser.add_argument(
        "--debug-dir", type=Path, default=None,
        help="中間 HTML/CSS/MD をダンプするディレクトリ (デバッグ用)",
    )
    parser.add_argument(
        "--format", dest="output_format",
        choices=["pdf", "md", "both"], default="pdf",
        help="出力形式 (default: pdf)。md は Markdown のみ、both は PDF と Markdown 両方を同名 stem で出力",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログを stderr に出力")
    args = parser.parse_args(argv)

    try:
        outputs = convert_zip(
            zip_path=args.zip_path,
            output_dir=args.output_dir,
            debug_dir=args.debug_dir,
            verbose=args.verbose,
            output_format=args.output_format,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    for p in outputs:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
