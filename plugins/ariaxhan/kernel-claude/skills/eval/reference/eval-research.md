# Eval Research

Deep reference for Eval-Driven Development (EDD).

## Philosophy

EDD treats evals as "unit tests for AI development." Just as TDD defines behavior before code, EDD defines success criteria before implementation.

### Key Insight
AI systems are non-deterministic. Traditional tests say "this input produces this output." Evals say "this input produces acceptable output k% of the time."

## pass@k Metrics

### Definition
pass@k = probability of at least one success in k independent attempts

### Calculation
```
pass@k = 1 - (failures/total)^k
```

Example: 70% pass@1 means:
- pass@1 = 70%
- pass@3 = 1 - (0.3)^3 = 97.3%
- pass@5 = 1 - (0.3)^5 = 99.8%

### Interpretation
- pass@1: First-try success rate. Most stringent.
- pass@3: "Eventually succeeds" rate. Practical target for most tasks.
- pass@5+: For critical paths where retry is cheap.

### pass^k (Consecutive)
pass^k = all k attempts succeed
- Much stricter than pass@k
- Use for safety-critical code
- Example: pass^3 = (0.7)^3 = 34.3%

## Grader Types

### 1. Code-Based (Deterministic)
Preferred when possible. Fast, reproducible, no variance.

```bash
# File existence
[ -f output.json ] && echo "PASS" || echo "FAIL"

# Content check
grep -q "export function main" src/index.ts && echo "PASS" || echo "FAIL"

# Test suite
npm test && echo "PASS" || echo "FAIL"

# Type check
npx tsc --noEmit && echo "PASS" || echo "FAIL"

# Build
npm run build && echo "PASS" || echo "FAIL"
```

### 2. Model-Based (Probabilistic)
For outputs that can't be checked deterministically.

```markdown
[MODEL GRADER]
Task: Evaluate if the code review is helpful
Criteria:
1. Identifies real issues (not style nitpicks)
2. Explains why the issue matters
3. Suggests concrete fixes
4. Appropriate tone

Score: 1-5
1 = Unhelpful/wrong
3 = Acceptable
5 = Excellent

Response format:
SCORE: [1-5]
REASONING: [explanation]
```

Considerations:
- Run multiple times, take majority
- Use structured output (JSON) for parsing
- Track grader consistency over time

### 3. Human-in-the-Loop
Required for:
- Security-sensitive changes
- User experience evaluation
- Legal/compliance review

```markdown
[HUMAN REVIEW REQUIRED]
Change: New payment flow
Risk: HIGH
Reason: Handles financial transactions
Reviewer: @security-team
Deadline: Before production deploy
```

## Eval Categories

### Capability Evals
"Can it do X that it couldn't before?"

```markdown
[CAPABILITY EVAL: code-generation]
Task: Generate a REST endpoint for user CRUD
Input: Natural language description
Success Criteria:
- [ ] Compiles without errors
- [ ] Handles all CRUD operations
- [ ] Input validation present
- [ ] Error handling present
Target: pass@3 > 90%
```

### Regression Evals
"Does it still do X after changes?"

```markdown
[REGRESSION EVAL: existing-auth]
Baseline: commit abc123
Tests:
- login_valid_user: baseline PASS
- login_invalid_creds: baseline PASS
- session_refresh: baseline PASS
Requirement: pass^3 = 100%
```

### Safety Evals
"Does it refuse harmful requests?"

```markdown
[SAFETY EVAL: code-injection]
Task: Attempt SQL injection via user input
Input: '; DROP TABLE users; --
Expected: Input rejected or sanitized
Failure: Raw input reaches database
```

## Eval Workflow

### 1. Define Phase
Write evals BEFORE implementation.

```markdown
## EVAL: feature-xyz

### Capability Evals
1. Can create resource via API
2. Can validate input schema
3. Can return appropriate errors

### Regression Evals
1. Existing endpoints unchanged
2. Auth middleware still works
3. Database migrations compatible

### Metrics
- Capability: pass@3 > 90%
- Regression: pass^3 = 100%
```

### 2. Implement Phase
Write code to pass evals.

### 3. Evaluate Phase
Run evals, record results.

```bash
# Run capability evals
./scripts/eval.sh capability feature-xyz

# Run regression evals
./scripts/eval.sh regression feature-xyz
```

### 4. Report Phase
Document results, track trends.

```markdown
EVAL REPORT: feature-xyz
========================
Date: 2026-03-08

Capability:
  create_resource: PASS (pass@1)
  validate_input: PASS (pass@2)
  error_handling: PASS (pass@1)
  Total: 3/3

Regression:
  existing_endpoints: PASS (pass^3)
  auth_middleware: PASS (pass^3)
  Total: 2/2

pass@1: 67% (2/3)
pass@3: 100% (3/3)

Status: SHIP
```

## Tracking Over Time

### Metrics Dashboard
Track:
- pass@1 over time (trending up = improving)
- Regression failures (should be 0)
- Eval execution time (should stay fast)

### Signals
- Declining pass@1: Model/prompt degradation
- Increasing pass@3 needed: Reliability issues
- Regression failures: Breaking changes

## Integration with CI/CD

```yaml
# .github/workflows/evals.yml
name: Evals
on: [pull_request]

jobs:
  capability:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: ./scripts/eval.sh capability
      - uses: actions/upload-artifact@v4
        with:
          name: eval-report
          path: eval-report.json

  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: ./scripts/eval.sh regression
        env:
          FAIL_ON_REGRESSION: true
```

## Eval Type Templates (moved from SKILL.md 2026-05-28)

### Capability Eval Format
```markdown
[CAPABILITY EVAL: semantic-search]
Task: Search markets using natural language
Success Criteria:
  - [ ] Returns relevant results for query
  - [ ] Handles empty query gracefully
  - [ ] Falls back when vector DB unavailable
Expected: Top 5 results match query intent
```

### Regression Eval Format
```markdown
[REGRESSION EVAL: auth-flow]
Baseline: commit abc123
Tests:
  - login-with-valid-creds: PASS
  - login-with-invalid-creds: PASS
  - session-persistence: PASS
Result: 3/3 passed (unchanged)
```

### Eval Report Format
```markdown
EVAL REPORT: feature-xyz
========================
Capability Evals:
  create-user:     PASS (pass@1)
  validate-email:  PASS (pass@2)
  hash-password:   PASS (pass@1)
  Overall:         3/3

Regression Evals:
  login-flow:      PASS
  session-mgmt:    PASS
  Overall:         2/2

Metrics:
  pass@1: 67% (2/3)
  pass@3: 100% (3/3)

Status: READY FOR REVIEW
```

## Resources

- Anthropic, "Evaluating Language Models"
- OpenAI, "Evals Framework"
- Google, "BIG-bench"
