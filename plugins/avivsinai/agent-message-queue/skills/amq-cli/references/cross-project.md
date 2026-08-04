# Cross-Project Messaging

Send messages between agents in different projects. Requires peer configuration in `.amqrc`.

## Peer Configuration

Each project's `.amqrc` maps peer names to their base root paths:

```json
{
  "root": ".agent-mail",
  "project": "proj-a",
  "peers": {
    "proj-b": "/Users/me/projects/proj-b/.agent-mail"
  }
}
```

- `project`: explicit self-identity (defaults to directory basename if absent)
- `peers`: name → absolute path to peer's base root

**Critical naming rule**: Peer keys must match the remote project's declared `project` name (or its directory basename if `project` is absent). Reply routing uses `reply_project` which is set to the sender's project identity — the receiver must have a peer entry with that exact name. If project A calls its peer `backend` but that project identifies as `api-server`, replies from `api-server` will fail because A has no peer named `api-server`.

Both projects must register each other as peers for round-trip messaging.

## Addressing

### Flag syntax (explicit)
```bash
amq send --to codex --project proj-b --body "hello"
amq send --to codex --project proj-b --session auth --body "to specific session"
```

### Inline syntax (terser)
```bash
amq send --to codex@proj-b --body "hello"
amq send --to codex@proj-b:auth --body "to specific session"
```

Flags take precedence over inline syntax.

## Same-Handle Messages

A matching sender and recipient handle has three distinct meanings:

| Route | Meaning |
|---|---|
| `--project` is present | A different agent instance in another project. AMQ stamps `from_project` and reply routing metadata. |
| `--session` or `--from-session` is present | A different agent instance in another session. AMQ stamps session reply routing metadata. |
| No routing dimension is present | A same-root self-send with no provenance beyond the handle. `amq send` refuses it by default. |

Use `--allow-self` only to confirm an intentional same-root self-send. The flag
does not make `--root` a routing dimension, add reply metadata, or bypass the
cross-tree and session-pin guards. To reach another instance of your handle,
use `--project` or `--session` instead; routed same-handle sends do not require
`--allow-self`.

## Session Defaults

`--project proj-b` without `--session` delivers to the **same session name** in the peer project. If your source root is `.agent-mail/collab`, the message goes to `proj-b's .agent-mail/collab`. Override with explicit `--session`.

## Reply Routing

Cross-project messages carry `reply_to` (handle@session) and `reply_project` (project name). When you receive a cross-project message:

```bash
amq reply --id <msg_id> --body "got it"
```

The CLI reads `reply_project` from the message, resolves the peer, and delivers to the correct project/session. The reply re-stamps `reply_to` and `reply_project` with the replier's own identity for continued round-trip.

## Thread Naming

- **Same project P2P**: `p2p/claude__codex`
- **Cross-session P2P**: `p2p/collab:claude__auth:codex`
- **Cross-project P2P**: `p2p/proj-a:collab:claude__proj-b:collab:codex`
- **Topical threads**: Use the same thread ID across all participating projects (e.g., `decision/api-v2`, `review/auth-module`)

## Safety

- `DeliverToExistingInbox`: Cross-project delivery **never creates directories** in the peer project. The target inbox must already exist (created by `amq init` or `amq coop init` in the peer project). This prevents accidental scaffolding.
- Peer paths must be absolute (or relative to `.amqrc` directory).
- `resolvePeer` validates the path exists before delivery.

## Decision Threads

Decentralized decision protocol for cross-project coordination, based on RFC 7282 rough consensus. Uses existing AMQ primitives — no new CLI commands.

### Process

1. **Propose**: Send a `decision` kind message on thread `decision/<topic>` with label `decision:proposal`
2. **Review/Object**: Participants reply with `decision:support` or `decision:objection` labels. Add `blocking` label for unresolved objections.
3. **Resolve**: Address blocking objections. Running code (tests) is stronger evidence than arguments.
4. **Close**: When all required projects have responded and no unresolved blocking objections remain, send `decision:final`.

### Convention

```bash
# Proposal
amq send --to codex --project proj-b --kind decision \
  --labels "decision:proposal,project:proj-a,project:proj-b" \
  --thread "decision/api-v2" \
  --context '{"proposal_id":"api-v2","question":"Adopt new API?","required_projects":["proj-a","proj-b"],"deadline":"2026-03-25"}' \
  --body "Proposal: migrate to API v2. All tests green."

# Support
amq reply --id <msg_id> --kind decision \
  --labels "decision:support" \
  --body "LGTM. Tests pass on our side."

# Objection
amq reply --id <msg_id> --kind decision \
  --labels "decision:objection,blocking" \
  --body "Breaks backward compat for our consumers."

# Final decision
amq reply --id <msg_id> --kind decision \
  --labels "decision:final" \
  --body "Adopted with backward-compat shim. Shipping in v0.25."
```

### Context schema for proposals

```json
{
  "proposal_id": "api-v2",
  "question": "Should we adopt the new API?",
  "options": ["adopt", "defer", "reject"],
  "required_projects": ["proj-a", "proj-b"],
  "deadline": "2026-03-25",
  "evidence": ["All CI green", "perf benchmarks attached"]
}
```

## What NOT to use cross-project for

- **Same project, different session**: Use `--session` instead
- **Swarm mode**: Agent teams are project-scoped. Use AMQ bridge for swarm notifications within a project.
- **Broadcasting**: No `--to @all` across projects. Send individually to each peer.
