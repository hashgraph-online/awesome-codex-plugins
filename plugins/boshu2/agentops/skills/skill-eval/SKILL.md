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
- skill-maintenance-recommendation
- probe-package
context_rel:
- kind: supplier-to
  with: skill-builder
user-invocable: true
metadata:
  tier: meta
  dependencies: []
  capabilities: ["evaluate_skill_decision","select_skill_measurement","read_skill_ab_results","author_seeded_probe"]
  effects: ["write_probe_package","dispatch_authorized_trials"]
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

This is an optional specialist: the selected runner owns execution and bounds,
and its native results own the measurements.

## Rules that decide the answer

- **Count every attempt.** Keep failed, crashed, interrupted, blocked, abandoned,
  missing and infrastructure-invalid attempts in the all-attempt accounting. A
  rerun adds an attempt; it never overwrites the one that failed. A run that
  shared its host with other work still counts for completion and tokens; keep
  its duration, labeled as measured on a shared host, rather than dropping it.
  Its timeout is not by itself a skill failure; when timeouts fall unevenly
  between arms, report them as a possible skill effect, not infrastructure.
- **Vary one thing.** Equalize instructions, tools, environment, model and
  effort across arms apart from the intended variable. If one arm's task prompt
  repeats the skill's direction, attribute the result to the combined
  instructions, not the skill alone. When you control launch order, alternate
  arms run by run, swap which goes first in each pair and rerun a dead run in
  its own slot; one whole arm and then the other turns load, rate limits and
  time of day into an apparent skill effect.
- **Confirm the skill loaded.** Before reading a zero or small delta as no
  benefit, check each treatment run for the skill actually being loaded or
  injected. A run where it never loaded measures routing, not content. When the
  act depends on a rule kept in a reference, also check that the run opened
  that file; a run that did not still counts; read its miss as the body's
  pointer to the reference failing, not the reference's rule, and report how
  many treatment runs opened the file. The behavioral probe injects only
  SKILL.md or a prelude, so it cannot answer this. Likewise, a case the
  no-skill arm already passes nearly in full has no headroom: report no
  headroom, not no value, and write a harder case ([seeding](references/seeding.md)).
- **Calibrate the grader.** Before trusting scores, confirm the judge or
  discriminator passes a response that plainly meets each criterion and fails
  one that plainly does not. A weak judge can fail correct responses wholesale.
- **Small samples are directional.** Report uncertainty with every difference.
  A difference without it shows neither benefit nor equivalence, and a
  zero-crossing interval is not equivalence. For two unpaired success rates,
  give each arm a Wilson interval, the difference with its own interval and
  Fisher's exact test, not a normal approximation, which breaks at 0/n, n/n and
  a handful of runs. AgentOps ships no tool for this; the stock calls are
  `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")` and
  `scipy.stats.fisher_exact`. Beside an inconclusive result, state the runs per
  arm needed to detect the smallest effect that would change the decision, and
  return insufficient evidence; running them is a new measurement with its own
  fixed stop and the caller's authorization, never an extension of this one.
- **Fix the stop before running.** Do not add trials until the result turns
  positive, remove losing observations or relax acceptance.
- **Know the noise before cutting.** Before trimming or retuning skill text for
  a new model, measure how much identical arms differ on the same cases. A cut
  must clear a bar fixed before the run, above that spread. A static read of
  the text is not a behavioral result. Saving a result means keeping the
  completed run; rerunning to save it adds another sample and more spend.

## Choose the question

