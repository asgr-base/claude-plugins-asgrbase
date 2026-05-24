"""yoshiki_29 (保険料納入告知額・領収済額通知書) 用 extractor。

XSLT 出力 HTML から以下のデータを意味的に抽出:
- お知らせ (oshirase)
- タイトル
- アナウンス文
- 本月分の保険料テーブル
- 前月分の領収済額テーブル
- 交付者情報 (発行日・徴収官・年金事務所印)
- 宛先 (郵便番号・住所・事業所名)
- 不服申立て注意書き 3 段落
"""
from __future__ import annotations

from .base import BaseExtractor, Block, Document


class Yoshiki29Extractor(BaseExtractor):
    form_id = "yoshiki_29"
    default_paper = "a3-landscape"

    def extract(self, html: str) -> Document:
        doc = self.parse(html)
        blocks: list[Block] = []

        # 1. お知らせ (oshirase)
        oshirase = self.find_by_class(doc, "oshirase")
        if oshirase is not None:
            blocks.append(Block(
                type="oshirase",
                data={"lines": self.text_lines(oshirase)},
                grid_area="oshirase",
            ))

        # 2. タイトル
        title_td = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' title ')]"
        )
        title_text = self.text(title_td[0]) if title_td else "保険料納入告知額・領収済額通知書"
        blocks.append(Block(type="title", data={"text": title_text}, grid_area="title"))

        # 3. アナウンス文 (本月分の前置き「あなたの本月分保険料額は...」)
        announcements = doc.xpath(
            "//pre[contains(concat(' ', normalize-space(@class), ' '), ' normal ')]"
        )
        if announcements:
            blocks.append(Block(
                type="announce",
                data={"text": self.text(announcements[0])},
                grid_area="announce",
            ))

        # 4. 本月分テーブル + 前月分テーブル
        #    XPath で 1 つ目と 2 つ目の保険料テーブル (Lterritory > 内側 table) を取得
        current = self._extract_payment_table(doc, kind="current")
        if current:
            blocks.append(Block(type="payment-current", data=current, grid_area="current"))

        previous = self._extract_payment_table(doc, kind="previous")
        if previous:
            blocks.append(Block(type="payment-previous", data=previous, grid_area="previous"))

        # 5. 注意書き
        appeals = self._extract_appeals(doc)
        if appeals:
            blocks.append(Block(type="appeal", data={"paragraphs": appeals}, grid_area="appeal"))

        # 6. 交付者情報 + 宛先 (簡易抽出)
        issuer = self._extract_issuer(doc)
        if issuer:
            blocks.append(Block(type="issuer", data=issuer, grid_area="issuer"))

        recipient = self._extract_recipient(doc)
        if recipient:
            blocks.append(Block(type="recipient", data=recipient, grid_area="recipient"))

        return Document(
            form_id=self.form_id,
            paper=self.default_paper,
            title=title_text,
            blocks=blocks,
        )

    def _extract_payment_table(self, doc, kind: str) -> dict | None:  # noqa: ANN001
        """本月分 or 前月分の保険料テーブルを抽出。

        L/Rterritory の中で midashiC セルを含むものだけがコンテンツテーブル。
        アナウンス文だけの Lterritory や末尾の注意書き Lterritory はスキップされる。
        """
        wrapper_class = "Lterritory" if kind == "current" else "Rterritory"
        tables = doc.xpath(
            f"//table[contains(concat(' ', normalize-space(@class), ' '), ' {wrapper_class} ')]"
            f"[.//td[contains(concat(' ', normalize-space(@class), ' '), ' midashiC ')]]"
        )
        if not tables:
            return None
        target = tables[0]

        # 見出し / 金額 / 合計を抽出
        midashi_all = target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' midashiC ')]"
        )
        # column_headers: 健康勘定 / 厚生年金勘定 / 業務勘定 (最初の 3 つ)
        # subheaders: 健康保険料 / 厚生年金保険料 / 子ども・子育て拠出金 (次の 3 つ)
        column_headers = [self.text(c) for c in midashi_all[:3]]
        subheaders = [self.text(c) for c in midashi_all[3:6]]

        smallR = [self.text(c) for c in target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' smallR ')]"
        )]
        amounts = smallR[:3]

        # yoshiki_29 の合計値は `normalR linetrb` クラス
        normalR = [self.text(c) for c in target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' normalR ')]"
        )]
        total_value = normalR[0] if normalR else ""

        # ヘッダ部分 (本月分: 「事業所整理記号 / 事業所番号 / 納付目的年月 / 納付期限」、
        # 前月分: 「N 年 M 月分保険料 / 領収日」)
        bigC = [self.text(c) for c in target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' bigC ')]"
        )]
        bigL = [self.text(c) for c in target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' bigL ')]"
        )]
        midashiSC = [self.text(c) for c in target.xpath(
            ".//td[contains(concat(' ', normalize-space(@class), ' '), ' midashiSC ')]"
        )]
        # 本月分は midashiSC ラベル (事業所整理記号/事業所番号/納付目的年月/納付期限) + bigC/bigL 値
        # 前月分は midashiSC (領収日) + bigC (年月分保険料 + 領収日値)
        header_pairs = []
        if kind == "current":
            for label, value in zip(midashiSC, bigL + bigC):
                header_pairs.append({"label": label, "value": value})
        else:
            for label, value in zip(midashiSC, bigC[1:]):  # 1 つ目は bigC は「年月分保険料」自体
                header_pairs.append({"label": label, "value": value})

        return {
            "title": bigC[0] if kind == "previous" and bigC else "",  # 前月分のみ「令和8年3月分保険料」
            "header_pairs": header_pairs,
            "column_headers": column_headers,
            "subheaders": subheaders,
            "amounts": amounts,
            "total_label": "合 計 額",
            "total_value": total_value,
        }

    def _extract_appeals(self, doc) -> list[str]:  # noqa: ANN001
        """smallTL の pre.normal 3 個を順に取得。"""
        cells = doc.xpath(
            "//td[contains(concat(' ', normalize-space(@class), ' '), ' smallTL ')]/pre"
        )
        return [self.text(c) for c in cells]

    def _innermost_table_excluding_outline(self, td):  # noqa: ANN001
        """td の祖先 table のうち、class=outline でない最も内側のものを返す。

        lxml の iterancestors() は確実に「子に近い順から外側へ」走査する。
        """
        for anc in td.iterancestors():
            if anc.tag != "table":
                continue
            cls = anc.get("class") or ""
            if "outline" not in cls.split():
                return anc
        return None

    def _extract_issuer(self, doc) -> dict | None:  # noqa: ANN001
        """交付者情報 (発行日・徴収官・年金事務所印・宛先) を抽出。

        td 境界で改行されるよう td_lines を使う。
        """
        nodes = doc.xpath(
            "//td[contains(normalize-space(.), '徴') and contains(normalize-space(.), '官')]"
        )
        for td in nodes:
            target = self._innermost_table_excluding_outline(td)
            if target is None:
                continue
            # tr 単位で行を取り、日付など細かい td 群を 1 行にまとめる
            lines = self.tr_lines(target)
            # 全文取り込み防止: 行数 20 以下に限定
            if 1 <= len(lines) <= 20:
                return {"lines": lines}
        return None

    def _extract_recipient(self, doc) -> dict | None:  # noqa: ANN001
        """宛先 (郵便番号・住所・事業所名・敬称) を抽出。

        yoshiki_29 では「交付者」と「宛先」が同じ Territory に同居していて、
        分割できないため issuer ブロックに統合する方針 → ここでは None を返す。
        """
        return None
