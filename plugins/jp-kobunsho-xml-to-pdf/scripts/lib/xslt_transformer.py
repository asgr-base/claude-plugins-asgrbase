"""XML + XSL → HTML (lxml.etree.XSLT)。

v1 同名モジュールから流用。
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree


class XSLTError(RuntimeError):
    pass


def transform(xml_path: Path, xsl_path: Path) -> str:
    """XML + XSL を XSLT 変換し、結果 HTML 文字列を返す。

    入力ファイルが存在しない・読めない・パースできない等は XSLTError でラップする。
    """
    try:
        xml = etree.parse(str(xml_path))
        xsl = etree.parse(str(xsl_path))
        transform = etree.XSLT(xsl)
        return str(transform(xml))
    except etree.XSLTApplyError as e:
        raise XSLTError(f"XSLT apply failed: {e}") from e
    except etree.XSLTParseError as e:
        raise XSLTError(f"XSLT parse failed: {e}") from e
    except etree.XMLSyntaxError as e:
        raise XSLTError(f"XML/XSL syntax error: {e}") from e
    except OSError as e:
        raise XSLTError(f"failed to read XML/XSL: {e}") from e
