# Private Style-Calibration Protocol

Use this protocol only when the user has provided a private Han Hu writing corpus or a local path to one. Do not create, upload, commit, or quote the corpus outside its authorized workspace.

## Locate and validate the corpus

1. Read the corpus path from the task or from the `HAN_HU_STYLE_CORPUS` environment variable. Do not assume a user-specific absolute path.
2. Require `calibration-profile.md` and `corpus-index.json`. Run `scripts/audit_style_calibration.py <corpus-root>` when available.
3. Treat each entry’s evidence status as binding. Prefer accepted or author-approved after-text. Use author-directed working text as a provisional exemplar and context-only material only for scope, claim ceilings, and process rules.

## Retrieve, draft, and audit

1. Identify the requested genre and rhetorical function: abstract, introduction, methods, results discussion, conclusion, review synthesis, figure caption, proposal, or reviewer response.
2. Retrieve two to four corpus entries matched to that function. Read only the selected excerpts and their rationale; do not load whole manuscripts merely to imitate phrasing.
3. Draft from the current project’s sources, data, figures, and citations. Examples control organization and prose choices, never the scientific content of the new work.
4. Run a separate style pass. Do not alter values, units, definitions, citations, evidence class, or claim ceiling without flagging the change.
5. Return a compact audit naming the exemplar IDs, their evidence status, any deliberate journal/project departure, and the smallest unresolved evidence need.

## Non-negotiable limits

- Do not present a Codex-generated revision as a Han Hu author edit without direct evidence.
- Do not treat a publication with multiple authors as evidence that every sentence is Han Hu’s personal wording.
- Do not use the corpus as an external training set or publish it in a public plugin, repository, issue, prompt gallery, or response.
- When no corpus is accessible, use [han-hu-research-style.md](han-hu-research-style.md) and state that exemplar retrieval was unavailable.
