"""XML + XSL → HTML 変換。e-Gov 公文書の XSLT 1.0 を lxml で実行する。"""
from __future__ import annotations

from pathlib import Path

from lxml import etree


class XSLTError(Exception):
    """XSLT 変換の失敗。"""


def transform(xml_path: Path, xsl_path: Path) -> str:
    """XML を XSL で変換して HTML 文字列を返す。"""
    xml_path = Path(xml_path)
    xsl_path = Path(xsl_path)
    if not xml_path.exists():
        raise FileNotFoundError(xml_path)
    if not xsl_path.exists():
        raise FileNotFoundError(xsl_path)
    try:
        xml_doc = etree.parse(str(xml_path))
        xsl_doc = etree.parse(str(xsl_path))
        transformer = etree.XSLT(xsl_doc)
        result = transformer(xml_doc)
    except (etree.XMLSyntaxError, etree.XSLTApplyError, etree.XSLTParseError) as e:
        raise XSLTError(f"XSLT 変換に失敗: {e}") from e
    return str(result)
