"""yoshiki_04 (社会保険料額情報) 用 extractor。"""
from __future__ import annotations

from .base import BaseExtractor, Block, Document


class Yoshiki04Extractor(BaseExtractor):
    form_id = "yoshiki_04"
    default_paper = "a4-landscape"

    def extract(self, html: str) -> Document:
        doc = self.parse(html)
        blocks: list[Block] = []

        # お知らせ
        oshirase = self.find_by_class(doc, "oshirase")
        if oshirase is not None:
            blocks.append(Block(
                type="oshirase",
                data={"lines": self.text_lines(oshirase)},
                grid_area="oshirase",
            ))

        # タイトル
        title_td = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' title ')]"
        )
        title_text = self.text(title_td[0]) if title_td else "社会保険料額情報"
        blocks.append(Block(type="title", data={"text": title_text}, grid_area="title"))

        # detail テーブルから保険料データを抽出
        detail = self.find_by_class(doc, "detail")
        if detail is not None:
            payment = self._extract_detail(detail)
            if payment:
                blocks.append(Block(type="payment", data=payment, grid_area="payment"))

        # 宛先 (jigyosho): jgshAddr/jgshName を全件取得、テキストを連結
        jgsh_addr_nodes = self.find_all_by_class(doc, "jgshAddr")
        jgsh_name_nodes = self.find_all_by_class(doc, "jgshName")
        address_lines: list[str] = []
        for node in jgsh_addr_nodes:
            for line in self.text_lines(node):
                if line and line not in address_lines:
                    address_lines.append(line)
        name_lines: list[str] = []
        for node in jgsh_name_nodes:
            for line in self.text_lines(node):
                if line and line not in name_lines:
                    name_lines.append(line)
        if address_lines or name_lines:
            blocks.append(Block(
                type="recipient",
                data={"address": address_lines, "name": name_lines},
                grid_area="recipient",
            ))

        # caption (上記は...のお知らせ)
        caption = self.find_by_class(doc, "caption")
        if caption is not None:
            blocks.append(Block(
                type="notice",
                data={"lines": self.text_lines(caption)},
                grid_area="notice",
            ))

        # jimusho (日本年金機構 / ○○年金事務所)
        jimusho = self.find_by_class(doc, "jimusho")
        if jimusho is not None:
            blocks.append(Block(
                type="footer",
                data={"lines": self.text_lines(jimusho)},
                grid_area="footer",
            ))

        return Document(
            form_id=self.form_id,
            paper=self.default_paper,
            title=title_text,
            blocks=blocks,
        )

    def _extract_detail(self, detail) -> dict:  # noqa: ANN001
        """detail テーブルから保険料データ (ヘッダ + 金額) を抽出。"""
        midashi_cells = detail.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' midashiC ')]"
        )
        bigC_cells = detail.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' bigC ')]"
        )
        bigR_cells = detail.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' bigR ')]"
        )

        return {
            "headers_top": [self.text(c) for c in midashi_cells[:4]],   # 事業所整理記号 / 事業所番号 / 納付目的年月 / 納付期限
            "values_top": [self.text(c) for c in bigC_cells[:4]],
            "headers_payment": [self.text(c) for c in midashi_cells[4:7]],  # 健康保険料 / 厚生年金保険料 / 子ども・子育て拠出金
            "values_payment": [self.text(c) for c in bigR_cells[:3]],
            "total_label": self.text(midashi_cells[7]) if len(midashi_cells) > 7 else "合計額",
            "total_value": self.text(bigR_cells[3]) if len(bigR_cells) > 3 else "",
        }
