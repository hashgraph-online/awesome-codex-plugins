---
name: skill-eval
description: 'Measure whether a skill helps a named task or needs revision or removal. Use when: a bounded routing or coding evaluation is requested; conformance alone cannot show benefit.'
---
# /skill-eval

Answer one named maintenance decision: **retain, revise, remove, or insufficient
evidence**. Choose the measurement that can answer that decision, use the caller's
accepted cases and resource envelope, make one scoped recommendation, and stop.
A completed evaluation does not require a positive difference.

This is an optional specialist. The repository's selected runner owns execution
and bounds; native results own measurements; BD and Git retain their authority.
Do not add a core skill, AO evaluation command, scheduler, dashboard, second
tracker, or mandatory review merely to run an experiment.

## Choose the question

| Caller decision | Measurement | What it can establish |
|---|---|---|
| Does loading this skill change a specific observable act? | Behavioral probe with `scripts/probe-skill.sh` | Behavior change on that scenario; not correct code or productivity |
| Does this package or version improve engineering outcomes at acceptable cost? | Repository-selected controlled coding comparison, such as `evals/skills-rpi` | Endpoint outcomes and cost on selected tasks; independent completion only when required exact-subject evidence exists |
| Does a qualified memory update help later work? | Separate frozen-versus-updated memory transfer test | Narrow later-task reuse evidence with skill and runtime held fixed |
| What happened in ordinary runs? | Existing native accounting and acceptance evidence | Observational failures, repairs and cost; not causal skill benefit |

Start from the caller's intended decision, not a mandatory quiz. Reuse an
existing accepted decision and scope. For a behavioral question, name one
observable action (a file written, tool used, criterion rejected); a belief such
as “understands validation” needs translation into an action. For coding or
memory questions, name unchanged task acceptance and the maintenance choice.

## Procedure

1. **Fix the decision and bounds.** Name the subject package/version or qualified
   memory update, relevant cases, allowed runtime and existing aggregate time,
   trial and cost limits. Do not infer billing enforcement from token counters.
   Smoke runs, infrastructure retries, interrupted attempts and inner review
   consume the same declared envelope. A new configuration or context does not
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
4. **Run within the selected consumer's bounds.** Equalize instructions, tools
   and environment across arms apart from the intended variable. Coding trials
   expose the actual selected package and required resources. A worktree or a
   prompt prohibition is not runtime isolation. Exclude operator home, production
   tracker, session history, sibling output and solutions; capture launched
   configuration and final artifacts outside the worker. Report an incompatible
   adapter as such; do not build a replacement platform to rescue a result.
5. **Read all attempts.** Use native runner results and existing accounting;
   collection must not require another model call or handwritten evaluation.
   Keep failed, abandoned, blocked, interrupted and missing attempts visible.
   Wrong identity, changed acceptance, contamination or ambiguous pairing cannot
   establish comparison proof even when a deterministic check passed.
6. **Compare only supported facts.** Pair by task and repetition; preserve
   repetitions within task clusters. Report case outcomes, denominators,
   uncertainty and failure disposition. Endpoint reward, worker done claim,
   in-workflow validator PASS and independent acceptance are different facts.
   Missing review, usage, billing, phase or feasibility evidence stays unknown.
7. **Recommend once and stop.** State retain, revise, remove or insufficient
   evidence, the scope and supporting facts, and what remains unproven. A
   concrete reproduced defect with clean controls can support a provisional
   narrow repair; general improvement needs held-out comparison. Do not add
   trials until green, require a positive result, or automatically publish a
   lesson. Do not remove losing observations or relax acceptance.

## Coding and memory readout

Use the development adapter documented in
[`evals/skills-rpi/readout.md`](../../evals/skills-rpi/readout.md), or the caller's
existing equivalent. Its report is a rebuildable view, not work authority.
The pilot's default `insufficient-evidence` recommendation is an honest limit;
the specialist may make a narrower supported maintenance recommendation and
must state its evidence and provisional scope.

- Report endpoint success against **all assigned/observed attempts** alongside
  any feasible-task rate. Retain infrastructure invalidity, infeasibility and
  unknown coverage separately; do not hide them by dropping the denominator.
- Report false completion, false acceptance and needless blocking separately
  when independent evidence measures them. Clean cases and abstentions are
  denominators, not opportunities to reward finding-count spray. Unknown is not
  zero. Deterministic code truth may settle an experimental criterion, while a
  required native handoff or exact-subject judgment remains unproven.
- Report raw time/cost distributions and total cost of all attempts per accepted
  outcome. Zero accepted outcomes makes that ratio undefined. Partial Harbor
  cost is not total billing. Native input includes cached input; native output
  includes reasoning. Keep counters distinct and never add native totals to
  Harbor totals or assume parents exclude children. Split producer, in-workflow
  validation, orchestration and grading only where native identity supports it.
  State the measurement window and excluded setup/analysis overhead.
- Use `evals/_stats` for paired task-cluster uncertainty after verifying its
  dependencies and semantics. A pilot is descriptive unless sample size and
  decision thresholds were justified and fixed in advance. A zero-crossing
  interval or `no_change` is **not equivalence**; equivalence needs its own margin
  and test. Same numeric repetitions/seeds do not prove controlled provider
  randomness. Do not extrapolate local results across libraries or models.
