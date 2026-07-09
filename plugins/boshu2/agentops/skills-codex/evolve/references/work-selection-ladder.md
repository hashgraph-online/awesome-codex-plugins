# /evolve — Work-Selection Ladder (Step 3, full procedure)

> Extracted from `skills/evolve/SKILL.md` Step 3 to keep the skill under the 10000-token ceiling (soc-opq5). SKILL.md keeps the summary + this pointer; this file owns the full per-rung procedure, code blocks, quality cascade, and dormancy hard-gate.

Selection is a ladder, not a one-shot check. After every productive cycle, return to the TOP of this step and re-read the queue before considering dormancy.

**Programmatic recommendation (soc-g2qd wire):** when present, consult the ladder primitive first and prefer its `.recommended_bead`; the rungs below are the cross-check + fallback.

```bash
ao loop next-work --help >/dev/null 2>&1 && RECO_BEAD=$(ao loop next-work --json 2>/dev/null | jq -r '.recommended_bead // empty')
```

When a repo-local program contract exists, apply a scope filter before Step 4:
- candidate work that clearly requires immutable-scope edits is not eligible for direct execution
- prefer harvested, beads, goals, and generated work that can plausibly land within mutable scope
- if the selected item is inherently out of scope, escalate it or convert it into durable follow-up work instead of invoking `/rpi` and hoping discovery widens scope

**Step 3.0: Scope filter — split-or-defer, never bail (soc-5qit)**

Before claiming a candidate, gate scope vs session budget. If the work touches > 5 non-uniform files, introduces a new shape (schema field, validator, contract surface), is operator-level epic work, OR `PRODUCTIVE_THIS_SESSION > 5` and would extend an arc rather than close one — route to **scout-mode**, which MUST produce one of:

1. **Split** — `bd create` 2-N child beads (each ≤5 files, single-shape) with `--deps discovered-from:<parent-id>`, annotate parent, then **re-enter Step 3** so the smallest child (or another ready bead) gets claimed THIS cycle.
2. **Defer** — annotate the candidate with `defer:<reason>` and re-enter Step 3 so the next-priority ready bead gets claimed.
3. **Park** (rare) — `bd update <id> --status blocked --notes "scope-too-big"` and re-enter Step 3.

Scout NEVER returns "no work done." If `bd ready` ≥1, the loop MUST claim one this cycle. See `references/scout-mode.md` and `references/mechanical-batches.md`.

**Metronome gate:** read `mode_repeat_streak` from `session-state.json`. If `>= 3` AND the candidate would repeat the trailing run's `mode`, BLOCK this rung and jump to the next. If `>= 5`, record the gap as bead/provenance evidence and require operator override. See `references/metronome-gate.md`.

**Step 3.1: Harvested work first**

Read `.agents/rpi/next-work.jsonl` and pick the highest-value unconsumed item. Prefer exact repo match, then concrete implementation work, then higher severity. Read `references/knowledge-loop-integration.md` for the claim/release protocol.

**Step 3.2: Open ready beads**

If no harvested item is ready, check `bd ready`. Pick the highest-priority unblocked issue.

**Step 3.3: Failing goals and directive gaps** (skip if `--beads-only`)

First assess directives, then goals:
- top-priority directive gap from `ao goals measure --directives`
- highest-weight failing goals (skip quarantined oscillators)
- lower-weight failing goals

This step exists even when all queued work is empty. Goals are the third source, not the stop condition.

```bash
DIRECTIVES=$(ao goals measure --directives 2>/dev/null)
FAILING=$(jq -r '.goals[] | select(.result=="fail") | .id' .agents/evolve/fitness-latest.json | head -1)
```

**Oscillation check:** Before working a failing goal, check if it has oscillated (improved-to-fail transitions >= 3 times). If so, quarantine it and try the next goal. See `references/oscillation.md` and `references/fitness-scoring.md` for the detection procedure.

**Duplicate-work guard (mandatory before every generator `bd create`).** The
generators below (3.4–3.7) and the Step-4 Split rung all create beads. A stale
phase-1 handoff repeatedly re-seeded beads for work already covered by an
existing bead or merged PR (ag-b8m≈ag-jov, ag-6kw≈ag-c2i — ag-6jt). Before
`bd create`, run the guard; skip creation when it reports a duplicate:

```bash
skills/evolve/scripts/duplicate-work-guard.sh "<candidate title>" || {
  echo "skip: existing work already covers this surface"; }
# exit 1 + "DUPLICATE: <id> [<status>] <title>" → an open/closed bead already
# covers it (exact title OR significant-token overlap). exit 0 → safe to create.
```

This complements the loop's origin/main fast-forward: the cron runs
`skills/evolve/scripts/sync-main-to-origin.sh` before discovery (wired into
`scripts/overnight-evolve.sh`), which fetches origin and fast-forwards local
`main` to `origin/main` so discovery diffs candidate slices against the true
merge base — already-merged work reports as done, not re-seen (ag-6jt). Run it
manually in any rpi worktree whose local `main` may be stale:

```bash
skills/evolve/scripts/sync-main-to-origin.sh
# → "DIFF_BASE: origin/main <sha>" — diff slices against THIS, not local main.
```

**Step 3.4: Testing improvements**

When queues and goals are empty, generate concrete testing work via `/test`:

```
if --no-lifecycle is NOT set:
  Skill(skill="test", args="coverage")
  Only files with < 40% coverage become queue items (severity threshold).
```

If `/test` is unavailable or `--no-lifecycle` is set, fall back to manual scanning:
- find packages/files with thin or missing tests
- look for missing regression tests around recent bug-fix paths
- identify flaky or absent headless/runtime smokes

