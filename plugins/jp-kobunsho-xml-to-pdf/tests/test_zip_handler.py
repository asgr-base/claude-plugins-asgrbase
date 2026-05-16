"""Tests for lib.zip_handler."""
import zipfile
from pathlib import Path

import pytest

from scripts.lib import zip_handler


FIXTURES = Path(__file__).parent / "fixtures"


def make_kobunsho_zip(tmp_path: Path) -> Path:
    """テスト用 ZIP を作る（e-Gov 公文書 ZIP の構造を模倣: 1 階層下にファイル）。"""
    zip_path = tmp_path / "test_kobunsho.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(FIXTURES / "sample_document.xml", "0123456789/sample_document.xml")
        zf.write(FIXTURES / "sample_kagami.xsl", "0123456789/sample_kagami.xsl")
    return zip_path


def test_extract_zip_returns_inner_directory(tmp_path):
    zip_path = make_kobunsho_zip(tmp_path)
    inner = zip_handler.extract_zip(zip_path, tmp_path / "extracted")
    assert inner.is_dir()
    assert (inner / "sample_document.xml").exists()
    assert (inner / "sample_kagami.xsl").exists()


def test_extract_zip_flat(tmp_path):
    """サブディレクトリのない ZIP も処理できる。"""
    zip_path = tmp_path / "flat.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(FIXTURES / "sample_document.xml", "sample_document.xml")
        zf.write(FIXTURES / "sample_kagami.xsl", "sample_kagami.xsl")
    inner = zip_handler.extract_zip(zip_path, tmp_path / "extracted")
    assert (inner / "sample_document.xml").exists()


def test_find_xml_files_returns_all_xmls(tmp_path):
    inner = zip_handler.extract_zip(make_kobunsho_zip(tmp_path), tmp_path / "ex")
    xmls = zip_handler.find_xml_files(inner)
    assert len(xmls) == 1
    assert xmls[0].name == "sample_document.xml"


def test_parse_xml_stylesheet_returns_xsl_href(tmp_path):
    inner = zip_handler.extract_zip(make_kobunsho_zip(tmp_path), tmp_path / "ex")
    xml = inner / "sample_document.xml"
    href = zip_handler.parse_xml_stylesheet(xml)
    assert href == "sample_kagami.xsl"


def test_parse_xml_stylesheet_returns_none_when_missing(tmp_path):
    """xml-stylesheet 指示がない XML は None を返す。"""
    unstyled = tmp_path / "no_style.xml"
    unstyled.write_text("<?xml version='1.0'?><root/>", encoding="utf-8")
    assert zip_handler.parse_xml_stylesheet(unstyled) is None


def test_extract_zip_raises_on_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        zip_handler.extract_zip(tmp_path / "nope.zip", tmp_path / "out")


def test_extract_zip_raises_on_non_zip(tmp_path):
    fake = tmp_path / "not.zip"
    fake.write_text("not a zip")
    with pytest.raises(zipfile.BadZipFile):
        zip_handler.extract_zip(fake, tmp_path / "out")
