---
name: framework-health
description: "Evaluate Mycelium's own process effectiveness. Measures cycle velocity, discard trends, confidence calibration, gate effectiveness, regression rate. Run quarterly or every 20 cycles."
metadata:
  instruction_budget: "50"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Framework Health Check

Mycelium evaluates its own process. This is triple-loop learning — the framework assessing whether it is getting better at producing good outcomes.

## When to Use

- Quarterly review (scheduled)
- After 20 completed leaf cycles (triggered by cycle-history.yml count)
- When process friction is suspected
- Before major framework changes (baseline measurement)

## Workflow

### 1. Load Cycle Data

Read `.claude/canvas/cycle-history.yml`.

**Framework-self-host detection** (per `engine/cycle-learning.md#framework-on-framework-exemption`): if the project root contains `plugins/mycelium/plugin.json` AND `CLAUDE.md` begins with `# Mycelium:`, this is the framework dogfooding itself. Skip the cycle-count gate and route to a corrections-graduation summary:
- Count entries in `.claude/memory/corrections.md` (total, and ×graduated-to-mechanism in the last 90 days).
- Read `.claude/memory/cluster-instances.md` and list clusters at-or-above their graduation criterion that are not yet graduated (this is the framework analogue of "actual outcome vs predicted ICE").
- Skip cycle-derived dimensions (velocity, discard rate, confidence calibration, regression rate) — they do not apply. Still run Steps 2b, 4b, 4c, 4d.

Otherwise (product project, not framework-self-host): if fewer than 5 cycles recorded, report:
"Insufficient cycle data for framework health assessment. [N] cycles recorded; minimum 5 needed. Continue recording outcomes."

### 2. Measure Five Dimensions

For each dimension, compute the metric and compare against trend (if prior assessments exist):

**Cycle Velocity**:
- Average days from diamond creation to completion, grouped by scale
- Trend: improving / stable / degrading
- If degrading: flag for investigation

**Discard Rate**:
- Count of discards per lifecycle phase
- Average discard phase (1-10 scale)
- Trend: shifting earlier (good) / shifting later (bad) / stable
- If >50% of discards at Phase 7+: flag "late discard pattern"

**Confidence Calibration**:
- **Cycle-class scope (per `engine/cycle-learning.md#cycle-class`)**: ONLY `product-leaf` cycles feed calibration. `meta-dogfood` (framework-self-development) and `observation` (strategic-process reflection) cycles carry no ICE *by design* — they are EXCLUDED, not missing. This matches `cycle-history.yml#calibration_summary`, which already excludes them from aggregates; the dimension was previously computed over all cycles, which is the bug this fixes.
- **Which confidence (note added 0.319.0)**: the bands below are on a 0.0-1.0 scale read as a chance of success. An ICE Confidence scored since 0.319.0 is a value of Gilad's Confidence Meter on 0-10 (`/mycelium:ice-score` Step 2), a sum of evidence weights and not a probability. Do NOT divide it by ten or place it in these bands. For a cycle whose `predicted.ice_score` carries a meter value, report that the calibration factor was not computed for it and say why. How to compare a meter-scored prediction with its outcome is not designed yet, and no source read describes it.
- For `product-leaf` cycles with predicted confidence/ICE and actual outcome:
  - Compute: actual success rate per confidence band (0.3-0.5, 0.5-0.7, 0.7-0.9)
  - Compare with expected rate (confidence 0.7 should succeed ~70%)
  - Report calibration factor: actual/expected
  - If calibration factor < 0.8 or > 1.2: flag miscalibration
- **If 0 product-leaf cycles**: report calibration as **"honestly empty — N meta-dogfood + M observation cycles, 0 product-leaf"**, status `empty-by-design`. Do NOT flag it as warning/critical and do NOT synthesize a factor from non-product cycles. For a project early in delivery (no leaf shipped yet) this is the correct early state; for a framework-self-host / dogfood project it is the steady state (its work is meta-dogfood, not product delivery).
  - **Masking guard (protects real product projects):** if the project is *actually doing product/delivery work* (active L3/L4 product diamonds, shipped features) yet shows 0 product-leaf cycles, that is a **cycle_class mis-assignment to investigate** — NOT an empty-by-design pass. Surface it: "0 product-leaf cycles despite active delivery — check cycle_class on recent entries." Only treat empty as by-design when the absence of product-leaf cycles is itself honest (discovery-phase or framework-self-development).

