---
name: thesis-word-format
description: Use when formatting Chinese doctoral thesis Word/DOCX deliverables, applying Northeastern University thesis layout guidance, GB/T 7714 sequential references, final reference lists, inline citation superscripts, or Chinese narrative citations such as 文献[n].
---

# Thesis Word Format

## When To Use

Use this skill when a Chinese 博士学位论文 DOCX needs thesis layout checks, GB/T 7714 sequential reference presentation, inline citation 上标 formatting, or narrative citation cleanup such as `文献[n]`.

Use `skills/thesis-zotero-dynamic/SKILL.md` first when the task is about Zotero dynamic fields. Use `skills/thesis-zotero-metadata/SKILL.md` first when wrong bibliography semantics come from Zotero metadata.

## Inputs And Outputs

- Input: one complete single DOCX thesis file.
- Main static output: `output/doc/论文_统一编号.docx`.
- Formatted citation-marker output: `output/doc/论文_统一编号_引用上标.docx`.
- Report output: `output/reports/citation_marker_report.json`.
- Reference files: `references/degree-format-summary.md`, `references/docx-format-execution-checklist.md`, and `references/citation-position-rules.md`.

## Standard Workflow

1. Read `references/degree-format-summary.md` before changing page layout, headings, body fonts, figure/table captions, or reference-list typography.
2. Read `references/docx-format-execution-checklist.md` before whole-document Word formatting changes.
3. Read `references/citation-position-rules.md` before editing inline citation placement.
4. Run the reference pipeline on a single DOCX input before citation-marker normalization.
5. Run `scripts/normalize_citation_markers.py` to set in-text numeric citation markers as superscript runs.
6. Render DOCX to PDF/PNG with LibreOffice and Poppler when available; otherwise report the remaining visual-review risk.

## Commands

```bash
uv run python scripts/run_all.py --input examples/demo/raw/thesis.docx
uv run python skills/thesis-word-format/scripts/normalize_citation_markers.py \
  output/doc/论文_统一编号.docx \
  output/doc/论文_统一编号_引用上标.docx \
  --report output/reports/citation_marker_report.json
```

## Acceptance Checks

- Terminal evidence citations keep `[n]` attached to the sentence and set `[n]` as Word superscript.
- Chinese sentence-openers use `文献[n]指出/提出/认为...` or `作者在文献[n]中...`; `文献` remains baseline and only `[n]` is superscript.
- English author-led openings such as `Chen等[n]...`, `Sun等[n]...`, or `Büsing等[n]...` are rewritten to `文献[n]...` unless the author name is semantically required.
- Reference-list numbers `[n]` are baseline, not superscript.
- Multiple references supporting one statement use one marker such as `[1,3-5]`, not repeated adjacent markers.
- Dynamic Zotero bibliography semantics are fixed through Zotero metadata and CSL, not by patching final bibliography text.

## Boundaries

- Do not edit `raw/`; source Word documents are read-only.
- Use project-local `uv` commands only.
- Keep generated files under `build/`, `output/`, or temporary scratch directories.
- Treat bibliography 语义 format as Zotero metadata plus CSL. Fix `itemType`, `language`, author metadata, and the project CSL when `[R]`/`[S]`, `et al.`, `等`, DOI, or URL behavior is wrong.
- After Zotero Refresh, `scripts/postprocess_zotero_bibliography.py` may clean layout/residue only: anchor residue, hanging indent, line spacing, and field-safe formatting.
- Preserve DOCX structure. Review risk boundaries before running on documents with Zotero fields, hyperlinks, footnotes, text boxes, bookmarks, or comments.
