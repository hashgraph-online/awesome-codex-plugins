# Actualize Track — Diff-Scoped Drift Detection and Confirmed Fixes

Plugin runtime asset. Loaded by the `review` skill — this track's primary
executor — when a branch review, a staleness signal, or drift-shaped wording ("are any
docs out of date?", "check if documentation matches the code", "audit all docs") routes here.
Gate record shape, state rules, and execution rules:
`skills/_shared/gate-contract.md`. Interview mechanics and question budget:
`skills/_shared/elicitation-contract.md`. Verdict vocabulary:
`skills/_shared/verdict-contract.md`. Each `budget` knob caps its gate inside the
5-question per-invocation ceiling of `skills/_shared/elicitation-contract.md`.

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
as the staleness precondition on a claim's owner.

## Detection procedure

The `actualize.verdict` gate runs these checks over every document in scope.
The read-only `archcore-auditor` agent MAY run the checks and collect
findings; the main thread confirms every label with the user — a subagent
MUST NOT interview, per `skills/_shared/elicitation-contract.md`.

Gather once, in parallel: `list_documents` (scope filter applied),
`list_relations`, and the scoped diff from `actualize.scope`. If git is
unavailable, skip the code-drift check and run cascade and temporal only.

1. **Code drift.** IF the scoped diff is empty, THEN skip this check. For
   each scoped document: read it with `get_document`;
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
4. **Mechanical facts.** Settle the claims a lookup can settle, once per
   review and independent of the diff, over the scope's documents (no
   argument: every document):

   1. IF the executor has a shell, THEN run
      `"${CLAUDE_SKILL_DIR:-<absolute dir of the executing SKILL.md>}/../../bin/cli-gte" 0.15.7`.
      Do not compare versions in prose.
   2. IF the result is `yes`, THEN run `archcore check [<scope document or directory> ...]`.
   3. IF the result is `no` or `__NO_CLI__`, THEN run
      `"${CLAUDE_SKILL_DIR:-<absolute dir of the executing SKILL.md>}/../../bin/check-references" "<project root>" [<scope path> ...]`,
      read its `unresolved` and `line-anchor` lines as `unresolved_path` and
      `line_anchor`, and report once: "The full corpus check requires Archcore
      CLI 0.15.7; checked paths and line anchors only."
   4. IF the executor has no shell, THEN use the output the calling skill
      supplied; IF there is none, THEN report the check as not run.
   5. Decide each finding by the table below, in the order the check gives —
      a live claim before history, an `accepted` document before a draft, a
      `normative` line before prose — from the finding's `line`. The check
      already searched every scanned file: do not search the code again for a
      `missing_identifier`, `missing_string`, or `unresolved_path`, and open
      the document only when `line` alone does not settle the claim. Do not
      read every document to find more findings.

   | Kind | Verdict |
   |---|---|
   | `unresolved_path` | `ok` for a `plan`, `rfc`, `idea`, or `prd` naming a file to create, a line that says it is historical, or another repository's path; a moved path (`moved to`) is `spec-wrong` with the new path; `glob-matches-nothing` is `spec-wrong` with a glob that matches; otherwise `spec-wrong` |
   | `missing_identifier`, `missing_string` | `spec-wrong` when the line claims this project has, calls, or shows the thing — a platform or third-party API the project MUST call and never calls included; `ok` when it names a rejected alternative, sample data, or an API the line only compares against. With `historical: true` the line narrates a removal: a cut candidate, not drift |
   | `draft_cited_by_code` | a shipped-draft candidate; check 6 judges these documents first |
   | `duplicate_text` | read both lines: values that disagree are a cross-document conflict, `spec-wrong` on the side the code contradicts; the same statement twice is a cut candidate in the document that does not own it |
   | `restated_code` | a cut candidate |
   | `dangling_code_citation`, `line_anchor` | observations |

   6. Report every finding on an `accepted` document that is not
      `historical`, and every `draft_cited_by_code` document by name: one line
      with its kind, document, subject, and verdict, an `ok` included. Group
      the other findings by kind with counts.
   7. Name each kind under `skipped` as not checked. Report each `omitted`
      count — the findings past the cap of 40 per kind — as it is; never
      extrapolate.