**Gate Effectiveness**:
- **SOURCE: `cycle-history.yml#cycles[].gates_fired`.** Named explicitly as of v0.121.0, because
  this dimension previously said "count the gates" without saying from what — and the field that
  `engine/cycle-learning.md` added expressly to close it (*"was unInstrumented in cycle records"*)
  was read by nothing. Producer specced, consumer unwired, dimension computed from air.
- For each theory gate, count: times checked, times passed, times failed
- Compute hit rate: failures / total checks
- Flag rubber stamps (0% failure rate) and hard blocks (>80% failure rate)
- **IF NO CYCLE CARRIES `gates_fired`, REPORT THE DIMENSION AS `no-data`, NAMING THE COUNT** —
  *"no-data: 0 of N closed cycles carry gates_fired"* — and say the next `/mycelium:retrospective`
  populates it. **Do NOT reconstruct gate outcomes from memory, the transcript, or a read of the
  guards.** A dimension filled by hand at assessment time reports on the assessor, not on the
  cycles, and it is indistinguishable in the dashboard from one backed by records. The validator
  already emits this absence as a WARN; the dashboard must not paper over what the validator flags.
- **Theory X/Y audit** (per `${CLAUDE_PLUGIN_ROOT}/harness/theory-tensions.md` Tension 7): for any hard-block gate, check it is *scaffolding* (surfaces its why, an escape hatch exists, leaves the user more capable), not *coercion* (compliance for its own sake, no surfaced reason, no escape). A high-block gate that fails this audit is a Theory-X drift to remediate, not just a strict gate.

**Demand Mix** (Seddon: value demand vs failure demand):
- **SOURCE: `cycle-history.yml#cycles[].demand_type`.** Named here at the same time the field was
  added, because the two fields above were specced first and read second — and were still at 0 of 16
  compliance months later. **A field whose consumer is written afterwards is the `gates_fired`
  shape**, and this dimension exists so demand type does not repeat it.
- Report the SPLIT, never the total: *"N cycles: X value, Y failure (Z%)"*. **A cycle count on its
  own is throughput and measures nothing** — the question is what share of the work was caused by
  earlier work.
- **THIS IS THE COUNTER-METRIC TO RELEASE THROUGHPUT, and it is why the dimension is worth having.**
  A rising release count reads as productivity; the same count with a rising failure share is a
  system generating its own work. Where a project's health file already praises a rising corrections
  count as "actively managed learning", that is a Goodhart inversion on this exact dimension —
  surface it.
- Flag a failure share above 50% as `warning`, and **say what it does NOT mean**: high failure demand
  is a finding about the system, not about the people, and remediating it by re-classing cycles is
  the fastest way to make the dimension useless.
- **IF NO CYCLE CARRIES `demand_type`, REPORT `no-data`, NAMING THE COUNT** — *"no-data: 0 of N
  closed cycles carry demand_type"*. **Do NOT infer demand type from commit messages, the
  transcript, or your own read of what the cycle looked like.** Same rule and same reason as Gate
  Effectiveness above: a dimension filled at assessment time reports on the assessor.
- **Cycles marked `reconstructed_post_hoc: true` are reported SEPARATELY and excluded from the
  split.** Reconstructed demand type is the weakest form of this measurement and must not be
  averaged into records made at cycle open.

**Regression Rate**:
- **SOURCE: `cycle-history.yml#cycles[].regressions.in_cycle_count`** (in-cycle phase regressions),
  named as of v0.121.0 for the same reason as Gate Effectiveness above. **Post-launch defects are
  NOT regressions here** — they live in `rework.post_delivery_regressions` and belong to a different
  question. Conflating them double-counts the second and hides the first.
- Count diamonds that regressed at least once / total diamonds
- Trend: decreasing (good) / increasing (bad) / stable
- **IF NO CYCLE CARRIES `regressions`, REPORT `no-data` WITH THE COUNT**, exactly as above. Zero
  recorded regressions and no field are different findings: the first is a healthy system, the
  second is an unmeasured one, and reporting them the same way is how an unmeasured system reads
  as healthy.

### 2b. Re-run Deferred Design-Verification Eval Scenarios

