"""Tests for lib.xslt_transformer."""
from pathlib import Path

import pytest

from scripts.lib import xslt_transformer


FIXTURES = Path(__file__).parent / "fixtures"


def test_transform_returns_html_string(tmp_path):
    # fixture XML は xml-stylesheet 指示で sample_kagami.xsl を参照
    # XSL は XML と同じディレクトリにある前提
    xml = FIXTURES / "sample_document.xml"
    xsl = FIXTURES / "sample_kagami.xsl"
    html = xslt_transformer.transform(xml, xsl)
    assert isinstance(html, str)
    assert "サンプル公文書" in html
    assert "親展" in html
    assert "<html" in html.lower()


def test_transform_raises_on_missing_xml(tmp_path):
    with pytest.raises(FileNotFoundError):
        xslt_transformer.transform(tmp_path / "missing.xml", FIXTURES / "sample_kagami.xsl")


def test_transform_raises_on_missing_xsl(tmp_path):
    with pytest.raises(FileNotFoundError):
        xslt_transformer.transform(FIXTURES / "sample_document.xml", tmp_path / "missing.xsl")


def test_transform_raises_on_invalid_xsl(tmp_path):
    bad = tmp_path / "bad.xsl"
    bad.write_text("not xsl")
    with pytest.raises(xslt_transformer.XSLTError):
        xslt_transformer.transform(FIXTURES / "sample_document.xml", bad)
