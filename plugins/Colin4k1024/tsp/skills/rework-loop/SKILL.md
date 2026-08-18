---
name: rework-loop
description: "Structured rework with git blame attribution for failed goal iterations. Maps failures to responsible changes and routes targeted fix briefs."
origin: ECC
---

# Rework Loop

Structured rework with blame attribution for failed goal iterations.
When the oracle says "fail," don't blindly retry — identify what broke,
map it to the responsible change, and route a targeted fix.

## When to Activate

- Oracle returns `fail` verdict during a goal iteration
- Code reviewer identifies rework-worthy issues
- Build/test failures after a maker iteration
- Manual invocation for targeted re-implementation

## Core Concept: Blame-Attributed Rework

Blind retry is the #1 waste in autonomous loops. A rework loop instead:

1. **Parses** failure output to extract specific failing locations
2. **Blames** via `git diff` / `git blame` to find the responsible change
3. **Constrains** the rework to only the affected scope
4. **Routes** to the right specialist (TS issues → typescript-reviewer, etc.)
5. **Tracks** rework attempts per location to detect persistent trouble spots

```
Oracle: FAIL
  │
  ▼
Parse failure → "tests/auth.test.ts:45 — token refresh assertion fails"
  │
  ▼
Blame → "src/auth/refresh.ts:23 changed in this iteration"
  │
  ▼
Rework brief → {file: "src/auth/refresh.ts", constraint: "only fix refresh logic"}
  │
  ▼
Route → backend-engineer or typescript-reviewer
  │
  ▼
Track → attempts[src/auth/refresh.ts] += 1
```

## Rework Brief Format

The rework brief is a structured context packet for the next iteration:

```markdown
## REWORK BRIEF

**Goal:** {original objective}
**Iteration:** {N} (rework attempt {M} for this location)

**Failing evidence:**
- Test: tests/auth.test.ts:45 — "should refresh expired tokens"
- Error: Expected token.expiresAt to be > now, got 2024-01-01

**Root cause (blame):**
- File: src/auth/refresh.ts:23
- Change: Added early return before expiry check
- Commit: (this iteration, uncommitted)

**Constraint:**
- ONLY modify src/auth/refresh.ts
- DO NOT touch test files (they define correct behavior)
- The refresh logic must handle: valid token, expired token, missing token

**Suggested fix:**
- Remove the early return at line 23
- Ensure expiry check runs before refresh attempt
```

## Escalation Triggers

Rework escalates to triage when:

| Condition | Action |
|-----------|--------|
| 3+ rework attempts on same location | Escalate: "persistent trouble spot" |
| Rework introduces new failures | Escalate: "regression cascade" |
| Blame maps to multiple unrelated files | Escalate: "scope too broad for targeted rework" |
| No clear blame (flaky test, env issue) | Escalate: "non-deterministic failure" |

## Blame Attribution Algorithm

1. **Parse failure output** for file paths and line numbers
2. **Get changed files** via `git diff --name-only` (this iteration vs last good)
3. **Intersect** failing files with changed files
4. **For each intersection:**
   - `git diff <file>` to extract specific hunks
   - Map test failure line to source change via call stack or import chain
5. **If no intersection:** failure is pre-existing or environmental → escalate

## Rework Tracking

Track attempts per file/function to detect patterns:

```json
{
  "src/auth/refresh.ts": {
    "attempts": 3,
    "lastAttempt": "2024-01-15T10:30:00Z",
    "outcomes": ["fail", "fail", "pass"],
    "totalCost": 1.20
  }
}
```

When `attempts >= 3` without convergence: this is a persistent trouble spot.
The loop should escalate rather than keep burning budget.

## Integration Points

- **`/goal`**: Rework replaces blind retry in the maker-oracle loop
- **`completion-oracle.js`**: Oracle's `failReasons` feed into blame parsing
- **`/triage`**: Escalated rework items go to triage inbox
- **Specialist agents**: Rework briefs route to appropriate specialists
- **Cost advisor**: Rework attempts count toward goal budget

## Hard Bans

- DO NOT retry without blame analysis (blind retry wastes budget)
- DO NOT modify test files during rework (tests define correct behavior)
- DO NOT expand scope beyond blamed files (scope creep = new bugs)
- DO NOT rework indefinitely (3 attempts max per location)
- DO NOT skip tracking (rework history enables pattern detection)
