# Recipes

## Morning: What's Most Important?

```bash
bv --robot-triage | jq '{
  work_on: .recommendations[:3] | map(.id + ": " + .title),
  clear_first: .blockers_to_clear,
  health: .project_health
}'
```

---

## Finding Parallelizable Work

```bash
# Independent tracks that can run concurrently
bv --robot-plan | jq '.tracks[] | {track: .id, tasks: [.tasks[].id]}'

# Best unblock target (highest ROI)
bv --robot-plan | jq '.plan.summary.highest_impact'
```

---

## Health Check

```bash
bv --robot-insights | jq '{
  cycles: (.Cycles | length),        # Must be 0
  density: .density,                  # < 0.3 is good
  longest_chain: (.CriticalPath | length),
  top_bottleneck: .Betweenness[0],
  articulation_points: .Articulation
}'
```

---

## Finding Stale/Forgotten Work

```bash
bv --robot-alerts | jq '.stale'           # No activity
bv --robot-suggest | jq '.duplicates'     # Potential dupes
bv --robot-suggest | jq '.missing_deps'   # Incomplete graph
```

---

## Scoped Queries

```bash
bv --robot-triage --label backend         # Just backend
bv --recipe actionable --robot-plan       # Only unblocked
bv --recipe high-impact --robot-triage    # Top PageRank only
bv --recipe bottlenecks --robot-insights  # High betweenness nodes
bv --recipe quick-wins --robot-triage     # Easy P2/P3 no blockers
```

---

## Historical Analysis

```bash
# What was the state 30 commits ago?
bv --robot-insights --as-of HEAD~30

# What changed since last release?
bv --robot-diff --diff-since v1.0.0

# Sprint burndown
bv --robot-burndown sprint-42
```

---

## Label-Based Triage

```bash
# Which domain is struggling?
bv --robot-label-health | jq '.results.labels[] | select(.health_level == "critical")'

# Cross-team dependencies
bv --robot-label-flow | jq '.bottleneck_labels'

# Which labels need attention?
bv --robot-label-attention --attention-limit=5
```

---

## Priority Misalignment

```bash
# Find high-confidence priority issues
bv --robot-priority | jq '.recommendations[] | select(.confidence > 0.6)'
```

---

## Diff & History

```bash
# What changed since last commit?
bv --robot-diff --diff-since HEAD~1 | jq '{from: .from_data_hash, to: .to_data_hash}'

# Correlation method distribution
bv --robot-history | jq '.stats.method_distribution'

# Why did this take so long?
bv --robot-causality br-123 | jq '.insights'
```

---

## Feedback System

```bash
# Record what you worked on
bv --feedback-accept br-123

# Record what you skipped
bv --feedback-ignore br-456

# Check current weights
bv --feedback-show
```

---

## Built-in Recipes Reference

| Recipe | Purpose |
|--------|---------|
| `default` | All open issues sorted by priority |
| `actionable` | Ready to work (no blockers) |
| `recent` | Updated in last 7 days |
| `blocked` | Waiting on dependencies |
| `high-impact` | Top PageRank scores |
| `stale` | Open but untouched for 30+ days |
| `quick-wins` | Easy P2/P3 items with no blockers |
| `bottlenecks` | High betweenness nodes |
| `triage` | Sorted by computed triage score |
| `closed` | Recently closed issues |
| `release-cut` | Closed in last 14 days |
