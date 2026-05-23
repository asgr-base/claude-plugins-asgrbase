"""様式判定: XSL ファイル名 → HTML 構造指紋 → generic のフォールバック。

Phase 0 調査結果 (debug/PHASE0_FINDINGS.md) に基づく:
- 各 ZIP には複数 XML が混在する (kagami + yoshiki) ため、XML 単位で判定する
- XSL ファイル名前方一致が最も確実 (yoshiki_NN_*, kagami.xsl)
- 不明 XSL は HTML 出現 class 指紋でフォールバック判定
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# 紙サイズ識別子
Paper = str  # "a4-portrait" | "a4-landscape" | "a3-landscape" | "auto"


@dataclass(frozen=True)
class FormSpec:
    """判定結果。convert_v2 はこれを semantic_rebuilder, grid_css, pdf_renderer に渡す。"""

    form_id: str  # "yoshiki_26" | "yoshiki_04" | "yoshiki_29" | "kagami_only" | "generic"
    paper: Paper
    adapter_name: str
    confidence: float  # 0.0–1.0
    reason: str  # 判定根拠 (ログ・デバッグ用)


# 様式 → 既定紙サイズ・アダプタ名
_FORM_DEFAULTS: dict[str, tuple[Paper, str]] = {
    "yoshiki_26": ("a4-portrait", "yoshiki_26"),
    "yoshiki_04": ("a4-landscape", "yoshiki_04"),
    "yoshiki_29": ("a3-landscape", "yoshiki_29"),
    "kagami_only": ("a4-portrait", "kagami_only"),
    "generic": ("auto", "generic"),
}


def _detect_by_xsl_filename(xsl_path: Path) -> str | None:
    """XSL ファイル名前方一致で様式 ID を返す。確実な経路。"""
    name = xsl_path.name.lower()
    if name == "kagami.xsl":
        return "kagami_only"
    m = re.match(r"^yoshiki_(\d+)_", name)
    if not m:
        return None
    # e-Gov 様式 ID は "04", "26", "29" 等の zero-pad 表記。そのまま辞書キーとして使う
    return f"yoshiki_{m.group(1)}"


def _detect_by_html_fingerprint(html: str) -> tuple[str, float, str] | None:
    """HTML 出現 class 指紋でフォールバック判定。
    戻り値 (form_id, confidence, reason)。未判定なら None。
    """
    has = lambda token: re.search(rf'class="[^"]*\b{token}\b', html) is not None  # noqa: E731

    # yoshiki_29 指紋: Territory + Lterritory + Rterritory + pre.normal
    if (
        has("Territory")
        and has("Lterritory")
        and has("Rterritory")
        and re.search(r'<pre[^>]*class="[^"]*\bnormal\b', html)
    ):
        return "yoshiki_29", 0.85, "fingerprint: Territory + L/Rterritory + pre.normal"

    # yoshiki_04 指紋: jgshAddr or jgshName + bigC/R/L + 1300px 級 width
    if (has("jgshAddr") or has("jgshName")) and re.search(r"\bwidth\s*[:=]\s*\"?\d{4,}", html):
        return "yoshiki_04", 0.80, "fingerprint: jgsh* + 4-digit width"

    # yoshiki_26 指紋: normalM_L + detail + equality + kyouji
    if has("normalM_L") and has("detail") and has("equality"):
        return "yoshiki_26", 0.75, "fingerprint: normalM_L + detail + equality"

    # kagami 指紋: class 出現ゼロ かつ HTML 小さい
    if not re.search(r'class="', html) and len(html) < 2500:
        return "kagami_only", 0.70, "fingerprint: no class + small HTML"

    return None


def detect_form(
    xml_path: Path,
    xsl_path: Path | None,
    html: str | None = None,
) -> FormSpec:
    """様式判定の入口。

    順序:
      1. XSL ファイル名前方一致 (confidence 0.95)
      2. HTML 構造指紋 (confidence 0.70–0.85)
      3. generic フォールバック (confidence 0.0, paper=auto)
    """
    # 1. XSL ファイル名
    if xsl_path is not None:
        form_id = _detect_by_xsl_filename(xsl_path)
        if form_id is not None and form_id in _FORM_DEFAULTS:
            paper, adapter = _FORM_DEFAULTS[form_id]
            return FormSpec(
                form_id=form_id,
                paper=paper,
                adapter_name=adapter,
                confidence=0.95,
                reason=f"xsl filename: {xsl_path.name}",
            )

    # 2. HTML 指紋
    if html is not None:
        fp = _detect_by_html_fingerprint(html)
        if fp is not None:
            form_id, conf, reason = fp
            paper, adapter = _FORM_DEFAULTS[form_id]
            return FormSpec(
                form_id=form_id,
                paper=paper,
                adapter_name=adapter,
                confidence=conf,
                reason=reason,
            )

    # 3. generic フォールバック
    paper, adapter = _FORM_DEFAULTS["generic"]
    return FormSpec(
        form_id="generic",
        paper=paper,
        adapter_name=adapter,
        confidence=0.0,
        reason=f"no match (xml={xml_path.name}, xsl={xsl_path.name if xsl_path else 'none'})",
    )
