---
name: impl-tracking
description: |
  Implementation tracking documents for maintaining living records of what was built, what is pending,
  what failed, and what dead ends were explored. Covers the full tracking document template, dead ends
  prevention, cross-iteration continuity, spec compaction, and inter-session feedback protocol.
  Trigger phrases: "implementation tracking", "track progress", "session tracking",
  "what did the agent do", "dead ends", "failed approaches"
---

# Implementation Tracking

## Core Principle: Track Everything, Especially Failures

Implementation tracking documents are **living records** that agents read and update every session. They serve as persistent memory across iterations, preventing duplicate work and preserving hard-won knowledge about what works and what does not.

The most valuable information in an implementation tracking document is not what succeeded — it is **what failed and why**. Dead ends documented today prevent agents from wasting hours retrying the same failed approaches tomorrow.

---

## Why Implementation Tracking Matters

| Purpose | What It Prevents |
|---------|-----------------|
| **Cross-iteration continuity** | Agents starting from scratch every session |
| **Dead end prevention** | Agents retrying approaches that already failed |
| **Progress visibility** | Humans not knowing what was done or what is left |
| **Test health awareness** | Agents not knowing current test state |
| **Issue tracking** | Known issues being forgotten between sessions |
| **File change tracking** | Uncertainty about what files were created or modified |

Without implementation tracking, every agent session begins with expensive rediscovery. With it, agents resume exactly where the last session left off.

---

## Full Implementation Tracking Document Template

Use this template for every implementation tracking document:

```markdown
# Implementation Tracking: {Domain or Scope}

## Status: {IN_PROGRESS | COMPLETE | BLOCKED}

**Last Updated:** {Date}
**Current Phase:** {Spec | Plan | Implement | Iterate | Monitor}
**Blocking Issues:** {None | Brief description of blockers}

---

## Task Status

| Task ID | Task | Status | Notes |
|---------|------|--------|-------|
| T-1 | {Task description} | DONE | {Completion notes} |
| T-2 | {Task description} | DONE | {Completion notes} |
| T-3 | {Task description} | IN_PROGRESS | {Current state, what remains} |
| T-4 | {Task description} | BLOCKED | {What is blocking, dependency} |
| T-5 | {Task description} | NOT_STARTED | {Prerequisites} |

### Task Dependencies
- T-4 blockedBy T-3 (needs auth module before API integration)
- T-5 blockedBy T-3, T-4

---

## Files Created

| File | Purpose | Spec Reference |
|------|---------|---------------|
| `src/auth/login.{ext}` | Login handler | spec-auth.md R1 |
| `src/auth/session.{ext}` | Session management | spec-auth.md R2 |
| `tests/auth/login.test.{ext}` | Login unit tests | spec-auth.md R1 AC1-3 |

## Files Modified

| File | Change | Reason |
|------|--------|--------|
| `src/app.{ext}` | Added auth middleware | spec-auth.md R3 |
| `src/config.{ext}` | Added session config | spec-auth.md R2 |

---

## Issues & TODOs

- [ ] **Issue:** Session expiry not tested under concurrent access — need load test
- [ ] **TODO:** Add rate limiting to login endpoint (spec-api.md R7)
- [ ] **TODO:** Implement password reset flow (spec-auth.md R4, NOT_STARTED)
- [x] **Resolved:** TypeScript compilation error in session.ts — fixed incorrect import path

---

## Dead Ends & Failed Approaches

### DE-1: JWT with asymmetric keys for session tokens
**What was attempted:** Implemented RS256 JWT tokens with public/private key pair.
**Root cause of failure:** Key rotation complexity exceeded the session management requirements. Added 200+ lines of key management code for no user-visible benefit. Symmetric HS256 with server-side session store is simpler and meets all spec criteria.
**Verdict:** Do not reattempt. Use symmetric tokens with server-side sessions instead.

### DE-2: Redis for session storage
**What was attempted:** Used Redis as the session store backend.
**Root cause of failure:** Redis dependency adds operational complexity. The application's expected concurrent user count (< 10,000) is well within what a database-backed session store handles. Redis would be premature optimization.
**Verdict:** Do not reattempt unless concurrent user requirements change significantly (> 100,000).

### DE-3: Cookie-based CSRF protection
**What was attempted:** Double-submit cookie pattern for CSRF.
**Root cause of failure:** Incompatible with the API's token-based auth flow. Clients send bearer tokens in headers, not cookies. CSRF protection is inherently handled by the token-based approach.
**Verdict:** Do not reattempt. Token-based auth does not need separate CSRF protection.

---

## Test Health

| Test Suite | Passing | Failing | Skipped | Line Coverage |
|------------|---------|---------|---------|---------------|
| Unit tests | 45 | 2 | 0 | 78% |
| Integration | 12 | 1 | 3 | n/a |
| E2E | 0 | 0 | 0 | n/a |

### Failing Tests
- `tests/auth/session.test.{ext}:34` — Session refresh fails when token is expired more than 24h. Needs spec clarification on refresh window.
- `tests/integration/api-auth.test.{ext}:89` — Timeout on concurrent login test. Likely race condition in session creation.

### Test Notes
- E2E tests not yet created (blocked on T-4: API integration)
- Integration test skip: 3 tests require external OAuth provider mock (TODO)

---

## Session Log

### Session 3 (current)
- Completed T-2 (session management)
- Started T-3 (API integration) — 60% complete
- Discovered DE-3 (CSRF not needed with token auth)
- 2 new failing tests identified

### Session 2
- Completed T-1 (login handler)
- Discovered DE-1 (JWT asymmetric keys too complex)
- Discovered DE-2 (Redis premature for this scale)
- Test health: 38 pass, 0 fail

### Session 1
- Set up auth module structure
- Created initial test scaffolding
- Established file ownership: auth/ owned by auth-agent
```

