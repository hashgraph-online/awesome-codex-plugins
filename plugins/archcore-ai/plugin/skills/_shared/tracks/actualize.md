# Actualize Track — Diff-Scoped Drift Detection and Confirmed Fixes

Plugin runtime asset. Loaded by the `review` skill — this track's primary
executor — when `/archcore:review --drift` or drift-shaped wording ("are any
docs out of date?", "check if documentation matches the code") routes here.
Gate record shape, state rules, and execution rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question budget:
`skills/_shared/elicitation-contract.md`. Verdict vocabulary:
`skills/_shared/verdict-contract.md`. Each `budget` knob is the per-gate
maximum, reached only in expert invocation; in auto mode every question draws
from the shared per-invocation ceiling in `skills/_shared/elicitation-contract.md`.

## Track state

[assumption] This track produces no draft artifact, so no `archcore:track`
state block persists between invocations. An interrupted run restarts at
`actualize.scope`; the executing skill MUST NOT re-ask a question or
confirmation already answered earlier in the same invocation. Accepted
answers and confirmations persist only in the running report; the
draft-artifact write-back in `skills/_shared/elicitation-contract.md` does
not apply — the executing skill MUST NOT create a draft artifact to hold
clarifications on this track.

## Callable mode

WHEN the calling skill pre-fills the scope — a zone's documents and paths —
the executing skill runs `actualize.scope` question-free under its
skip_when. The conductor (`skills/_shared/delta-routing.md`) uses this mode
as the staleness precondition on a touched zone.

## Detection procedure

The `actualize.verdict` gate runs these checks over every document in scope.
The read-only `archcore-auditor` agent MAY run the checks and collect
findings; the main thread confirms every label with the user — a subagent
MUST NOT interview, per `skills/_shared/elicitation-contract.md`.

Gather once, in parallel: `list_documents` (scope filter applied),
`list_relations`, and the scoped diff from `actualize.scope`. If git is
unavailable, skip the code-drift check and run cascade and temporal only.

1. **Code drift.** For each scoped document: read it with `get_document`;
   extract file and directory references from the content (paths such as
   `src/`, `lib/`, function names, module names); flag the document when a
   referenced path appears in the scoped diff's changed files. Cite the
   specific changed files. [assumption] The source compared changes since
   the document's last modification (diff from the last doc commit, plus
   `git log --oneline -20` for recent activity); this track substitutes the
   branch-scoped diff from `actualize.scope`, so a document already updated
   after the code change within the branch may be flagged and resolves to
   `ok` on inspection.
2. **Cascade.** From the relation graph, find source documents that name a
   scoped document as the target of `implements`, `depends_on`, or
   `extends`. Compare `git log -1 --format=%aI -- .archcore/<source>`
   against the same command for the target. Flag the source when the target
   was modified after it.
3. **Temporal.** Flag: `draft` documents whose last git modification is more
   than 30 days old; `accepted` documents containing TODO, FIXME, or TBD
   markers; plans whose phase descriptions reference past dates; `rejected`
   documents still targeted by active `implements` or `depends_on` relations.

Label every finding with exactly one verdict — `spec-wrong`, `code-wrong`,
or `ok` — per the definitions in `skills/_shared/verdict-contract.md`. Track
mapping: cascade and temporal findings that need a document change land on
`spec-wrong`. [assumption] The source protocol scored severity (critical /
cascade / temporal), not direction; the direction split is this track's
mapping.

## Fix forms

Offer fixes one document at a time, in the source's forms:

- Code drift, `spec-wrong`: read the current code; propose the document
  update that matches it.
- Cascade, `spec-wrong`: read the source and its updated target; identify
  discrepancies; propose the reconciling update.
- Temporal, `spec-wrong`: propose a status change or TODO-marker removal via
  `update_document`; when the user chooses removal of a long-stale draft,
  use `remove_document` under the same per-document confirmation.
  [assumption] Removal derives from the source report's "consider accepting
  or removing" guidance for long-stale drafts; the source fix flow itself
  used only `update_document`.
- Any `code-wrong`: report the violating code and the governing document.
  The executing skill MUST NOT edit code on this track.

## Gates

### gate: actualize.scope

- Purpose: Fix the diff to check — the document-versus-code pairs the track judges.
- Entry conditions:
  - skip_when: the `review` skill pre-filled the scope with a `branch-state` output block per `skills/_shared/branch-state.md`, or the request names an explicit path or topic.
  - The branch work boundary resolves per `skills/_shared/branch-state.md`.
- Elicitation knobs:
  - trigger: the branch-state procedure yields a sentinel whose caller response requests an explicit path or topic.
  - taxonomy: Functional Scope & Behavior from `skills/_shared/coverage-taxonomy.md`. [assumption]
  - budget: 1 [assumption] — the source flow scoped from arguments without questions; one question covers the sentinel fallback.
- Produces: none — the scope (diff plus matched documents) is stated in the running report.
- Exit checks:
  - blocking: the recorded scope names either a `branch-state` output block or an explicit path or topic.
  - advisory: at least one `.archcore/` document references a path inside the scoped diff.
- Next: `actualize.verdict`.

### gate: actualize.verdict

- Purpose: Run the detection procedure and label every finding `spec-wrong`, `code-wrong`, or `ok`.
- Entry conditions:
  - skip_when: zero documents fall in scope — report "no documents in scope; no drift detected" and exit the track.
  - `actualize.scope` passed its blocking exit check.
- Elicitation knobs:
  - trigger: the evidence for a finding supports both `spec-wrong` and `code-wrong`.
  - taxonomy: Functional Scope & Behavior, Misc / Placeholders from `skills/_shared/coverage-taxonomy.md`. [assumption]
  - budget: 2 [assumption] — derived from the source's per-finding confirmation flow.
- Produces: none — findings live in the report presented to the user.
- Exit checks:
  - blocking: every finding carries exactly one verdict: `spec-wrong`, `code-wrong`, or `ok`.
  - blocking: every `spec-wrong` and `code-wrong` finding cites its evidence — changed files, modification dates, or content markers.
  - advisory: the report groups findings by verdict and ends with a one-line count summary.
- Next: `actualize.fix` when at least one finding is `spec-wrong` or `code-wrong`; otherwise exit with "All documents appear current. No staleness detected."

### gate: actualize.fix

- Purpose: Apply user-confirmed document fixes for `spec-wrong` findings; report `code-wrong` findings without touching code.
- Entry conditions:
  - skip_when: no finding is labeled `spec-wrong` — report the `code-wrong` and `ok` findings and exit the track.
  - `actualize.verdict` passed its blocking exit checks.
- Elicitation knobs:
  - trigger: a `spec-wrong` finding awaits its fix confirmation.
  - taxonomy: Terminology & Consistency, Misc / Placeholders from `skills/_shared/coverage-taxonomy.md`. [assumption]
  - budget: 1 question per document carrying a `spec-wrong` finding [assumption] — the source rule is "always confirm each fix with the user before applying, one document at a time"; the per-gate maximum equals the count of such documents.
- Produces: none — the gate updates existing documents via `update_document`; it creates no document.
- Exit checks:
  - blocking: every `update_document` call was preceded by the user's confirmation of that document's fix.
  - blocking: the executing skill modified no code file.
  - advisory: every `code-wrong` finding appears in the final report with its evidence.
- Next: exit — report applied fixes, declined fixes, and `code-wrong` findings.
