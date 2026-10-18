---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies. Dispatches one focused agent per problem domain, runs them concurrently, then integrates.
---

# Dispatching Parallel Agents

## Core Principle

Dispatch one agent per independent problem domain. Let them work concurrently.
3 problems solved in parallel = time of 1.

## When to Use

Use when:
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations

Do NOT use when:
- Failures are related (fixing one might fix others)
- Agents would edit the same files
- You need full system context to understand any single problem

## The Pattern

### 1. Identify Independent Domains
Group problems by what's broken. Each domain must be fixable independently.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** One test file or subsystem
- **Clear goal:** Exactly what to achieve
- **Constraints:** What NOT to change
- **Expected output:** Summary of what was found and fixed

### 3. Dispatch in Parallel

```
Task("Fix auth-flow.test.ts failures — timing issues in login flow")
Task("Fix payment-webhook.test.ts failures — missing mock for Stripe")
Task("Fix user-profile.test.ts failures — stale closure in useEffect")
```

### 4. Review and Integrate

- Read each summary
- Verify fixes don't conflict (check for edits to same files)
- Run full test suite
- Integrate all changes

## Agent Prompt Structure

Good prompts are:
1. **Focused** — one clear problem domain
2. **Self-contained** — all context to understand the problem included
3. **Specific about output** — what should the agent return?

```
Fix the 3 failing tests in src/auth/auth-flow.test.ts:
1. "should redirect after login" - expects /dashboard but gets /
2. "should persist session" - session expires immediately
3. "should handle expired tokens" - throws instead of redirecting

Root context: auth was refactored in commit a1b2c3 to use JWT.
Do NOT change production code — test-only fix unless you find a real auth bug.
Return: what you found and what you changed.
```

## Common Mistakes

- Too broad: "Fix all the tests" → agent gets lost
- No constraints → agent refactors everything
- No expected output → you don't know what changed
- Parallel agents editing the same files → conflicts

## Verification After Agents Return

1. Review each summary — understand what changed
2. Check for conflicts — did agents edit the same code?
3. Run full suite — verify all fixes work together
4. Spot check — agents can make systematic errors