5. **Cut test.** A cut candidate leaves the document when its every fact is
   `code-says` in the sense of `skills/_shared/tracks/describe.md` (describe
   rule 2): a file list, a prop or field list, a signature, a step-by-step walk
   through code, a changelog line, a removal narrative. It stays when it
   carries a `code-cannot-say` fact: a reason, a rejected alternative, a
   constraint no test or linter enforces, production knowledge, a contract
   clause no test covers, or a graded obligation a `rule` or `spec` states.
   Cut only the code-says part, never the whole document for one line.
6. **Shipped draft.** For each `draft` `adr`, `spec`, `rule`, `doc`, or
   `guide` in scope that the current branch did not create or change, verify
   its sampled claims (Deep check 1 selection). Flag it `spec-wrong` when at
   least one claim verified, none failed, no other check flagged the
   document, and nothing supersedes it — no `supersedes` edge targets it and
   its body does not say it is superseded, even in part. A `plan` belongs to the closeout track; an `idea`, `prd`, or
   `rfc` records intent, not shipped state. A draft the branch created or
   changed is not a finding: the closeout track offers its acceptance, and
   the `review` skill names `/archcore:review close out <feature>` when no `plan`
   matched. Age alone never flags it. A draft that carries an
   `archcore:track` state block is unfinished work, never a shipped draft.
7. **Hung plans.** A `plan` is a work order, not canon, and the closeout
   track removes only a plan the branch matched. For every other `plan` in
   scope, read it, take its last change from `git log -1 --format=%aI`, and
   compare its tasks and `## Declared Delta` paths against the default branch
   resolved per `skills/_shared/branch-state.md`. Flag it:
   - `shipped` — every task is present on the default branch and nothing
     remains open; cite the commits or paths that fulfil it.
   - `abandoned` — last changed more than 60 days ago [assumption] and no path
     it names changed on the default branch since; cite the date and the
     paths checked.
   A plan with open tasks and recent activity on its paths, or one carrying
   an `archcore:track` state block, is `ok`. `git log` on the plan file only
   — never read every document to find plans.

