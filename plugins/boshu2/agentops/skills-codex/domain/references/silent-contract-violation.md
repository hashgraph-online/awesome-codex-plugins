---
name: Silent Contract Violation
kind: anti-pattern
status: draft
see-also: [anti-pattern, slice, citation]
---
# Silent Contract Violation

A failure mode of tool-use agents where generated code **runs to completion,
raises no exception, and is still wrong** — so execution-based feedback (tests,
exit codes, CI green) cannot see it. The failure the verification membrane
exists to catch.

## Definition

An agent composes calls to tools/skills and the program executes "successfully,"
but a *contract* between calls was violated invisibly. Four contract categories
(adopted from RubricRefine, Anduril, arxiv 2605.09730v3) name where the violation
lands — and are the `category` enum on a `verdict.v1` finding:

- **tool-choice** — the wrong tool/skill was routed for the task.
- **output-contract** — the produced artifact's shape does not match the declared
  `output_contract` / `produces`.
- **call-signature** — a call's inputs do not satisfy the callee's declared
  `consumes`.
- **data-provenance** — a call consumes an argument no upstream step produced
  (hallucinated or orphaned input).

## Signature

Green tests, zero raised exceptions, a clean exit — yet wrong routing, a
mismatched output shape, or an argument with no real source. The tell is that
*nothing failed loudly*; the defect is in the seams between calls, not inside any
one call.

## Cost

The most expensive class of failure to catch late: it survives every
execution-based gate and only surfaces downstream as corrupt data, a wrong action
already taken (especially in stateful/expensive environments where retry is
unsafe), or a confidently-wrong result a human trusts because "it ran."

## Cause

Verification that fires only *after* execution, plus reliance on exceptions as
the failure signal. The contracts exist (every `SKILL.md` declares
`consumes`/`produces`/`output_contract`) but nothing scores a plan against them
*before* dispatch. Unstructured self-critique misses it; structured,
registry-conditioned contract checks catch it.

## Refusal

When composing or reviewing a multi-step tool/skill plan, do **not** treat
"it ran without error" as evidence of correctness. Score the plan against the
four contract categories *before* the expensive/stateful action — a
pre-execution contract gate — and record violations as `verdict.v1` findings
with the matching `category`. Single-step calls are exempt (the failure mode is
inter-tool; see RubricRefine's flat single-step result).

## When to use

- Reviewing a Workflow script, `rpi`/`crank` wave, or any composed tool plan
  before it spends tokens or takes a live action.
- Triaging "it passed but produced the wrong thing" reports — name the category
  rather than re-describing the symptom.

## What it is not

- Not a runtime crash or a raised exception (those are caught by execution).
- Not a style/quality nit — it is a *contract* violation between calls.
- Not a substitute for the author≠judge independence invariant; the
  pre-execution check is structured self-grade, a cheaper inner rung beneath
  cross-model verification, never a replacement for it.

## Incident citation

- `bd` epic **ag-5elx** (RubricRefine integration) / bead **ag-twl8** — this
  entry and the `verdict.v1` `category` enum were added together so the
  membrane has a name for the run-clean-but-wrong class it is built to catch.

## See also

- `anti-pattern.md` — the shape this Entry follows
- `slice.md` — what a Silent Contract Violation corrupts when it triggers
- `citation.md` — how this anti-pattern is applied during a Slice