---

## Dead Ends: The Most Critical Section

**Dead ends prevent agents from retrying failed approaches.** This is the single most important function of implementation tracking.

### Why Dead Ends Matter

Without dead end documentation:
1. Agent encounters a problem in session 5
2. Agent tries approach X — spends 30 minutes, fails
3. Session ends
4. In session 6, a new agent encounters the same problem
5. Agent has no memory of session 5's failure
6. Agent tries approach X again — wastes another 30 minutes
7. This repeats indefinitely

With dead end documentation:
1. Agent encounters a problem in session 5
2. Agent tries approach X — spends 30 minutes, fails
3. Agent documents the dead end: what was tried, why it failed, what to do instead
4. In session 6, a new agent reads the dead end
5. Agent skips approach X and uses the recommended alternative
6. Problem solved in 5 minutes instead of 30

### Dead End Format

Every dead end entry must include:

```markdown
### DE-{N}: {Short description of the approach}
**What was attempted:** {Specific description of the approach taken}
**Root cause of failure:** {Why it did not work — a clear technical explanation, not just "it broke"}
**Verdict:** Do not reattempt. {Recommended alternative, or conditions under which the approach might become viable}
```

### Rules for Dead Ends

1. **Always document the root cause.** "It didn't work" is not useful. "Failed because the library's async API is incompatible with the synchronous middleware chain" is useful.
2. **Include the alternative.** What should be done instead?
3. **Be specific about conditions.** If a retry might make sense under different conditions, state those conditions explicitly.
4. **Never delete dead ends during compaction** unless they are older than 5 sessions and the underlying conditions have changed.

---

## Cross-Iteration Continuity

Implementation tracking documents are the primary mechanism for continuity between iteration loop passes and between human-initiated sessions.

### How Agents Use Tracking Documents

At the start of every iteration or session, the agent:

1. **Reads the tracking document** to understand current state
2. **Checks task status** to identify the highest-priority unblocked work
3. **Reviews dead ends** to avoid retrying failed approaches
4. **Checks test health** to understand what is passing and failing
5. **Reviews open issues** for context on known problems

At the end of every iteration or session, the agent:

