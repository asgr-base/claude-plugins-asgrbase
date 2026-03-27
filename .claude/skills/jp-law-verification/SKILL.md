---
name: jp-law-verification
description: Verify legal basis using e-Gov Law API. Search Japanese laws (income tax, labor, corporate) for articles on withholding tax, social insurance, employment regulations. Use when user mentions laws, legal requirements, tax regulations, or requests accurate legal references.
version: 2.1.0
author: claude_code
createDate: 2026-01-10
updateDate: 2026-01-25
license: Apache-2.0
---

# 日本法令確認（Japanese Law Verification）

## Quick Start

Use `e-gov-law:find_law_article` to retrieve specific law articles:

```bash
e-gov-law:find_law_article(law_name="所得税法", article_number="183")
```

**Important**: Always use fully qualified tool name: `e-gov-law:find_law_article`

## Common Law References

**Tax laws**:

- 所得税法 第183条 - Withholding tax obligations
- 所得税法 第28条 - Salary income
- 所得税法 第83条 - Spouse deduction
- 地方税法 第45条の2 - Local tax spouse deduction

**Labor laws**:

- 労働基準法 第24条 - Wage payment principles
- 労働基準法 第39条 - Paid annual leave
- 雇用保険法 - Employment insurance
- 労働者災害補償保険法 - Workers' compensation

**Corporate laws**:

- 会社法 - Corporate operations
- 民法 - Civil code

For complete reference tables, see [LAW_REFERENCE.md](LAW_REFERENCE.md)

## Workflow

### Step 1: Identify relevant law and article

Based on user's question, determine which law and article to check.

### Step 2: Search using MCP tool

```bash
e-gov-law:find_law_article(law_name="法令名", article_number="条番号")
```

**Article number formats** (all accepted):

- "183"
- "第183条"
- "183条"
- "325条の3"

### Step 3: Interpret and respond

Quote the article text verbatim, then apply to user's situation.

**Response template**:

```markdown
## 法的根拠

【法令名】第○条に基づくと...

（条文引用）

## 実務への適用

この規定により、御社の場合は...
```

## Important Notes

**MCP Tool Usage**:

1. Use fully qualified tool name: `e-gov-law:find_law_article`
2. Use official law names (避ける: 略称 "所法")
3. Article numbers: "第" and "条" are optional

**Interpretation Guidelines**:

- Quote articles verbatim (no paraphrasing)
- Check enforcement dates and revision history
- Review related articles (e.g., main law + enforcement order)
- Recommend expert consultation when uncertain

## Troubleshooting

**"tool not found" error**:

```markdown
❌ Wrong: find_law_article(law_name="所得税法", article_number="183")
✅ Correct: e-gov-law:find_law_article(law_name="所得税法", article_number="183")
```

**Law not found**: Use official names, avoid abbreviations

## Example Usage

**User**: "When should I withhold tax for December salary paid in January?"

**Workflow**:

1. Check 所得税法 第183条
2. Run: `e-gov-law:find_law_article(law_name="所得税法", article_number="183")`
3. Response: "Based on Article 183, withholding occurs '支払の際' (at payment time) = actual payment date"

## Setup Requirements

This skill requires e-Gov Law MCP server. See [README.md](README.md) for installation instructions.

---

**Version**: 2.1.0
**Last Updated**: 2026-01-11
**Author**: Claude Code (Sonnet 4.5)
