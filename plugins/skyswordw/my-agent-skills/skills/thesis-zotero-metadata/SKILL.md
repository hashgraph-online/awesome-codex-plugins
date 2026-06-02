---
name: thesis-zotero-metadata
description: Use when auditing or enriching Zotero Group Library metadata for a thesis reference project, preparing metadata patches, handling DOI/identifier gaps, or coordinating metadata cleanup before rebuilding Zotero dynamic thesis DOCX files.
---

# Thesis Zotero Metadata

## When To Use

Use this skill when Zotero Group Library records need author cleanup, DOI/identifier enrichment, `itemType` correction, language correction, report/standard classification, or metadata patch preparation before rebuilding a Zotero dynamic thesis DOCX.

Use `skills/thesis-zotero-dynamic/SKILL.md` for field generation, Word Refresh, bibliography rebuilding, and final DOCX audit. Use `skills/thesis-word-format/SKILL.md` for visible Word layout and citation-marker formatting.

## Inputs And Outputs

- Input: one complete single DOCX thesis file and an existing Zotero Group Library.
- API key: project-local `.env.local` only.
- Group identifier: `--group-id` or `ZOTERO_GROUP_ID`.
- Audit output: `output/reports/zotero_metadata_audit.json` and `.md`.
- Patch output: `output/reports/zotero_metadata_patch.json` and `.md`.
- Apply log: `output/reports/zotero_metadata_apply_log.json`.
- Downstream output: rebuilt Zotero dynamic DOCX plus final audit reports.

## Standard Workflow

1. Build or refresh the single DOCX reference model so the metadata audit has current citekeys and expected reference types.
2. Audit the configured Zotero Group Library against project artifacts: title, author, year, Zotero `itemType`, `language`, DOI, URL, citekey, and expected GB/T type.
3. Enrich incomplete records through Crossref, OpenAlex, and Semantic Scholar. Prefer exact DOI/title matches and record source confidence.
4. Patch non-DOI records too. Reports, white papers, and research reports must be Zotero `report`; ITU-T recommendations and technical standards must be Zotero `standard`; journal and conference papers remain `journalArticle` and `conferencePaper`.
5. Set language before Word Refresh: English scholarly items use `language=en-US` so bibliography output uses `et al.`; Chinese items use `language=zh-CN` so Chinese author lists may use `等`.
6. Generate a reviewable metadata patch before applying anything.
7. Apply only approved patches through the Zotero Web API.
8. Rebuild the dynamic DOCX with the Zotero dynamic workflow, open it in Word, run Zotero Refresh, rebuild or refresh bibliography, and audit the final document.

## Commands

```bash
uv run python scripts/run_all.py --input examples/demo/raw/thesis.docx
uv run python scripts/audit_zotero_metadata.py --input examples/demo/raw/thesis.docx --group-id "$ZOTERO_GROUP_ID"
uv run python scripts/enrich_zotero_metadata.py --input examples/demo/raw/thesis.docx --group-id "$ZOTERO_GROUP_ID"
uv run python scripts/enrich_zotero_metadata.py --input examples/demo/raw/thesis.docx --group-id "$ZOTERO_GROUP_ID" --apply
uv run python scripts/rebuild_dynamic_after_metadata.py --input examples/demo/raw/thesis.docx --group-id "$ZOTERO_GROUP_ID"
```

## Acceptance Checks

- No duplicate citekeys in the Group Library.
- No inverted English initials such as `firstName=Yang, lastName=D`.
- No fake visible `Others` creator except the Zotero-compatible `others` marker where required.
- DOI-bearing journal/conference items have container title, volume/issue/pages when public metadata provides them.
- Expected `itemType` mismatches are zero: `report` for reports and white papers, `standard` for technical standards, `journalArticle` for journals, and `conferencePaper` for conferences.
- English scholarly items have `language=en-US`; Chinese records have `language=zh-CN`.
- Word Refresh after patching does not reintroduce Chinese `等` in English bibliography entries, `[Z]` fallbacks for reports/standards, or hidden DOI/URL formatting problems.

## Boundaries

- Do not edit `raw/`; source Word documents are read-only.
- Use project-local `uv` commands only.
- Keep generated audits, patches, reports, and checkpoint DOCX files under `build/`, `output/`, or `tmp/`.
- Store Zotero Web API keys only in project-local `.env.local`; never put keys in global shell config, source files, committed docs, or generated reports.
- Do not write to Zotero SQLite. Use the Zotero Web API for updates and local/exported artifacts for review.
- Leave uncertain metadata matches flagged for manual review rather than applying speculative patches.
