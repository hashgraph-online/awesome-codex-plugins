---
name: bvssh-check
description: "Use to evaluate whether current work aligns with Better Value Sooner Safer Happier. Run at diamond completion and periodically."
metadata:
  instruction_budget: "50"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# BVSSH Check Skill

Evaluate alignment with Better Value Sooner Safer Happier.

## Workflow

For each dimension, assess current state:

### Better
- [ ] Quality improving or stable (not degrading)?
- [ ] Technical debt under control (not growing unchecked)?
- [ ] User satisfaction metrics stable or improving?
- [ ] Defect rate stable or declining?
- Evidence: [cite specific metrics or observations]

### Value
- [ ] Delivering measurable user or business outcomes?
- [ ] Outcome metrics moving (not just output metrics)?
- [ ] Work aligned with strategic priorities?
- [ ] Not shipping features nobody uses?
- Evidence: [cite specific metrics or observations]

### Sooner
- [ ] Lead time stable or decreasing?
- [ ] Batch sizes small?
- [ ] WIP limits respected?
- [ ] Handoffs minimized?
- [ ] No unnecessary waiting or queuing?
- Evidence: [cite specific metrics or observations]

### Safer
- [ ] Security posture maintained or improved?
- [ ] Compliance requirements met?
- [ ] Risk being actively managed (not ignored)?
- [ ] Rollback capability tested?
- [ ] No new single points of failure?
- [ ] Error budget healthy? (SRE -- check dora-metrics.yml sre section)
- Evidence: [cite specific metrics or observations]

### Happier
Smart's Happier covers four stakeholders: **customers, colleagues, citizens, and climate**. "Not 'more for less' at any human or climatic cost."

**Colleagues:**
- [ ] Team working at sustainable pace? No chronic overtime? (XP -- Beck)
- [ ] AI tools helping or adding cognitive load? (APEX DevX)
- [ ] No signs of burnout?
- [ ] Team has autonomy and purpose?
- [ ] Learning happening continuously?

**Customers:**
- [ ] Users expressing satisfaction?
- [ ] Customer advocacy high? (Not just retained — actively recommending?)

**Citizens:**
- [ ] Positive societal impact? (Open knowledge sharing, accessibility, inclusivity)
- [ ] No harm to communities or vulnerable groups?

**Climate:**
- [ ] Compute/token usage proportionate to value delivered? (Not brute-forcing with retries)
- [ ] Waste prevented? (Projects killed before unnecessary code, discovery before delivery)
- [ ] Sustainable resource usage patterns?

- Evidence: [cite specific metrics or observations]

### CALMS Culture Assessment (Willis & Humble)

*CALMS originated as CAMS (Culture, Automation, Measurement, Sharing) coined by Damon Edwards and John Willis at DevOpsDays Mountainview 2010. Jez Humble added the L (Lean) to create CALMS.*

Assess the five cultural dimensions that explain WHY DORA outcomes are what they are:

- [ ] **Culture**: Is there a learning culture? Blameless post-mortems? Psychological safety? Or blame-and-fear?
- [ ] **Automation**: Are repetitive tasks automated (testing, deployment, provisioning)? Or manual and error-prone?
- [ ] **Lean**: Are batch sizes small? WIP limited? Waste actively identified and removed? Or big-batch waterfall?
- [ ] **Measurement**: Are you measuring outcomes (DORA, BVSSH) or outputs (velocity, story points)? Watch for MORF anti-pattern.
- [ ] **Sharing**: Is knowledge shared across teams? Cross-functional collaboration? Or siloed expertise?
- Evidence: [cite specific observations or team feedback]

**Automation — cite a measurement, not an impression.** The four fitness functions emit machine-readable counts, so the Automation rating can rest on evidence rather than narrative:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_wiring.py" --root .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_wiring_contract.py" --root .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_negative_control.py" --root .
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_test_authenticity.py" --root .
```

Record under `calms_assessment.automation`:

```yaml
wiring_integrity:
  unwired_mechanisms: 0       # check_wiring / check_wiring_contract
  guards_that_cannot_fail: 0  # check_negative_control
  inauthentic_tests: 0        # check_test_authenticity
  ungoverned_files: 12        # files matching NO contract rule
  measured_at: "YYYY-MM-DD"
```

`ungoverned_files` is the load-bearing field and the one most likely to be dropped: it counts what **no rule covers**. A `0/0/0` beside 400 ungoverned files reports the health of a subset while implying the whole — which is the same false green the other three exist to catch, one level up.

**Why this belongs in BVSSH at all.** Smart's framework separates **output** from **outcome**, and built-but-not-wired is the purest case of output *without* outcome: a mechanism that ships, passes review, raises coverage, appears in the changelog, and does nothing. It bears hardest on three dimensions — **Value** (if delivered-and-inert cannot be distinguished from delivered-and-connected, value claims are not merely hard to measure but *unfalsifiable*), **Safer** (an unwired safety mechanism gives *negative* safety: false assurance displaces the attention that absence would attract), and **Better** (a defect no quality gate catches). It does **not** obviously help **Sooner** — these checks add first-pass friction, and the counter-argument is about avoided rework, not speed. Say that plainly rather than claiming all five.

**Interpreting CALMS with DORA**: DORA tells you WHAT your delivery performance is. CALMS explains WHY. If DORA metrics are poor, CALMS identifies the cultural root cause. If DORA is good but CALMS is weak, the performance is fragile.

## Output

**Lead with the verdict; make Red pop** (Von Restorff, per `harness/design-principles.md` — a declining dimension buried in a uniform table is the one thing the reader must not scroll past; graduated from two consecutive `/framework-health` 4e flags, 2026-06-05 + 2026-06-12):

```
## BVSSH Assessment

