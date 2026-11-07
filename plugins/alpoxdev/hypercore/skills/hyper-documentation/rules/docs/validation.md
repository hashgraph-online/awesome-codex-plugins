# Validation Rules for Hyper Docs

**Purpose**: Make completion claims evidence-backed instead of stylistic opinions.

## 1. Completion Contract

Every completion records:

```text
Claim → Risk → Evidence → Verification → Result → Caveat
```

`Result` is an inspected outcome, not a confidence statement. Decide `ship`, `iterate`, `caveated ship`, or `block`; never hide skipped checks, failed guards, or residual risk.

## 2. Risk Depth and Scope

Classify each material claim before selecting checks:

| Depth | Use when | Minimum evidence and gate |
|---|---|---|
| Low | Local wording or formatting with no behavioral, source, or side-effect change | Readback plus structural check |
| Medium | Workflow, instruction, link, schema, or portability behavior changes | Representative scenario, explicit oracle, and inspected result |
| High | External/current claims, tools, subagents, safety boundaries, consequential actions, or bounded loops | Normal, missing-capability/context, boundary, adversarial, and regression scenarios; output and trajectory checks |
| Critical | Production, destructive, credentialed, publication, deployment, or irreversible effects | Explicit authority, precondition/approval gate, independent evidence, and block on uncertainty |

For bulk or “all X” requests, search/glob the full candidate set, record include/exclude criteria, add or justify new candidates, rescan before completion, and report intentional exclusions.

A non-deterministic claim is measured over repeated trials, and the record states the trials per case, the per-case rate, and an interval. A pass/fail from one run is reported as an anecdote, not as evidence.

Reject future source dates. Do not change `last_verified_at` or equivalent verification dates unless actually rechecked.

## 3. Evaluation Contract

For every medium-or-higher-risk claim, define:

| Element | Required meaning |
|---|---|
| Scenario | Input, context, capabilities, and relevant failure or adversarial condition |
| Oracle | Observable required and forbidden behavior; not self-grading |
| Runner | Who/what executes the scenario and with what capability limits |
| Judge | Deterministic check, qualified reviewer, or stated rubric that evaluates the oracle |
| Trace | Required execution trajectory evidence when tools, state, delegation, or side effects matter |
| Gate | Pass/fail threshold, keep/discard rule, and ship/iterate/caveated ship/block consequence |

Suitable verification remains claim-matched: structure uses heading/fence/link/readback checks; source claims use a ledger or claim-source matrix and current official evidence; prompt/instruction changes use smoke cases and known-failure readback; harness changes use tool, safety, context/state, and eval boundaries.

A document that specifies a memory, notes, or retrieval-corpus store carries its own checks: every write path is reviewed, stored entries carry provenance fields, and a later session reading the store is replayed. Retrieved text becomes durable context at that write, which is the point where a review has to happen.

### 3.1 Judging a non-deterministic result

| Decision | Requirement |
|---|---|
| Metric | Report `pass^k` when consistency is the product, `pass@k` when one success is enough, and never only the mean of a single trial per case |
| Gate | Declare an equivalence margin separately from the interval the run count buys; a change inside the margin does not block, and a narrow interval never licenses ignoring a regression |
| Grading target | Prefer the deterministic check and grade the artifact, not the path; a tool-call sequence check punishes valid approaches the designer did not anticipate |
| Partial credit | Award it on multi-component tasks, because "identified the problem but failed the write" and "failed immediately" are different results |
| Grader integrity | Test the grader with a case that fails for the wrong reason; make passing require solving the task; isolate every trial from the previous one |
| Coverage | Test where the behavior should occur and where it should not, so the set cannot train over-triggering; two domain experts should reach the same verdict from the task text alone, because a 0% pass rate usually means a broken task or grader rather than incapable behavior |
| Judge | Give the rubric, a counterexample per dimension, and an "unknown" verdict; score dimensions independently; record the judge's model, version, and agreement with human labels |

A model judge that decides an outcome is either calibrated against a human-labelled sample with the agreement rate recorded, or reported as uncalibrated. Agreement near 80% is the observed ceiling, because that is roughly where humans disagree with each other; a judge reported at 100% is a broken measurement, and a panel of judges is not a substitute for calibration.

