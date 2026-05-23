"""kagami_only (表紙のみ) 用 extractor。"""
from __future__ import annotations

from .base import BaseExtractor, Block, Document


class KagamiOnlyExtractor(BaseExtractor):
    form_id = "kagami_only"
    default_paper = "a4-portrait"

    def extract(self, html: str) -> Document:
        doc = self.parse(html)
        body = doc.xpath("//body")
        target = body[0] if body else doc
        lines = self.text_lines(target)
        title = lines[0] if lines else "公文書"
        return Document(
            form_id=self.form_id,
            paper=self.default_paper,
            title=title,
            blocks=[
                Block(type="header", data={"lines": lines}, grid_area="header"),
            ],
        )
