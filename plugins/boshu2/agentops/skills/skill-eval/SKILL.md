---
name: skill-eval
description: 'Measure whether a skill helps by comparing runs with and without it. Use when: reading skill A/B results or deciding to keep, revise or remove one.'
practices:
- measurement-over-assertion
- ab-testing
skill_api_version: 1
hexagonal_role: supporting
consumes:
- skill-source-package
produces:
- probe-package
- probe-result.v1
context_rel:
- kind: supplier-to
  with: skill-builder
user-invocable: true
metadata:
  tier: meta
  dependencies: []
  capabilities: ["author_seeded_probe","run_probe_tier","evaluate_skill_decision"]
  effects: ["write_probe_package","dispatch_probe_producer"]
  canonical_status: canonical
  disposition: keep_specialist
  stability: experimental
output_contract: one recommendation (retain, revise, remove or insufficient evidence) with cases, all-attempt denominators, paired outcomes, uncertainty, cost and unknowns
---

# Skill Eval

Answer one named maintenance decision: **retain, revise, remove, or insufficient
evidence**. Choose the measurement that can answer that decision, use the caller's
accepted cases and resource envelope, make one scoped recommendation, and stop.
A completed evaluation does not require a positive difference.

This is an optional specialist. The selected runner owns execution and bounds;
native results own measurements; BD and Git retain their authority. Do not add
a core skill, AO evaluation command, scheduler, dashboard, second tracker, or
mandatory review merely to run an experiment.

## Rules that decide the answer

- **Count every attempt.** Keep failed, crashed, interrupted, blocked, abandoned,
  missing and infrastructure-invalid attempts in the all-attempt accounting. A
  rerun adds an attempt; it never overwrites the one that failed.
- **Vary one thing.** Equalize instructions, tools, environment, model and
  effort across arms apart from the intended variable. If one arm's task prompt
  repeats the skill's direction, attribute the result to the combined
  instructions, not the skill alone.
- **Confirm the skill loaded.** Before reading a zero or small delta as no
  benefit, check each treatment run for the skill actually being loaded or
  injected. A run where it never loaded measures routing, not content.
- **Calibrate the grader.** Before trusting scores, confirm the judge or
  discriminator passes a response that plainly meets each criterion and fails
  one that plainly does not. A weak judge can fail correct responses wholesale.
- **Small samples are directional.** Report uncertainty with every difference.
  A difference without it shows neither benefit nor equivalence, and a
  zero-crossing interval is not equivalence.
- **Fix the stop before running.** Do not add trials until the result turns
  positive, remove losing observations or relax acceptance.

## Choose the question

| Caller decision | Measurement | What it can establish |
|---|---|---|
| Does a natural request load this skill? | `claude plugin eval` with a with-only `tool_used: Skill` grader, or [routing probes](../../evals/routing-probes/README.md) | Whether the description routes; not whether loading helps |
| Does loading this skill change a specific observable act? | Behavioral probe with `scripts/probe-skill.sh` | Behavior change on that scenario; not correct code or productivity |
| Does the installed plugin change graded answers end to end? | `claude plugin eval` against its no-plugin baseline | Routing and content together on the selected cases |
| Does this package or version improve engineering outcomes at acceptable cost? | Repository-selected controlled coding comparison, such as `evals/skills-rpi` | Endpoint outcomes and cost on selected tasks; independent completion only when required exact-subject evidence exists |
| Does a qualified memory update help later work? | Separate frozen-versus-updated memory transfer test | Narrow later-task reuse evidence with skill and runtime held fixed |
| What happened in ordinary runs? | Existing native accounting and acceptance evidence | Observational failures, repairs and cost; not causal skill benefit |

Start from the caller's intended decision, not a mandatory quiz. For a
behavioral question, name one observable action (a file written, tool used,
criterion rejected); a belief such as “understands validation” needs translation
into an action. For coding or memory questions, name unchanged task acceptance
and the maintenance choice.

## Runners

`claude plugin eval <plugin-path> --model <id>` is Claude Code's evaluator. It
runs the cases in the plugin's eval directory (`evals/` by default) with the
plugin and, by default (`--ablation with-without`), without it, scores each
response with the case graders (LLM graders use `--judge-model`, default haiku)
and reports the score delta. `--runs` sets repetitions per case,
`--max-cost-usd` caps spend and `--json` writes per-run results. The model
decides whether to load each skill, so the delta mixes routing with content.
By default it also publishes its HTML report (prompts, responses and verdicts)
to claude.ai and writes results under the plugin's eval directory: pass
`--no-publish`, and point `--output-dir`, `--json` and `--report` at
caller-selected storage. Confirm flags with `claude plugin eval --help`.

`scripts/probe-skill.sh` is the repository runner for small behavioral probes.
It injects the exact SKILL.md bytes (or a declared prelude) into the treatment
arm of a cross-family producer, grades with a deterministic discriminator and
replays immutable fixtures. Loading is forced, so it measures the text's effect
on one act, not routing. Neither runner's result substitutes for the other.
Probe forms, headroom classifications and legacy ledger rules are in
[behavioral probes](references/behavioral-probes.md).

