---
name: learn
description: 'Optionally analyze collections of durable Triggers: "learn from verdicts", "mine validation history".'
---
# Learn

Learn is an optional, off-path consumer of durable `verdict.v2` collections.
It may summarize recurring evidence and propose a candidate deterministic check
for later human or caller evaluation.

Learn does not run during RPI, validate a subject, alter a verdict, mutate a
plan, promote a rule, choose continuation, or mint lifecycle artifacts. Missing
Learn output never changes whether a candidate is valid.

When invoked, bind every observation to verdict and finding digests, distinguish
repeated objectives from repeated reviews of one objective, disclose the sample
size, and stop at advisory evidence.

Overweight failures: a `NOT_PROVEN` or `FAIL` verdict carries more teaching
value than a PASS, because it names a rule the loop lacked. Harvest kernels
from failed lanes first — the canonical example is the mutating-check
quarantine in `skills/validate/SKILL.md`, a durable rule minted from a
`NOT_PROVEN`-then-`PASS` verdict pair.

Prune for provenance decay: every cited artifact must still resolve — the
file exists or the verdict digest is present under `.agents/ao/verdicts/`. A
citation that no longer resolves gets pruned rather than paraphrased, and
confidence in a lesson that has not been reproduced since its source decayed
goes down, not sideways.

When the caller asks for a durable artifact, write the observations under
`.agents/scratch/learn/` and return the path; otherwise return them inline.
The write is advisory and TTL'd — it is never a source of record, and its
absence never changes whether a candidate is valid.
