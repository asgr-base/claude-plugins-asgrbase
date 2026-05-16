#!/usr/bin/env python3
"""e-Gov 公文書 ZIP を PDF に変換する CLI エントリポイント。

使い方:
  python convert.py <zip_path> [--output-dir DIR] [--portrait|--landscape]
                               [--no-fit] [--zoom 0.7] [--verbose]
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

# 同ディレクトリの lib/ をインポートできるよう sys.path を調整
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from lib import zip_handler, xslt_transformer, fit_to_page  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="e-Gov 公文書 ZIP を PDF に変換します。",
    )
    p.add_argument("zip_path", type=Path, help="入力 ZIP ファイルパス")
    p.add_argument("--output-dir", type=Path, default=None,
                   help="出力先ディレクトリ（既定: ZIP と同じディレクトリ）")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--portrait", action="store_true", help="A4 縦を強制")
    g.add_argument("--landscape", action="store_true", help="A4 横を強制")
    p.add_argument("--no-fit", action="store_true",
                   help="自動 fit を無効化（XSL 元の見た目を保つ）")
    p.add_argument("--zoom", type=float, default=None,
                   help="手動 zoom（指定すると fit より優先）")
    p.add_argument("--verbose", action="store_true",
                   help="各 XML の処理ログを stderr に出力")
    return p


def _log(msg: str, verbose: bool):
    if verbose:
        print(msg, file=sys.stderr)


def convert_zip(
    zip_path: Path,
    output_dir: Path,
    *,
    orientation: str | None = None,
    no_fit: bool = False,
    zoom: float | None = None,
    fonts_dir: Path | None = None,
    verbose: bool = False,
) -> list[Path]:
    """ZIP を展開し、含まれる全 XML を PDF 化して output_dir に書き出す。

    返り値: 生成された PDF のパスリスト。
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kobunsho_") as tmp:
        work = Path(tmp)
        inner = zip_handler.extract_zip(zip_path, work)
        xmls = zip_handler.find_xml_files(inner)
        if not xmls:
            raise RuntimeError(f"ZIP に XML が見つかりません: {zip_path}")

        opts = fit_to_page.FitOptions(
            force_orientation=orientation,  # type: ignore[arg-type]
            no_fit=no_fit,
            manual_zoom=zoom,
            fonts_dir=fonts_dir,
        )

        outputs: list[Path] = []
        for xml_path in xmls:
            xsl_href = zip_handler.parse_xml_stylesheet(xml_path)
            if not xsl_href:
                _log(f"SKIP {xml_path.name}: xml-stylesheet 指示が見つかりません", verbose)
                continue
            xsl_path = xml_path.parent / xsl_href
            if not xsl_path.exists():
                _log(f"SKIP {xml_path.name}: 参照されている XSL がありません ({xsl_href})", verbose)
                continue

            html = xslt_transformer.transform(xml_path, xsl_path)
            pdf_bytes, result = fit_to_page.render(html, str(xml_path.parent), opts)
            out_path = output_dir / (xml_path.stem + ".pdf")
            out_path.write_bytes(pdf_bytes)
            outputs.append(out_path)
            _log(
                f"OK {xml_path.name} -> {out_path.name}  "
                f"({result.orientation}, zoom={result.zoom:.2f}, fits={result.fits})",
                verbose,
            )
        return outputs


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.zip_path.exists():
        print(f"ERROR: ZIP が見つかりません: {args.zip_path}", file=sys.stderr)
        return 2

    output_dir = args.output_dir or args.zip_path.parent
    orientation = "portrait" if args.portrait else ("landscape" if args.landscape else None)

    # フォントディレクトリ: plugin 配下の fonts/
    fonts_dir = _SCRIPT_DIR.parent / "fonts"
    fonts_dir = fonts_dir if fonts_dir.exists() else None

    try:
        outputs = convert_zip(
            args.zip_path,
            output_dir,
            orientation=orientation,
            no_fit=args.no_fit,
            zoom=args.zoom,
            fonts_dir=fonts_dir,
            verbose=args.verbose,
        )
    except (FileNotFoundError, RuntimeError, xslt_transformer.XSLTError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not outputs:
        print("WARNING: 変換可能な XML が見つかりませんでした", file=sys.stderr)
        return 1

    for p in outputs:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
