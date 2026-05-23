"""抽出基底クラスと共通データ構造。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from lxml import html as lxml_html


@dataclass
class Block:
    """1 つの意味ブロック (Grid セルとして配置される単位)。

    type: "title", "header-box", "address-box", "table", "footer", "appeal", "footer-block"
    grid_area: CSS grid-area 名。未指定なら type と同名
    data: テンプレートに渡す任意データ (dict)
    """

    type: str
    data: dict[str, Any]
    grid_area: str | None = None

    @property
    def area(self) -> str:
        return self.grid_area or self.type.replace("-", "_")


@dataclass
class Document:
    """抽出された 1 文書のすべてのデータ。"""

    form_id: str
    paper: str  # "a4-portrait" / "a4-landscape" / "a3-landscape"
    title: str
    blocks: list[Block] = field(default_factory=list)


class BaseExtractor:
    """抽出基底クラス。サブクラスは extract() をオーバーライド。"""

    form_id: str = ""
    default_paper: str = "a4-portrait"

    def extract(self, html: str) -> Document:  # noqa: ANN001
        raise NotImplementedError

    # ----- 共通ヘルパー -----

    @staticmethod
    def parse(html: str):  # noqa: ANN001
        """lxml.html で document または fragment をパース。"""
        if "<html" in html.lower():
            return lxml_html.document_fromstring(html)
        return lxml_html.fromstring(html)

    @staticmethod
    def text(node) -> str:  # noqa: ANN001
        """node の全文テキストを正規化して返す (連続空白を 1 つに)。"""
        if node is None:
            return ""
        txt = node.text_content() if hasattr(node, "text_content") else str(node)
        # 改行と連続空白を 1 個の空白に
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    @staticmethod
    def text_lines(node) -> list[str]:  # noqa: ANN001
        """node 内のテキストを <br> や改行で分割して返す。空行はスキップ。"""
        if node is None:
            return []
        # text_content は <br> を改行として返さないので、独自ロジック
        out: list[str] = []
        if hasattr(node, "iter"):
            current = []

            def flush():
                if current:
                    out.append("".join(current).strip())
                    current.clear()

            def walk(el):  # noqa: ANN001
                if el.tag == "br":
                    flush()
                else:
                    if el.text:
                        current.append(el.text)
                    for child in el:
                        walk(child)
                        if child.tail:
                            current.append(child.tail)

            walk(node)
            flush()
        return [line for line in (re.sub(r"\s+", " ", l).strip() for l in out) if line]

    @staticmethod
    def td_lines(root):  # noqa: ANN001
        """root 配下の各 <td> のテキストを 1 行として返す。
        td 境界 = 改行として扱うため、入れ子 table を含む宛先・発行者情報に最適。"""
        if root is None:
            return []
        lines: list[str] = []
        for td in root.iter("td"):
            if td.find(".//table") is not None:
                continue
            txt = td.text_content() if hasattr(td, "text_content") else ""
            txt = re.sub(r"\s+", " ", txt).strip()
            if not txt or txt in ("-", "−"):
                continue
            lines.append(txt)
        result: list[str] = []
        for line in lines:
            if line not in result and len(line.strip()) > 1:
                result.append(line)
        return result

    @staticmethod
    def tr_lines(root):  # noqa: ANN001
        """root 配下の **最内側 <tr>** のテキストを 1 行として返す。
        tr の入れ子で外側 tr が内容を二重取得するのを防ぐ。
        単独の記号 (-, , 等) は除外するが、日本語 1 文字 (「様」等) は残す。"""
        if root is None:
            return []
        skip_pattern = re.compile(r"^[\s\-_,.;:・]+$")
        lines: list[str] = []
        for tr in root.iter("tr"):
            if tr.find(".//tr") is not None:
                continue
            text = tr.text_content() if hasattr(tr, "text_content") else ""
            text = re.sub(r"\s+", " ", text).strip()
            if not text or skip_pattern.match(text):
                continue
            if text not in lines:
                lines.append(text)
        return lines

    @staticmethod
    def find_by_class(root, class_name: str):  # noqa: ANN001
        """class を持つ最初の要素を返す。"""
        results = root.xpath(
            f".//*[contains(concat(' ', normalize-space(@class), ' '), ' {class_name} ')]"
        )
        return results[0] if results else None

    @staticmethod
    def find_all_by_class(root, class_name: str):  # noqa: ANN001
        return root.xpath(
            f".//*[contains(concat(' ', normalize-space(@class), ' '), ' {class_name} ')]"
        )