Re-run any eval scenario tagged `regression` AND `router-discipline` from `.claude/evals/scenarios/integration/`. These are deferred design-time decisions that need periodic re-verification (the AGENTS.md router design is the canonical case — see `agents-md-router-discipline.yml`).

For each scenario:
- Run via `/mycelium:eval-runner` against the scenario file
- Compare result against the scenario's `baseline_reference` field
- Report:
  - **Same outcome** → design holding; no action
  - **Improved** → either the design got better OR the model improved; investigate which (a model improvement that hides a design regression is a Goodhart trap)
  - **Regressed** → design drifted; flag for remediation in this assessment

If a scenario fails its `success_criteria` for the first time, log to corrections.md as a new generalizable correction with the scenario name as evidence. Do not auto-remediate — surface the regression for human review.

### 3. Run Threshold Calibration

If cycle count ≥ minimum_n for any threshold in `.claude/canvas/thresholds.yml`:
- Apply calibration rules from `${CLAUDE_PLUGIN_ROOT}/engine/adaptive-thresholds.md`
- Update calibrated values
- Log changes in .claude/harness/decision-log.md

**The ratchet (added 0.216.0).** `validate_canvas.py` now carries two findings from
`check_cycle_recording.py` so this step cannot be skipped silently: `calibration is due` when the
eligible input count for a threshold has reached its `minimum_n` while `based_on_n` is still 0, and
`uncalibrated because N of M cycles are <class> cycles carrying <field>` when the count is below the
minimum but the total is not, which is the case a `calibration_status` note blaming the cycle count
gets wrong (the dogfood canvas carried that note for three months against 17 cycles and a minimum of
10; the real reason was zero product-leaf cycles with a non-null `ice_accuracy`). Now
that second finding is a WARN only while `thresholds.yml#_meta.calibration_status` blames the count
(it speaks of `minimum_n`, too few cycles or the cycle count, and names neither the cycle class nor
the calibration field). Once the note names the true reason, or when there is no note, the same
state is one `COVERAGE (calibration)` line for all such thresholds: no edit can end it, only
recording cycles of that class with an estimate before the work and an actual after it, and a WARN
that kept printing after its note was corrected (dogfood 2026-10-10) taught the reader to scroll
past the WARN list. A third finding
names every solution leaf in a terminal state with no cycle row, because that is how the loop goes
unfed. Neither computes a value: calibrating a product threshold on meta-dogfood cycles is a category
error, and the output is the prompt with the numbers in it. Since 0.319.0 the same function also
prints one line when `thresholds.yml` still carries `ice_advance`, the threshold on the ICE total
that release retired: the line says the key is read by nothing and can be removed. It is not a
calibration that is due. Since 0.320.0 it prints the same kind of line for `bakeoff_delta`, the ICE
gap that decided a leaf bakeoff until that release retired it.

### 4. Check Goodhart Counter-Metrics

For each dimension, verify the counter-metric is not degrading:
- Velocity improving BUT outcome quality declining? Flag.
- Earlier discards BUT false positive rate rising? Flag.
- Better calibration BUT decision speed dropping? Flag.

### 4b. Cluster Graduation-Readiness (added 2026-05-08)

Read `.claude/memory/cluster-instances.md`. For each cluster:
- **Compare instance count to graduation criterion.** If a cluster has reached or exceeded its stated criterion without being graduated to the corresponding mechanism (e.g., 6+ instances with spec-only status when promotion bar requires implemented detection rules), surface as a graduation-readiness flag.
- **For `spec`-status clusters with linked spec docs** (e.g., `${CLAUDE_PLUGIN_ROOT}/engine/consistency-check-spec.md`): check whether the spec's promotion-bar conditions have been met. Concretely: count detection rules drafted vs. required, FP-rate measurements available vs. needed.
- **Recursive check**: if a cluster's stated graduation criterion has been met for >30 days without graduation action, that's itself an instance of the documented-rule-diverges-from-enforcement cluster — log it.
- **Output**: include cluster status in the dashboard under a new "Cluster Graduation Status" section.

This step closes the recursion the cluster log was created to address: graduation criteria become mechanically auditable rather than promises stored in commit messages.

### 4c. Receipts Highlights Rotation Cadence (added 2026-05-08)

The README's "How Mycelium got smarter" section shows 5 case headers; the full list lives in `docs/receipts/cases/`. Stale README highlights are a Goodhart signal: if the receipts surface freezes, the framework's "we get smarter with each cycle" claim degrades to "we got smarter once".