1. **Updates task status** for all tasks worked on
2. **Records new files** created or modified
3. **Documents any dead ends** discovered
4. **Updates test health** with current pass/fail counts
5. **Adds issues** for any new problems found
6. **Updates the session log** with a summary of work done

### The Read-Work-Update Cycle

```
┌─────────────────────────────────────┐
│  1. Read impl tracking              │
│  2. Identify highest-priority task  │
│  3. Check dead ends for this area   │
│  4. Implement                       │
│  5. Run validation gates            │
│  6. Update impl tracking            │
│  7. Commit                          │
└─────────────────────────────────────┘
        ↓ (next iteration)
┌─────────────────────────────────────┐
│  1. Read impl tracking (updated)    │
│  2. ...                             │
└─────────────────────────────────────┘
```

---

## Spec Compaction

When implementation tracking files exceed approximately 500 lines, they become unwieldy for agents to process. Compaction compresses the file while preserving active context.

### When to Compact

- File exceeds 500 lines
- More than half the tasks are DONE
- Session log has more than 5 entries
- Dead ends section has entries older than 5 sessions that are no longer relevant

### Compaction Process

1. **Create archive:** Copy current file to `impl/archive/impl-{scope}-v{N}.md`
2. **Remove from active file:**
   - Completed tasks (keep only a count: "12 tasks completed, see archive")
   - Resolved issues (marked with [x])
   - Old session log entries (keep last 2-3 sessions)
   - Dead ends older than 5 sessions IF the underlying conditions changed
3. **Preserve in active file:**
   - All IN_PROGRESS and NOT_STARTED tasks
   - All BLOCKED tasks with their blockers
   - All open issues
   - Recent dead ends (last 3-5 sessions)
   - Current test health
   - Active cross-references
   - Files created/modified (keep all — this is the file manifest)
4. **Target:** Under 500 lines in the active file
5. **Add archive reference:**
   ```markdown
   > **Archive:** Previous tracking history available in impl/archive/impl-all-v2.md
   > 12 tasks completed in prior sessions. See archive for details.
   ```

### Compaction Rules

- **Never delete information** — always archive first
- **Never remove active dead ends** — they prevent retrying failures
- **Always keep the full file manifest** — agents need to know what files exist
- **Preserve test health** — agents need current state, not historical

---

## Inter-Session Feedback Protocol

For structured handoffs between sessions (especially when different humans or automation systems manage sessions), use the inter-session feedback protocol.

### XML Format

```xml
<session-report>
  <session-id>2026-03-14-session-3</session-id>
  <timestamp>2026-03-14T14:30:00Z</timestamp>

  <task id="T-1">
    <title>Implement session management</title>
    <status>DONE</status>
    <files-modified>true</files-modified>
    <summary>
      Implemented session creation, validation, and refresh.
      Added server-side session store with database backend.
      Created 3 new files, modified 2 existing files.
    </summary>
    <obstacles kind="NONE"></obstacles>
    <next-steps>
      Proceed to API integration (T-3). Session module is ready.
    </next-steps>
  </task>

  <task id="T-2">
    <title>API endpoint integration</title>
    <status>PARTIAL</status>
    <files-modified>true</files-modified>
    <summary>
      Completed GET /users and POST /login endpoints.
      PUT /users and DELETE /users not started.
    </summary>
    <obstacles kind="TEMPORARY">
      Waiting for session management to stabilize (now done).
    </obstacles>
    <next-steps>
      Continue with PUT/DELETE endpoints. All dependencies resolved.
    </next-steps>
  </task>

  <task id="T-3">
    <title>OAuth provider integration</title>
    <status>BLOCKED</status>
    <files-modified>false</files-modified>
    <summary>
      Investigation complete. OAuth provider requires API key registration.
    </summary>
    <obstacles kind="PERMANENT">
      Cannot proceed without OAuth API credentials.
      Human action required: register application with OAuth provider.
    </obstacles>
    <next-steps>
      Skip until credentials are available. Focus on other tasks.
    </next-steps>
  </task>
</session-report>
```

