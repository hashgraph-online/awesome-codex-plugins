---
name: corrections-audit
description: "Use to analyze correction trends, surface recurring patterns, and graduate repeat corrections to guardrails or anti-patterns."
metadata:
  instruction_budget: "40"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Corrections Audit Skill

Analyze corrections.md for trends, recurring patterns, and actionable insights.


## Attribution: run the script, do not count by hand

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_correction_attribution.py" --root . --snapshot
```

**Added 2026-08-03.** This audit's headline number — *who caught the mistake* —
was computed by hand and had been produced exactly twice, six weeks apart, each
time because a human remembered to look. It is the only number that answers the
question the correction loop exists to answer: **more harness, or more context.**

The script reports the escape rate **and its denominator, every time**. At the
time of writing 14 of 72 entries carry a catcher, so the rate covers 19% of the
corpus — quoting it without that is a claim about the whole wearing borrowed
clothes, which is the failure this repo spent 2026-08-02/03 removing from its own
checks. If it prints `NO RATE AVAILABLE`, that is not 0%: it means nothing in the
corpus says who caught anything.

`--snapshot` appends the reading to `.claude/evals/metrics/corrections/<date>.json`, the same layout the other metric adapters use. **The level is not the signal.** Trend `caught_by_hook_or_check` rising in absolute terms; the ratio can also be improved by logging fewer user-caught mistakes, which is why this script never gates on it.

**Attribution is a HARD RULE at write time**, not a suggestion — see `engine/agent-operating-contract.md`. It was advisory until 2026-08-03 and 72 of 100 entries carry no catcher as a result. Do not backfill those in bulk: who caught a mistake six weeks ago is not recoverable by inference, and a guessed catcher corrupts the only number this loop produces.

**For entries written before the rule, add one phrase per new entry** — `caught by user`,
`caught by hook`, `caught by review`, `self-caught`. The parser reads the prose
forms already present rather than requiring a new field, so nothing existing
needs rewriting.

## When to Use

- Loop 2 (Incremental) cadence: after every 3+ corrections are logged
- When the same correction category appears 3+ times
- During `/mycelium:diamond-assess` if corrections gate has findings
- Before starting a new diamond at the same scale as a previously corrected one

## Workflow

1. **Load corrections AND warnings AND clusters**: Read `.claude/memory/corrections.md`, `.claude/memory/warnings-log.md`, AND `.claude/memory/cluster-instances.md` (the cluster log graduated 2026-05-08 — canonical record of recurring-pattern instances and their graduation status; without it, "the cluster has graduated N times" has no auditable backing).
   - If corrections + warnings both empty AND no clusters logged: report "No corrections, warnings, or clusters to audit" and stop
   - Treat all three as inputs to the same pattern analysis. Corrections capture agent-introduced failures; warnings capture framework-state debt; cluster-instances capture cross-cluster pattern accumulation with explicit graduation criteria. Same recurring-pattern shape, different vantage points.

2. **Categorize by frequency**:
   - Group corrections by `Category` (bias, security, engineering, process, communication)
   - Group by `Scope` (discovery, delivery, orchestration, quality)
   - Count occurrences per group

3. **Detect recurring patterns**:
   - [ ] Same category appears 3+ times -> candidate for guardrail graduation
   - [ ] Same scope appears 3+ times -> candidate for domain-level CLAUDE.md update
   - [ ] Same mistake repeats after prevention was documented -> prevention strategy failed, needs escalation

4. **Check origin distribution** (APEX alignment):
   - Count corrections by `Origin` (ai-generated, human-written, ai-assisted)
   - If ai-generated corrections dominate (>60%): flag for prompt/context improvement, BUT see `detection_origin` cross-check below before acting on this interpretation
   - If human-written corrections dominate (>60%): flag for process/training improvement
   - If ai-assisted is high: check if the AI contribution or the human contribution caused the issue

4b. **Cross-check with detection_origin** (when field is present — see .claude/memory/README.md):
   - Count corrections by `Detection_origin` if present (user / agent_self / hook / evaluator / eval_runner / external_review)
   - **Critical disambiguation**: if Origin is heavily ai-generated AND detection_origin is heavily `user`, the apparent AI-quality signal is actually a HARNESS-DETECTION GAP. The AI is generating failures and the user is the only entity catching them. The right intervention is more harness checks (hooks, evaluators), NOT more AI context.
   - If detection_origin is dominantly `user` (>70%): flag for harness-detection gap. Suggest where new hooks or evaluators could catch the failure modes earlier.
   - If detection_origin is well-distributed across mechanisms: harness coverage is healthy; trust the Origin signal at face value.
   - Surfaced 2026-05-03 (mycelium-roadmap dogfood): without this cross-check, the audit's "100% ai-generated → improve prompt context" framing would have driven the wrong intervention. Real signal was "AI generates, user catches" — fixed by shipping the framework-guard hook (harness-detection layer), not by improving prompts.

5. **Root-cause recurring corrections** (5 Whys):
   For each correction that appears 3+ times, apply 5 Whys to find the systemic root:
   - Why did this happen? -> Why did that happen? -> ... -> [systemic root cause]
   - Stop when you reach something changeable: a guardrail, gate, process step, or prompt instruction
   - Anti-pattern: stopping at "human error" or "agent didn't follow instructions" — ask why the system allowed it
   *Source: Toyoda/Ohno (5 Whys), adapted for agentic workflows.*

6. **Identify graduation candidates** (across corrections, warnings, AND cluster-instances):
   - Correction logged 3+ times with same root cause -> propose new guardrail (draft G-XX entry) AND ensure a cluster-instances.md entry exists for the pattern
   - Warning class with `Count: 3+` and `Status: open` in `.claude/memory/warnings-log.md` -> graduation candidate. Consult `${CLAUDE_PLUGIN_ROOT}/engine/warning-handbook.md` for the canonical fix; if the canonical fix is "manifest-driven" or similar structural pattern that's already shipped, the recurrence indicates a regression, not a new pattern.
   - Correction reveals a failure mode not in ${CLAUDE_PLUGIN_ROOT}/harness/anti-patterns.md -> propose new anti-pattern entry
   - Correction reveals a successful mitigation -> propose new pattern in patterns.md
   - **Cross-cluster patterns**: when corrections + warnings together reveal the same shape (e.g., "documented rule diverges from enforcement" — fired both via validator gaps in warnings-log AND via agent-behavior corrections), graduate to a meta-pattern in patterns.md and consider whether one upstream mechanism could close both surfaces.

6b. **Cluster-instance audit** (graduated 2026-05-08):
   For each entry in `cluster-instances.md`:
   - **Update instance count**: if any correction logged since the last audit fits an existing cluster's shape, increment that cluster's instance count and add a row to its instance log. If the shape is new and recurs (≥2 candidates), propose a new cluster section.
   - **Check graduation criterion**: each cluster has a stated graduation criterion (e.g., "≥3 instances, ≥3 detection rules validated, <5% FP"). If a cluster has crossed its criterion without being graduated, flag it as a graduation-readiness signal.
   - **Cross-reference spec docs**: if a cluster has a `spec` graduation status (e.g., "documented-rule-diverges-from-enforcement" → `${CLAUDE_PLUGIN_ROOT}/engine/consistency-check-spec.md`), check whether new instances introduce subclass shapes the spec hasn't yet considered. New subclasses extend the spec; recurring known subclasses just increment the count.
   - **Surface mis-counted clusters**: a recurring failure mode silently accumulating without a cluster entry IS the harness-context-debt the cluster log was created to scope. If you find correction patterns that should have been counted but weren't, propose backfill entries.
   - **Recursive check**: a cluster's graduation criterion not being honored is itself an instance of the documented-rule-diverges-from-enforcement cluster. If you detect this, log it as a new instance of that cluster (with appropriate eyebrow-raising in the report).

6c. **Scan `docs/receipts/cases/` frontmatter for graduation signals** (added 2026-05-08 with the docs restructure):
   For each case file in `docs/receipts/cases/*.md`:
   - **Parse YAML frontmatter** (`id`, `date`, `contributor`, `mechanism_or_status`, `commits`, `subclass`).
   - **Cross-reference with `cluster-instances.md`**: if the case's `subclass` field names a known cluster, ensure the cluster's instance count includes this case. If the case is the first instance of a recurring shape that has no cluster entry, propose a new cluster.
   - **Detect mechanism-or-status patterns**: if multiple cases share a `mechanism_or_status: in-progress` and the underlying friction recurs, that is a graduation-readiness signal — the partial fix has not converged. If multiple cases share `mechanism_or_status: one-off`, check whether they actually share a root-cause shape that warrants graduation to a cluster.
   - **Report contributor distribution**: which contributors produce the most receipts? Solo internal-dogfood receipts are valid but the framework's claim of community-shaped feedback weakens if external_human contributor cases are sparse. Flag if external receipts < internal receipts × 0.2 across the last 90 days.
   - **Identify candidate-graduation cases**: a `mechanism_or_status: spec` that has been at spec ≥30 days without a promotion-bar update is a stalled-spec signal worth surfacing.
   *The frontmatter exists specifically so this audit step can detect graduations from cases without parsing prose. See `docs/contributing/style.md#receipts-case-file-frontmatter`.*

6d. **Consistency-as-evidence pattern detection** (added 2026-05-09 with the anti-pattern graduation):
   Scan `corrections.md` entries for the *Consistency-as-Evidence* signature:
   - Mistake involves a generalization (claim of structural significance, "this means", "this generalizes to")
   - At least one piece of supporting evidence in the entry's mistake or correction sections is consistency-only (the data is compatible with the hypothesis but the cause was not isolated)
   - User intervention caught the failure post-publication, not the agent pre-publication
   If 3+ instances within a rolling 90-day window: surface as graduation-confirmed (the anti-pattern *Consistency-as-Evidence* in `${CLAUDE_PLUGIN_ROOT}/harness/anti-patterns.md` #7). If the pattern recurs after graduation, that's a signal the prevention layer needs strengthening (e.g., harden Technique 4 in `/devils-advocate` from skill-time check to ambient hook).

6e. **Stale-state-read pattern detection** (added 2026-05-09 with the anti-pattern graduation):
   Scan `corrections.md` for the *Stale State Read* signature:
   - Mistake involves a script, validator, or check producing nominally-correct output against an outdated reference
   - Root cause: read default was hardcoded local path without explicit-source override, OR a sync flow read pre-replacement state
   - Same epistemic shape as anti-pattern #8 in `${CLAUDE_PLUGIN_ROOT}/harness/anti-patterns.md`
   Track instance count. The 5th instance graduates the prevention layer beyond the existing `parse_manifest.py --manifest=<path>` worked example: scan the codebase via `validate-template.sh` Check 29 for state-reading scripts that lack explicit-source parameters. Until then, the anti-pattern entry is the primary defense.

7. **Consolidate memory files** (automated hygiene):
   - **Deduplication**: Identify corrections that describe the same root cause in different words. Merge into a single entry, preserving all dates and evidence.
   - **Contradiction detection**: Flag corrections that contradict each other (e.g., "always use X" vs "never use X"). Present conflicts to the user for resolution.
   - **Staleness removal**: Corrections older than 6 months whose prevention has been verified effective (no recurrence) can be archived to `.claude/memory/corrections-archive.md`.
   - **Size cap**: If corrections.md exceeds 50 entries, consolidate the oldest resolved entries into a summary paragraph in the archive.
   - Apply the same consolidation to `.claude/memory/patterns.md`.
   *Inspired by: greyhaven-ai/autocontext curator agent — periodic dedup, cap, and contradiction removal.*

8. **Update TL;DR section**:
   - Regenerate the TL;DR in corrections.md with the top 5 most impactful corrections
   - Impact = frequency x severity (blocking vs. quality vs. cosmetic)

9. **Recommend actions**:
   - For each graduation candidate: specific guardrail text, tier, and constraint type
   - For failed preventions: what went wrong and what stronger mechanism to use
   - For origin imbalances: specific context improvements

## Output Format

```
## Corrections Audit

### Summary
Total corrections: [N]
Period: [earliest date] to [latest date]

### Frequency Analysis
| Category | Count | Trend |
|----------|-------|-------|
| engineering | 3 | rising |
| bias | 1 | stable |

### Origin Distribution
| Origin | Count | % |
|--------|-------|---|
| ai-generated | 4 | 57% |
| human-written | 2 | 29% |
| ai-assisted | 1 | 14% |

### Recurring Patterns
- [Pattern description]: [N] occurrences -> [recommendation]

### Cluster Status (from cluster-instances.md)
| Cluster | Instances | Status | Graduation criterion | Notes |
|---|---|---|---|---|
| documented-rule-diverges-from-enforcement | 8 | spec | ≥3 detection rules validated, <5% FP | Spec at ${CLAUDE_PLUGIN_ROOT}/engine/consistency-check-spec.md (graduated 2026-05-08) |

### Graduation Candidates
1. [Correction pattern] -> Proposed guardrail: G-XX "[text]" `[TIER]` `[type]`
2. [Cluster X reaching its graduation criterion] -> Proposed promotion from <current_status> to <next_status>: <action>

### Failed Preventions
- [Correction] was logged again despite prevention "[strategy]" -> [escalation]

### TL;DR Update
[Updated summary for corrections.md TL;DR section]
```


## Prior findings first (added v0.96.0)

Before producing new findings, **rule on the previous run's** — per `${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml#prior_findings_first`. For each: CLOSED (name what closed it), STILL-OPEN (carry it forward with a horizon), or DECLINED (a reason AND a re-open trigger). If there is no prior run, say so and continue.

**Scoring goes first because it is the boring half.** A periodic instrument that produces findings and never scores its old ones accumulates a ranking nobody reads — `theory-audit-2026-04-17.md` ranked its gaps and sat unconsumed for four months. Anything placed after the interesting work is what a long session drops.

**A finding ranked HIGH must leave this skill with a home** — tag or create an opportunity on the framework-side root of the OST (`opportunities.yml`, `rolls_up_to`), or decline it with a re-open trigger. Scoring alone does not close the loop: it fires only when someone runs this skill again, so on a slow cadence findings still sleep. An opportunity is read by instruments on their own schedule. Not `human-tasks.yml` — that canvas is scoped to offline HUMAN work (interviews, outreach), and an engineering finding filed there is a category error.

## Theory Citations
- Mycelium internal learning loop
- APEX framework (origin-aware quality tracking)
- Senge: systems thinking (recurring patterns signal structural issues)