- For memory, hold skill/runtime fixed and compare frozen with independently
  qualified updated memory in fresh later sessions, using an unseen transfer
  task and an unrelated or invalidating control. Count acquisition, qualification,
  retrieval and downstream trial cost separately. Package available, content
  delivered, relevant action and later outcome are separate facts. Saving a page
  earns no benefit credit; coding-pilot completion does not establish compounding.

Raw trials and new proof belong in caller-selected protected external non-Git
storage. Only public/sanitized fixtures cleared for that destination belong in
Git. Preserve legacy `.agents/` evidence. Existing independent support and
disclosure review precedes memory import; this skill does not auto-publish
transcripts or mutate knowledge from aggregate scores (ADR-0016).

## Behavioral probes: preserve their existing meaning

`scripts/probe-skill.sh` remains the runner for small behavioral regression
probes and immutable replay. It exposes an empty workspace and one injected
SKILL.md, not a complete installed-package coding trial. Its verdict measures
**behavior change**, never quality uplift or productive engineering completion.
Existing ledger entries retain that meaning and their recorded limitations.

| Probe form | Use when | Discriminator |
|---|---|---|
| Tier 1 — quiz | A decision rule is the caller's behavioral question | The answer/action on the scenario |
| Tier 2 — seeded task | Applying a discipline in work is the question | Whether the agent acted on a realistic planted defect |

Either form may be the starting point. Use
[`references/seeding.md`](references/seeding.md) for seeded tasks. Grade the act,
never vocabulary copied from the treatment. A floor probe detects at least one
act; a multi-defect band needs both lower and upper bounds to catch omission and
finding spray. Calibrate against a transcript performing the act without the
prelude's wording and one repeating the wording without the act.

The declared `treatment_source` remains the only arm variable: `canonical-skill`
uses exact SKILL.md bytes and is the mode the coverage gate counts;
`injected-prelude` establishes prelude-only evidence. Live runs use the selected
authorized native producer with equal scenario and repetitions. Effort levels
are a declared experimental choice, not a prerequisite for every question.

```bash
bash scripts/probe-skill.sh --probe <id> --replay
# Only within an already authorized live envelope:
bash scripts/probe-skill.sh --probe <id> --live --capture --reps 3 --output out.json
bash scripts/check-skill-probe-headroom.sh
```

The existing `skill.probe-headroom` gate in `cli/internal/probeheadroom` owns
classification and thresholds. Its multi-effort saturation rule remains the
legacy gate contract; do not fabricate enough runs to satisfy it or rederive
the rule in a new report. Read and report the actual answer:

- **SATURATED:** the probe cannot distinguish the targeted act. Preserve the
  observation as a scenario limitation in the RUNBOOK; do not append a skill
  verdict to the legacy ledger. Do not infer skill value or lack of value.
- **FLOOR:** treatment did not act. Check the discriminator on a known passing
  transcript. The result alone does not prove the skill cannot help elsewhere.
- **UNMEASURED:** no usable measurement, not INERT.
- **SEPARATED:** the gate found usable headroom. This classification itself does
  not establish positive treatment benefit; retain the actual probe verdict.

Legacy behavioral ledger rows cite the headroom result, model, effort and
sample size. Append one row only under that ledger's existing admissibility
rules; preserve a valid INERT or losing result. Small samples remain
directional. If producer failure or truncation makes a rep `infra`
(discriminator exit 2), exclude it from the legacy **usable behavioral rate**
and report its count in the all-attempt accounting. Zero usable treatment reps
is UNMEASURED, never INERT. This rate convention does not authorize dropping
infrastructure attempts from coding-cohort accounting.

## Output and completion

One scoped recommendation with the decision, cases, all attempts/coverage,
paired outcomes when valid, uncertainty, cost/unknowns and failure disposition.
For behavioral authoring, also supply the existing probe package (`probe.json`,
`question.md`, `discriminator.sh`, `fixtures/`, and a prelude only in
`injected-prelude` mode) and its replay result. Use the legacy ledger/RUNBOOK
only for their existing consumers. No new per-run worksheet is required.

Done when the requested measurement has reached its accepted stop, the relevant
replay/oracle checks discriminate, missing coverage is explicit, and one
recommendation answers the named maintenance decision. Insufficient evidence,
an adverse result or an incompatible runtime can complete this evaluation;
none counts as demonstrated skill benefit.

## References

- Behavioral runner and conventions: [`scripts/probe-skill.sh`](../../scripts/probe-skill.sh), [`evals/skill-probes/README.md`](../../evals/skill-probes/README.md).
- Behavioral verdicts and non-verdict incidents: [`LEDGER.md`](../../evals/skill-probes/LEDGER.md), [`RUNBOOK.md`](../../evals/skill-probes/RUNBOOK.md).
- Existing coverage and headroom gates: [`check-skill-probe-coverage.sh`](../../scripts/check-skill-probe-coverage.sh), [`check-skill-probe-headroom.sh`](../../scripts/check-skill-probe-headroom.sh).
- Evidence and overclaim limits: ADR-0011, ADR-0016 and [`RPI traversal`](../../docs/architecture/rpi-traversal.md).