> **Verdict: [HEALTHY | N dimension(s) RED/declining — [name them]]** — [one line on the single most important move]

Date: [date]
Diamond: [ID if applicable]

| Dimension | Status | Trend | Key Evidence |
|-----------|--------|-------|-------------|
| Better | Green/Amber/Red | Improving/Stable/Declining | ... |
| Value | Green/Amber/Red | Improving/Stable/Declining | ... |
| Sooner | Green/Amber/Red | Improving/Stable/Declining | ... |
| Safer | Green/Amber/Red | Improving/Stable/Declining | ... |
| Happier | Green/Amber/Red | Improving/Stable/Declining | ... |

### CALMS Culture Health
| Dimension | Status | Key Signal |
|-----------|--------|-----------|
| Culture | Green/Amber/Red | ... |
| Automation | Green/Amber/Red | ... |
| Lean | Green/Amber/Red | ... |
| Measurement | Green/Amber/Red | ... |
| Sharing | Green/Amber/Red | ... |

Overall: [summary and recommended actions]
```

Any **Red** cell (either table) gets a bolded `**Red**` + a one-line `Blocking:`-style callout under its table — never left as an undifferentiated table value.

**A recommended deferral says what it is waiting on, not only when (v0.211.0).** Two kinds of deferral have opposite remedies and one date-shaped sentence hides which is which. **Capacity-deferred** work waits on the founder's hours: give it a date. **Evidence-gated** work waits on someone else to act (a cohort's output, a reply, a third party's calendar): name the dependency and who holds it, and give it a review date, not a due date. Every deferral in the recommended actions carries one of the two words. On 2026-05-23 a run framed three evidence-gated items as capacity-deferred; on 2026-08-18 three horizons set through a holiday expired and were read as findings. A deferral that names its dependency does not expire, it waits.

## Canvas (MANDATORY — the source of truth, do this FIRST)

`.claude/canvas/bvssh-health.yml` is the canonical record. The decision log is provenance; the canvas is what the framework READS. Write the canvas before the decision log — if only one of the two lands, it must be this one.

**APPEND** to `assessment_history`:

```yaml
  - date: "YYYY-MM-DDT00:00:00Z"
    better: "improving|stable|declining"
    value: "improving|stable|declining"
    sooner: "improving|stable|declining"
    safer: "improving|stable|declining"
    happier: "improving|stable|declining"
    notes: |
      Trigger for this assessment; per-dimension evidence; CALMS line;
      Overall verdict + recommended actions.
```

**UPDATE** in the same pass:
1. `last_assessed` (top-level) **and** `calms_assessment.last_assessed` — both, to today. `hooks/session-start.sh` reads the top-level one to compute the "BVSSH overdue" reminder; leaving it stale makes the hook nag overdue forever, immediately after a completed assessment.
2. `calms_assessment.<dimension>.status` + `evidence` for any CALMS dimension whose rating changed. State the downgrade/upgrade reason and, for a downgrade, the recovery bar.
3. `_meta.last_validated` + a one-line `_meta.notes` addition naming what changed.
4. The per-dimension snapshot blocks at the top of the file (`better:`, `value:`, … `current_state` / `trend` / `metrics`) when they no longer match the assessment you just wrote. These are a snapshot of the newest assessment, not history — stale blocks here are the file's most common rot.

**THEN VERIFY** (per the operating contract's verify-after-write rule): re-read the fields you just wrote and confirm the *value fields* changed, not only the timestamps. Do not report the assessment complete until `last_assessed` reads today's date in the file itself.

**Why this section exists (added v0.59.0):** it was missing. The skill mandated the decision-log append and never mentioned the canvas, while `session-start.sh` computed overdue-ness from the canvas — so assessments landed in provenance and never in the file the framework reads. Three orphaned assessments across two repos before the cause was found (2026-05-20 framework; 2026-06-20 + 2026-07-11 dogfood). A prose rule written into a canvas notes field failed to prevent the recurrence, because the skill never had the step. `scripts/check_bvssh_reconcile.py` is the mechanical backstop.

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### BVSSH Assessment — <YYYY-MM-DD>` entry to `.claude/harness/decision-log.md` with: all 5 dimension ratings, CALMS ratings, key evidence, recommended actions.

Keep the date in the heading — `check_bvssh_reconcile.py` matches heading dates against `assessment_history` dates to detect orphans.


## Prior findings first (added v0.96.0)

Before producing new findings, **rule on the previous run's** — per `${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml#prior_findings_first`. For each: CLOSED (name what closed it), STILL-OPEN (carry it forward with a horizon), or DECLINED (a reason AND a re-open trigger). If there is no prior run, say so and continue.

**Scoring goes first because it is the boring half.** A periodic instrument that produces findings and never scores its old ones accumulates a ranking nobody reads — `theory-audit-2026-04-17.md` ranked its gaps and sat unconsumed for four months. Anything placed after the interesting work is what a long session drops.

**A finding ranked HIGH must leave this skill with a home** — tag or create an opportunity on the framework-side root of the OST (`opportunities.yml`, `rolls_up_to`), or decline it with a re-open trigger. Scoring alone does not close the loop: it fires only when someone runs this skill again, so on a slow cadence findings still sleep. An opportunity is read by instruments on their own schedule. Not `human-tasks.yml` — that canvas is scoped to offline HUMAN work (interviews, outreach), and an engineering finding filed there is a category error.

## Theory Citations
- Smart: Sooner Safer Happier (BVSSH framework)
- Willis & Humble: CALMS (Willis coined CAMS at DevOpsDays 2010, Humble added Lean -- explains WHY DORA outcomes are what they are)
- Forsgren: Accelerate (metrics alignment)
