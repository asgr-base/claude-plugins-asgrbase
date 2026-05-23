"""yoshiki_26 (健康保険・厚生年金保険口座振替開始通知書) 用 extractor。

XSL 構造:
- <table class="Lterritory"> 配下に受取人 (郵便番号・住所・会社名・氏名)
- <table class="Rterritory"> 配下に 〈事業主の方へ〉 お知らせ (pre.oshirase)
- <td class="title">「健康保険・厚生年金保険口座振替開始通知書」
- normalTitleM_L allline (ラベル) + 隣接 td (値) の key-value で通帳情報
- pre.kyouji が不服申立て注意書き
"""
from __future__ import annotations

from .base import BaseExtractor, Block, Document


class Yoshiki26Extractor(BaseExtractor):
    form_id = "yoshiki_26"
    default_paper = "a4-portrait"

    def extract(self, html: str) -> Document:
        doc = self.parse(html)
        blocks: list[Block] = []

        # 1. 受取人 (Lterritory 配下の normalM_L 群)
        lterritory = doc.xpath(
            "//table[contains(concat(' ', normalize-space(@class), ' '), ' Lterritory ')]"
        )
        if lterritory:
            recipient_lines = self._extract_recipient_lines(lterritory[0])
            if recipient_lines:
                blocks.append(Block(
                    type="recipient",
                    data={"lines": recipient_lines},
                    grid_area="recipient",
                ))

        # 2. 〈事業主の方へ〉 お知らせ (pre.oshirase)
        oshirase_pre = doc.xpath(
            "//pre[contains(concat(' ', normalize-space(@class), ' '), ' oshirase ')]"
        )
        if oshirase_pre:
            blocks.append(Block(
                type="oshirase",
                data={"text": self.text(oshirase_pre[0])},
                grid_area="oshirase",
            ))

        # 3. タイトル
        title_td = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' title ')]"
        )
        title_text = self.text(title_td[0]) if title_td else "健康保険・厚生年金保険口座振替開始通知書"
        blocks.append(Block(type="title", data={"text": title_text}, grid_area="title"))

        # 4. 通帳情報 (normalTitleM_L allline = ラベル、隣接 td = 値)
        passbook_rows = self._extract_passbook(doc)
        if passbook_rows:
            blocks.append(Block(
                type="passbook",
                data={"rows": passbook_rows},
                grid_area="passbook",
            ))

        # 5. 不服申立て注意書き (pre.kyouji)
        kyouji_pre = doc.xpath(
            "//pre[contains(concat(' ', normalize-space(@class), ' '), ' kyouji ')]"
        )
        if kyouji_pre:
            blocks.append(Block(
                type="appeal",
                data={"text": self.text(kyouji_pre[0])},
                grid_area="appeal",
            ))

        return Document(
            form_id=self.form_id,
            paper=self.default_paper,
            title=title_text,
            blocks=blocks,
        )

    def _extract_recipient_lines(self, lterritory) -> list[str]:  # noqa: ANN001
        """Lterritory 内の受取人住所・会社名・氏名・受付番号を行ごとに抽出。

        XSL 構造: Lterritory 直下の <td class="normalM_L"> が各行を表す。
        各 td 内のテキストを 1 行として扱う (内側 table のテキストは結合される)。
        """
        lines: list[str] = []
        # 直下の <td> を順に走査 (Lterritory > tr > td、または Lterritory > tbody > tr > td)
        direct_tds = lterritory.xpath("./tr/td | ./tbody/tr/td")
        for td in direct_tds:
            txt = self.text(td)
            if not txt or txt in ("-", "−"):
                continue
            lines.append(txt)
        # 重複と短すぎる断片を除外
        result: list[str] = []
        for line in lines:
            if line and line not in result and len(line.strip()) > 1:
                result.append(line)
        return result[:6]  # 最大 6 行

    def _extract_passbook(self, doc) -> list[dict]:  # noqa: ANN001
        """normalTitleM_L allline (ラベル) と following-sibling td (値) を pair で取得。"""
        labels = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' normalTitleM_L ')]"
        )
        rows: list[dict] = []
        seen_labels: set[str] = set()
        for label_td in labels:
            label = self.text(label_td)
            if not label or label in seen_labels:
                continue
            seen_labels.add(label)
            # 隣接 td (1 番目) を値とする
            value_tds = label_td.xpath("following-sibling::td[1]")
            if not value_tds:
                continue
            value = self.text(value_tds[0])
            if value:
                rows.append({"label": label, "value": value})

        # 金融機関名称は 2 行 (銀行名 + 支店名) で構成されるが、
        # 上記ロジックでは 1 行目しか取れない。XSL の rowspan="2" 構造を補正する。
        # 「金融機関名称」ラベルの隣接 td の text_content() が 1 行の場合、
        # その親 tr の次の tr の最初の td も値に含める。
        for i, row in enumerate(rows):
            if "金融機関名称" in row["label"]:
                # XSL 上で銀行名 + 支店名が 2 行の td に分かれている場合の補正
                label_td = [t for t in labels if self.text(t) == row["label"]]
                if label_td:
                    # parent tr の次の tr の最初の td
                    parent_tr = label_td[0].getparent()
                    next_tr = parent_tr.getnext()
                    if next_tr is not None and next_tr.tag == "tr":
                        first_td_in_next = next_tr.find("td")
                        if first_td_in_next is not None:
                            extra = self.text(first_td_in_next)
                            if extra and extra not in row["value"]:
                                row["value"] = row["value"] + " " + extra

        return rows
