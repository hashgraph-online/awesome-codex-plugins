---
name: research
description: 'Trace code or test a recurring pattern to answer one cited question. Use when: uncertainty needs evidence. Not for external feature teardowns; use reverse-engineer.'
---
# Research

Answer the caller's bounded question with cited evidence. Choose ordinary
investigation, repository tracing or pattern evidence according to the question;
these are optional modes, not a sequence. A quick answer needs no report file.

## Investigation

1. State the question and the decision it informs. Reuse the accepted scope and
   identify what evidence would answer it; do not expand the objective mid-search.
2. Inspect the smallest relevant sources. For changing external facts, use
   current primary sources. Verify search hits against the actual source.
3. Distinguish observation, inference, contradiction and unknown. Every material
   claim cites evidence; source agreement does not erase shared provenance.
4. Lead with the answer, then show evidence and remaining gaps. Each part of the
   question is answered or explicitly unknown with the searched scope disclosed.

Code claims cite the observed commit plus `file:line`. For uncommitted content,
state HEAD and the changed-file status; do not claim the working bytes can be
replayed from HEAD. Keep source identity and freshness visible. Search output,
CASS, MS and prior reports are leads, not authority or required phases. Use the
current agent by default; additional readers and runtimes require caller
selection or existing authorization.

For several supplied reports, retain each source's identifier, author/runtime
when known and revision/date. Compare claims as agreement, contradiction or
unknown while preserving their original evidence. Repeated quotations of one
upstream source are not independent corroboration. Verify decisive claims at
their source and return one synthesis; do not launch recursive synthesis passes.

## Repository tracing

For a repository model or audit, start from its declared entry points in docs,
build manifests or command help and verify them against executable paths.
Follow a relevant flow through entry, domain logic, integration and tests;
prefer a completed trace to a shallow directory inventory. Report an interrupted
trace at its exact file/line and explain what is missing. Choose a useful lens
such as persistence, authorization, CLI, build or test without requiring a sweep
of every lens.

An inline investigation may use dirty working-tree evidence with explicit limits.
When a durable `codebase-recon.v1` pack is selected, its stricter contract applies:

- Write `codebase-recon.json` and a cited `codebase-recon.md` companion at the
  caller's chosen location, default `.agents/scratch/codebase-recon/<run-id>/`.
  Keep mental model, bounded audit, pattern evidence and synthesis distinct.
- Bind the exact current full commit OID, at least one complete baseline flow,
  claims with kind, confidence and evidence, and inspected/uninspected scope. Fact and inference citations
  resolve to repository-relative regular files at that commit; the companion
  report includes line references. Unknowns remain explicit.
- The manifest `report` names the companion and its lowercase SHA-256. The
  companion has one `<!-- codebase-recon-report.v1 -->` marker and
  `manifest_commit`, `manifest_mode`, `flows_sha256`, `claims_sha256`, and
  `coverage_sha256` markers; section digests hash the `jq -cS` output for each
  section, including its trailing newline.
- Discover validated priors with
  `skills/research/scripts/codebase-recon/validate-output.sh --repo-root <target> --discover-priors`.
  Prefer a verified delta when it answers the request. Delta evidence needs a
  valid ancestor chain, `baseline_verified: true` and the exact changed paths
  between the prior and current commits; do not relabel a directory scan as delta.
- Run `skills/research/scripts/codebase-recon/validate-output.sh --repo-root
  <target> <recon.json>` before handoff. It checks both artifacts and rechecks
  their identities, HEAD and source state; dirty source outside `.agents/` cannot
  satisfy this commit-bound pack. Return a validation failure without disguising
  it as a completed recon pack.

Preserve earlier `.agents/recon/<run-id>/` packs and their exact cited identities.
Prior discovery checks both legacy and current roots; never move or delete old
proof to match a new layout. See the [recon scenarios](references/codebase-recon/codebase-recon.feature).

## Pattern evidence

For a recurring implementation shape, test whether the similarity represents a
reusable rule. Record replayable searches, examined hits and exclusions. Align
independent implementations by their role in the behavior, then separate required
invariants, legitimate variation and incidental syntax. Copies of one lineage
do not count as independent evidence.

A `pattern-mining.v1` promotion needs at least three distinct anchored exemplars,
a candidate formed before inspecting a separate holdout, a passing holdout and
successful back-application of every refinement to the original exemplars.
Every invariant needs supporting alignment. Otherwise preserve the result as
`outcome: hypothesis` with `route: no-action`; do not package weak evidence as a rule.

For this selected durable mode, write `pattern-mining.json` to
`.agents/scratch/pattern-mining/<run-id>/` or an authorized caller location and
run `skills/research/scripts/pattern-mining/validate-output.sh <pattern.json>`.
Preserve the schema's `outcome`, `exemplars`, `invariants`, `variations`,
`incidental`, `holdout`, `back_application` and `route` fields. The compatibility route
value `operationalize` on a valid promotion refers to
[Skill Builder's distillation mode](../skill-builder/SKILL.md#distill-expertise);
it is not a retired skill invocation or automatic dispatch.

Recommend the least committed useful shape: no action, a reference/checklist
line, a template, helper or gate. A gate needs demonstrated cost of violation,
not merely recurrence. Research returns evidence; adoption remains an explicit
caller decision. See [pattern scenarios](references/pattern-mining/pattern-mining.feature).

## Output and boundaries

Return a cited answer directly unless a durable output was requested or the
selected evidence contract requires one. Ordinary durable reports follow
[findings.json](schemas/findings.json): question, scope, answer, evidence,
contradictions, unknowns, checked and unchecked areas. Multi-report synthesis
also retains `source_ledger` and `comparison`. Selected recon and pattern modes
retain their own validated formats instead of forcing them into this schema.

Use only authorized sources and destinations. For restricted or mined episode
material, follow [Memory's access and storage boundary](../memory/SKILL.md).
Research selects no work, owns no merged context store, mutates no lifecycle
state and issues no semantic verdict. The native caller owns implementation,
judgment and completion of the authorized outcome.