For each case currently on the README:
- **Check git-log staleness**: when did the case header last change? If >90 days, flag as a rotation candidate.
- **Check for newer cases**: are there cases under `docs/receipts/cases/` newer than the rotation candidate that better demonstrate the framework's recent behavior?
- **Recommend rotation**: surface specific rotate-out / rotate-in pairs in the dashboard. Rotation is a maintainer decision, not automatic — but the flag forces the decision rather than letting it drift.
- **Highlight gap signal**: if no case has been added to `docs/receipts/cases/` in >60 days, flag as a possible-low-friction signal — either the framework genuinely caused no recent friction (rare), or the dogfood loop has weakened (usually).

Per `docs/contributing/style.md#highlights-rotation`. Cases stay in `docs/receipts/cases/` even when rotated off README; only the README mention rotates.

### 4d. Docs Health Cross-Surface (added 2026-05-08)

Run a lightweight version of `/mycelium:canvas-health` step 9b on `docs/`:
- Stub freshness (any forthcoming-doc `Last updated` >60 days)
- Length budget compliance (hard caps)
- Marketing-voice scan
- Information-scent scan on links

Surface in the dashboard. Full details delegate to `/mycelium:canvas-health`.

### 4e. Chat-UX Axiom Audit of Skill Output Templates (added 2026-05-30)

The chat-UX nudges in `${CLAUDE_PLUGIN_ROOT}/harness/design-principles.md` ("the chat is a UI") shape *live* output, which has no stored corpus to audit retroactively. What *is* auditable is the static surface that pre-shapes live output: the `## Output`/`## Output Format` blocks in `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md`. Scan each for two axiom violations:

- **Hick's Law** — an output template that instructs the agent to present a *list of options/recommendations* with no "recommend one" / "priority" / "top-N" cue. A template that emits N equally-weighted choices manufactures decision-tax on every invocation. Flag templates with option-lists lacking a recommendation cue.
- **Von Restorff (isolation)** — an output template that renders a blocker, gate, error, or STOP condition as undifferentiated prose rather than a visually distinct marker (`ON HOLD`, `Gated by:`, a leading verdict line). Flag blocker-bearing templates whose blocker does not visually pop.

