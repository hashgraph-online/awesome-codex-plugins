---
name: research
description: 'Answer one cited question: how code works, or whether a repeated pattern deserves a rule. Use when: asked how, why, or whether to enforce a pattern.'
practices:
- pragmatic-programmer
- ddd-bounded-context
hexagonal_role: driving-adapter
consumes:
- research-question
produces:
- research-report
- codebase-recon.v1
- pattern-mining.v1
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  capabilities: [research, codebase_recon, pattern_mining]
  effects: [write_research_report, write_recon_pack, write_pattern_evidence]
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  dependencies: []
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
output_contract: cited answer; findings.json for ordinary durable reports; validated codebase-recon.v1 or pattern-mining.v1 for selected evidence modes
---
# Research

Answer the caller's bounded question with cited evidence. Choose ordinary
investigation, repository tracing or pattern evidence according to the question;
these are optional modes, not a sequence. A quick answer needs no report file.
[Plan](../plan/SKILL.md) owns unified discovery and resumption when the question
is part of shaping a change; return this cited answer to that existing intent
without restarting its interview or taking over caller choices.

## Evidence rules

- **One lineage counts once.** Copies, ports and repeated quotations of one
  upstream source are a single exemplar, however many files or reports carry
  them. Check provenance before counting instances as independent.
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
  material claim cites evidence; source agreement does not erase shared provenance.

## Investigation

1. State the question and the decision it informs. Reuse the accepted scope and
   identify what evidence would answer it; do not expand the objective mid-search.
2. Inspect the smallest relevant sources and verify search hits against the
   actual source. External facts that change (versions, vendor behavior,
   standards) need current primary sources. This skill pre-approves only local
   tools: use the host's web tools when available and permitted; otherwise mark
   the external claim unknown and name the source that would settle it.
3. Lead with the answer, then show evidence and remaining gaps. Each part of the
   question is answered or explicitly unknown with the searched scope disclosed.

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

## Repository tracing

For a repository model or audit, start from its declared entry points in docs,
build manifests or command help and verify them against executable paths.
Follow a relevant flow through entry, domain logic, integration and tests;
prefer a completed trace to a shallow directory inventory. Report an interrupted
trace at its exact file/line and explain what is missing. Choose a useful lens
such as persistence, authorization, CLI, build or test without requiring a sweep
of every lens.

An inline investigation may use dirty working-tree evidence with explicit
limits. A selected durable `codebase-recon.v1` pack is commit-bound and follows
the [recon pack contract](references/codebase-recon/pack-contract.md), checked by
`skills/research/scripts/codebase-recon/validate-output.sh`.

## Pattern evidence

For a recurring implementation shape, test whether the similarity represents a
reusable rule under the evidence rules above. Record replayable searches,
examined hits and exclusions, then report:

```text
exemplars: <file:line> per independent lineage; copies listed under their source
invariant: <what every exemplar shares and the behavior needs>
variation: <legitimate differences>; incidental: <syntax, names>
cost:      <demonstrated cost of violation, or "none found">
shape:     <no action | reference line | template | helper | gate> and why
outcome:   hypothesis | promote (three independent exemplars, passing holdout and back-application)
```

A selected durable `pattern-mining.v1` record follows the
[pattern pack contract](references/pattern-mining/pack-contract.md), checked by
`skills/research/scripts/pattern-mining/validate-output.sh`. Research returns
evidence; adoption remains an explicit caller decision.

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
