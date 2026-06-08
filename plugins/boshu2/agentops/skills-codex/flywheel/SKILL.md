---
name: flywheel
description: "Run flywheel."
---
# Flywheel Skill
Monitor the knowledge flywheel health.
## The Flywheel Model
```
Sessions → Transcripts → Forge → Pool → Promote → Knowledge
     ↑                                               │
     └───────────────────────────────────────────────┘
                    Future sessions find it
```

**Velocity** = Rate of knowledge flowing through
**Friction** = Bottlenecks slowing the flywheel

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

  # Learnings modified in last 30 days (active pool)
  ACTIVE_30D=$(find .agents/learnings/ -name "*.md" -mtime -30 2>/dev/null | wc -l | tr -d ' ')
  echo "Active learnings (30d): $ACTIVE_30D"

  # Forge candidates awaiting promotion
  FORGE_PENDING=$(ls .agents/forge/*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "Forge candidates pending: $FORGE_PENDING"

  # Citation tracking (if citations.jsonl exists)
  if [ -f .agents/ao/citations.jsonl ]; then
    CITATION_COUNT=$(wc -l < .agents/ao/citations.jsonl | tr -d ' ')
    UNIQUE_CITED=$(grep -o '"artifact_path":"[^"]*"' .agents/ao/citations.jsonl 2>/dev/null | sort -u | wc -l | tr -d ' ')
    echo "Total citations: $CITATION_COUNT"
    echo "Unique learnings cited: $UNIQUE_CITED"
  else
    echo "No citation data (citations.jsonl not found)"
  fi

  # Session outcomes (if outcomes.jsonl exists)
  if [ -f .agents/ao/outcomes.jsonl ]; then
    OUTCOME_COUNT=$(wc -l < .agents/ao/outcomes.jsonl | tr -d ' ')
    echo "Session outcomes recorded: $OUTCOME_COUNT"
  fi
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

  # Pool inventory
  echo "Pool depths:"
  for pool in learnings patterns forge knowledge research retros; do
    COUNT=$(ls .agents/${pool}/*.md 2>/dev/null | wc -l | tr -d ' ')
    echo "  $pool: $COUNT"
  done

  # Global patterns
  GLOBAL_COUNT=$(ls ~/.codex/patterns/*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "  global patterns: $GLOBAL_COUNT"

  # Check for promotion-ready learnings (see references/promotion-tiers.md)
  echo "See: references/promotion-tiers.md for tier definitions"
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

## Cache Eviction
Read `references/cache-eviction.md` for the full eviction pipeline (passive tracking → confidence decay → maturity scan → archive).

## Hub Budget & Phase 4 Hardening

Phase 4 (soc-ytpq) governance for `~/.agents/learnings/` — all advisory, none block by default. Full details in `references/hub-budget.md`.

- **Size budget:** target ≤ 250 MB / ≤ 5,000 files. Restore via `ao maturity --evict --target-size=250M` (lowest-utility-first; respects `lifecycle.IsEvictionEligible` so canonical / high-confidence files are protected).
- **Volume gate:** `ao harvest` WARNs when promotions exceed `--max-promotions=N` (default 500; `AO_MAX_PROMOTIONS=N` env as fallback; ≤0 disables). WARN-only — the 2,638-promotion `soc-ujls` drain proves a hard gate would falsely block legitimate runs.
- **Provenance:** every promoted file carries `source_rig:` in its frontmatter (empty writers serialize as `source_rig: unknown`). Both `harvest.Promote` and `pool.(*Pool).Promote` content-dedup against the same hub via `~/.agents/pool/promoted-index.jsonl`.
- **Re-bloat triage:** check `SkipGlobalHub` defaults to `true` (the agentops-b3v / soc-ujls fix), then `grep -h '^source_rig:' ~/.agents/learnings/*.md | sort | uniq -c | sort -rn` to identify the regressed writer. Use `--target-size`, never raw `rm`.

## Key Rules
- **Monitor regularly** - flywheel needs attention
- **Address friction** - bottlenecks slow compounding
- **Feed the flywheel** - run $post-mortem (or $post-mortem --quick)
- **Prune stale knowledge** - archive old artifacts

## Examples

**User says:** `$flywheel` — Counts pool depths, checks recent activity, validates artifact consistency, writes health report to `.agents/flywheel-status.md`.

**Hook trigger:** After `$post-mortem` — Compares current vs historical metrics, flags velocity drops and friction points.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| All pool counts zero | `.agents/` directory missing or empty | Run `$post-mortem` (or `$post-mortem --quick`) to seed knowledge pools |
| Velocity always zero | No recent extractions (last 7 days) | Run `$post-mortem` (or `$post-mortem --quick`) to extract and index learnings |
| "ao CLI not available" | ao command not installed or not in PATH | Install ao CLI or use manual pool counting fallback |
| Stale artifacts >50% | Long time since last session or inactive repo | Run `$provenance --stale` to audit and archive old artifacts |

## Reference Documents

- [references/artifact-consistency.md](references/artifact-consistency.md)
- [references/promotion-tiers.md](references/promotion-tiers.md)
- [references/hub-budget.md](references/hub-budget.md)
- [references/cache-eviction.md](references/cache-eviction.md)

## Local Resources

### references/

- [references/artifact-consistency-allowlist.txt](references/artifact-consistency-allowlist.txt)
- [references/artifact-consistency.md](references/artifact-consistency.md)
- [references/cache-eviction.md](references/cache-eviction.md)
- [references/hub-budget.md](references/hub-budget.md)
- [references/promotion-tiers.md](references/promotion-tiers.md)

### scripts/

- `scripts/artifact-consistency.sh`
- `scripts/validate.sh`
