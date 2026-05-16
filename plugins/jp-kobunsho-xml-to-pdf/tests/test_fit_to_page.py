"""Tests for lib.fit_to_page."""
from scripts.lib import fit_to_page


SMALL_HTML = """<!doctype html><html><head><meta charset="utf-8"></head>
<body><h1>テスト</h1><p>短い内容</p></body></html>"""

WIDE_HTML = """<!doctype html><html><head><meta charset="utf-8">
<style>body { margin: 100px 80px; }
table { width: 1400px; }
td { padding: 10px; }
</style></head>
<body><table><tr>""" + "".join(f"<td>列{i}</td>" for i in range(20)) + "</tr></table></body></html>"


def test_small_html_fits_portrait_at_zoom_1():
    pdf_bytes, result = fit_to_page.render(SMALL_HTML, "", fit_to_page.FitOptions())
    assert pdf_bytes.startswith(b"%PDF")
    assert result.fits
    assert result.orientation == "portrait"
    assert result.zoom == 1.0
    assert result.attempts == 1


def test_wide_html_fits_after_normalization():
    """1400px の固定幅でも、normalizer + 2-pass fit で 1 ページに収まる。"""
    pdf_bytes, result = fit_to_page.render(WIDE_HTML, "", fit_to_page.FitOptions())
    assert pdf_bytes.startswith(b"%PDF")
    assert result.fits, f"fit failed: {result}"
    assert result.page_count == 1


def test_no_fit_disables_normalization():
    opts = fit_to_page.FitOptions(no_fit=True)
    pdf_bytes, result = fit_to_page.render(WIDE_HTML, "", opts)
    assert pdf_bytes.startswith(b"%PDF")
    # no_fit では正規化されず、widow 1400px がそのまま → 1 ページに収まらない可能性が高い
    # （仕様: fit 検査結果は False になるが、PDF は出る）
    assert result.zoom == 1.0


def test_force_landscape():
    opts = fit_to_page.FitOptions(force_orientation="landscape")
    pdf_bytes, result = fit_to_page.render(SMALL_HTML, "", opts)
    assert pdf_bytes.startswith(b"%PDF")
    assert result.orientation == "landscape"


def test_manual_zoom_overrides():
    opts = fit_to_page.FitOptions(manual_zoom=0.5)
    pdf_bytes, result = fit_to_page.render(SMALL_HTML, "", opts)
    assert pdf_bytes.startswith(b"%PDF")
    assert result.zoom == 0.5
    assert result.attempts == 1