This is the **buildable** form of the self-audit; the live-output version is unenforceable (no corpus). Surface counts + offending skills in the dashboard. Do not auto-edit skills — flag for maintainer review (a template's flat option-list may be deliberate). Graduation path: if the same skill is flagged across two assessments, promote to a mechanical `tests/bash` check (then it inherits G-V12 / Check 37).

**Temporal independence required.** "Flagged across two assessments" means two assessments separated by independent observation windows — a quarterly run, a cycle-count-trigger run, or an explicit re-audit after deliberate skill-template edits. Same-day re-runs with no intervening skill edit are mechanically the same flag, not two observations; record the prior run's flag-set as the baseline and check the next independent run against it. Without this rule, any agent running `/mycelium:framework-health` twice in a row would graduate the entire flagged set on the second run. The rule applies symmetrically to 4b (cluster graduation-readiness) and 4d (docs health) — re-flagging in the same session does not count as independent confirmation.

### 4f. Gap-Analysis Diff Audit (added 2026-06-12)

The 2026-06-12 five-dimension gap analysis (code/hooks, doc-vs-mechanism consistency, flows/lifecycle, documentation, packaging/CI/schemas — decision-log "Five-dimension deep-dive gap analysis") is a repeatable audit shape. Its expensive failure mode was NOT finding gaps — it was stale premises: 4 of 6 backlog-derived items were already shipped or already graduated, found only by ground-truthing against the current tree.

On each quarterly run:
- **Diff, don't rediscover.** Locate the previous gap-analysis decision-log entry and its priority list. For each prior finding: re-verify its CURRENT state against the tree (shipped / still-open / changed shape) BEFORE any new fan-out. A finding carried forward without re-verification is a stale-state read (anti-pattern #8) on the audit's own output.
- **Promise-registry sweep**: read `${CLAUDE_PLUGIN_ROOT}/engine/consistency-check-spec.md` § Promise registry. For each open row, check whether the implementing artifact has landed (close the row, citing the version) or the trigger has fired (escalate to the cluster catalog). New "skill X will do Y" claims found in docs without an implementing artifact or `Gated by:` marker become new rows.
- **Schema-coverage trend**: run `validate_canvas.py` and record the schema-less WARN count in the dashboard. The count should be monotonically non-increasing; an increase means a new canvas file was taught without a schema or waiver (preemptive-registry trigger fired — see spec).
- **New fan-out only for new surface**: dimensions whose prior findings all re-verify unchanged get a light pass; spend the deep fan-out where the tree actually changed since the last run.
- Temporal-independence rule from 4e applies: a same-session re-run is not a second observation.

### 4g. Theory-Fidelity Cadence Trigger (added 2026-06-18)

`/theory-fidelity` is the *semantic* audit (is each theory faithfully operationalized vs distorted/over-claimed?) — it needs source-grounding and an LLM, so it runs on cadence, not every push. The `check_theory_fidelity.py` CI guard covers only the *structural* subset (references resolve, gates grounded, no name-only theory). This step is the trigger for the semantic half.

- **Recommend `/theory-fidelity` when the theory surface moved OR quarterly.** Check whether `docs/theories.md`, `engine/theory-gates.md`, or any skill's `Source:`/`## Theory Citations` line changed since the last `/theory-fidelity` run (git-log the paths against that date). If yes, surface in the dashboard: "Theory surface changed since last fidelity audit — run `/theory-fidelity`." **The quarterly half is on the review schedule since v0.329.0** (`engine/review-schedule.yml`, reported at session start by `scripts/review_schedule.py`): read the last run with `review_schedule.py --list` rather than from the decision log, whose headings were measured to undercount. This step keeps only the surface-moved trigger, which no calendar can see.
- **Confirm the structural guard is green**: run `check_theory_fidelity.py` inline and report. A guard failure is a structural-drift finding (phantom skill/gate ref, name-only theory) for the dashboard; it does NOT substitute for the semantic audit.
- Temporal-independence (4e) applies.

### 4h. Test adequacy: the mutation sample (added 0.192.0)

`engine/feedback-loops.md` names the mutation testing score as the counter-metric for test coverage,
and until 0.192.0 nothing computed it. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mutation_sample.py" --root <framework repo> --modules 12 --mutants-per-module 12
```

It mutates code tokens in a seeded random sample of the shipped checks (never strings, comments or
docstrings), runs each module's own tests with bytecode caching disabled, and reports killed versus
survived. **Report the survivor lines, not only the score**: each survivor is a line whose behaviour
no test constrains. On the framework repo the first honest run (2026-09-10) read 76% over 129
mutants, with exit codes on clean paths, an OR-predicate never exercised branch by branch, and
`<`-versus-`<=` boundaries as the survivors; eleven tests were written against them the same day.
A rising score with a falling first-pass rate is the gaming shape; read it beside the coverage floor
and the negative-control check. Framework-repo only: a consumer without `plugins/mycelium/scripts`
gets UNKNOWN, which is not a pass. Same-session re-runs are not two observations (4e).

### 4i. Retirement candidates: what could go (added 0.215.0)

The framework only grows: at 0.180.4 it carried 61 skills and 23 gates with none retired, and no
mechanism reported another as unread or unfired. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_retirement_candidates.py" --project-dir . --window-days 60
```

For every skill, hook and check it prints the last evidence of use from the records this project
already writes (a dated decision-log or corrections mention, a read-log row, the newest row of the
state file the hook writes, the gate list) and who reads it (another skill, an engine doc, a hook, a
runtime manifest, the gate set). **A candidate is a mechanism with no fire in the window and no
reader.** The report prints them under "named by nothing that runs (unwired, not necessarily
dead)": "no reader" means nothing sends an agent to the mechanism, which is not the same as nobody
needing it (dogfood 2026-10-11: `harms-check` and `friction-log` were listed twice, and both were
unwired, not unneeded). Report each candidate as "wire it in where its own text says it belongs, or
retire it", never as dead. Three things to report beside the list, because each bounds what it means: the hooks that
write no record and so cannot be measured (the first fix there is a record, not retirement); the
"quiet but read" rows, which are not candidates and are listed so a reader can disagree; and that no
runtime records a skill invocation, so a skill used and never written about is invisible here. The
first dogfood run (2026-09-15, 60 days) listed 136 mechanisms, 3 candidates after the two new
checks gained their callers (`/canvas-sync`, last named 2026-06-14; `check_gated_by.py`, a
self-declared draft stub; one guard whose log file the installed plugin did not yet write), and 10
hooks with no record. Retirement happens by release with the row's evidence in the changelog. The
script removes nothing.