Convert any real finding into durable work:
- add a bead when the work needs tracked backlog ownership, or
- append a queue item under the shared next-work contract when it should flow directly back into `/rpi`

**Step 3.5: Validation tightening and bug-hunt passes**

If testing improvement generation returns nothing, run lifecycle generators then bug-hunt sweeps:

```
if --no-lifecycle is NOT set:
  a) Skill(skill="deps", args="audit")
     Only deps with CVSS >= 7.0 or 2+ major versions behind become queue items.

  b) if perf-sensitive code detected (benchmarks exist, hot path patterns):
       Skill(skill="perf", args="profile --quick")
       Convert significant perf findings to queue items.
```

If lifecycle generators return nothing or are skipped, fall back to manual sweeps:
- missing validation gates
- weak lint/contract coverage
- bug-hunt style audits for risky areas
- stale assumptions between docs, contracts, and runtime truth

Again: convert findings into beads or queue items, then immediately select the highest-priority result and continue.

**Step 3.6: Drift / hotspot / dead-code mining**

If the prior generators are empty, mine for complexity debt via `/refactor`:

```
if --no-lifecycle is NOT set:
  Skill(skill="refactor", args="--sweep all --dry-run")
  Only functions with CC > 20 become queue items (severity threshold).
```

If `/refactor` is unavailable or `--no-lifecycle` is set, fall back to manual mining:
- complexity hotspots
- stale TODO/FIXME markers
- dead code
- stale docs
- stale research
- drift between generated artifacts and source-of-truth files

Do not stop here. Normalize findings into tracked work and continue.

**Step 3.7: Feature suggestions**

If all concrete remediation layers are empty, propose one or more specific feature ideas grounded in the repo purpose, write them as durable work, and continue:
- create a bead when the feature needs review/backlog treatment
- or append a queue item with `source: "feature-suggestion"` when it is ready for the next `/rpi` cycle

**Quality mode (`--quality`)** — inverted cascade (findings before directives):

Step 3.0q: Unconsumed high-severity post-mortem findings:
```bash
HIGH=$(jq -r 'select(.consumed==false) | .items[] | select(.severity=="high") | .title' \
  .agents/rpi/next-work.jsonl 2>/dev/null | head -1)
```

Step 3.1q: Unconsumed medium-severity findings.

Step 3.2q: Open ready beads.

Step 3.3q: Emergency gates (weight >= 5) and top directive gaps.

Step 3.4q: Testing improvements.

Step 3.5q: Validation tightening / bug-hunt / drift mining.

Step 3.6q: Feature suggestions.

This inverts the standard cascade only at the top of the ladder: findings BEFORE goals and directives. It does NOT skip the generator layers.

When evolve picks a finding, claim it first in next-work.jsonl:
- Set `claim_status: "in_progress"`, `claimed_by: "evolve-quality:cycle-N"`, `claimed_at: "<timestamp>"`
- Set `consumed: true` only after the /rpi cycle and regression gate succeed
- If the /rpi cycle fails (regression), clear the claim and leave `consumed: false`

See `references/quality-mode.md` for scoring and full details.

**Nothing found?** HARD GATE — dormancy only when ALL sources empty (soc-5qit):

```bash
READY_BEADS=$(ao beads exec ready --json 2>/dev/null | jq -r 'length // 0' 2>/dev/null || echo 0)
HARVESTED=$(jq -r 'select(.consumed==false) | .severity' .agents/rpi/next-work.jsonl 2>/dev/null | wc -l | tr -d ' ')
FAILING_GOALS=$(jq -r '.goals[] | select(.result=="fail") | .id' .agents/evolve/fitness-latest.json 2>/dev/null | wc -l | tr -d ' ')
IDLE_STREAK=$(jq -r '.idle_streak // 0' .agents/evolve/session-state.json 2>/dev/null)

if [ "$READY_BEADS" -gt 0 ] || [ "$HARVESTED" -gt 0 ] || [ "$FAILING_GOALS" -gt 0 ]; then
  continue  # work exists — loop back to Step 3 (agile invariant)
fi
if [ "${GENERATOR_EMPTY_STREAK:-0}" -ge 2 ] && [ "${IDLE_STREAK:-0}" -ge 2 ]; then
  REASON="stagnation: all sources empty x3"
  # soc-g2qd wire: under loop, write-stop-marker refuses → log blocked + operator-wait, never self-halt (ADR-0007).
  if ao loop write-stop-marker --help >/dev/null 2>&1; then
    ao loop write-stop-marker --marker dormant --reason "$REASON" --mode loop 2>/dev/null \
      || ao loop blocked --reason "$REASON" --needed-context "queue empty; operator adds work or marker" 2>/dev/null || true
  else
    printf '%s\n%s\n%s\n' "cycle $CYCLE" "$(date -u +%FT%TZ)" "$REASON" > .agents/evolve/DORMANT  # fallback
  fi
fi
```

**Agile invariant (soc-5qit):** `bd ready ≥ 1` ⇒ loop NEVER writes DORMANT, NEVER exits. The only path to DORMANT is fully empty backlog + dry generators. Context exhaustion → HANDOFF, not DORMANT.

If work layers were empty but generators haven't exhausted 3 passes yet, persist `GENERATOR_EMPTY_STREAK` and loop back to Step 1.

A cycle is idle only if NO work source returned actionable work and every generator layer also came up empty. A cycle that targeted an oscillating goal and skipped it counts as idle only after the remaining ladder was exhausted.

If `--dry-run`: report what would be worked on and go to Teardown.
