"""Jinja2 custom filter: Markdown 表現の汎用ヘルパー。

Markdown テンプレート (`templates/*.md.j2`) から `{{ value | md_table }}` 等で呼び出す。
"""
from __future__ import annotations

from typing import Iterable


def _escape_cell(cell: object) -> str:
    """Markdown table セル内に入れる文字列を安全化。

    - None → 空文字
    - パイプ `|` はエスケープ
    - 改行は半角空白に
    """
    if cell is None:
        return ""
    s = str(cell)
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace("|", "\\|")
    return s.strip()


def md_table(rows: Iterable[Iterable[object]], headers: Iterable[object] | None = None) -> str:
    """list of rows を Markdown table 文字列に変換する。

    Args:
        rows: 各行のセル iterable。
        headers: ヘッダ行 (省略時は 1 列目の長さからプレースホルダ生成)。

    Returns:
        Markdown table 文字列 (前後の改行なし)。
    """
    rows_list = [list(r) for r in rows]
    if not rows_list:
        return ""

    if headers is None:
        col_count = max(len(r) for r in rows_list)
        headers_list = [""] * col_count
    else:
        headers_list = [_escape_cell(h) for h in headers]
        col_count = len(headers_list)

    # 行のセル数を col_count に揃える
    for r in rows_list:
        while len(r) < col_count:
            r.append("")

    lines: list[str] = []
    lines.append("| " + " | ".join(headers_list) + " |")
    lines.append("|" + "|".join(["---"] * col_count) + "|")
    for r in rows_list:
        lines.append("| " + " | ".join(_escape_cell(c) for c in r[:col_count]) + " |")
    return "\n".join(lines)


def md_kv(pairs: Iterable[object], label_key: str = "label", value_key: str = "value") -> str:
    """[{label, value}, ...] を Markdown の key-value 表 (2 列) に変換する。

    Args:
        pairs: dict or object のリスト。
        label_key / value_key: dict の場合のキー名 (default: "label" / "value")。
                                object の場合は同名属性を参照。

    Returns:
        Markdown table 文字列。
    """
    rows: list[list[str]] = []
    for p in pairs:
        if isinstance(p, dict):
            label = p.get(label_key, "")
            value = p.get(value_key, "")
        else:
            label = getattr(p, label_key, "")
            value = getattr(p, value_key, "")
        rows.append([_escape_cell(label), _escape_cell(value)])
    if not rows:
        return ""
    return md_table(rows, headers=["項目", "内容"])


def md_paragraphs(lines: Iterable[object]) -> str:
    """行リストを段落 (空行区切り) に変換する。

    各行は別段落として、間に空行を挟む。
    """
    out: list[str] = []
    for line in lines:
        if line is None:
            continue
        s = str(line).strip()
        if s:
            out.append(s)
    return "\n\n".join(out)


def register(env) -> None:  # noqa: ANN001
    """Jinja2 Environment にフィルタを登録する。"""
    env.filters["md_table"] = md_table
    env.filters["md_kv"] = md_kv
    env.filters["md_paragraphs"] = md_paragraphs
