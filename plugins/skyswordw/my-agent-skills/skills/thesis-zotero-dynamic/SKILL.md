---
name: thesis-zotero-dynamic
description: Use when migrating a thesis Word DOCX from static numeric citations to Zotero dynamic citations, preparing a Zotero Group Library handoff, auditing CSL_CITATION fields, or maintaining GB/T 7714-2015 Word citation refreshability.
---

# Thesis Zotero Dynamic

## When To Use

Use this skill when a single DOCX thesis has static numeric citations and needs Zotero dynamic citations, a Zotero Group Library handoff, generated candidate Word fields, Word Refresh validation, or citation-field auditing.

Use `skills/thesis-zotero-metadata/SKILL.md` first when Zotero records have wrong authors, `itemType`, `language`, report/standard classification, or `et al.` behavior. Use `skills/thesis-word-format/SKILL.md` for visible Word layout and citation-marker superscript cleanup.

## Inputs And Outputs

- Input: one complete single DOCX thesis file.
- Static baseline: `output/doc/论文_统一编号.docx`.
- Zotero import files: `output/zotero/refs.bib` and `output/zotero/refs.csl.json`.
- Operator copy: `output/doc/论文_zotero_dynamic_operator.docx`.
- Migration checklist: `output/zotero/operator_migration_checklist.json`.
- Candidate dynamic DOCX: `output/doc/论文_zotero_dynamic_generated_candidate.docx`.
- Final audited dynamic DOCX: `output/doc/论文_zotero_dynamic.docx`.
- Project CSL: `styles/neu-thesis-gbt7714-2015-numeric.csl`.

## Standard Workflow

1. Build the static baseline from the single DOCX.
2. Create or select a Zotero Group Library and import `refs.bib`; confirm citekeys are `ref001` through the final reference.
3. Audit metadata before field generation. Confirm `itemType` and `language`: reports/white papers/research reports -> `report`, ITU-T/technical standards -> `standard`, English scholarly items -> `en-US`, Chinese items -> `zh-CN`.
4. Generate the operator placeholder copy and checklist.
5. With Zotero running and its local API available, generate a dynamic-field candidate DOCX from the operator placeholders.
6. Install the project CSL and select `NEU Thesis GB/T 7714-2015 Numeric` in Word Zotero Document Preferences.
7. Open the candidate in Word. It must open without repair. Run Zotero Refresh, then use Add/Edit Bibliography to insert or rebuild the bibliography.
8. If Word bibliography insertion is unreliable, rebuild only the bibliography field result from Zotero Local API plus the selected project CSL.
9. Run bibliography postprocess for layout/residue cleanup.
10. Audit the final DOCX against the operator checklist.

## Commands

```bash
uv run python scripts/run_all.py --input examples/demo/raw/thesis.docx
uv run python scripts/prepare_zotero_operator_docx.py --input examples/demo/raw/thesis.docx
uv run python scripts/generate_zotero_field_docx.py --group-id "$ZOTERO_GROUP_ID"
uv run python scripts/install_project_csl.py
uv run python scripts/rebuild_zotero_bibliography_from_api.py --group-id "$ZOTERO_GROUP_ID"
uv run python scripts/postprocess_zotero_bibliography.py output/doc/论文_zotero_dynamic.docx
uv run python scripts/audit_zotero_docx.py output/doc/论文_zotero_dynamic.docx \
  --checklist output/zotero/operator_migration_checklist.json \
  --output-dir output/reports/final_dynamic_after_refresh
```

## Acceptance Checks

- `CSL_CITATION` fields match the checklist citation positions.
- Extracted citation items match checklist occurrences.
- `csl_bibliography_fields=1`.
- No static citation markers or operator placeholders remain.
- No `[[ZOTERO_BIBLIOGRAPHY` or `]]` residue remains.
- English bibliography entries do not contain Chinese `等`; English multi-author entries use `et al.`.
- Report entries use `[R]` or `[R/OL]`; standard entries use `[S]` or `[S/OL]`; journal and conference records use `[J]` and `[C]`.
- Bibliography paragraphs use hanging indent, not first-line indent.
- The document opens in Word without repair, Zotero Refresh completes, and Add/Edit Bibliography can refresh or rebuild the bibliography.

## Boundaries

- Do not edit `raw/`; source Word documents are read-only.
- Use project-local `uv` commands only.
- Keep generated copies under `build/`, `output/`, or `tmp/`.
- Never treat unverified fields as final.
- Do not write to Zotero SQLite; scripts may copy it for read-only itemID lookup.
- Prefer Zotero Group Library workflows so collaborators can refresh and edit citations from the same shared library.
- Generated `ADDIN ZOTERO_ITEM`, `CSL_CITATION`, or `CSL_BIBLIOGRAPHY` fields are allowed only in generated copies, and must be validated by the Zotero Word plugin before handoff.