## 4. Trace Assertions

When agents, subagents, tools, or background workflows are documented, require relevant trajectory evidence:

- bounded objective, scope, output, and stop condition
- independent work or explicit sequencing; declared write ownership and no shared-resource conflicts
- least-privilege capability access and explicit unavailable-capability fallback, skip, or block path
- child evidence reporting, parent synthesis, and parent final verification
- approval/precondition gates for consequential side effects
- no loop, or observable feedback, metric/rubric, guard, bounded iterations, keep/discard rule, and stop condition

## 5. Smoke Eval Shape

Use compact cases at the selected risk depth:

```yaml
id: unique-case-id
risk: low|medium|high|critical
scenario:
  intent: user goal
  context: { files: [], sources: [], capabilities: [] }
  condition: normal|missing_context|boundary|adversarial|regression
oracle:
  must: [required behavior]
  must_not: [forbidden behavior]
runner: capability-limited executor
judge: deterministic check, or a stated rubric with its calibration status
trace: required trajectory evidence or none
runs: 3
gate: aggregate rule, equivalence margin, and ship decision
```

A trigger case is not a boolean: every case in the positive, negative, and boundary categories states its own `expect` (`trigger` or `no_trigger`), `runs`, and `threshold`, and the run records the measured rate. Do not let a case inherit a default, because `runs` changes what the rate means. Three runs and a 0.5 threshold are a recommended starting point, not a validated optimum. Do not invent a third expectation value for an ambiguous boundary case; record it as `no_trigger` with a note. Record the model and runtime identity and the run count beside any measured rate, and state the target interval width rather than a bare pass rate.

The maintained regression surface is the `mode: docs` cases in `../../assets/evals/hyper-documentation-cases.jsonl`. Run or manually exercise every changed behavior against that fixture before completion. Do not rewrite expected behavior merely to make a candidate pass; add newly observed failures as regression cases.

## 6. Readback and Bilingual Gate

Read the document as a new maintainer, an agent under context pressure, and a reviewer seeking stale, unsupported, mixed-concern, future-dated, or authority-conflicting claims. Fail when the validation path requires unrelated-file searching.

Check English/Korean mirrors for equivalent contract fields, route conditions, loop/runtime behavior, phase order, risk depth, gates, and representative behavioral cases—not file presence alone.

Compare the `en` and `ko` cases with `mode: docs` in `../../assets/evals/hyper-documentation-cases.jsonl` by scenario type, expected route, required/forbidden behavior, trace, and gate. IDs and prose may be localized; behavioral coverage may not disappear.

## 7. Reviewer Quick Gate

Fail or block the document when any condition is true:

- canonical docs present fixed model literals or runtime-only syntax as universal
- provider-sensitive/current claims lack appropriate evidence, provenance, or non-future dates
- a versioned standard is cited without its edition, or a claim rests on a page that only points at the artifact
- a non-deterministic claim is reported from a single run, or a model judge that decides an outcome is presented as calibrated when its agreement rate was never measured
- retrieved content, tool output, or subagent output is treated as instruction authority, or quoted into the document as if it were one
- a required capability silently reduces requested scope, or consequential effects lack authority/gates
- a loop is unbounded, self-graded only, baseline-changing, or keeps a failed-guard result
- harness docs omit in-scope scenario/oracle/runner/judge/trace/gate coverage
- English/Korean mirrors expose incompatible behavioral contracts

## Sources

> Content checked 2026-11-03 against the repository instruction base; no external URL was opened for this file.

| Claim | Source |
|---|---|
| The risk-depth scale, the completion contract, and the reviewer gate | `instructions/validation/index.md` |
| Trial reporting, `pass@k` versus `pass^k`, grader integrity, and judge calibration | `instructions/validation/references/evaluation-design.md` |
| The judgement rules and the evidence discipline this file applies | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| The regression fixture and the EN/KO behavioral comparison named in this file | `../../assets/evals/hyper-documentation-cases.jsonl`, `mode: docs` cases (this package) |
