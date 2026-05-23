"""generic extractor — 未知様式のフォールバック。

e-Gov XSL で共通に使われる class 名 (oshirase / title / caption / pre.normal /
jgshAddr / jgshName / jimusho / detail) を自動検出し、それぞれを Block として返す。
これにより、様式専用 extractor が無い未知文書でも「意味のあるブロック」が抽出される。
"""
from __future__ import annotations

from .base import BaseExtractor, Block, Document


class GenericExtractor(BaseExtractor):
    form_id = "generic"
    default_paper = "a4-portrait"

    def extract(self, html: str) -> Document:
        doc = self.parse(html)
        blocks: list[Block] = []

        # 1. お知らせ (oshirase)
        oshirase_nodes = self.find_all_by_class(doc, "oshirase")
        for node in oshirase_nodes:
            lines = self.text_lines(node)
            if lines:
                blocks.append(Block(
                    type="oshirase",
                    data={"lines": lines},
                    grid_area="oshirase",
                ))
                break  # 最初の 1 つだけ採用

        # 2. タイトル
        title_td = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' title ')]"
        )
        title_text = ""
        if title_td:
            title_text = self.text(title_td[0])
        if title_text:
            blocks.append(Block(type="title", data={"text": title_text}, grid_area="title"))

        # 3. detail テーブル (お金関連の表): 内側全 td を順に取り出して row 化
        detail_tables = doc.xpath(
            "//table[contains(concat(' ', normalize-space(@class), ' '), ' detail ')]"
        )
        for i, dt in enumerate(detail_tables):
            rows = self._table_to_rows(dt)
            if rows:
                blocks.append(Block(
                    type="detail",
                    data={"rows": rows, "index": i},
                    grid_area=f"detail-{i}" if i > 0 else "detail",
                ))

        # 4. 宛先 (jgshAddr / jgshName)
        addr_nodes = self.find_all_by_class(doc, "jgshAddr")
        name_nodes = self.find_all_by_class(doc, "jgshName")
        if addr_nodes or name_nodes:
            address_lines: list[str] = []
            for node in addr_nodes:
                for line in self.text_lines(node):
                    if line and line not in address_lines:
                        address_lines.append(line)
            name_lines: list[str] = []
            for node in name_nodes:
                for line in self.text_lines(node):
                    if line and line not in name_lines:
                        name_lines.append(line)
            blocks.append(Block(
                type="recipient",
                data={"address": address_lines, "name": name_lines},
                grid_area="recipient",
            ))

        # 5. caption (中段の注記)
        caption = self.find_by_class(doc, "caption")
        if caption is not None:
            lines = self.text_lines(caption)
            if lines:
                blocks.append(Block(
                    type="notice",
                    data={"lines": lines},
                    grid_area="notice",
                ))

        # 6. pre.normal / pre.kyouji (注意書き)
        appeal_pres = doc.xpath(
            "//pre[contains(concat(' ', normalize-space(@class), ' '), ' normal ') "
            "or contains(concat(' ', normalize-space(@class), ' '), ' kyouji ')]"
        )
        appeal_paragraphs = [self.text(p) for p in appeal_pres if self.text(p)]
        if appeal_paragraphs:
            blocks.append(Block(
                type="appeal",
                data={"paragraphs": appeal_paragraphs},
                grid_area="appeal",
            ))

        # 7. jimusho (発行元事務所)
        jimusho = self.find_by_class(doc, "jimusho")
        if jimusho is not None:
            lines = self.text_lines(jimusho)
            if lines:
                blocks.append(Block(
                    type="footer",
                    data={"lines": lines},
                    grid_area="footer",
                ))

        # 8. 何も検出できなかった場合は body 全体を 1 ブロック化
        if not blocks:
            body = doc.xpath("//body")
            target = body[0] if body else doc
            lines = self.text_lines(target)
            blocks.append(Block(
                type="main",
                data={"lines": lines or ["(no content)"]},
                grid_area="main",
            ))

        return Document(
            form_id=self.form_id,
            paper=self.default_paper,
            title=title_text or "公文書",
            blocks=blocks,
        )

    def _table_to_rows(self, table) -> list[list[str]]:  # noqa: ANN001
        """detail table を行 (各セルのリスト) に変換。"""
        rows: list[list[str]] = []
        for tr in table.iter("tr"):
            if tr.find(".//tr") is not None:  # 入れ子 tr は外側スキップ
                continue
            cells: list[str] = []
            for td in tr.findall(".//td"):
                if td.find(".//td") is not None:
                    continue
                txt = self.text(td)
                if txt:
                    cells.append(txt)
            if cells:
                rows.append(cells)
        return rows
