"""HTML 内の固定 px サイズ指定を緩めて、用紙幅にフィットしやすくする。

e-Gov 公文書の XSL は画面表示前提の固定 px width（例: 1400px）や
大きな margin（例: 100px 80px）を含む。そのままだと A4 横でも収まらない。
"""
from __future__ import annotations

import re


_CSS_WIDTH_PX = re.compile(r'(width\s*:\s*)(\d+)\s*px', re.IGNORECASE)
_ATTR_WIDTH = re.compile(r'(\bwidth\s*=\s*")(\d+)(")', re.IGNORECASE)
_CSS_MARGIN = re.compile(r'margin\s*:\s*([^;}"]+)', re.IGNORECASE)
_TABLE_LAYOUT_FIXED = re.compile(r'table-layout\s*:\s*fixed', re.IGNORECASE)
_BAD_CELLPADDING = re.compile(r'(\bcellpadding\s*=\s*")(\d+)px(")', re.IGNORECASE)


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


def normalize_table_layout(html: str) -> str:
    """`table-layout: fixed` を `auto` に置換する。

    fixed レイアウトはセル幅の合算で表全体が広がる挙動を起こすため、
    auto に変更してブラウザの自動レイアウトに任せる。
    """
    return _TABLE_LAYOUT_FIXED.sub("table-layout: auto", html)


def normalize_cellpadding(html: str) -> str:
    """属性値 `cellpadding="20px"` のような単位付き指定（HTML4 仕様外）から px を除去する。

    WeasyPrint がこれを誤解釈してセルが過大に膨らむケースがあるため、数値のみに正規化する。
    """
    return _BAD_CELLPADDING.sub(r'\1\2\3', html)


def normalize_all(html: str) -> str:
    """すべての正規化をまとめて適用する（推奨デフォルト）。"""
    html = normalize_widths(html)
    html = normalize_margins(html)
    html = normalize_table_layout(html)
    html = normalize_cellpadding(html)
    return html


def force_all_widths_relative(html: str) -> str:
    """**最終手段** — すべての width 指定（CSS + 属性）を 100% に強制する。

    XSL が複雑な class 階層で固定幅を多用しており、通常の normalize では収まらない場合に
    使用する。レイアウトの「列幅バランス」は崩れる可能性があるが、印刷用紙に収まることを最優先。
    """
    html = re.sub(
        r'(width\s*:\s*)(?:auto|\d+(?:px|%|em|rem|pt))',
        r'\g<1>100%',
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r'(\bwidth\s*=\s*")(?:\d+(?:px)?|100%)(")',
        r'\g<1>100%\g<2>',
        html,
        flags=re.IGNORECASE,
    )
    # table-layout: fixed は実質的に意味がなくなるため auto に
    html = _TABLE_LAYOUT_FIXED.sub("table-layout: auto", html)
    return html
