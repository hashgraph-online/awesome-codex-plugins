---
name: learn
description: 'Optionally analyze collections of durable verdicts for recurring evidence after the critical path. Triggers: "learn from verdicts", "mine validation history".'
---
# Learn

Learn is an optional, off-path consumer of durable `verdict.v2` collections.
It may summarize recurring evidence and propose a candidate deterministic check
for later human or caller evaluation.

## Prompt

```text
Mine .agents/ao/verdicts/ for recurring patterns across the last 20
verdict.v2 records in agentops-wt/train2-c. I want candidate deterministic
checks for anything that shows up as a repeated NOT_PROVEN or FAIL cause,
with digests cited so I can trace each observation back.
```

## It's working if

Observable in the trace, without reading the prose:

- Every observation binds a `verdict.v2` digest and a finding id from
  `.agents/ao/verdicts/`.
- A `NOT_PROVEN` or `FAIL` verdict pair is harvested before a `PASS`-only
  pattern.
- A citation that no longer resolves under `.agents/ao/verdicts/` is
  pruned rather than paraphrased.
- Output written to `.agents/scratch/learn/` is labeled advisory and
  TTL'd, not a source of record.

## Contract

Learn does not run during RPI, validate a subject, alter a verdict, mutate a
plan, promote a rule, choose continuation, or mint lifecycle artifacts. Missing
Learn output never changes whether a candidate is valid.

When invoked, bind every observation to verdict and finding digests, distinguish
repeated objectives from repeated reviews of one objective, disclose the sample
size, and stop at advisory evidence.

Inspect informative failures first, but verdict color alone establishes neither
learning value nor a missing rule. Cite the live hypothesis falsified or the
uncertainty resolved, distinguish pre-existing discovery from introduced
regression, and retain unknown causes as unknown. Repetition may justify causal
examination; it does not prove that the design was wrong or require a new gate.
The mutating-check quarantine in `skills/validate/SKILL.md` is an example grounded
in a specific subject-mutation incident and a NOT_PROVEN-then-PASS pair.

Knowledge is revisable. Preserve evidence and provenance when retracting an
unsupported or stale belief; artifact accumulation is not a monotonic increase
in truth or utility. Negative, null, and contradictory results remain visible.

A repeated finding class may support a check proposal only when causal evidence
identifies a preventable defect and a concrete consumer needs that check. Name
the exact behavior the check would refuse and why existing checks missed it;
two sightings alone do not justify a gate. The proposal is advisory text for a
human or caller to weigh; Learn never edits a gate, registry, or check script,
and learning never changes a completed verdict or selects another experiment.

Prune for provenance decay: every cited artifact must still resolve — the
file exists or the verdict digest is present under `.agents/ao/verdicts/`. A
citation that no longer resolves gets pruned rather than paraphrased, and
confidence in a lesson that has not been reproduced since its source decayed
goes down, not sideways.

When the caller asks for a durable artifact, write the observations under
`.agents/scratch/learn/` and return the path; otherwise return them inline.
The write is advisory and TTL'd — it is never a source of record, and its
absence never changes whether a candidate is valid.
