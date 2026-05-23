"""様式別データ抽出層。

XSLT 出力 HTML を lxml で解析し、意味的データ (事業所名・保険料金額・宛先等) を
dataclass に抽出する。後段の Jinja2 テンプレートはこのデータから真のレスポンシブ
HTML を生成する。
"""
from __future__ import annotations

from .base import BaseExtractor, Document, Block
from .yoshiki_29 import Yoshiki29Extractor
from .yoshiki_04 import Yoshiki04Extractor
from .yoshiki_26 import Yoshiki26Extractor
from .kagami_only import KagamiOnlyExtractor
from .generic import GenericExtractor

EXTRACTORS: dict[str, type[BaseExtractor]] = {
    "yoshiki_29": Yoshiki29Extractor,
    "yoshiki_04": Yoshiki04Extractor,
    "yoshiki_26": Yoshiki26Extractor,
    "kagami_only": KagamiOnlyExtractor,
    "generic": GenericExtractor,
}


def get_extractor(form_id: str) -> BaseExtractor:
    """form_id に対応する extractor インスタンスを返す。未知なら generic にフォールバック。"""
    cls = EXTRACTORS.get(form_id, GenericExtractor)
    return cls()


__all__ = ["BaseExtractor", "Document", "Block", "EXTRACTORS", "get_extractor"]