`scripts/probe-skill.sh`, `evals/` and the probe gates exist only in an
AgentOps source checkout. Elsewhere, use `claude plugin eval` or the caller's
runner and say which one replaced the repository runner.

## Procedure

1. **Fix the decision and bounds.** Name the subject package/version or qualified
   memory update, relevant cases, allowed runtime and existing aggregate time,
   trial and cost limits. Do not infer billing enforcement from token counters.
   Smoke runs, infrastructure retries, interrupted attempts and inner review
   consume the same declared envelope; a new configuration or context does not
   renew it. Do not launch live work without caller authorization and bounds.
2. **Choose the smallest relevant measurement.** Use behavioral probes for acts,
   coding tasks for engineering outcomes, and separate later sessions for memory.
   There is no universal two-effort requirement. Keep the deployed model and
   effort unless the caller's decision concerns effort. Retain easy regression
   and cost controls; do not weaken the producer to manufacture separation.
3. **Freeze and calibrate.** Fix task, acceptance, package, model/runtime,
   environment and grader identities before trials. Executable oracles must
   accept the intended solution and reject plausible incorrect/no-op solutions.
   Include genuinely correct and incomplete cases when evaluating judgment.
   Exposed incidents are development cases, never unseen holdouts by renaming.
   Broken or leaked cases invalidate affected comparisons; preserve their
   historical disposition when versioning a correction.
4. **Run within the selected consumer's bounds.** Coding trials expose the actual
   selected package and required resources. A worktree or a prompt prohibition
   is not runtime isolation. Exclude operator home, production tracker, session
   history, sibling output and solutions; capture launched configuration and
   final artifacts outside the worker. Report an incompatible adapter as such;
   do not build a replacement platform to rescue a result.
5. **Read all attempts.** Use native runner results and existing accounting;
   collection must not require another model call or handwritten evaluation.
   Wrong identity, changed acceptance, contamination or ambiguous pairing cannot
   establish comparison proof even when a deterministic check passed.
6. **Compare only supported facts.** Pair by task and repetition; preserve
   repetitions within task clusters. Endpoint reward, worker done claim,
   in-workflow validator PASS and independent acceptance are different facts.
   Missing review, usage, billing, phase or feasibility evidence stays unknown.
   A worker following an instruction establishes adherence, not reduced rework
   or causal benefit. A passing case far from a failed boundary does not prove
   the boundary is repaired. Coding and memory comparisons follow
   [coding and memory readout](references/coding-memory-readout.md).
7. **Recommend once and stop.** A concrete reproduced defect with clean controls
   can support a provisional narrow repair; general improvement needs held-out
   comparison. Do not automatically publish a lesson.

Raw trials and new proof go to caller-selected protected external non-Git
storage; only public, sanitized fixtures cleared for that destination belong in
Git (ADR-0016).

## Output

```text
Decision: retain | revise | remove | insufficient evidence; scope <skill, version, cases>
Question: <maintenance decision and the measurement chosen>
Setup: <runner, model, effort, grader; what differs between arms>
Attempts: <per arm: assigned, completed, crashed or infra, interrupted, reruns>
Outcomes: <paired by case and repetition; whether the skill loaded in each treatment run>
Uncertainty: <interval and method, or "directional, n=<count>">
Cost: <measured time and cost per arm, or unknown>
Not proven: <confounds, missing coverage, what this measurement cannot show>
```

For behavioral authoring, also supply the existing probe package (`probe.json`,
`question.md`, `discriminator.sh`, `fixtures/`, and a prelude only in
`injected-prelude` mode) and its replay result. No new per-run worksheet is
required.

Done when the requested measurement has reached its accepted stop, the relevant
replay/oracle checks discriminate, missing coverage is explicit, and one
recommendation answers the named maintenance decision. Insufficient evidence,
an adverse result or an incompatible runtime can complete this evaluation;
none counts as demonstrated skill benefit.

## References

- Behavioral runner and conventions: [`scripts/probe-skill.sh`](../../scripts/probe-skill.sh), [`evals/skill-probes/README.md`](../../evals/skill-probes/README.md), [seeding](references/seeding.md).
- Behavioral verdicts and non-verdict incidents: [`LEDGER.md`](../../evals/skill-probes/LEDGER.md), [`RUNBOOK.md`](../../evals/skill-probes/RUNBOOK.md).
- Existing coverage and headroom gates: [`check-skill-probe-coverage.sh`](../../scripts/check-skill-probe-coverage.sh), [`check-skill-probe-headroom.sh`](../../scripts/check-skill-probe-headroom.sh).
- Evidence and overclaim limits: ADR-0011, ADR-0016 and [`RPI traversal`](../../docs/architecture/rpi-traversal.md).
