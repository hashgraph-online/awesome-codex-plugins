---
name: research
description: "Answer one cited question on code, history, claims or patterns. Use when: asked how it works, why it changed, if a claim or done/shipped report holds, or a pattern warrants a rule."
practices:
- pragmatic-programmer
- ddd-bounded-context
- evidence-based-engineering
hexagonal_role: driving-adapter
consumes:
- research-question
- native-source-evidence
produces:
- research-report
- codebase-recon.v1
- pattern-mining.v1
- reality-check-report.v1
- goal-measurement-report
- native-status-snapshot
context_rel:
- kind: supplier-to
  with: plan
skill_api_version: 1
user-invocable: true
metadata:
  capabilities: [research, codebase_recon, pattern_mining, compare_claim_to_evidence, measure_declared_goals, report_native_status]
  effects: [write_research_report, write_recon_pack, write_pattern_evidence, write_advisory_gap_report, write_goal_snapshot, write_requested_rendered_spec]
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  dependencies: []
  triggers: ["holds up", "really done"]
output_contract: cited answer; findings.json for ordinary durable reports; validated codebase-recon.v1, pattern-mining.v1 or reality-check-report.v1 for selected evidence modes; per-item claim ledger with no verdict
---
# Research

Answer the caller's bounded question with cited evidence. Choose ordinary
investigation, claim checking, a claimed-state audit, decision lineage,
repository tracing or pattern evidence according to the question; these are
optional modes, not a sequence. A quick answer needs no report file.
[Plan](../plan/SKILL.md) owns unified discovery and resumption when the question
is part of shaping a change; return this cited answer to that existing intent
without restarting its interview or taking over caller choices.

## Evidence rules

- **One lineage counts once.** Copies, ports and repeated quotations of one
  upstream source are a single exemplar, however many files or reports carry
  them. Check provenance before counting instances as independent, and stop
  searching once new queries return only sources already read.
- **Separate the invariant from the incidental.** Align instances by their role
  in the behavior; name what must hold, what legitimately varies and what is
  incidental syntax. An instance missing the invariant is not an instance.
- **Recurrence does not earn a gate.** A blocking check needs a demonstrated
  cost of violation: an incident, defect or measured harm traced to the
  pattern's absence. Recommend the least committed useful shape: no action, a
  reference or checklist line, a template, a helper, and only then a gate.
- **Thin evidence stays a hypothesis.** Fewer than three independent exemplars,
  or no passing holdout, leaves a pattern a hypothesis; say what evidence would
  confirm or refute it.
- Keep observation, inference, contradiction and unknown separate. Every
  material claim cites evidence; a claim taken from a document or report cites
  a passage that asserts it, not one that only discusses the topic, else mark
  it unsupported. Say when a decisive claim rests on one source; agreement does
  not erase shared provenance.
- **A call is not the callee's behavior.** Seeing code call `retry`, `validate`
  or a service shows only that the call happens. Before a claim relies on what
  the callee guarantees (retried, atomic, idempotent, ordered, durable), read
  its implementation or tests, or an external service's published contract;
  otherwise mark the guarantee unknown in the claim itself, not in a later
  caveat.
- **A search that found nothing proves absence only if it could have matched.**
  Before saying something does not exist or is unused, check the search's exit
  status and error output, whether results were truncated, whether ignore rules
  or default filters skipped relevant paths (ignored, hidden, vendored or
  generated files), and that the intended ref or tree was searched rather than
  a stale index. Where cheap, confirm the same search finds a term known to be
  present. A failed or mis-scoped search is an unknown with its cause, not
  "none found". For "unused" or "nothing calls this", text search also misses
  re-exports, aliases, reflection, string-keyed dispatch, dependency injection,
  generated code and outside consumers; prefer the host's references-aware
  tool when it has one, and name which of these remain unchecked.

## Investigation

1. State the question and the decision it informs. Reuse the accepted scope and
   identify what evidence would answer it; do not expand the objective mid-search.
   Use the subject, range and sources the caller named. Report an empty range,
   a missing subject or an unreachable named source as such instead of
   answering about an adjacent one; name any substitute the caller allowed.
