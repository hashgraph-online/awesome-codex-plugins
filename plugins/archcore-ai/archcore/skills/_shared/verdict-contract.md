# Verdict Contract — Direction Labels for Document-Versus-Code Findings

Plugin runtime asset. Loaded by the `plan` skill for an `amend` claim
(`skills/_shared/delta-routing.md`) and by the `review` skill at the
`actualize.verdict` gate (`skills/_shared/tracks/actualize.md`) and the
`closeout.verify` gate (`skills/_shared/tracks/closeout.md`). This file
defines the shared verdict vocabulary; each consumer's own gates decide when
a finding arises.

## Verdicts

One verdict names one direction. Do not introduce synonyms.

- `spec-wrong` — the document is stale; the code, or the document's updated
  upstream, is the newer truth.
- `code-wrong` — the code violates a document whose content still stands,
  for example an `accepted` spec or rule.
- `ok` — the flagged pair matches on inspection; no change needed.

## Authority before a verdict

1. The executing skill MUST label a finding `spec-wrong` or `code-wrong` only
   after it resolves which side holds authority.
2. WHEN the code contradicts a clause of an accepted document, the executing
   skill MUST report an authority conflict and wait for the user's decision
   before any write.
3. WHEN the code extends an accepted document without contradicting any of
   its clauses, the executing skill MUST treat the finding as an update of
   that document's owner clause, not as a conflict.
4. The executing skill MUST NOT treat a newer commit date of the code as
   authority over an accepted document.

## Labeling rules

1. The executing skill MUST label every finding with exactly one verdict.
   Exception: an authority conflict under rule 2 above carries no verdict
   until the user decides.
2. Every `spec-wrong` finding MUST cite its evidence — the changed files,
   modification dates, or content markers that show the document is stale.
3. Every `code-wrong` finding MUST cite its evidence — the violating code
   and the document it violates.

## Consumer duties

1. WHEN the `plan` skill resolves an `amend` claim labeled `spec-wrong`, the
   `plan` skill MUST edit the covering `spec`.
2. WHILE resolving a `spec-wrong` entry, the `plan` skill MUST obtain the
   user's confirmation before the `spec` edit.
3. WHEN the `plan` skill resolves an `amend` claim labeled `code-wrong`, the
   `plan` skill MUST fix the code against the covering `spec`.
4. The actualize and closeout tracks MUST use these verdicts without
   redefinition.
5. A review-side track (`actualize`, `closeout`) MUST NOT edit a code file.
6. WHEN a review-side track labels a finding `code-wrong`, the executing
   skill MUST report the violating code and the governing document.