| Caller decision | Measurement | What it can establish |
|---|---|---|
| Does a natural request load this skill? | When Claude is explicitly authorized, `claude plugin eval . --eval-dir evals/plugin-eval/routing --ablation none --model <id> --no-publish --json <out>` with a `tool_used: Skill` grader (the AgentOps `evals/plugin-eval/routing` suite). The [routing probes](https://github.com/boshu2/agentops/blob/main/evals/routing-probes/README.md) (AgentOps source checkout only) are weaker: v1 needs an opt-in telemetry hook, v2 grades `ao skills find` ranking, not loading | Natural-request loading on the observed host/catalog; not whether loading helps |
| Does supplied skill text change a specific observable act? | Behavioral probe with the available authorized Codex adapter in the AgentOps source checkout's `scripts/probe-skill.sh` | Behavior change under forced source injection; not routing, correct code or productivity |
| Does the installed plugin change graded answers end to end? | `claude plugin eval` against its no-plugin baseline, only when explicitly authorized and available | Routing and content together on the selected cases |
| Does this package or version improve engineering outcomes at acceptable cost? | Repository-selected controlled coding comparison, such as `evals/skills-rpi` | Endpoint outcomes and cost on selected tasks; independent completion only when required exact-subject evidence exists |
| Does a qualified memory update help later work? | Separate frozen-versus-updated memory transfer test | Narrow later-task reuse evidence with skill and runtime held fixed |
| What happened in ordinary runs? | Existing native accounting and acceptance evidence | Observational failures, repairs and cost; not causal skill benefit |

Start from the caller's intended decision, not a mandatory quiz. For a
behavioral question, name one observable action (a file written, tool used,
criterion rejected); a belief such as “understands validation” needs translation
into an action. For coding or memory questions, name unchanged task acceptance
and the maintenance choice.

Prefer cases drawn from real use when authorized session history exists: a
caller correcting, redoing or overriding the result right after the skill ran
is the clearest sign of a miss. Label each case as drawn from use or written
from the skill's own text; cases written from the text test what the author
expected, not what users hit. With no usable history, say so rather than
presenting text-derived cases as representative.

A skill whose result depends on the caller's answers, such as an interview, is
not measured by its first turn; never run it where its questions reach a real
person. Measure the dialogue as in [dialogue skills](references/dialogue-skills.md).

## Runners

Select the intersection of the caller's runtime authority, an available adapter
and the named question. A runner's presence grants no runtime permission. If no
route meets all three, return **insufficient evidence** with the missing route;
do not automatically substitute another runtime or build a replacement runner.
Forced SKILL.md injection, natural-request routing and installed-package coding
comparisons answer different questions.

When Claude Code is explicitly authorized and its evaluator is available,
`claude plugin eval <plugin-path> --model <id>` is an optional route. It
runs the cases in the plugin's eval directory (`evals/` by default) with the
plugin and, by default (`--ablation with-without`), without it, scores each
response with the case graders (LLM graders use `--judge-model`, default haiku)
and reports the score delta. `--runs` sets repetitions per case,
`--max-cost-usd` caps spend and `--json` writes per-run results. The model
decides whether to load each skill, so the delta mixes routing with content.
By default it also publishes its HTML report (prompts, responses and verdicts)
to claude.ai and writes results under the plugin's eval directory: pass
`--no-publish`, and point `--output-dir`, `--json` and `--report` at
caller-selected storage. Confirm flags with `claude plugin eval --help`. In an
AgentOps checkout, run the suites as
[`evals/plugin-eval/README.md`](https://github.com/boshu2/agentops/blob/main/evals/plugin-eval/README.md) shows and
grade with its `grade.py`: the default Haiku judge failed every criterion of
correct `validate` responses there.

In an AgentOps source checkout, `scripts/probe-skill.sh` runs small behavioral
probes through the Codex adapter
(`scripts/lib/codex-exec.sh`), only when Codex and its isolation support are
available and authorized. It injects the exact SKILL.md bytes (or a declared
prelude), so it measures the text's effect on one act, not routing or an
installed package. Neither runner's result substitutes for the other. Commands,
replay limits and headroom classes are in [behavioral probes](references/behavioral-probes.md).

The probe runner, `evals/`, the probe gates and every github.com/boshu2/agentops
link in this skill are AgentOps source checkout only; installed skills do not
ship them. Elsewhere, use the
caller's authorized existing runner if it supports the question and record its
identity and limits; with none, report the measurement unsupported rather than
installing or starting a replacement.

## Procedure

1. **Fix the decision and bounds.** Name the subject (package, version or
   memory update), the cases, the runtime and the time, trial and cost limits,
   and get the caller's authorization before any live run. Smoke runs, retries
   and interrupted attempts spend the same limits; a new configuration does not
   renew them. Token counters are not billing enforcement.
2. **Choose the smallest measurement that answers it.** Probes for one act,
   coding tasks for engineering outcomes, separate later sessions for memory.
   Keep the deployed model and effort unless the decision is about effort. Keep
   easy cases as regression and cost controls; never weaken the control arm to
   manufacture separation.
3. **Freeze and calibrate.** Fix task, acceptance, package, model, environment
   and grader before trials. An executable oracle must accept the intended
   solution and reject plausible wrong and no-op ones; for judgment, include
   correct and incomplete cases. A case already used to write or tune the skill
   is a development case; renaming it does not make it a holdout. A broken or
   leaked case voids the comparisons it touched. Dry-run a new or changed
   readout on known input. An A/A gap beyond chance is a harness, labeling or
   scoring defect to fix before comparing, not noise.
4. **Isolate the run.** Give trials the selected package and resources; keep
   out the operator's home, production tracker, session history, sibling output
   and solutions. A worktree or a prompt prohibition is not isolation. Capture
   the launched configuration and final artifacts outside the worker. Report an
   incompatible adapter rather than building a replacement.
5. **Read all attempts** from the runner's native results. Wrong identity,
   changed acceptance, contamination or ambiguous pairing voids a comparison
   even when a check passed.
6. **Compare only supported facts.** Pair by case and repetition. Endpoint
   reward, a worker's done claim, an in-workflow validator PASS and independent
   acceptance are different facts; missing evidence stays unknown. Following an
   instruction shows adherence, not reduced rework, and a pass far from a failed
   boundary does not show the boundary is repaired. Coding and memory
   comparisons follow [coding and memory readout](references/coding-memory-readout.md).
7. **Recommend once and stop.** First read a few treatment transcripts, not only
   graded outputs: turns spent on steps that do not move the task, and a helper
   several runs wrote for themselves, are revise targets a passing score hides.
   A repeated helper is a candidate bundled script under
   [Skill Builder](../skill-builder/SKILL.md)'s occurrence rule. A reproduced
   defect with clean controls supports a provisional narrow repair; general
   improvement needs a held-out comparison. Do not auto-publish a lesson.

Raw trials and new proof go to caller-selected protected storage outside Git;
only sanitized public fixtures cleared for that destination belong in Git
(ADR-0016).

## Output

```text
Decision: retain | revise | remove | insufficient evidence; scope <skill, version, cases>
Question: <maintenance decision and the measurement chosen>
Setup: <runner, model, effort, grader; what differs between arms>
Attempts: <per arm: assigned, completed, crashed or infra, interrupted, reruns>
Outcomes: <paired by case and repetition; whether the skill loaded in each treatment run>
Uncertainty: <interval and method, or "directional, n=<count>"; runs per arm needed if inconclusive>
Cost: <measured time and cost per arm, or unknown>
Not proven: <confounds, missing coverage, what this measurement cannot show>
```

Done when the requested measurement has reached its accepted stop, the relevant
replay/oracle checks discriminate, missing coverage is explicit, and one
recommendation answers the named maintenance decision. Insufficient evidence,
an adverse result or an incompatible runtime can complete this evaluation;
none counts as demonstrated skill benefit.

## References

- Behavioral runner and conventions: [`scripts/probe-skill.sh`](https://github.com/boshu2/agentops/blob/main/scripts/probe-skill.sh), [`evals/skill-probes/README.md`](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/README.md), [seeding](references/seeding.md).
- Plugin A/B suites and grader: [`evals/plugin-eval/README.md`](https://github.com/boshu2/agentops/blob/main/evals/plugin-eval/README.md).
- Behavioral verdicts and non-verdict incidents: [`LEDGER.md`](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/LEDGER.md), [`RUNBOOK.md`](https://github.com/boshu2/agentops/blob/main/evals/skill-probes/RUNBOOK.md).
- Existing coverage and headroom gates: [`check-skill-probe-coverage.sh`](https://github.com/boshu2/agentops/blob/main/scripts/check-skill-probe-coverage.sh), [`check-skill-probe-headroom.sh`](https://github.com/boshu2/agentops/blob/main/scripts/check-skill-probe-headroom.sh).
- Evidence and overclaim limits: ADR-0011, ADR-0016 and [`RPI traversal`](https://github.com/boshu2/agentops/blob/main/docs/architecture/rpi-traversal.md).
