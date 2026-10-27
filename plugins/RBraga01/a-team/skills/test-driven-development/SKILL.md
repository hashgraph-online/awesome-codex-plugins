---
name: test-driven-development
description: Enforce RED-GREEN-REFACTOR discipline for every implementation task. Use for all new features, bug fixes, and refactors. The core rule — if you didn't watch the test fail, you don't know if it tests the right thing.
---

# Test-Driven Development

## The Core Rule

```
IF YOU DIDN'T WATCH THE TEST FAIL, YOU DON'T KNOW IF IT TESTS THE RIGHT THING.
```

A green test you've never seen red is not a test — it's a decoration.

## The Three Phases (Non-Negotiable)

### Phase RED — Write a Failing Test

Write the test FIRST. Not after. Not "I'll add it later." **First.**

The test must:
- Describe the behavior you want, not the implementation
- Be specific enough to fail for the right reason
- Cover the exact scenario you're about to implement

```typescript
// RED: Write this BEFORE writing the function
test('returns empty array when no users match the filter', () => {
  const result = filterActiveUsers([])
  expect(result).toEqual([])
})
```

**Run it. Watch it fail.**

```bash
npm test -- --testPathPattern="user-filter"
# Expected: FAIL (function doesn't exist yet)
```

If the test passes before you write the implementation: the test is wrong. Rewrite it.

### Phase GREEN — Write Minimal Implementation

Write the **smallest possible code** that makes the test pass. Nothing more.

- No extra features "while I'm here"
- No optimization
- No handling of edge cases not yet covered by tests
- Ugly code that passes is better than beautiful code that doesn't exist yet

```typescript
// GREEN: Minimal implementation that passes the test
function filterActiveUsers(users: User[]): User[] {
  return users.filter(u => u.active)
}
```

**Run it. Watch it pass.**

```bash
npm test -- --testPathPattern="user-filter"
# Expected: PASS
```

If it still fails: read the error message carefully. Fix only what the message tells you.

### Phase REFACTOR — Improve Without Breaking

Now clean up. Rename, extract, simplify — **while keeping tests green**.

```bash
# Run tests continuously during refactor
npm test -- --watch --testPathPattern="user-filter"
```

Rules during refactor:
- Tests must stay green at every step
- No new behavior — only structural improvement
- If tests go red: undo the last change, understand why

## Adding More Tests (Expand-Contract Pattern)

After GREEN for the first case, expand coverage:

```
RED  → watch new test fail
GREEN → minimal code to pass
RED  → add next edge case test
GREEN → handle the edge case
...
REFACTOR → clean up all at once when coverage is complete
```

Cover in order:
1. Happy path (basic success case)
2. Empty / null inputs
3. Boundary values (min, max, exactly-at-limit)
4. Error paths (invalid input, dependency failure)
5. Concurrent / race conditions if applicable

## What to Test vs. What NOT to Test

**Test:**
- Public API surface (exported functions, class methods, HTTP endpoints)
- Business logic decisions
- Data transformations
- Error handling

**Do NOT test:**
- Implementation details (private functions, internal state)
- Third-party library behavior
- Framework internals

## Mocking External Dependencies

External dependencies (database, APIs, file system) must be mocked in unit tests:

```typescript
// Mock the DB before testing the service
jest.mock('../db/users')
const mockFindUser = db.findUser as jest.MockedFunction<typeof db.findUser>
mockFindUser.mockResolvedValue({ id: '1', name: 'Alice', active: true })
```

Integration tests should hit real dependencies — but unit tests must be fast and isolated.

## Coverage Gate

After each feature or bug fix, verify coverage meets the project minimum:

```bash
npm run test:coverage
# Required: ≥ 80% branches, functions, lines, statements
```

If coverage drops below threshold: add tests before moving on.

## TDD Red Flags — You're Doing It Wrong

- Writing the implementation before writing the test
- Running the test only after implementation (never seeing it red)
- Writing tests that test the implementation, not the behavior
- Skipping the refactor phase ("it works, ship it")
- Writing multiple failing tests before making any pass
- Adding edge cases without first making them fail

If you catch yourself rationalizing any of these: stop, revert to the last green state, and start the RED phase properly.

## Integration with A Team Workflow

TDD fits into the full workflow:
1. `brainstorming` → spec approved
2. `writing-plans` → plan with test strategy included
3. **`test-driven-development`** ← you are here, per task
4. `subagent-driven-development` → each subagent runs TDD internally
5. `verification-before-completion` → final proof before claiming done
6. `finishing-a-development-branch` → branch wrap-up