### 4j. Record the run (added v0.329.0)

This review is on the schedule (`engine/review-schedule.yml`, every 90 days), and the schedule does
not read decision-log headings, which were measured to undercount. When the dashboard is written, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_schedule.py" --record framework-health --project-dir .
```

Without it, session start keeps reporting framework-health as past its cadence.

### 5. Generate Dashboard

## Output

```
## Framework Health Dashboard

Assessment date: [date]
Cycles analyzed: [N]
Period: [date range]

### Dimensions

| Dimension | Current | Trend | Status | Counter-Metric |
|-----------|---------|-------|--------|----------------|
| Cycle velocity | [X days avg] | [improving/stable/degrading] | [healthy/warning/critical] | Outcome quality: [OK/degrading] |
| Discard rate | [avg phase X] | [earlier/stable/later] | [healthy/warning/critical] | False positive rate: [OK/rising] |
| Confidence calibration | [factor X.XX, or "empty (0 product-leaf)"] | [improving/stable/diverging/—] | [healthy/warning/critical/empty-by-design] | Decision speed: [OK/slowing] |
| Gate effectiveness | [see detail] | — | [healthy/warning/critical] | Flow speed: [OK/slowing] |
| Demand mix | [X value / Y failure, Z% failure, or "no-data: 0 of N"] | [improving/stable/degrading] | [healthy/warning/critical] | Throughput: [OK/inflating] |
| Regression rate | [X%] | [decreasing/stable/increasing] | [healthy/warning/critical] | Innovation rate: [OK/declining] |

### Threshold Calibration

*(The "ICE advance | 100" row that stood here until 0.319.0 is gone: the threshold is retired, see `engine/adaptive-thresholds.md`. If the project's `thresholds.yml` still has `ice_advance`, report it as retired and removable, not as a threshold awaiting calibration.)*

*(The "Bakeoff delta | 20%" row that stood here until 0.320.0 is gone too: no ICE gap decides a leaf bakeoff, see `engine/adaptive-thresholds.md` and `orchestration/leaf-bakeoff.md`. If the project's `thresholds.yml` still has `bakeoff_delta`, report it as retired and removable, not as a threshold awaiting calibration.)*

| Threshold | Default | Calibrated | Based On | Change |
|-----------|---------|-----------|----------|--------|
| Confidence factor | 1.0 | [value or "insufficient data"] | N cycles | [+/-] |

### Pattern Signals Active

[List any active pattern detector signals from ${CLAUDE_PLUGIN_ROOT}/engine/pattern-detector.md]

### Recommendations

[Specific actions based on findings — not generic advice]
```

## Rules

- Never modify thresholds without sufficient data (respect minimum_n)
- Always check counter-metrics before celebrating improvement
- Log all threshold changes in .claude/harness/decision-log.md
- If all dimensions are healthy, say so and suggest next review date


## Prior findings first (added v0.96.0)

Before producing new findings, **rule on the previous run's** — per `${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml#prior_findings_first`. For each: CLOSED (name what closed it), STILL-OPEN (carry it forward with a horizon), or DECLINED (a reason AND a re-open trigger). If there is no prior run, say so and continue.

**Scoring goes first because it is the boring half.** A periodic instrument that produces findings and never scores its old ones accumulates a ranking nobody reads — `theory-audit-2026-04-17.md` ranked its gaps and sat unconsumed for four months. Anything placed after the interesting work is what a long session drops.

**A finding ranked HIGH must leave this skill with a home** — tag or create an opportunity on the framework-side root of the OST (`opportunities.yml`, `rolls_up_to`), or decline it with a re-open trigger. Scoring alone does not close the loop: it fires only when someone runs this skill again, so on a slow cadence findings still sleep. An opportunity is read by instruments on their own schedule. Not `human-tasks.yml` — that canvas is scoped to offline HUMAN work (interviews, outreach), and an engineering finding filed there is a category error.

## Theory Citations

- Argyris: Triple-loop learning (learning how to learn)
- Forsgren: Accelerate (measuring capabilities, not just outputs)
- Goodhart: Counter-metrics for every metric
- Deming: Statistical process control (data-driven threshold adjustment)
