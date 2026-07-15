"""v2.1.0 Markdown 同時変換モードのテスト。

- md_filters.md_table / md_kv のユニットテスト
- convert_zip(..., output_format="md" / "both") の振る舞い
- 4 ZIP fixture が手元にある環境では、yoshiki_29 の Markdown 出力の必須キーワード検証
  (fixture が無い CI 環境では skip)
"""
import zipfile
from pathlib import Path

import pytest

from scripts import convert
from scripts.lib import md_filters


FIXTURES = Path(__file__).parent / "fixtures"

# 実 fixture (実 PII を含むためリポジトリには置かない) があるディレクトリ。
# 環境変数 KOBUNSHO_REAL_FIXTURES で指定した場合のみ実データ検証を行う。
import os
_REAL_FIXTURES = Path(os.environ.get("KOBUNSHO_REAL_FIXTURES", "/nonexistent"))


def _make_zip(tmp_path: Path, name: str = "test.zip") -> Path:
    z = tmp_path / name
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(FIXTURES / "sample_document.xml", "0123456789/sample_document.xml")
        zf.write(FIXTURES / "sample_kagami.xsl", "0123456789/sample_kagami.xsl")
    return z


# ----- md_filters のユニットテスト -----


def test_md_table_basic():
    out = md_filters.md_table([["a", "b"], ["c", "d"]], headers=["X", "Y"])
    lines = out.splitlines()
    assert lines[0] == "| X | Y |"
    assert "---" in lines[1]
    assert lines[2] == "| a | b |"
    assert lines[3] == "| c | d |"


def test_md_table_escapes_pipe():
    out = md_filters.md_table([["a|b", "c"]], headers=["X", "Y"])
    assert "a\\|b" in out


def test_md_table_handles_none_cells():
    out = md_filters.md_table([[None, "x"]], headers=["A", "B"])
    assert "|  | x |" in out


def test_md_table_empty_rows():
    assert md_filters.md_table([]) == ""


def test_md_kv_from_dicts():
    out = md_filters.md_kv([{"label": "key1", "value": "val1"}, {"label": "key2", "value": "val2"}])
    assert "| 項目 | 内容 |" in out
    assert "| key1 | val1 |" in out
    assert "| key2 | val2 |" in out


def test_md_kv_empty():
    assert md_filters.md_kv([]) == ""


# ----- convert_zip() の振る舞い -----


def test_convert_zip_format_pdf_default(tmp_path):
    """default は v2.0.x 互換 (PDF のみ)。"""
    z = _make_zip(tmp_path)
    outputs = convert.convert_zip(z, tmp_path / "out")
    assert len(outputs) == 1
    assert outputs[0].suffix == ".pdf"


def test_convert_zip_format_md(tmp_path):
    """--format md は .md のみ出力。"""
    z = _make_zip(tmp_path)
    outputs = convert.convert_zip(z, tmp_path / "out", output_format="md")
    assert len(outputs) == 1
    assert outputs[0].suffix == ".md"
    md = outputs[0].read_text(encoding="utf-8")
    # frontmatter が含まれる
    assert "form_id:" in md
    assert "title:" in md


def test_convert_zip_format_both(tmp_path):
    """--format both は .pdf + .md の対で出力。"""
    z = _make_zip(tmp_path)
    outputs = convert.convert_zip(z, tmp_path / "out", output_format="both")
    suffixes = sorted(p.suffix for p in outputs)
    assert suffixes == [".md", ".pdf"]
    # 同 stem で対になっている
    stems = {p.stem for p in outputs}
    assert len(stems) == 1


def test_convert_zip_invalid_format(tmp_path):
    z = _make_zip(tmp_path)
    with pytest.raises(ValueError):
        convert.convert_zip(z, tmp_path / "out", output_format="docx")


def test_cli_format_both_outputs(tmp_path, capsys):
    z = _make_zip(tmp_path)
    out = tmp_path / "out"
    rc = convert.main([str(z), "--output-dir", str(out), "--format", "both"])
    assert rc == 0
    captured = capsys.readouterr()
    assert ".pdf" in captured.out
    assert ".md" in captured.out


# ----- 実 fixture を使った integration (実 PII を含むためローカル限定) -----


def _has_real_fixture(stem_prefix: str) -> Path | None:
    if not _REAL_FIXTURES.exists():
        return None
    matches = list(_REAL_FIXTURES.glob(f"{stem_prefix}*.zip"))
    return matches[0] if matches else None


@pytest.mark.skipif(
    not _REAL_FIXTURES.exists(),
    reason="個人 fixture (実 PII を含む) が無い CI 環境では skip",
)
def test_yoshiki_29_markdown_keywords(tmp_path):
    """yoshiki_29 ZIP → Markdown に必須キーワードが含まれる。

    実 PII を assert に含めないため、構造的なキーワード (見出し・項目名) と
    「カンマ区切り数値が出現するか」のみを検証する。
    """
    import re

    z = _has_real_fixture("1381260511998936")
    if z is None:
        pytest.skip("yoshiki_29 fixture が見つからない")
    outputs = convert.convert_zip(z, tmp_path / "out", output_format="md")
    md_files = [p for p in outputs if p.suffix == ".md"]
    assert md_files, "Markdown 出力が無い"
    combined = "\n".join(p.read_text(encoding="utf-8") for p in md_files)
    # 「保険料納入告知額」は XSL で各文字間に空白が入るため、空白を除いてマッチング
    normalized = combined.replace(" ", "").replace("　", "")
    # 構造キーワード (文書タイトル / 章見出し)
    for kw in ["保険料納入告知額", "不服申立て", "事業所整理記号", "合計額"]:
        assert kw.replace(" ", "") in normalized, f"必須キーワード '{kw}' が Markdown に含まれない"
    # 金額が少なくとも 1 件はカンマ区切り表示されていること (例: 1,234)
    assert re.search(r"\d{1,3},\d{3}", combined), "カンマ区切り金額が Markdown に含まれない"


@pytest.mark.skipif(
    not _REAL_FIXTURES.exists(),
    reason="個人 fixture (実 PII を含む) が無い CI 環境では skip",
)
def test_yoshiki_26_markdown_keywords(tmp_path):
    z = _has_real_fixture("1381260310539437")
    if z is None:
        pytest.skip("yoshiki_26 fixture が見つからない")
    outputs = convert.convert_zip(z, tmp_path / "out", output_format="md")
    md_files = [p for p in outputs if p.suffix == ".md"]
    assert md_files
    combined = "\n".join(p.read_text(encoding="utf-8") for p in md_files)
    # 通帳情報の見出しと、振替開始通知書のタイトルが含まれる
    assert "通帳情報" in combined
    assert "口座振替開始通知書" in combined.replace(" ", "").replace("　", "")
