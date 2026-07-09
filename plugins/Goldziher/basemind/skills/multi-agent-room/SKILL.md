---
name: multi-agent-room
description: >-
  Orchestrate a team of named subagents in a shared room with group chat and
  direct messages. One orchestrator drives multiple peers with distinct
  identities; each subagent sees its own inbox and can cross-check findings via DM.
---

# Multi-agent room orchestration

Run a team of NAMED subagents that chat in shared rooms and via direct messages,
all coordinated by one orchestrator. Each subagent has its own identity, inbox, and
capability to broadcast to the team or send a private message to one peer.

## When to use it

Orchestrate subagents when:

- Multiple reviewers need to see each other's work (code review, audit, cross-validation).
- A subagent should hand off findings to a peer for verification.
- The team needs a shared narrative thread (all readable in one room history).
- You want to parallelize independent work (each agent runs concurrently) and then synthesize.

## Setup

1. **Pick a room id and scope.** For a private team, scope the room to a unique session token:
   `scope: {session: "<token>"}` — pick any shared string (the room id works). The scope selector
   is externally tagged, so the session variant carries its token (`{session: "…"}`), not a bare
   `"session"`; only `global` is a bare string. Agents join by posting to the room, so unrelated
   agents never see it. For machine-wide rooms, use `scope: "global"`.

   ```text
   room_create {room: "review-pr-42", scope: {session: "review-pr-42"}, title: "Code review panel"}
   ```

2. **Assign each subagent a short name.** Pass `as_agent` to every tool call the subagent makes.
   Names like `"security"`, `"perf"`, `"correctness"` are clearer than defaults.

3. **Distribute the subagent contract.** Each subagent's prompt should include:
   - Its assigned `as_agent` name (e.g. `"security"`).
   - The shared room id (e.g. `"review-pr-42"`).
   - Instructions to:
     - Call `agent_register {as_agent: "security", name: "Security Reviewer", …}` once.
     - Call `room_post` with `as_agent: "security"` to broadcast findings.
     - Call `dm_send {to_agent: "perf", as_agent: "security", …}` to DM a peer.
     - Call `inbox_read {as_agent: "security"}` to see DMs and cross-room messages.

## Group chat vs direct messages

- **Room post** (`room_post` + `as_agent`): broadcast to the team. Use for:
  - Announcing a finding that the whole team should see.
  - Replying to a peer's discovery in the shared thread.
  - Summarizing your work.

- **Direct message** (`dm_send` + `as_agent` + `to_agent`): send to one peer. Use for:
  - Asking a peer to cross-check your finding.
  - Sharing a detail not ready for broadcast.
  - Hand-off: `"I found X; can you validate my approach?"`.

## Reading and synthesis

As the orchestrator:

1. Let all subagents post to the room and DM each other (in parallel).
2. Read the shared room: `room_history {room: "review-pr-42"}` (front-matter only).
3. For each message that matters, fetch the body: `message_get {message_id: "…"}`.
4. Read each subagent's inbox for DMs: `inbox_read {as_agent: "security"}`, etc.
   (DMs appear as regular front-matter; bodies come from `message_get`.)
5. Synthesize: combine the findings into a verdict, decision, or report.

## Example: two-agent security + performance cross-check

**Orchestrator setup:**

```text
room_create {room: "review-auth-pr", scope: {session: "review-auth-pr"}}

# Spawn agent "security"
# Prompt: "You are agent 'security' on room 'review-auth-pr'. Register yourself,
# analyze the diff for auth bugs, post findings to the room, and DM 'perf'
# asking them to check if your fix has performance implications."

# Spawn agent "perf"
# Prompt: "You are agent 'perf' on room 'review-auth-pr'. Register yourself,
# analyze the diff for performance regressions, post findings to the room, and DM
# 'security' with your take on their auth fix."
```

**Agent "security" steps:**

```text
agent_register {
  as_agent: "security", name: "Security Reviewer", description: "Auth auditor"
}
room_post {
  room: "review-auth-pr", as_agent: "security", subject: "SQL injection check",
  body: "Parameter X is quoted..."
}
dm_send {
  to_agent: "perf", as_agent: "security", subject: "Cross-check: sanitized input",
  body: "I added validation at line 42..."
}
inbox_read {as_agent: "security", mark_read: true}  # See perf's response
```

**Agent "perf" steps:**

```text
agent_register {
  as_agent: "perf", name: "Performance Reviewer", description: "Latency auditor"
}
room_post {
  room: "review-auth-pr", as_agent: "perf", subject: "Cache impact check",
  body: "New validation adds ~2ms..."
}
dm_send {
  to_agent: "security", as_agent: "perf", subject: "Auth fix validated",
  body: "Sanitization looks solid..."
}
```

**Orchestrator synthesis:**

```text
room_history {room: "review-auth-pr"}  # See full thread
message_get {message_id: "msg-sec-1"}  # Get security's body
message_get {message_id: "msg-perf-1"}  # Get perf's body
inbox_read {as_agent: "security"}  # See the DM from perf (front-matter)
message_get {message_id: "msg-dm-perf-1"}  # Get perf's DM body
# Synthesize: "Security + perf sign off. Ready to merge."
```

## Recency and room freshness

Reads default to RECENT so stale chatter never confuses an agent:

- `room_history` / `inbox_read` return only the **last 24 hours** of messages by default. Pass
  `since_hours: N` for a wider window, or `since_hours: 0` for the full append-only log. Nothing is
  ever deleted — older history stays reachable explicitly.
- Every front-matter row carries `age_secs` (seconds since the message was posted) so you can gauge
  staleness without converting timestamps yourself.
- `room_list` flags each room `stale: true` when it has had no post for over 7 days (or never). The
  CLI renders this as an `ACTIVE` / `STALE` marker per room. Skip stale rooms unless you are
  intentionally reviewing old context.
- `Global` is reserved for MACHINE-WIDE ops coordination (resource / CPU contention), NOT per-repo
  chat — use a repo / session room for team work.

## Notes

- Each subagent auto-joins the room when it first posts (if the room's scope applies).
- DMs use private pairwise rooms (`dm:<lo>:<hi>`) that both ends auto-join.
- Front-matter-only reads (history, inbox) are cheap. Fetch bodies only when needed.
- The CLI offers parity: `basemind comms post --as-agent security …`,
  `basemind comms dm --to perf --as-agent security …`,
  `basemind comms history <room> --since-hours 0` (all history),
  `basemind comms rooms` (shows ACTIVE / STALE per room).
