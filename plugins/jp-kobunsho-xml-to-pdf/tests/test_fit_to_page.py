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

# 属性 width で広いケース（新ZIP の口座振替通知書を模倣）
ATTR_WIDE_HTML = """<!doctype html><html><head><meta charset="utf-8"></head>
<body><table width="580"><tr>""" + "".join(f'<td width="50">列{i}</td>' for i in range(15)) + "</tr></table></body></html>"


def test_small_html_fits_portrait_at_zoom_1():
    pdf_bytes, result = fit_to_page.render(SMALL_HTML, "", fit_to_page.FitOptions())
    assert pdf_bytes.startswith(b"%PDF")
    assert result.fits_horizontally
    assert result.orientation == "portrait"


def test_wide_html_fits_horizontally_after_normalization():
    """1400px の固定幅でも、normalizer で auto 化されて横はみ出しなしになる。"""
    pdf_bytes, result = fit_to_page.render(WIDE_HTML, "", fit_to_page.FitOptions())
    assert pdf_bytes.startswith(b"%PDF")
    assert result.fits_horizontally, f"horizontally fit failed: {result}"


def test_attr_width_html_fits_via_aggressive_css():
    """属性 width=580 の table も aggressive CSS injection で横はみ出しなしになる。"""
    pdf_bytes, result = fit_to_page.render(ATTR_WIDE_HTML, "", fit_to_page.FitOptions())
    assert pdf_bytes.startswith(b"%PDF")
    assert result.fits_horizontally, f"horizontally fit failed: {result}"


def test_no_fit_disables_normalization():
    opts = fit_to_page.FitOptions(no_fit=True)
    pdf_bytes, result = fit_to_page.render(WIDE_HTML, "", opts)
    assert pdf_bytes.startswith(b"%PDF")
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
