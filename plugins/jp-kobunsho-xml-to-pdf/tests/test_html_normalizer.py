"""Tests for lib.html_normalizer."""
from scripts.lib import html_normalizer


def test_normalize_css_width_replaces_large_px_with_auto():
    html = '<div style="width: 1400px; height: 100px;">x</div>'
    result = html_normalizer.normalize_widths(html, threshold=600)
    assert "1400px" not in result
    assert "auto" in result


def test_normalize_css_width_keeps_small_px():
    html = '<div style="width: 320px;">x</div>'
    result = html_normalizer.normalize_widths(html, threshold=600)
    assert "320px" in result


def test_normalize_attr_width_replaces_large():
    html = '<table width="1400">x</table>'
    result = html_normalizer.normalize_widths(html, threshold=600)
    assert 'width="1400"' not in result


def test_normalize_attr_width_keeps_small():
    html = '<table width="500">x</table>'
    result = html_normalizer.normalize_widths(html, threshold=600)
    assert 'width="500"' in result


def test_normalize_margins_shrinks_large_to_target():
    html = '<div style="margin: 100px 80px 35px 80px;">x</div>'
    result = html_normalizer.normalize_margins(html, threshold=30, target=5)
    # 全て >30px だったので 5px に縮む
    assert "100px" not in result
    assert "80px" not in result
    assert "35px" not in result
    assert "5px" in result


def test_normalize_margins_keeps_small():
    html = '<div style="margin: 10px;">x</div>'
    result = html_normalizer.normalize_margins(html, threshold=30, target=5)
    assert "10px" in result


def test_normalize_margins_handles_mixed_values():
    html = '<div style="margin: 100px 5px;">x</div>'
    result = html_normalizer.normalize_margins(html, threshold=30, target=5)
    # 100px は縮む、5px はそのまま
    assert "100px" not in result
    # 結果として margin: 5px 5px のような形に
    assert result.count("5px") >= 2


def test_normalize_does_not_affect_non_matching_text():
    html = "<p>テキスト本文 - widthという文字列は含まれる</p>"
    result = html_normalizer.normalize_widths(html)
    assert "テキスト本文" in result
