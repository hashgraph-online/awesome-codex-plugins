# Manuscript Revision And Submission

Use this reference for reviewer/editor revisions, response documents, highlighted manuscripts, clean/marked comparisons, Overleaf source packages, and submission-packet audits.

## Preserve Technical Meaning

Before substantive editing, record the technical invariants that must not change silently:

- variables, equations, sign conventions, units, and system boundaries;
- geometry, operating conditions, boundary/initial conditions, and property states;
- dataset identity, sample size, splits, exclusions, and uncertainty definition;
- measured, simulated, derived, assumed, or proposed status;
- claim strength, limitations, citations, figures, tables, and permissions.

After editing, compare these invariants. Use [result-change-and-construct-audit.md](result-change-and-construct-audit.md) when a result or definition changes materially.

## Reviewer Response

Treat the response document as the reviewer's roadmap. Repeat every comment, answer directly and respectfully, describe the scientific diagnosis and action, identify the location, and state any unresolved evidence need.

Use this structure:

```text
Comment X: [reviewer/editor comment]

Response: [direct answer and rationale]

Specific revision: [before/after text or a complete description of the analysis, figure, table, or structural change]

Location of changes: [section, paragraph, equation, table, figure, or reference]
```

For major changes, quote or closely reproduce the revised text. Avoid entries such as "Changes made" without enough detail to verify the response. If a methodological concern requires new analysis, data, validation, or uncertainty treatment, do that work when feasible; do not close it through wording alone.

When the requested evidence is available locally or through authorized sources, address a substantive reviewer concern through the needed analysis, data extraction, model evaluation, figure revision, or source verification. Do not substitute a passive limitation statement or weaker framing merely because the substantive response takes more time. If the author has not specified the preferred effort level and the alternatives differ materially in time or scope, present i) a prose-only response with its unresolved limitation and ii) a substantive response with the required work. Recommend the substantive response and proceed with it when the user has requested a thorough revision. Pause only when the work meets an explicit human-pause condition, requires unavailable evidence, or requires an author-positioning decision.

Prefer a formal narrative response with editor/reviewer headings. A tracking matrix may support the work but should not replace the submitted response. Start from [response-to-reviewers.md](../assets/templates/response-to-reviewers.md) and use [reviewer-response-matrix.csv](../assets/templates/reviewer-response-matrix.csv) internally when useful.

## Highlighted Manuscript

- Highlight only changed phrases, clauses, or sentences. Do not highlight unchanged portions of a paragraph, title, table, or caption.
- Use a consistent color for the editor and each reviewer when requested.
- State the color key in the response document. Avoid adding body text that changes marked-manuscript pagination unless the journal requires it.
- Keep the clean and marked sources identical except for intentional change-marking commands.
- Remove reviewer-response residue from manuscript prose.

## Citation And Structure Audit

After moving, adding, or deleting text:

1. Recheck citation keys and first-appearance order.
2. Verify high-risk citation intent semantically, especially figure permissions, datasets, software, preprints, and data availability.
3. Recheck section, figure, table, and equation numbering and cross-references.
4. Confirm that each main figure/table is cited and interpreted.
5. Confirm that figure roles, captions, and placement still support the revised narrative.

Use [citation-integrity.md](citation-integrity.md) and [scientific-figure-and-artifact-qa.md](scientific-figure-and-artifact-qa.md) for the full checks.

## Clean And Marked PDF Comparison

Compare both content and rendering:

- same page count, title, authors, abstract, keywords, acknowledgments, availability statement, and references;
- same figures, tables, captions, numbering, and permissions;
- no punctuation or spacing introduced by color macros;
- no unintentional reflow, float movement, table break, or blank page;
- no color-key paragraph, response note, or reviewer language present in only one manuscript.

Use text extraction for content and raster/page inspection for layout. Treat differences as findings to investigate; PDF extraction and raster comparison can each produce false positives.

## Submission Packet

Inspect every file, not only the final PDF.

Check for:

- temporary files, lock files, obsolete drafts, comparison artifacts, and duplicate source entry points;
- placeholders, unresolved citations, prompt fragments, AI instructions, revision notes, and tracked changes/comments;
- missing figures, bibliography files, style/class files, supplements, declarations, and response documents;
- source/PDF mismatch, stale timestamps, inconsistent dates, and clean/marked divergence;
- typos, broken glyphs, reference punctuation, and permissions;
- journal-specific file types, declarations, naming, and upload limits.

## Overleaf And Source Package

- Keep one documented active compile entry point unless clean and marked variants are intentionally provided.
- Remove stale alternate files such as generated autocite drafts unless they are current and documented.
- Include every referenced figure, bibliography, class/style file, and supplement required to compile.
- Use the engine required by the source. Use XeLaTeX or LuaLaTeX when `fontspec`, CJK, Devanagari, Arabic, or other Unicode font handling requires it.
- Keep the production README short and accurate.
- Compile the package after extraction in a clean temporary directory.
- If a journal rejects zip uploads, prepare individual source and figure files with compatible relative paths.

Run `scripts/audit_latex_project.py` for a non-destructive mechanical preflight. Compile and visually inspect the resulting PDF before calling the package ready.