2. Inspect the smallest relevant sources and verify search hits against the
   actual source. External facts that change (versions, vendor behavior,
   standards) need current primary sources, through the host's web tools when
   available and permitted; otherwise mark the claim unknown and name the
   source that would settle it. Before a query leaves the host, strip host
   names, IP addresses, file paths, query fragments, account or customer
   identifiers and internal names, and search on the generic error class with
   the library and version; if no safe form remains, skip the lookup and say so.
   For how a third-party library, tool or service behaves here, answer from the
   version this repository resolves (lockfile, installed binary's version or
   vendored copy) and that version's source, tests or release notes; latest
   docs, web answers and recall are leads, so say when they describe another
   version. Before recommending an external API, SDK, auth scope or service,
   check deprecation, sunset and breaking-change notices for that version and
   state any, or say that status is unchecked.
3. Lead with the answer, then show evidence and remaining gaps. Each part of the
   question is answered or explicitly unknown with the searched scope disclosed.
   Before settling a consequential answer, look once for the strongest contrary
   evidence. When the caller asked for an explanation, write for their level in
   plain words and mark which reasons are documented, which are your inference
   and which are unknown.

Code claims cite the observed commit plus `file:line`. For uncommitted content,
state HEAD and the changed-file status; do not claim the working bytes can be
replayed from HEAD. Keep source identity and freshness visible. Search output,
CASS, MS and prior reports are leads, not authority or required phases. Use the
current agent by default; additional readers and runtimes require caller
selection or existing authorization.

For several supplied reports, retain each source's identifier, author/runtime
when known and revision/date. Compare claims as agreement, contradiction or
unknown while preserving their original evidence. Verify decisive claims at
their source and return one synthesis; do not launch recursive synthesis passes.

## Claim checking

