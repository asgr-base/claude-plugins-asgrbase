"""ZIP 展開・XML 列挙・xml-stylesheet 解析。

v1 同名モジュールから流用 (アルゴリズムを真似る形)。
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

from lxml import etree


def extract_zip(zip_path: Path, work_dir: Path) -> Path:
    """ZIP を work_dir に展開し、中身の (受付番号サブディレクトリ or work_dir 自体) を返す。"""
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(work_dir)
    subdirs = [p for p in work_dir.iterdir() if p.is_dir()]
    return subdirs[0] if subdirs else work_dir


def find_xml_files(directory: Path) -> list[Path]:
    """直下の .xml ファイルをソート列挙。"""
    return sorted(directory.glob("*.xml"))


def parse_xml_stylesheet(xml_path: Path) -> str | None:
    """XML 先頭の <?xml-stylesheet href="..."?> を解析し href を返す。"""
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        return None
    for pi in tree.xpath("//processing-instruction('xml-stylesheet')"):
        m = re.search(r'href="([^"]+)"', pi.text or "")
        if m:
            return m.group(1)
    return None


def find_non_xml_files(directory: Path) -> list[Path]:
    """XML 以外のファイル (DTA バイナリ・CSV 等) を返す。verbose ログ用。"""
    out: list[Path] = []
    for p in sorted(directory.iterdir()):
        if p.is_file() and p.suffix.lower() not in {".xml", ".xsl"}:
            out.append(p)
    return out
