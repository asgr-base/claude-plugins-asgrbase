"""e-Gov 公文書 ZIP の展開と XML 検出。"""
from __future__ import annotations

import zipfile
from pathlib import Path

from lxml import etree


def extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    """ZIP を dest_dir に展開し、公文書ファイルが置かれている実ディレクトリを返す。

    e-Gov ZIP は 1 階層下にファイルがある構造（受付番号フォルダ）が多いため、
    展開後に「単一のサブディレクトリのみ」なら、そのサブディレクトリを返す。
    フラット構造（直下にファイル）なら dest_dir 自体を返す。
    """
    zip_path = Path(zip_path)
    dest_dir = Path(dest_dir)
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    entries = [p for p in dest_dir.iterdir() if not p.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return dest_dir


def find_xml_files(directory: Path) -> list[Path]:
    """ディレクトリ直下の .xml ファイルをソートして返す。"""
    return sorted(Path(directory).glob("*.xml"))


def parse_xml_stylesheet(xml_path: Path) -> str | None:
    """XML 冒頭の `<?xml-stylesheet type="text/xsl" href="..."?>` から href を返す。

    指示がなければ None。XSLT 1.0 / HTML 互換のスタイルシートに限定はしない。
    """
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        return None
    for instr in tree.xpath("//processing-instruction('xml-stylesheet')"):
        text = instr.text or ""
        for part in text.split():
            if part.startswith("href="):
                return part.split("=", 1)[1].strip('"').strip("'")
    return None