To check whether a draft, report or answer is true, split it into atomic
claims a source could confirm or refute. A claim that work is done, shipped or
wired in is a [claimed-state audit](#claimed-state-audit). Opinions and
predictions are not checked; say so. Check first what would mislead most:
numbers, quotations, attributions, superlatives and the claims the conclusion
rests on. Recall from training is a lead, never the source.

- **Re-derive, do not re-read.** A claim produced from data (a query, a script,
  a repository count) is checked through a different path: another query, a
  different key or grouping, or the underlying files themselves. Re-running the
  producer repeats its mistake, and a report's own numbers are not evidence for
  that report.
- **Association is not authorship.** "X wrote, decided or caused Y" needs a
  statement or record of exactly that relation. Appearing in the same commit,
  meeting or document is weaker evidence; report it as such.
- Return each claim as supported, contradicted, unsupported or not checkable,
  with its citation and the path used. Corrections are proposals; editing the
  checked document belongs to [Doc](../doc/SKILL.md).

## Claimed-state audit

For a claim that work is done, shipped, fixed, working or wired in (an agent's
done report, a ticket summary, a changelog line, a status post), compare an
expected state with observable evidence, item by item. The named failure mode
is auditing only what the diff touched: a claimed item with no trace in the
evidence is a gap, not something to leave out of the report.

A request to check a stated claim, measure declared goals or report native
status selects this audit without another question. A bare "is it ready?" with
no claim and no settled purpose is ambiguous: ask once, by the shared
[advice or acceptance](../review/references/advice-or-acceptance.md) rule. This
audit is not acceptance and cannot substitute for
[Validate](../validate/SKILL.md)'s fresh, author-distinct judgment; if
acceptance is wanted, hand off and report a missing fresh reviewer as a gap.

1. Read the exact claim and its source, and split it into its separate items,
   including work that was never started.
2. Give each item its own disposition: **confirmed** (cite the evidence),
   **gap** (cite what is missing or contradicts it) or **unverifiable** (name
   the evidence that would settle it). Credit only what the evidence shows: a
   reported run without its output, behavior left to a default or another
   component, and a test that exercises code without asserting the claimed
   outcome are unverifiable, not confirmed. Do not resolve an untestable claim
   by assertion.
3. **Reachable from a live entry point.** Code that no live entry point (a
   route, command, job, handler or exported API that production invokes)
   reaches is not wired in, whatever its own tests show. For a claim that
   behavior is implemented, also search the code behind it for pretend
   implementations: constant or hard-coded results, TODO or not-implemented
   branches, sample data, or test doubles outside test code. Trace each hit to
   its callers before classifying it. A placeholder that a production path
   reaches makes the item a gap; a double used only by tests, or code nothing
   calls, does not.
4. **Delivery is reachability in current remote state.** A claim that work was
   pushed, merged, shipped or fixed in a named commit or pull request is
   settled by reachability, not by a local ref, push output or saved status;
   whether the content is still present at the target head and does what is
   claimed is checked as above. Pushed means reachable
   from the named remote branch, or from the pull request's current head in its
   own head repository, forks included. Merged means reachable from the target
   branch the claim names, otherwise the default branch head, or a pull request
   merged with that branch as its base; a merge into another base does not
   confirm it. Shipped means present in what the repository's release policy
   names (a tag, published release or deployment), read from that source. Where
   squash or rebase broke ancestry, compare the content with the target rather
   than assume an equivalent commit. Check a supplied SHA or pull request
   number's form before it reaches a command.
5. For a plan, compare proposed scope with the original goal; additions that
   lack authority are scope escalation the report cannot approve. Repeated
   measurements reuse the same question and criteria; a changed question starts
   a different comparison.
6. Return the ledger with checked and not-checked scope. Keep native tracker,
   Git, runtime, deterministic-check and semantic-judgment facts distinct.

```text
Claim: <the claim as stated, and where it came from>
| # | Stated item | Disposition | Evidence, or what would settle it |
|---|---|---|---|
| 1 | <item> | confirmed / gap / unverifiable | <file:line, command output, artifact> |
Checked: <what was inspected>. Not checked: <what was not>.
```

The ledger reports evidence; it carries no overall PASS, FAIL, verdict or
readiness call, even when every item is confirmed. Its durable form is under
[Output and boundaries](#output-and-boundaries).

### Health, goals and status

For "is this repository healthy" or "do the checks pass", run the project's
own read-only checks (declared in its instructions or CI configuration, or
found in its build files), preferring a `--check`, dry-run or verify variant,
and record where each came from. List any step that writes tracked files,
publishes, deploys or needs credentials as not run, with the reason. Run each
separately and keep going after a failure. Report each as passed, failed, not
run (tool unavailable) or not determined (output not captured), from its exit
status rather than parsed output, and name declared checks you did not run.
Fix nothing, and fold no results into one score that hides a failure.

Running `ao goals` against the declared goals source is in
[goals](references/goals.md); reading the evidence store with `ao status`, and
what a snapshot cannot show, is in [status](references/status.md). A recent
artifact timestamp proves evidence recency, not an active worker. Do not add,
remove, prioritize, migrate or repair goals, or turn a measurement gap into
assigned work.

## Adoption questions

For "should we adopt, replace or keep X" or "does advisory Y reach us", the
answer needs both sides. Ours: the current tool and a cited place it is used,
or a searched absence plus where X would plug in, and any earlier decision on
the same question. Theirs: a current primary source for each external fact the
answer rests on. A strong side never covers a missing one; then answer "not yet
answerable" and list what to inspect. Keeping the current tool or doing nothing
is a real option. Sourcing, ranking and the fit, license, cost-of-staying and
maintenance facts are in [adoption evidence](references/adoption-evidence.md).

## Decision lineage

For "why is it like this" or "how did this idea change", trace one decision or
idea through commits, ADRs, issues, reviews and prior reports into dated, cited
buckets: first appearance, clearest statement, current form, reversals,
contradictions (two claims that cannot both hold) and abandoned variants. An
empty bucket says what was searched; a supersession is not a contradiction; do
not smooth messy history into a tidy story. Before presenting a past reason as
binding, check that its cause still holds in the current tree or record; if
not, report that as evidence for reopening, leaving the call to its owner or
the caller.

## Repository tracing

For a repository model or audit, start from its declared entry points in docs,
build manifests or command help and verify them against executable paths.
Follow a relevant flow through entry, domain logic, integration and tests;
prefer a completed trace to a shallow directory inventory. Report an interrupted
trace at its exact file/line and explain what is missing. Choose a useful lens
such as persistence, authorization, CLI, build or test without requiring a sweep
of every lens. In any trace, a how-it-works answer included, say what each step
reads or changes and keep the error and edge branches the question depends on,
not only the success path. Source and tests establish behavior; a file name or
a claim in the conversation does not.

An inline investigation may use dirty working-tree evidence with explicit
limits; a selected durable `codebase-recon.v1` pack is commit-bound.

## Pattern evidence

For a recurring implementation shape, test whether the similarity represents a
reusable rule under the evidence rules above. Record replayable searches,
examined hits and exclusions, then report:

```text
exemplars: <file:line> per independent lineage; copies listed under their source
invariant: <what every exemplar shares and the behavior needs>
variation: <legitimate differences>; incidental: <syntax, names>
cost:      <demonstrated cost of violation, or "none found">
shape:     <no-action | reference-line | template | helper | gate> and why
outcome:   hypothesis | promote (three independent exemplars, passing holdout and back-application)
```

Research returns evidence; adoption remains an explicit caller decision.

## Output and boundaries

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows
it as "Base directory for this skill"; Codex lists this skill's SKILL.md path;
in an AgentOps source checkout it is `skills/research`. Replace `<skill-dir>`
with that absolute path before running a command. The working directory stays
the user's repository. If the host did not show where this skill is installed,
use the directory of the SKILL.md you read. If you cannot determine it, do not
guess a path or run a same-named script from the current repository; say the
bundled script is unavailable and check the artifact's fields by hand against
its format.

Return a cited answer directly unless a durable output was requested or the
selected mode requires one. To save a report, use the location the caller
named, else the repository's existing research or decision-notes location and
naming; with neither, return the answer and ask where to save it. Read the file
back and report its exact path. Each durable mode keeps its own format:

- **Ordinary report:** [findings.json](schemas/findings.json) allows only
  `topic`, `summary`, `findings` (each `area`, `observation`, `evidence` and
  optional `implications`), `checked`, `not_checked` and `schema_version: 1`.
  Multi-report synthesis adds `source_ledger` and `comparison` (`agreements`,
  `contradictions`, `unknowns`).
- **Claimed-state audit:** `reality-check-report.json` in the
  [reality-check-report.v1](schemas/reality-check-report.v1.schema.json) format,
  a name kept from the retired Reality Check skill. It holds `claim`; `coverage`,
  one row per stated item with `goal` (the item), `disposition` and `evidence`
  (required for confirmed and gap); and at least one `findings` entry with a
  `category` (confirmed, gap, incomplete-evidence or changed-assumption), a
  `statement` and cited `evidence`. When every item is unverifiable, record one
  incomplete-evidence finding that cites the searches. It has no verdict,
  readiness or PASS field. Check it with
  `bash "<skill-dir>/scripts/claim-audit/validate-output.sh" <report.json>`.
- **Repository tracing:** `codebase-recon.v1` by the
  [recon pack contract](references/codebase-recon/pack-contract.md), checked by
  `bash "<skill-dir>/scripts/codebase-recon/validate-output.sh" --repo-root <target> <recon.json>`.
- **Pattern evidence:** `pattern-mining.v1` by the
  [pattern pack contract](references/pattern-mining/pack-contract.md), checked by
  `bash "<skill-dir>/scripts/pattern-mining/validate-output.sh" <pattern.json>`.

Use only authorized sources and destinations. For restricted or mined episode
material, follow [Memory's access and storage boundary](../memory/SKILL.md).
Research selects no work, owns no merged context store, mutates no lifecycle
state and issues no semantic verdict. Beyond requested reports and packs, its
only output side effects are the documented goal snapshots and requested
report/spec writes of a claimed-state audit. The native caller owns implementation,
judgment and completion of the authorized outcome.
