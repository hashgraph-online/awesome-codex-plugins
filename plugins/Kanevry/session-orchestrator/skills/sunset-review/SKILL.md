---
name: sunset-review
description: Use this skill when the user wants to identify unused, near-zero-use, or stale skills/agents/commands in the plugin surface so they can be demoted or retired. Combines agent-dispatch telemetry (start-events only) with static reference scanning, classifies every surface item into Active / Investigate / Demote / Retire, and emits a Markdown report plus JSON sidecar. NEVER auto-deletes — surfaces candidates for human decision. Quarterly cadence. <example>Context: The plugin surface has grown and the maintainer wants to prune dead weight. user: "/sunset-review" assistant: "Running the sunset walk — classifying skills, agents, and commands by usage telemetry + static refs, grouped by Retire / Demote / Investigate / Active. No item is deleted automatically; I'll surface Retire/Demote candidates for your decision." <commentary>The user wants a usage-driven prune candidate list; this skill runs the read-only walker, presents grouped verdicts, and writes a sidecar — it never deletes.</commentary></example>
model: inherit
color: amber
---

# Sunset Review Skill

Identify which skills, agents, and commands in the plugin surface are still earning their keep, and which are candidates to **Demote** (downgrade docs/tier) or **Retire** (remove). The skill is advisory: it produces a ranked candidate list and a sidecar artifact. **It never deletes anything.**

## Why this is a distinct skill (not /repo-audit)

`/repo-audit` answers "does this repo match the ecosystem baseline?" — a pass/fail compliance check. `/sunset-review` answers a different question — "which parts of OUR surface are unused?" — with different inputs (dispatch telemetry + static ref scanning), a different cadence (quarterly, not per-session), and a different output (prune candidates, not compliance status). Folding it into repo-audit would muddy both.

## Core data contract (read this before trusting any verdict)

The walker — `scripts/lib/sunset/walker.mjs` — is **read-only** and was built against the following grep-verified telemetry facts. Do not override them:

