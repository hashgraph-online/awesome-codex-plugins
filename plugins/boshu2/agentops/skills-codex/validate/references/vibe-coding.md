# Vibe-Coding Science Reference

**JIT-loaded by /vibe skill and validation agents**

---

## Vibe Levels (Trust Calibration)

| Level | Trust | Verify | Use For | Tracer Test |
|:-----:|:-----:|:------:|---------|-------------|
| **5** | 95% | Final only | Format, lint, imports | Smoke (2m) |
| **4** | 80% | Spot check | Boilerplate, renames | Environment (5m) |
| **3** | 60% | Key outputs | CRUD, tests, known patterns | Integration (10m) |
| **2** | 40% | Every change | New features, integrations | Components (15m) |
| **1** | 20% | Every line | Architecture, security | All assumptions (30m) |
| **0** | 0% | N/A | Novel research | Feasibility (15m) |

**Most tasks are L3.** When in doubt, go lower.

---

## The 5 Core Metrics

| Metric | Target | Red Flag | What It Means |
|--------|:------:|:--------:|---------------|
| **Iteration Velocity** | >3/hr | <1/hr | Feedback loop frequency |
| **Rework Ratio** | <30% | >50% | Building vs debugging |
| **Trust Pass Rate** | >80% | <60% | Code acceptance rate |
| **Debug Spiral Duration** | <30m | >60m | Time stuck on issues |
| **Flow Efficiency** | >75% | <50% | Productive time ratio |

**The key number:** Trust Pass Rate. If >80%, building. If <60%, debugging.

---

## Rating Thresholds

| Metric | ELITE | HIGH | MEDIUM | LOW |
|--------|:-----:|:----:|:------:|:---:|
| Velocity | >5 | ≥3 | ≥1 | <1 |
| Rework | <30% | <50% | <70% | ≥70% |
| Trust Pass | >95% | ≥80% | ≥60% | <60% |
| Spiral | <15m | <30m | <60m | ≥60m |
| Flow | >90% | ≥75% | ≥50% | <50% |

---

## PDC Framework

| Phase | Question | Actions |
|-------|----------|---------|
| **Prevent** | Could we have avoided this? | Specs, checkpoints, tests, 40% rule |
| **Detect** | How did we catch it? | TDD, verify claims, monitor |
| **Correct** | How do we fix it? | Fresh session, rollback, modularize |

**Investment ratio:** Prevention (1x) > Detection (10x) > Correction (100x)

---

## The 12 Failure Patterns

### Inner Loop (Seconds-Minutes)

| # | Pattern | Symptom | Fix |
|:-:|---------|---------|-----|
| 1 | **Tests Lie** | AI says "pass" but broken | Run tests yourself |
| 2 | **Amnesia** | Forgets constraints | Fresh session (>40%) |
| 3 | **Drift** | "Improving" undirected | Smaller tasks |
| 4 | **Debug Spiral** | 3rd log, no fix | Real debugger |

### Middle Loop (Hours-Days)

| # | Pattern | Symptom | Fix |
|:-:|---------|---------|-----|
| 5 | **Eldritch Horror** | 3000-line function | Test. Modularize |
| 6 | **Collision** | Same files | Clear territories |
| 7 | **Memory Decay** | Re-solving | Bundle maintenance |
| 8 | **Deadlock** | Agents waiting | Break cycle |

### Outer Loop (Weeks-Months)

| # | Pattern | Symptom | Fix |
|:-:|---------|---------|-----|
| 9 | **Bridge Torch** | API broke downstream | Roll back |
| 10 | **Deletion** | "Unused" removed | Approval required |
| 11 | **Gridlock** | PRs backed up | Fast lane |
| 12 | **Stewnami** | Half-done pile | Limit WIP |

---

## Code Review Calibration

| Task | Max Level | Notes |
|------|:---------:|-------|
| Generate review comments | L4 | Suggestions only |
| Apply review suggestions | L3 | Verify applies |
| Security review findings | L2 | Higher risk |
| Automated linting | L5 | Fully automated |

---

## Grade Mapping

| Vibe Grade | Trust Pass | Verdict |
|:----------:|:----------:|---------|
| **A** | >95% | ELITE - ship it |
| **B** | ≥80% | HIGH - minor fixes |
| **C** | ≥60% | MEDIUM - needs work |
| **D** | <60% | LOW - significant issues |
| **F** | <40% | BLOCK - systemic problems |

---

## 40% Context Rule

| Utilization | Effect | Action |
|:-----------:|--------|--------|
| 0-40% | Optimal | Continue |
| 40-60% | Degradation | Checkpoint |
| 60-80% | Instruction loss | Save state |
| 80-100% | Confabulation | STOP |

---

**Source:** gitops/docs/methodology/vibe-ecosystem/vibe-coding/