**Deep checks.** WHEN the request asks for a full documentation audit ("audit
all docs", "full audit", "deep review"), also run these, within one budget:
at most 20 documents and at most 3 claims per document. Choose `accepted`
`rule`, `cpat`, and `spec` documents first, since they bind the code; fill the
rest in proportion to the document count of each type.

1. **Claim sampling.** The corpus check already settled paths, names, and
   quoted strings; sample what it cannot settle. In each chosen document,
   take up to 3 checkable claims, in this order of preference: a prohibition
   or an exclusive ownership ("MUST NOT", "only X may"), which one search for
   the forbidden call or the other writer can refute; a literal value such as
   a version, a limit, a TTL, a key list, or a route; then a stated behavior.
   A claim is one sentence or one table row that states one fact the code can
   confirm. Verify each against the code. A claim the document pins to a revision is checked at
   that revision. A claim about another repository, a past event, or a
   result that needs a tool re-run is unverifiable, not failed. Each failed claim is a drift finding. Report held, failed, and
   unverifiable counts per type with the sample size; the share describes the
   sample, not the corpus.
2. **Cross-document conflict.** For each of these subjects — runtime and
   framework versions, the presence of a dependency or tool, timeouts and
   TTLs, cookie lifetimes, size and count limits, ports — search the scope for the documents that state a value
   (`search_documents` or `Grep`), and compare the values with each other and
   with the code. Label each document whose value disagrees with the code
   `spec-wrong`; IF the code matches none of them, THEN label all of them
   `spec-wrong`. A value that one document alone states and the code
   contradicts counts too. Add any conflict met while reading the sampled
   documents.
3. **Type fitness.** Note content that another type owns, per the shared
   content-kind ownership rule: graded obligations, in any language, inside a
   `doc`, `adr`, or `plan`; a decision with rejected alternatives inside a
   `doc` or `spec`; a numbered runbook inside a `rule`; a requirement only
   inside an HTML comment (`skills/_shared/precision-rules.md` Rule 12). Each
   is an observation.
4. **Relation candidates.** Apply the body signals and the dense-`related`
   shape from `skills/_shared/relation-authoring.md`. Each candidate is an
   observation with its outcome.

WHEN the budget or the agent's turn limit stops a check, report how much of
the scope it covered and stop; never extrapolate the rest.

Label every drift finding — checks 1 to 4 and 6, a failed claim from Deep
check 1, and Deep check 2 — with
exactly one verdict, `spec-wrong`, `code-wrong`, or `ok`, per the
definitions in `skills/_shared/verdict-contract.md`. Track mapping: cascade
and temporal findings that need a document change land on `spec-wrong`.
[assumption] The source protocol scored severity (critical / cascade /
temporal), not direction; the direction split is this track's mapping.
Observations — line anchors, dangling code citations, the sampled claim
counts, type fitness, and relation candidates — carry no verdict and do not
enter the fix budget. A cut candidate that passes the cut test is a `cut`
line in the fix batch.

## Fix forms

Offer every fix in one batch: one line per document with each proposed change
(the verdict, the edit or the cut, the evidence), and one confirmation for the
list, recommended answer "apply all"; the user strikes the lines to keep as
they are. A status change to `accepted` names the document in its own line, so
striking it keeps the draft. The forms per finding:

- Code drift, `spec-wrong`: read the current code; propose the document
  update that matches it. For an `adr` whose decision the code no longer
  follows, propose a new decision through `/archcore:document <decision>`
  that supersedes it; correct a path or a name in place.
- Cascade, `spec-wrong`: read the source and its updated target; identify
  discrepancies; propose the reconciling update.
- Temporal, `spec-wrong`: propose a status change or TODO-marker removal via
  `update_document`; for an `rfc`, name `/archcore:document <rfc title>` to
  resolve it instead of a status change; offer the removal of a long-stale
  draft as a line of the batch, and call `remove_document` after the batch
  confirmation.
  [assumption] Removal derives from the source report's "consider accepting
  or removing" guidance for long-stale drafts; the source fix flow itself
  used only `update_document`.
- Mechanical facts, `spec-wrong`: propose the new path or name when the check
  or one search finds it; otherwise propose rewriting the claim against the
  code that replaced it, or removing it.
- Cut: remove the code-says part and keep the rest; replace a removed list
  with one `@path` when the reader needs the location.
- Shipped draft, `spec-wrong`: propose `accepted`; apply it only after the
  user accepts that document by name.
- Hung plans, `spec-wrong`: one line per plan in the same batch (filename,
  `shipped` or `abandoned`, the evidence), recommended answer "remove". Call
  `remove_document` per remaining plan and report each with the commit that
  still carries the file; name an uncommitted plan as unrecoverable before
  asking. Residue a `shipped` plan still carries — an open decision, a
  repeated procedure — goes in its line as a note; the batch creates no
  document.
- Cross-document conflict and failed claim, `spec-wrong`: propose the edit
  that matches the code.
- Observations: list them after the verdicts. Offer a fix only when the user
  asks — for a line anchor, remove the number and keep the path, naming a
  symbol only when the document's own text names it; for type fitness,
  propose moving the content to a document of the owning type.
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
  - blocking: every drift finding carries exactly one verdict: `spec-wrong`, `code-wrong`, or `ok`; observations carry none.
  - blocking: every `spec-wrong` and `code-wrong` finding cites its evidence — changed files, modification dates, or content markers.
  - advisory: the report groups findings by verdict and ends with a one-line count summary.
- Next: `actualize.fix` when at least one finding is `spec-wrong` or `code-wrong`; otherwise exit with "All documents appear current. No staleness detected."

### gate: actualize.fix

- Purpose: Apply the user-confirmed fix batch — `spec-wrong` fixes, cuts, hung-plan removals; report `code-wrong` findings without touching code.
- Entry conditions:
  - skip_when: no finding is labeled `spec-wrong` and no cut passed the cut test — report the `code-wrong` and `ok` findings and exit the track.
  - `actualize.verdict` passed its blocking exit checks.
- Elicitation knobs:
  - trigger: a `spec-wrong` finding awaits its fix confirmation.
  - taxonomy: Terminology & Consistency, Misc / Placeholders from `skills/_shared/coverage-taxonomy.md`. [assumption]
  - budget: 1 — the whole fix batch, hung plans and cuts included, is one confirmation; a fix the user strikes is declined, not asked again.
- Produces: none — the gate updates existing documents via `update_document`; it creates no document.
- Exit checks:
  - blocking: every `update_document` and `remove_document` call followed the batch confirmation and applies a line the user did not strike.
  - blocking: the executing skill modified no code file.
  - advisory: every `code-wrong` finding appears in the final report with its evidence.
- Next: exit — report applied fixes, declined fixes, and `code-wrong` findings.
