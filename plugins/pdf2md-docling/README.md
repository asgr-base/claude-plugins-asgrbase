# pdf2md-docling

Production-grade PDF to Markdown converter using Docling with TableFormer.

## What It Does

Converts PDF files to Markdown with high-accuracy table extraction using Docling and TableFormer. Exports images as separate PNG files. Includes a 12-step post-processing pipeline for production-grade output.

## Key Features

- **Docling + TableFormer** — Accurate table structure preservation
- **Image Export** — Referenced PNG files (not inline Base64)
- **12-Step Post-Processing Pipeline**:
  - Phase A: File organization (image movement)
  - Phase B: Cleanup (Unicode PUA removal, path normalization, JSON formatting)
  - Phase C: Structure rebuild (header dedup, orphaned fences, table merging)
  - Phase D: Final formatting (table optimization, cell-internal newlines)
- **14-Item Quality Checklist** — File size, image paths, table structure validation
- **Handles Complex Documents** — APDU tables, cryptographic protocols, MRZ, ASN.1

## Usage

```
/pdf2md-docling
```

Use for PDF to Markdown conversion requiring precise table structure.

## File Structure

```
pdf2md-docling/
├── SKILL.md              # Main workflow guide
├── IMPLEMENTATION.md     # Detailed Python code for 12-step pipeline
├── CHANGELOG.md          # Version history
└── TROUBLESHOOTING.md    # Error handling, FAQ
```

## Requirements

- Docling CLI (`pip install docling`)
- Python 3.10+
- Claude Code CLI

## License

Apache 2.0
