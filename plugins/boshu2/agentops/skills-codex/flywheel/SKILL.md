---
name: flywheel
description: Check knowledge flywheel health.
---
# Flywheel Skill

> **Loop position:** move 7 (capture + ratchet) of the [operating loop](../../docs/architecture/operating-loop.md) — monitors the knowledge-pool health that the promotion ratchet feeds.
Monitor the knowledge flywheel health.
## The Flywheel Model
```
Sessions → Transcripts → Forge → Pool → Promote → Knowledge
     ↑                                               │
     └───────────────────────────────────────────────┘
                    Future sessions find it
```

**Velocity** = rate of knowledge flowing through. **Friction** = bottlenecks slowing the flywheel.

### Folded triggers (ag-s43tg wave 1): `ratchet` routes here

- **`ratchet` → flywheel gate tracking.** Use when asked to record Brownian Ratchet gates —
  tracking progress through the RPI workflow with permanent gates
  (`Progress = Chaos × Filter → Ratchet`; merged/closed/stored progress can't be un-ratcheted).
- Gate surface: `ao ratchet status` / `ao ratchet check <step>` / `ao ratchet record <step>
  --output "<artifact-path>"` over the chain at `.agents/ao/chain.jsonl`
  (steps: `research`, `plan`, `implement`, `vibe`, `post-mortem`).
- Ratchet tracks and locks progress; it does not run the loop itself — pair with `$crank`
  (epic loop) or `$swarm` (Ralph loop) to execute work.

## Execution Steps
Given `$flywheel`:
### Step 1: Measure Knowledge Pools
```bash
# Count top-level artifact files (avoid counting directories)
LEARNINGS=$(find .agents/learnings -maxdepth 1 -type f 2>/dev/null | wc -l)
PATTERNS=$(find .agents/patterns -maxdepth 1 -type f 2>/dev/null | wc -l)
RESEARCH=$(find .agents/research -maxdepth 1 -type f 2>/dev/null | wc -l)
RETROS=$(find .agents/retros -maxdepth 1 -type f 2>/dev/null | wc -l)
echo "Learnings: $LEARNINGS"
echo "Patterns: $PATTERNS"
echo "Research: $RESEARCH"
echo "Retros: $RETROS"
```

### Step 2: Check Recent Activity
```bash
# Recent learnings (last 7 days)
find .agents/learnings -maxdepth 1 -type f -mtime -7 2>/dev/null | wc -l
# Recent research
find .agents/research -maxdepth 1 -type f -mtime -7 2>/dev/null | wc -l
```
### Step 3: Detect Staleness
```bash
# Old artifacts (> 30 days without modification)
find .agents/ -name "*.md" -mtime +30 2>/dev/null | wc -l
```
### Step 3.5: Check Cache Health
```bash
if command -v ao &>/dev/null; then
  # Get citation report (cache metrics)
  CITE_REPORT=$(ao metrics cite-report --json --days 30 2>/dev/null)
  if [ -n "$CITE_REPORT" ]; then
    HIT_RATE=$(echo "$CITE_REPORT" | jq -r '.hit_rate // "unknown"')
    UNCITED=$(echo "$CITE_REPORT" | jq -r '(.uncited_learnings // []) | length')
    STALE_90D=$(echo "$CITE_REPORT" | jq -r '.staleness["90d"] // 0')
    echo "Cache hit rate: $HIT_RATE"
    echo "Uncited learnings: $UNCITED"
    echo "Stale (90d uncited): $STALE_90D"
  fi
else
  # ao-free fallback: compute approximate metrics from files
  echo "Cache health (ao-free fallback):"
  echo "Active learnings (30d): $(find .agents/learnings/ -name '*.md' -mtime -30 2>/dev/null | wc -l | tr -d ' ')"
  echo "Forge candidates pending: $(ls .agents/forge/*.md 2>/dev/null | wc -l | tr -d ' ')"
  if [ -f .agents/ao/citations.jsonl ]; then
    echo "Total citations: $(wc -l < .agents/ao/citations.jsonl | tr -d ' ')"
    echo "Unique learnings cited: $(grep -o '"artifact_path":"[^"]*"' .agents/ao/citations.jsonl 2>/dev/null | sort -u | wc -l | tr -d ' ')"
  else
    echo "No citation data (citations.jsonl not found)"
  fi
  [ -f .agents/ao/outcomes.jsonl ] && echo "Session outcomes recorded: $(wc -l < .agents/ao/outcomes.jsonl | tr -d ' ')"
fi
```

### Step 4: Check ao CLI Status

```bash
if command -v ao &>/dev/null; then
  ao metrics flywheel status 2>/dev/null || echo "ao metrics flywheel status unavailable"
  ao status 2>/dev/null || echo "ao status unavailable"
  ao maturity --scan 2>/dev/null || echo "ao maturity unavailable"
  ao anti-patterns 2>/dev/null || echo "ao anti-patterns unavailable"
  ao badge 2>/dev/null || echo "ao badge unavailable"

  # Knowledge maintenance
  ao dedup --merge 2>/dev/null || true
  ao contradict 2>/dev/null || true
  ao constraint review 2>/dev/null || true
  ao curate status 2>/dev/null || true
  ao metrics health 2>/dev/null || true
  ao metrics cite-report --days 30 2>/dev/null || true

  # Active pruning: archive stale, evict low-utility, and curate noisy uncited learnings
  ao maturity --expire --archive 2>/dev/null || true
  ao maturity --evict --archive 2>/dev/null || true
  ao maturity --curate --archive 2>/dev/null || true

  # Retrieval quality: use the representative live corpus when it exists
  if [ -d cli/cmd/ao/testdata/retrieval-bench-live ]; then
    ao retrieval-bench --live --corpus cli/cmd/ao/testdata/retrieval-bench-live --json 2>/dev/null || true
  fi
else
  echo "ao CLI not available — using file-based metrics"
  echo "Pool depths:"
  for pool in learnings patterns forge knowledge research retros; do
    echo "  $pool: $(ls .agents/${pool}/*.md 2>/dev/null | wc -l | tr -d ' ')"
  done
  echo "  global patterns: $(ls ~/.codex/patterns/*.md 2>/dev/null | wc -l | tr -d ' ')"
  echo "See references/promotion-tiers.md for tier definitions"
fi
```

### Step 4.5: Process Metrics (from skill telemetry)

If `.agents/ao/skill-telemetry.jsonl` exists, use `jq` to extract: invocations by skill, average cycle time per skill, gate failure rates. Include in health report (Step 6) under `## Process Metrics`.

### Step 5: Validate Artifact Consistency

Cross-reference validation: scan knowledge artifacts for broken internal references.
Use `scripts/artifact-consistency.sh` (method documented in `references/artifact-consistency.md`).
Default allowlist lives at `references/artifact-consistency-allowlist.txt`; use `--no-allowlist` for a full raw audit.

Health indicator: >90% = Healthy, 70-90% = Warning, <70% = Critical.

### Step 6: Write Health Report

**Write to:** `.agents/flywheel-status.md`

```markdown
# Knowledge Flywheel Health

**Date:** YYYY-MM-DD

## Pool Depths
| Pool | Count | Recent (7d) |
|------|-------|-------------|
| Learnings | <count> | <count> |
| Patterns | <count> | <count> |
| Research | <count> | <count> |
| Retros | <count> | <count> |

## Velocity (Last 7 Days)
- Sessions with extractions: <count>
- New learnings: <count>
- New patterns: <count>

## Artifact Consistency
- References scanned: <count>
- Broken references: <count>
- Consistency score: <percentage>%
- Status: <Healthy/Warning/Critical>

## Cache Health
- Hit rate: <percentage>%
- Uncited learnings: <count>
- Stale (90d uncited): <count>
- Status: <Healthy/Warning/Critical>

## Retrieval Quality
- Live corpus coverage: <percentage or unavailable>
- Live corpus learnings: <count or unavailable>
- Status: <Healthy/Warning/Critical>

## Health Status
<Healthy/Warning/Critical>

## Friction Points
- <issue 1>
- <issue 2>

## Recommendations
1. <recommendation>
2. <recommendation>
```

### Step 7: Report to User

Tell the user:
1. Overall flywheel health
2. Knowledge pool depths
3. Recent activity
4. Any friction points
5. Recommendations

## Health Indicators

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Learnings/week | 3+ | 1-2 | 0 |
| Stale artifacts | <20% | 20-50% | >50% |
| Research/plan ratio | >0.5 | 0.2-0.5 | <0.2 |
| Cache hit rate | >80% | 50-80% | <50% |

## Golden Signals

Four golden signals (always shown) reveal whether knowledge is truly compounding or just accumulating noise.

```bash
ao flywheel status              # table output with golden signals
ao flywheel status --json       # machine-readable
```

### The Four Signals

| # | Signal | Question | Key Metric |
|---|--------|----------|------------|
| 1 | **Velocity Trend** | Is σρ-δ increasing? | Linear regression slope of baseline velocities (7d/30d) |
| 2 | **Citation Pipeline** | Are citations useful? | % of feedback with reward > 0.6 |
| 3 | **Research Closure** | Is research being mined? | % orphaned research (no learning backlink) |
| 4 | **Reuse Concentration** | Is the whole pool active? | Gini coefficient of citation distribution |

### Verdicts and Thresholds

| Signal | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Velocity Trend | compounding (slope > +0.01) | stagnant | decaying (slope < -0.01) |
| Citation Pipeline | reinforcing (>60% high-util) | inert (30-60%) | degrading (<30%) |
| Research Closure | mining (<=10% orphans) | — | hoarding (>=10% orphans) |
| Reuse Concentration | distributed (Gini<0.4, active>30%) | concentrated | dormant (Gini>0.7 or active<10%) |

**Overall verdict:** 3+ healthy = **compounding**, 3+ critical = **decaying**, mixed = **accumulating**.

### Recommended Actions

| Verdict | Action |
|---------|--------|
| **decaying** | Run `$compile` cycle, archive stale artifacts, increase citation via `ao lookup` |
| **accumulating** | Review orphaned research (`$research`→`$post-mortem --quick` pipeline), improve forge quality |
| **compounding** | Maintain cadence. Consider capturing baselines (`ao metrics baseline`) for trend tracking |

## Cache Eviction
Read `references/cache-eviction.md` for the full eviction pipeline (passive tracking → confidence decay → maturity scan → archive).

## Hub Budget & Phase 4 Hardening

Phase 4 (soc-ytpq) governance for `~/.agents/learnings/` — all advisory, none block by default. Full details in `references/hub-budget.md`.

- **Size budget:** target ≤ 250 MB / ≤ 5,000 files. Restore via `ao maturity --evict --target-size=250M` (lowest-utility-first; respects `lifecycle.IsEvictionEligible` so canonical / high-confidence files are protected).
- **Volume gate:** `ao harvest` WARNs when promotions exceed `--max-promotions=N` (default 500; `AO_MAX_PROMOTIONS=N` env as fallback; ≤0 disables). WARN-only — the 2,638-promotion `soc-ujls` drain proves a hard gate would falsely block legitimate runs.
- **Provenance:** every promoted file carries `source_rig:` in its frontmatter (empty writers serialize as `source_rig: unknown`). Both `harvest.Promote` and `pool.(*Pool).Promote` content-dedup against the same hub via `~/.agents/pool/promoted-index.jsonl`.
- **Re-bloat triage:** check `SkipGlobalHub` defaults to `true` (the agentops-b3v / soc-ujls fix), then `grep -h '^source_rig:' ~/.agents/learnings/*.md | sort | uniq -c | sort -rn` to identify the regressed writer. Use `--target-size`, never raw `rm`.

## Key Rules
- **Monitor regularly** - flywheel needs attention; address bottlenecks early
- **Feed the flywheel** - run $post-mortem (or $post-mortem --quick)
- **Prune stale knowledge** - archive old artifacts
## Examples
**User says:** `$flywheel` — Counts pool depths, checks recent activity, validates artifact consistency, writes health report to `.agents/flywheel-status.md`.
**Hook trigger:** After `$post-mortem` — Compares current vs historical metrics, flags velocity drops and friction points.
## Troubleshooting
| Problem | Cause | Solution |
|---------|-------|----------|
| All pool counts zero | `.agents/` directory missing or empty | Run `$post-mortem` (or `--quick`) to seed knowledge pools |
| Velocity always zero | No recent extractions (last 7 days) | Run `$post-mortem` (or `--quick`) to extract and index learnings |
| "ao CLI not available" | ao command not installed or not in PATH | Install ao CLI or use manual pool counting fallback |
| Stale artifacts >50% | Long time since last session or inactive repo | Run `/provenance --stale` to audit and archive old artifacts |

## Reference Documents
- [references/artifact-consistency.md](references/artifact-consistency.md)
- [references/promotion-tiers.md](references/promotion-tiers.md)
- [references/hub-budget.md](references/hub-budget.md)
- [references/cache-eviction.md](references/cache-eviction.md)
- [references/flywheel-cli.feature](references/flywheel-cli.feature) — Executable spec: `ao flywheel` CLI command behavior, linked to cmd tests (soc-jnfgi)
