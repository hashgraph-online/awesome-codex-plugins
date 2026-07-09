# The 12 Metrics

| Metric | What It Finds | High Score Means |
|--------|---------------|------------------|
| **PageRank** | Recursive importance | Everything depends on this (fix first) |
| **Betweenness** | Path traffic | Bottleneck — blocks multiple paths |
| **In-Degree** | Direct blockers | Many things waiting on this |
| **Out-Degree** | Direct dependencies | This needs many things done first |
| **HITS Authority** | Destination node | Core deliverable, end goal |
| **HITS Hub** | Source node | Epic that spawns work |
| **Eigenvector** | Influential neighbors | Connected to important things |
| **Critical Path** | Longest chain | Zero slack — delays cascade |
| **Cycles** | Circular deps | **Broken graph — fix immediately** |
| **K-Core** | Structural strength | Core number indicates shell membership |
| **Articulation** | Cut vertices | Removal disconnects graph |
| **Slack** | Longest-path slack | Buffer before delays cascade |

---

## Two-Phase Analysis

- **Phase 1 (instant)**: degree, topo sort, density — always available
- **Phase 2 (async, 500ms timeout)**: PageRank, betweenness, HITS, eigenvector, cycles

Check the `status` field in robot output:
```bash
bv --robot-insights | jq '.status'
# computed | approx | timeout | skipped
```

---

## Reading the Metrics

```bash
# What's blocking the most stuff? (fix these first)
bv --robot-insights | jq '.PageRank[:5]'

# What's the bottleneck? (everything flows through here)
bv --robot-insights | jq '.Betweenness[:3]'

# Is the graph healthy?
bv --robot-insights | jq '{cycles: .Cycles, density: .density}'
# cycles must be [], density < 0.3 is healthy

# What's the critical path? (can't parallelize these)
bv --robot-insights | jq '.CriticalPath'

# Cut vertices (removing disconnects graph)
bv --robot-insights | jq '.Articulation'

# Slack (buffer before delays cascade)
bv --robot-insights | jq '.Slack[:5]'

# K-core decomposition
bv --robot-insights | jq '.KCore'
```

---

## Metric Combinations (Decision Matrix)

| Pattern | Meaning | Action |
|---------|---------|--------|
| High PageRank + High Betweenness | Critical bottleneck | Drop everything, fix this |
| High PageRank + Low Betweenness | Foundation piece | Important but not blocking |
| Low PageRank + High Betweenness | Unexpected chokepoint | Investigate why |
| High Authority + Low Hub | End goal | This is what you're building toward |
| High Hub + Low Authority | Epic/umbrella | Break it down further |

---

## Healthy Graph Thresholds

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Cycles | 0 | 1-2 | 3+ |
| Density | < 0.3 | 0.3-0.5 | > 0.5 |
| Critical path | < 10 nodes | 10-20 | > 20 |
