"""Integration test for convert.convert_zip()."""
import unicodedata
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
    # v3.0.0: 出力名は HTML <title>（公文書の正式名称）由来
    assert "サンプル公文書.pdf" in captured.out


def test_cli_main_returns_non_zero_on_missing_zip(tmp_path, capsys):
    rc = convert.main([str(tmp_path / "missing.zip")])
    assert rc != 0


# ---- v3.0.0 回帰: 入れ子 table 様式のデータ完全性（Chromium 忠実印刷） ----

def _make_nested_zip(tmp_path: Path) -> Path:
    z = tmp_path / "nested.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(FIXTURES / "sample_nested_table.xml", "9999/sample_nested_table.xml")
        zf.write(FIXTURES / "sample_nested_table.xsl", "9999/sample_nested_table.xsl")
    return z


def _pdf_text(pdf_path: Path) -> str:
    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(pdf_path))
    raw = "".join(page.extract_text() or "" for page in reader.pages)
    # IPAex + pypdf は一部の漢字を康熙部首 (U+2Fxx) で返すため NFKC で正規化する
    return unicodedata.normalize("NFKC", raw)


def test_nested_table_pdf_keeps_all_values(tmp_path):
    """v2 の generic フォールバックで欠損した表データが PDF テキスト層に残ること。

    2026-07-15 の本番公文書（様式 7130001）で標準報酬月額・生年月日・種別が
    PDF から消失した事故の回帰テスト。
    """
    z = _make_nested_zip(tmp_path)
    out_dir = tmp_path / "out"
    outputs = convert.convert_zip(z, out_dir, output_format="pdf")
    assert len(outputs) == 1
    text = _pdf_text(outputs[0]).replace(" ", "").replace("　", "")

    for expected in ("サンプル太郎", "099千円", "098千円", "S60.1.1", "第一種"):
        assert expected in text.replace("．", "."), f"missing: {expected}"

    # 重複出力の回帰: 氏名が 1 回だけ現れること（v2 は全文が 2 回描画された）
    assert text.count("サンプル太郎") == 1

    # pre の折り返し互換: 長文の末尾まで印字されること（溢れると欠落する）
    assert "欠落します" in text