### Field Definitions

| Field | Values | Purpose |
|-------|--------|---------|
| `status` | DONE, PARTIAL, BLOCKED | Current state of the work item |
| `files-modified` | true, false | Whether code was modified (helps humans prioritize review) |
| `summary` | Free text | What was accomplished — be specific |
| `obstacles.kind` | NONE, TEMPORARY, PERMANENT | TEMPORARY = will resolve on its own; PERMANENT = requires human action |
| `next-steps` | Free text | What the next session should do with this item |

### When to Use the Feedback Protocol

- **Between human-managed sessions:** When a human starts each session and needs to know what happened
- **Automation handoffs:** When an orchestration system decides what to work on next
- **Work queue generation:** The `/ck:next-session` command consumes this feedback to generate prioritized work items

> For the full session feedback protocol reference, see `references/session-feedback-protocol.md`.

---

## Work Queue Handoff

At the end of a session, generate a `plan-next-session.md` that prioritizes work for the next session:

```markdown
# Next Session Work Queue

## WI-1: Complete API endpoint integration
- **Category:** feature
- **Size:** M
- **Priority:** high
- **Spec reference:** plan-api.md
- **What to do:** Implement PUT /users and DELETE /users endpoints
- **Files to modify:** src/api/users.{ext}, tests/api/users.test.{ext}
- **Acceptance criteria:**
  - [ ] PUT /users/{id} updates user record and returns 200
  - [ ] DELETE /users/{id} removes user and returns 204
  - [ ] Both endpoints require valid session token

## WI-2: Fix failing session refresh test
- **Category:** bugfix
- **Size:** S
- **Priority:** medium
- **Spec reference:** plan-auth.md
- **What to do:** Investigate and fix session refresh failure for tokens expired > 24h
- **Files to modify:** src/auth/session.{ext}, tests/auth/session.test.{ext}
- **Acceptance criteria:**
  - [ ] Session refresh test passes for tokens expired < 24h
  - [ ] Clear error message for tokens expired > 24h (if that is the intended behavior)

## WI-3: Create E2E test scaffolding
- **Category:** test
- **Size:** M
- **Priority:** medium
- **Spec reference:** plan-testing.md
- **What to do:** Set up E2E test framework and create smoke tests
- **Files to modify:** tests/e2e/setup.{ext}, tests/e2e/smoke.test.{ext}
- **Acceptance criteria:**
  - [ ] E2E framework runs successfully
  - [ ] Smoke test verifies application starts and login works
```

This removes the orientation cost at the start of each session — agents begin productive work immediately. The next agent reads this file and begins working immediately on the highest-priority item.

---

## Integration with Other Skills

### With `ck:cavekit-writing`

Implementation tracking references specs by requirement ID. When a task is completed, its acceptance criteria map back to spec requirements. When dead ends are found, they may reveal spec gaps that need revision.

### With `ck:validation-first`

Test health in the tracking document reflects validation gate results. Failing tests indicate which gates are not passing. The tracking document records which gates each task must clear.

### With `ck:context-architecture`

Implementation tracking documents live in `context/impl/`. When files grow too large, archive to `context/impl/archive/`. The CLAUDE.md in `context/impl/` instructs agents on tracking conventions.

### With `ck:methodology`

Implementation tracking is used primarily during the Implement and Iterate phases of the Hunt. The iteration loop reads and updates tracking documents every pass. The Monitor phase reviews tracking documents for progress signals.

---

## Summary

1. **Track everything, especially failures** — dead ends are the most valuable information
2. **Use the template** — consistent format lets agents parse tracking documents reliably
3. **Update every session** — stale tracking is worse than no tracking
4. **Document dead ends with root causes** — "it didn't work" is not useful; "failed because X, do Y instead" is
5. **Compact when large** — archive resolved content, keep active files under 500 lines
6. **Use the feedback protocol** for structured handoffs between sessions
7. **Generate work queues** to eliminate discovery overhead at session start
