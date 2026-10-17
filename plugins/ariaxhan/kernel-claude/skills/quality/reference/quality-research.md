# AI Code Quality Research

**Sources:** CodeRabbit 2025, SonarSource, METR Study, Endor Labs, MIT 2025

---

## Stats

| Metric | Finding |
|--------|---------|
| Security flaws | 40-62% of AI code |
| Buggier than human | 1.7x more issues |
| Technical debt | +30-41% after adoption |
| Perceived vs actual | Think 20% faster, actually 19% slower |
| Review burden | 2-3x longer |

---

## The Big 5: What AI Actually Breaks

### 1. Input Validation Omission

**Frequency:** Nearly universal unless prompted.

```yaml
symptoms:
  - No Zod/Pydantic schema
  - String concat in queries
  - No file upload validation

detection:
  - grep -r "req\.body" | grep -v "parse\|validate\|z\."
  - Search for raw db.query with string interpolation

fix:
  - Zod schema for every API endpoint
  - Parameterized queries only
```

### 2. Edge Case Blindness

**Frequency:** Almost all AI code misses edge cases.

```yaml
symptoms:
  - Empty array crashes loops
  - Null user in auth routes
  - No timeout handling

detection:
  - Array access without length check
  - Optional chaining overuse (?.?.?.)
  - async without try-catch

fix:
  - Test null, empty, boundary, concurrent, timeout
  - Edge cases FIRST, not last
```

### 3. Error Handling Gaps

**Frequency:** ~70% incomplete.

```yaml
symptoms:
  - Empty catch blocks
  - No error logging
  - 500s without context

detection:
  - grep -r "catch.*{}"
  - console.log in catch (not proper logging)

fix:
  - Every catch: log, set status, return useful message
  - Structured logging
```

### 4. Duplication Explosion

**Frequency:** 8x increase with AI.

```yaml
symptoms:
  - Same validation in 5 endpoints
  - Copy-pasted error handling

detection:
  - jscpd
  - Functions > 50 lines

fix:
  - Extract common patterns
  - Set duplication threshold in CI
```

### 5. Complexity Spiral

**Frequency:** +15-25% cyclomatic.

```yaml
symptoms:
  - Nested ternaries 3+ deep
  - Functions > 100 lines
  - God components

detection:
  - eslint complexity rule
  - Files > 500 lines

fix:
  - Functions < 30 lines
  - Extract early returns
```

---

## Velocity Calibration

| Task Type | AI Speed | Review Burden |
|-----------|----------|---------------|
| Boilerplate | 10x | Low |
| Config/Docker | 8-10x | Low |
| API integration | 3-5x | Medium |
| Domain logic | 2-5x | High |
| Architecture | 1x | Human-led |

---

## The Paradox

**METR 2025:** Devs perceive 20% faster, measure 19% slower.

**Why:** Time saved generating < time lost reviewing, debugging, fixing.

**Fix:** 50-70% planning, 30-50% coding. Quality gates before review.

---

## R-Factor: Measurement Definitions

Per-component measurement for the composite quality score:

```
test_pass_rate:      passing tests / total tests
acceptance_rate:     acceptance criteria met / total criteria
scope_accuracy:      files in contract / files actually changed (1.0 = perfect scope)
security_clean_rate: 1.0 if no security findings, 0.0 otherwise
budget_compliance:   1.0 if within budget, decreases proportionally over budget
first_try_rate:      1.0 if merged without revision, decreases per revision round
```

### Usage integration

- Validator reports R-factor in verdict
- /kernel:forge uses R-factor in quench phase (>= 0.8 = survived)
- /kernel:metrics displays R-factor trend
- agentdb verdict stores R-factor in evidence JSON

---

## ADSR: Baselines and Integration

### Baselines (computed from AgentDB history)

```
tokens_per_tier:     avg from agentdb execution_traces
files_per_contract:  avg from agentdb contracts
duration_per_task:   avg from agentdb events
```

Require at least 10 historical data points before enforcing thresholds.

### Integration points

- validator checks baselines during quench phase
- forge loop checks between iterations
- orchestrator checks after each agent completes
