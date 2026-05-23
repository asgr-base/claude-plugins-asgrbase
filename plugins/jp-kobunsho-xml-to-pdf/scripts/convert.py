"""convert.py — e-Gov 公文書 ZIP → PDF 変換 (v2.0.0)。

extractors/ (lxml で意味データ抽出) → templates/ (Jinja2 で HTML 生成)
→ css/grid_v2.css (CSS Grid 配置) → WeasyPrint で PDF 化、というパイプライン。

XSL の table 入れ子に依存せず、意味データを抽出して div ベースの HTML を再構築する。
WeasyPrint の border-collapse バグ (Issue #2333 等) を構造的に回避し、
真のレスポンシブレイアウトと均一な罫線品質を実現する。
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib import zip_handler, xslt_transformer  # noqa: E402
from lib.form_detector import detect_form, FormSpec  # noqa: E402
from lib.render_v2 import render_v2  # noqa: E402


def _log(msg: str, verbose: bool) -> None:
    if verbose:
        print(msg, file=sys.stderr)


def convert_zip(
    zip_path: Path,
    output_dir: Path,
    *,
    debug_dir: Path | None = None,
    verbose: bool = False,
) -> list[Path]:
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

            spec = detect_form(xml_path, xsl_path, html)
            _log(f"  → form={spec.form_id} paper={spec.paper} conf={spec.confidence:.2f}", verbose)

            if debug_dir is not None:
                (debug_dir / f"{xml_path.stem}.raw.html").write_text(html, encoding="utf-8")

            try:
                pdf_bytes = render_v2(
                    xml_html=html,
                    form_spec=spec,
                    base_url=str(xml_path.parent),
                    debug_dir=debug_dir,
                )
            except Exception as e:
                _log(f"RENDER ERROR {xml_path.name}: {e}", verbose)
                continue

            out_path = output_dir / (xml_path.stem + ".pdf")
            out_path.write_bytes(pdf_bytes)
            outputs.append(out_path)
            _log(f"OK {xml_path.name} -> {out_path.name}", verbose)

    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="e-Gov 公文書 ZIP (XML+XSL) を 1 ページに収まる PDF に変換"
    )
    parser.add_argument("zip_path", type=Path, help="入力 ZIP のパス")
    parser.add_argument(
        "--output-dir", type=Path, default=Path.cwd(),
        help="PDF 出力先 (デフォルト: カレントディレクトリ)",
    )
    parser.add_argument(
        "--debug-dir", type=Path, default=None,
        help="中間 HTML/CSS をダンプするディレクトリ (デバッグ用)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="詳細ログを stderr に出力")
    args = parser.parse_args(argv)

    try:
        outputs = convert_zip(
            zip_path=args.zip_path,
            output_dir=args.output_dir,
            debug_dir=args.debug_dir,
            verbose=args.verbose,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    for p in outputs:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
