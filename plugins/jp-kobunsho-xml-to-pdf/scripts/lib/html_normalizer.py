"""HTML 内の固定 px サイズ指定を緩めて、用紙幅にフィットしやすくする。

e-Gov 公文書の XSL は画面表示前提の固定 px width（例: 1400px）や
大きな margin（例: 100px 80px）を含む。そのままだと A4 横でも収まらない。
"""
from __future__ import annotations

import re


_CSS_WIDTH_PX = re.compile(r'(width\s*:\s*)(\d+)\s*px', re.IGNORECASE)
_ATTR_WIDTH = re.compile(r'(\bwidth\s*=\s*")(\d+)(")', re.IGNORECASE)
_CSS_MARGIN = re.compile(r'margin\s*:\s*([^;}"]+)', re.IGNORECASE)


def normalize_widths(html: str, threshold: int = 600) -> str:
    """`width: NNNpx` および `width="NNN"` の NNN が threshold 超なら auto に置換する。"""
    def _css(m: re.Match) -> str:
        return f"{m.group(1)}auto" if int(m.group(2)) > threshold else m.group(0)

    def _attr(m: re.Match) -> str:
        return f'{m.group(1)}auto{m.group(3)}' if int(m.group(2)) > threshold else m.group(0)

    html = _CSS_WIDTH_PX.sub(_css, html)
    html = _ATTR_WIDTH.sub(_attr, html)
    return html


def normalize_margins(html: str, threshold: int = 30, target: int = 5) -> str:
    """`margin: A B C D` の各値が threshold 超なら target に縮める。"""
    def _replace(m: re.Match) -> str:
        parts = [p for p in re.split(r'\s+', m.group(1).strip()) if p]
        out = []
        for p in parts:
            num_match = re.match(r'(-?)(\d+)\s*px', p)
            if num_match:
                sign = num_match.group(1)
                v = int(num_match.group(2))
                if v > threshold:
                    v = target
                out.append(f"{sign}{v}px")
            else:
                out.append(p)
        return "margin: " + " ".join(out)

    return _CSS_MARGIN.sub(_replace, html)