1. **Both agent dispatch and skill-invocation telemetry are now consumed.** `subagents.jsonl` records agent dispatches; `skill-invocations.jsonl` records Skill tool selection events (L1 telemetry, epic #645). Agents are assessed by agent-dispatch counts; **skills are assessed by real selection counts from `skill-invocations.jsonl`, supplemented by static reference scanning.** Commands still have no invocation telemetry and are assessed by static reference scanning only. Skills with zero invocations in the window receive a zero-count (not null), so the low-coverage guard still applies and can downgrade Retire → Investigate when the telemetry window is short.
2. **Only `event === "start"` records count.** `agent_type` is `null` on every `stop` event. A stop event must never mark an agent cold. The walker filters to start events.
3. **Telemetry only spans ~18 days.** A 90-day window cannot be satisfied by 18 days of data. **MANDATORY GUARDRAIL:** when `coverageDays < windowDays`, every `Retire` verdict is downgraded to `Investigate` and `meta.lowConfidence` is set true. Retiring on sub-window data is unsafe — treat any cold finding as "investigate", not "delete".
4. **Zero ≠ near-zero.** A never-dispatched agent (e.g. `memory-proposal-collector`, a by-design reference doc) is a Retire candidate; a once-dispatched agent (`db-specialist`, `ui-developer` at n=1) is a Demote candidate. The walker distinguishes them.

## Verdict tiers

| Verdict | Meaning | Action posture |
|---|---|---|
| **Active** | Agent dispatch above floor, OR skill invoked-by-command / command invokes-a-live-skill, OR ≥2 non-boilerplate refs | Keep |
| **Investigate** | Coverage < window (low-confidence), OR conflicting signals — **default-safe bucket** | Manual review |
| **Demote** | Single dispatch (n=1), OR a skill with a single cross-ref and no command linkage | Consider downgrading docs/tier |
| **Retire** | `dispatch===0` AND `nonBoilerplateRefs===0` AND `coverage>=window` | Strong remove candidate (verify first) |

## Phases

### Phase 1 — Resolve config + window
- Read Session Config for any `sunset-review.window-days` override; default to 90 (`DEFAULT_WINDOW_DAYS`).
- The window is the period over which dispatch counts are tallied. Keep the default unless the operator has a reason to narrow it.

### Phase 2 — Run the walker (JSON mode)
Run the read-only walker and capture its JSON:

```bash
node scripts/lib/sunset/walker.mjs --json --window-days 90 > /tmp/sunset-walk.json
```

Exit 0 = walk completed (cold findings are exit 0, **not** an error). Exit 1 = bad args / surface dir missing. Exit 2 = system error. The walker writes no files — it is pure analysis.

Optionally scope to one kind for focused review:

```bash
node scripts/lib/sunset/walker.mjs --json --kind agent
```

### Phase 3 — Classify & present (NEVER auto-delete)
- Group the `items[]` array by `verdict`, ordered Retire → Demote → Investigate → Active.
- Lead with `meta.lowConfidence`. If true, state plainly: "telemetry covers only N days (< window); all Retire candidates were downgraded to Investigate — do not retire anything this run."
- For each Retire/Demote candidate, show its `reasons[]` and `signals{}` so the operator can sanity-check the verdict against their own knowledge (a low-traffic-but-load-bearing item should be spared).

### Phase 4 — Emit report + sidecar
Mirror the repo-audit sidecar convention. Write both:
- **Markdown report:** `.orchestrator/metrics/sunset-review-<unix-timestamp>.md` — the grouped, human-readable verdict list with reasons.
- **JSON sidecar:** the walker's full JSON output, persisted alongside for trend tracking.

```bash
mkdir -p .orchestrator/metrics
```

The sidecar is the durable record; the Markdown is the readable summary.

**Skill Health (advisory)** — render a per-skill health advisory block into the report.
- **Source:** per-skill verdicts come from `scoreSkillHealth()` in `scripts/lib/skill-health/score.mjs`, computed over the L2 join (`scripts/lib/skill-health/join.mjs`) plus any optional L3 judgments — the same telemetry the walker already surfaces on `item.signals.judge`. The mechanical/CI surface for this data is harness-audit `category9` ("Skill-Health Surfacing").
- **Rendering:** add a `## Skill Health` section to the Markdown report. List each skill that has sufficient samples with its `verdict` (`insufficient signal` | `trigger description unclear` | `instructions wrong`) and its `diagnosis` string. Skills below the sample threshold (`MIN_SAMPLES_FOR_VERDICT`, ~20) are NOT scored per-skill — collapse them into a single line: "Insufficient signal (N skills)".
- **Firewall (MANDATORY):** the health advisory NEVER edits any skill file and NEVER pushes a skill toward Retire or Demote on health data alone. It may only annotate the existing verdict, or trigger the existing Active→Investigate downgrade the walker already applies — never an escalation. This mirrors the walker's advisory-only judge firewall: annotate or downgrade-to-Investigate, never escalate toward Retire/Demote.
- **Default-empty:** when telemetry is absent or insufficient (the common case today), render exactly "Skill Health: insufficient signal across all skills (no action)". This is a healthy state, not a finding — do not surface it as a candidate.

### Phase 5 — Cadence note (the SKILL writes last-run, NOT the walker)
- Sunset review runs **quarterly**. The walker is stateless and writes no runtime file — recording the last-run timestamp is **this skill's** responsibility, so a session-start nudge can fire when a quarter has elapsed.
- After writing the report, record the run time (e.g. into `.orchestrator/metrics/sunset-review-last-run.json` with an ISO timestamp). This keeps the walker free of mutable runtime state and concurrency surface.

## Draft-issue creation (coordinator-side only — AUQ-004)

If the operator wants to file removal/demotion issues for the surfaced candidates, that decision **must be made by the coordinator via `AskUserQuestion`** — a dispatched agent cannot call `AskUserQuestion` (AUQ-004). When this skill runs inside a dispatched agent, it surfaces the candidate list and defers issue creation to the coordinator thread. Never auto-file issues and never auto-delete surface items.

## Output Summary
- Grouped verdict list printed to the user (Retire/Demote/Investigate/Active).
- Markdown report at `.orchestrator/metrics/sunset-review-<timestamp>.md`.
- JSON sidecar (walker output) alongside.
- Last-run timestamp recorded for the quarterly cadence nudge.
- **Zero deletions. Zero auto-filed issues.**

## See Also
- `scripts/lib/sunset/walker.mjs` — the read-only walker (CLI + exported functions).
- `skills/repo-audit/SKILL.md` — the sibling compliance audit (different question).
- `.claude/rules/cli-design.md` — JSON-first / exit-code contract the walker follows.
- `.claude/rules/ask-via-tool.md` — AUQ-004 (agents cannot call AskUserQuestion).
