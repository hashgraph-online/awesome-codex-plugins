---
name: performance-audit
description: Systematic performance investigation workflow. Use when performance regressions are suspected, before and after optimisation work, or as a pre-release gate for performance-critical features. Produces a baseline, identifies the real bottleneck, and validates improvement with hard numbers.
---

# Performance Audit

## The Law

```
A PERFORMANCE CLAIM WITHOUT NUMBERS IS AN OPINION.
"I think it's faster" is not a result.
"p95 latency dropped from 480ms to 42ms on a 1000-item dataset" is a result.
```

## When to Use

- Before any optimisation work (establish baseline first)
- When a performance regression is reported
- As a pre-release gate on performance-critical features
- After an optimisation to validate the improvement

## Audit Workflow

### Step 1: Define the Performance Goal

Before measuring anything, define what "good" looks like:

| Category | Example target |
|----------|---------------|
| API latency | p95 < 200ms at 100 concurrent users |
| Page load | First Contentful Paint < 1.5s on 4G |
| Mobile frame rate | 60fps during scroll, 0 jank frames |
| Build time | Full build < 3 minutes |
| Memory | Peak heap < 512MB under load |
| Bundle size | JS bundle < 250KB gzipped |

If no target exists, the first audit establishes the baseline that becomes the target.

### Step 2: Measure the Baseline

Run the benchmark **before any changes**. Record:
- Tool used and exact command
- Input size and conditions
- Raw numbers (min, p50, p95, p99, max)
- System state (CPU, memory, concurrent users)

```markdown
## Baseline — YYYY-MM-DD

**Feature:** User search endpoint
**Tool:** k6
**Command:** `k6 run --vus 50 --duration 60s scripts/search-load-test.js`
**Input:** 1000-user dataset, query="test"

| Metric | Value |
|--------|-------|
| p50 | 45ms |
| p95 | 380ms |
| p99 | 720ms |
| Error rate | 0.2% |
| Throughput | 210 req/s |
```

### Step 3: Profile — Find the Real Bottleneck

Use the appropriate tool for the stack. Read the output. Don't guess.

**Web APIs**
```bash
# Node.js — CPU profile
node --prof app.js
# Run load test, then:
node --prof-process isolate-*.log > profile.txt

# Python — flame graph
pip install py-spy
py-spy record -o profile.svg --pid $(pgrep -f "python app.py")

# Go — pprof
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Database — slow query log
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT ...;
```

**Frontend**
```bash
# Bundle analysis
npx webpack-bundle-analyzer stats.json
npx source-map-explorer dist/main.js

# Runtime: Chrome DevTools → Performance tab
# Record interaction → identify long tasks (>50ms)

# Lighthouse CI
npx lhci autorun
```

**Mobile**
- Android: Android Studio → Profiler → CPU/Memory/Network
- iOS: Xcode → Instruments → Time Profiler
- Flutter: `flutter run --profile` → DevTools → Performance overlay

### Step 4: Report the Finding

State the bottleneck with evidence, not assumption:

```markdown
## Bottleneck Found

**Location:** `UserSearchService.search()` — lines 45-67
**Evidence:** pprof shows 78% of CPU time in this function
**Root cause:** For each of 50 search results, a separate `getUserById()` DB call is made (N+1 query)
**Impact:** 47 sequential DB calls per request × ~8ms each = ~376ms per request
```

### Step 5: Apply One Change

Single change. Document hypothesis and expected impact before applying:

```markdown
## Change Applied

**Hypothesis:** Replacing per-item DB lookups with a single JOIN will eliminate 46 of the 47 DB calls
**Change:** `UserSearchService.search()` — replace loop + `getUserById()` with `getUsersByIds(ids)` JOIN
**Files modified:** `src/services/UserSearchService.ts`
**Expected impact:** p95 latency from 380ms to < 50ms
```

### Step 6: Re-Measure and Compare

Run the **exact same benchmark** from Step 2.

```markdown
## After Optimisation — YYYY-MM-DD

**Change:** N+1 query replaced with single JOIN

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| p50 | 45ms | 12ms | -73% |
| p95 | 380ms | 38ms | -90% |
| p99 | 720ms | 65ms | -91% |
| Error rate | 0.2% | 0.1% | -50% |
| Throughput | 210 req/s | 890 req/s | +324% |

**Verdict:** IMPROVEMENT CONFIRMED
**Root cause validated:** DB calls per request: 47 → 1
**No regression:** error rate stable, memory unchanged
```

### Step 7: Verdict

| Verdict | Criteria |
|---------|---------|
| **IMPROVEMENT CONFIRMED** | Measurable improvement on target metric, no regression elsewhere |
| **INCONCLUSIVE** | No measurable change — hypothesis was wrong; identify next bottleneck |
| **REGRESSION** | Change made things worse — revert immediately, re-diagnose |
| **GOAL MET** | Target from Step 1 achieved — further optimisation not required |

## Performance Budget (Pre-Release Gate)

For release-critical features, define performance budgets in `docs/performance-budgets.md`:

```yaml
api_latency:
  endpoint: POST /api/search
  p95_ms: 200
  measured_with: k6
  load: 100 concurrent users

bundle_size:
  entry: main.js
  max_gzip_kb: 250
  measured_with: webpack-bundle-analyzer

mobile_fps:
  screen: SearchScreen
  min_fps: 60
  tool: Android Profiler
```

CI fails if any budget is exceeded. Performance is a feature — it regresses like any other feature.
