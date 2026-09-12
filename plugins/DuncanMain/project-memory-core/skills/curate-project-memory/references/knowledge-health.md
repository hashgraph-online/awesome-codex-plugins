# Knowledge health

Use the deterministic checker for structural signals, then inspect the affected notes before drawing conclusions.

## Checks

- missing or inconsistent `project_id`;
- missing required properties by note type;
- overdue `review_after` dates;
- old current-state notes without a review date;
- accepted decisions that claim to be superseded but lack `superseded_by`;
- absolute Windows or Unix paths in durable Markdown;
- repository-relative code references whose target no longer exists, when a repository root is available;
- unmerged implementation states without a branch or revision scope;
- empty project navigation sections;
- possible credential-like content;
- broken local wikilinks;
- mixed project IDs within a project folder or duplicate decision titles.
- duplicate stable knowledge IDs;
- missing knowledge IDs or review state when a Team note enables shared-vault conventions.

## Response policy

Classify findings as errors, warnings, or information. Explain evidence, not certainty. A structural check cannot prove that prose is factually current.

Never print suspected secret values. Never delete, rewrite, or supersede notes automatically. Propose focused repairs and require confirmation for semantic changes.

## Portable report

Run `scripts/generate_health_report.py` to write `Health Report.md` when results should remain visible in Obsidian or on mobile. The report contains only structural finding codes, affected vault-relative files, safe messages, counts, and generation metadata. It must not contain the absolute vault path, secret values, or raw checker output. Regenerate it after meaningful repairs; treat it as derived review data, not canonical project truth.
