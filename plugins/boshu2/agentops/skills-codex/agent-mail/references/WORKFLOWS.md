# Agent Mail Workflow Patterns

## Table of Contents
- [Standard Bead Workflow](#standard-bead-workflow)
- [Collaborative Review](#collaborative-review)
- [Context Handoff](#context-handoff)
- [Conflict Resolution](#conflict-resolution)
- [Daily Standup Pattern](#daily-standup-pattern)

---

## Standard Bead Workflow

The canonical workflow for working on a bead with coordination. BR/beads is the durable bus for status, ownership, priority, dependencies, and completion evidence. Agent Mail is the side channel for file reservations, lane notifications, acknowledgements, and handoff messages.

### Steps

```
1. Bootstrap session
   macro_start_session(human_key="/abs/path", program="codex-cli", model="YOUR_MODEL")

2. Pick work
   ao beads exec ready --json → select bd-123

3. Reserve files
   file_reservation_paths(
     project_key="/abs/path",
     agent_name="GreenCastle",
     paths=["src/auth/**/*.ts"],
     reason="bd-123"
   )

4. Announce start
   send_message(
     project_key="/abs/path",
     sender_name="GreenCastle",
     to=["BlueLake", "RedBear"],  # Other active agents
     subject="[bd-123] Starting auth refactor",
     body_md="Reserving src/auth/**. Expected 2 hours.",
     thread_id="bd-123",
     ack_required=true
   )

5. Work on bead
   - Make changes
   - Periodically check inbox
   - Reply in thread with progress updates
   - Keep durable state/evidence on the bead, not only in mail

6. Complete
   ao beads exec update bd-123 --notes "Validation: npm test, CI run 123, commit abc123"
   ao beads exec close bd-123 --reason "Implemented OAuth flow"
   release_file_reservations(project_key="/abs/path", agent_name="GreenCastle")
   send_message(
     ...
     subject="[bd-123] Completed",
     body_md="OAuth flow implemented. Ready for review."
   )
```

If the mail thread and BR disagree, fix BR first. Treat the mail thread as context that may be cited from the bead, not as the work record itself.

### One-Writer Rule

Before editing any hot path, acquire an exclusive Agent Mail reservation for the exact directory or file set. If the reservation conflicts, do not write there. Message the holder in the bead thread, split the scope, or wait for the lease to expire. This is the lane boundary that keeps parallel workers from corrupting each other's files.

---

## Collaborative Review

When you need another agent to review your work.

### Requester

```
# After completing work
send_message(
  project_key="/abs/path",
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="[bd-123] Review request: Auth module",
  body_md="""
## What changed
- Implemented OAuth 2.0 flow
- Added token refresh logic
- Updated middleware

## Files to review
- `src/auth/oauth.ts`
- `src/middleware/auth.ts`

## Testing
- Run `npm test -- --grep auth`
""",
  thread_id="bd-123",
  importance="high",
  ack_required=true
)
```

### Reviewer

```
# Acknowledge receipt
acknowledge_message(project_key="/abs/path", agent_name="BlueLake", message_id=1234)

# After review
reply_message(
  project_key="/abs/path",
  message_id=1234,
  sender_name="BlueLake",
  body_md="""
## Review complete

**Approved** with minor suggestions:

1. Line 45: Consider using early return pattern
2. Line 78: Add error handling for token expiry

Tests pass. Good to merge.
"""
)
```

---

## Context Handoff

When you need to hand off work to another agent.

### Outgoing Agent

```
# Before losing context or ending session
send_message(
  project_key="/abs/path",
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="[bd-123] Handoff: Auth module",
  body_md="""
## Current state
- OAuth flow 80% complete
- Token storage implemented
- Refresh logic TODO

## What's left
1. Implement token refresh (see `src/auth/refresh.ts`)
2. Add error handling for expired tokens
3. Update tests

## Key decisions made
- Using JWT for tokens (not opaque)
- 15-minute access token lifetime
- Refresh via httpOnly cookie

## Files touched
- `src/auth/oauth.ts` (main flow)
- `src/auth/storage.ts` (token storage)
- `src/middleware/auth.ts` (middleware)

## Context I had
- User stories in bd-120, bd-121
- API spec in docs/auth-api.md
""",
  thread_id="bd-123",
  importance="high",
  ack_required=true
)

# Transfer file reservations explicitly or let them expire
release_file_reservations(project_key="/abs/path", agent_name="GreenCastle")
```

### Incoming Agent

```
# Prepare for thread
macro_prepare_thread(
  project_key="/abs/path",
  thread_id="bd-123",
  program="codex-cli",
  model="YOUR_MODEL"
)

# Claim reservations
file_reservation_paths(
  project_key="/abs/path",
  agent_name="BlueLake",
  paths=["src/auth/**"],
  reason="bd-123 handoff"
)

# Acknowledge
reply_message(
  project_key="/abs/path",
  message_id=1234,
  sender_name="BlueLake",
  body_md="Received handoff. Resuming from token refresh. Will update thread with progress."
)
```

---

## Conflict Resolution

When file reservation conflicts occur.

### Detecting Conflict

```
file_reservation_paths(
  project_key="/abs/path",
  agent_name="GreenCastle",
  paths=["src/api/routes.ts"]
)

# Returns: {granted: [...], conflicts: [{path: "src/api/routes.ts", holders: ["BlueLake"]}]}
```

### Resolution Options

**Option A: Wait and retry**
```
# Conflict exists, wait for other agent
send_message(
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="File access: src/api/routes.ts",
  body_md="I need to modify routes.ts for bd-123. How long until you're done?"
)

# Wait for reply, then retry reservation
```

**Option B: Coordinate scope**
```
send_message(
  sender_name="GreenCastle",
  to=["BlueLake"],
  subject="Coordinate: src/api/routes.ts",
  body_md="""
We both need routes.ts:
- I need to add auth routes (lines 50-100)
- What section do you need?

Can we split the file or take turns?
"""
)
```

**Option C: Non-exclusive reservation**
```
# Both agents use shared reservation
file_reservation_paths(
  project_key="/abs/path",
  agent_name="GreenCastle",
  paths=["src/api/routes.ts"],
  exclusive=false,
  reason="shared: auth routes"
)
```

---

## Daily Standup Pattern

For longer-running multi-agent projects.

### Broadcast Status

```
send_message(
  project_key="/abs/path",
  sender_name="GreenCastle",
  to=["BlueLake", "RedBear", "YellowFox"],
  subject="Standup: GreenCastle",
  body_md="""
## Yesterday
- Completed bd-123 (OAuth flow)
- Started bd-124 (Token refresh)

## Today
- Finish bd-124
- Start bd-125 (Auth middleware)

## Blockers
- Waiting on API spec update from BlueLake

## File reservations
- src/auth/** (until ~3pm)
""",
  importance="normal"
)
```

### Query Active Work

```bash
# Via NTM
ntm locks PROJECT --all-agents

# Via Agent Mail
# Use resource://file_reservations/{slug}
```
