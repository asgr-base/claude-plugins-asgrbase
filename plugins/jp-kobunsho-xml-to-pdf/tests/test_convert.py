"""Integration test for convert.convert_zip()."""
import zipfile
from pathlib import Path

import pytest

from scripts import convert


FIXTURES = Path(__file__).parent / "fixtures"


def _make_zip(tmp_path: Path, name: str = "test.zip") -> Path:
    z = tmp_path / name
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(FIXTURES / "sample_document.xml", "0123456789/sample_document.xml")
        zf.write(FIXTURES / "sample_kagami.xsl", "0123456789/sample_kagami.xsl")
    return z


def test_convert_zip_creates_pdf(tmp_path):
    z = _make_zip(tmp_path)
    out_dir = tmp_path / "out"
    pdfs = convert.convert_zip(z, out_dir, verbose=False)
    assert len(pdfs) == 1
    assert pdfs[0].suffix == ".pdf"
    assert pdfs[0].read_bytes().startswith(b"%PDF")


def test_convert_zip_raises_on_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert.convert_zip(tmp_path / "nope.zip", tmp_path / "out")


def test_convert_zip_skips_xml_without_stylesheet(tmp_path):
    z = tmp_path / "no_style.zip"
    bad_xml = tmp_path / "bad.xml"
    bad_xml.write_text("<?xml version='1.0'?><root/>", encoding="utf-8")
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(bad_xml, "sub/bad.xml")
    pdfs = convert.convert_zip(z, tmp_path / "out", verbose=False)
    assert pdfs == []


def test_cli_main_returns_zero_on_success(tmp_path, capsys):
    z = _make_zip(tmp_path)
    out = tmp_path / "out"
    rc = convert.main([str(z), "--output-dir", str(out)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "sample_document.pdf" in captured.out


def test_cli_main_returns_non_zero_on_missing_zip(tmp_path, capsys):
    rc = convert.main([str(tmp_path / "missing.zip")])
    assert rc != 0
