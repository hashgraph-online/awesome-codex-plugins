---
name: agent-mail
description: Use when coordinating agents with Agent Mail
---
<!-- TOC: Boundary | Disciplines | When to Use What | Bootstrap | Reservations | Beads | Troubleshooting | References -->

# Using Agent Mail

> **Core Insight:** Agent Mail is the side channel for leases, notifications, acknowledgements, and handoffs. BR/beads is the durable coordination bus and source of truth for work state, evidence, and decisions.

> **⚠️ TWO SURFACES — read this first.** Every operation has BOTH an MCP-tool form (`send_message`, `fetch_inbox`, …) AND a CLI form (`am mail send`, `am mail inbox`, …). The MCP tools are only present when the agent-mail MCP server is wired into your session's tool surface — **a plain CLI/shell agent (or a session where the MCP server didn't load) will NOT have them.** In that case use the `am` CLI, which works from any shell. **Discoverability trap (br cp-jgcl):** the send/reply verbs live under the `am mail` group, which `am --help` does NOT list, and the read commands have flat aliases (`am inbox`, `am status`) but **`am send` does not exist** — it is **`am mail send`**. When in doubt: `am mail --help`, `am macros --help`, `am file_reservations --help`.

**Don't re-learn the command surface from this skill.** The MCP server self-describes its tools and resources in your tool list; the CLI self-describes via `am --help` and the group helps above. This skill carries only the operating doctrine: when to use mail, the reservation discipline, and the coordination boundaries. Full tool/parameter catalog: [TOOLS.md](references/TOOLS.md).

> **When this applies (scope guard).** Agent Mail coordination — `start-session`, identity registration, file reservations, cross-lane ACKs — is **required when ≥2 lanes/panes share the repo** (a swarm, or you plus a concurrent peer session). With **only one active writer** (no second lane/pane), do **not** register or reserve against yourself — coordination is an escalation, not a session-start tax. If you are the sole writer, skip to the work. (Doctrine: [operating-loop principle 8](../../docs/architecture/operating-loop.md#governing-principles) — single-agent-first.)
>
> **Asymmetry guardrail — the part of the de-mandate that does NOT relax.** AM answers a **contention** axis; ATM answers a separate **durability** axis (they're not a package — full 4-case matrix in [`using-atm`](../using-atm/SKILL.md#when-to-use-atm-vs-am-the-4-case-matrix)). The de-mandate removes the single-writer *session-start tax*, **not** the *collision guard*. The costs are asymmetric: an **unneeded** AM call costs one command; a **missing** one lets two writers silently clobber a shared file and the merge looks like ordinary conflict cleanup while the design forked. So the **`≥2-writers → reserve` reflex stays non-negotiable.** "Trust the models" does not grant two concurrent writers consistency on one path. **Partition before you lock:** if you can cut the write-sets disjoint (sole writer per file), do that instead of reserving — locks are the fallback when partition fails.

## Coordination Boundary

| Need | Source of truth |
|------|-----------------|
| Work queue, status, dependencies, priority, closure evidence | BR/beads (`br`/`bv`) |
| File ownership, active edit leases, lane notifications, acks | Agent Mail |
| Final proof that work is done | Bead notes/closure plus git/CI evidence |
| "Who may write this hot path right now?" | Agent Mail file reservation |

Use Agent Mail to prevent collisions and notify active agents. Do not use it as the durable task queue, audit log, or final evidence store. If a mail thread and BR disagree, reconcile the bead first and link the mail thread from the bead note if the conversation matters.

One-writer-per-hot-dir rule: reserve the path before editing it. If the reservation conflicts, do not write into that path; coordinate with the holder, narrow scope, or wait for the lease to clear.

## Coordination disciplines (2026-06-09, cards 1–5, cp-hhd7)

### Durable lane identities (card 1, cp-9lrb)

Register a **durable adjective+noun identity** at session start. Pane text and
human relay are unauditable and load the operator. The ledger is the bus — both
lanes must be registered to exchange auditable messages. Do not coordinate via
informal pane text when `send_message` + `fetch_inbox` is available.

### Content-push, not pointers (card 2, cp-9lrb)

When sending a lane a message, **push the content** — include the actual text,
diff, or decision. A pointer to a message-id the recipient cannot discover by
inbox is still a relay. If the recipient's inbox is broken and they cannot read
by-id, a pointer is a dead end. Short content fits in the body; long content goes
to a committed artifact with an absolute path, not an AM-internal id.

### Intent on the graph first — dedup (card 3, cp-hhtu)

Before any actor acts on a bead (intake, admit, implement, validate, mutate),
**update the bead status and set the actor on the graph first**, then check for an
existing actor. Parallel pipelines are blind to each other at every tier — dedup
via the ledger, not behavioral coordination. Five exhibits of same-bead parallel
work hit the fleet in one day (impl/validate/admission/mutation/intake, cp-hhtu).
The fix is structural: intent on the graph is the lock.

### ACK-with-id on routed writes (card 5, cp-fmt8)

When routing a write through a single writer (e.g. a beads-intake lane), require
**ACK-with-id** back to the requester — the AM message id of the filed bead or the
`br show <id>` output confirming the record exists. An unacknowledged routed write
is invisible work. "Are these filed?" must not be a question — the ACK closes it.

## When to Use What

| Situation | Action |
|-----------|--------|
| Starting any agent session | `macro_start_session` (CLI: `am macros start-session`) |
| **Confirm a lane actually registered** | `am robot agents --project <abs> --active` — must list your name and each peer lane |
| About to edit files | reserve paths → edit → release reservations |
| Need to tell another agent something | `send_message` with `thread_id` (CLI: `am mail send`) |
| Picking up someone else's work | `macro_prepare_thread` |
| Need durable work state or evidence | Update BR/beads, then link the mail thread if useful |
| Can't message an agent | `request_contact` → wait for approval |
| Server seems broken | `health_check()` first; CLI-only: `doctor check --verbose` → `doctor repair --yes` |

## Session Bootstrap

**Call `macro_start_session` (or `am macros start-session --project <abs> --program <p> --model <m> --task "<desc>"`) at the start of every *multi-lane* agent session** (skip it when you are the sole writer — see the scope guard above). One call: ensures project exists → registers your identity → reserves files → fetches inbox. Returns `{project, agent, file_reservations, inbox}`.

**Verify the lane registered.** A pane can *look* spawned and still have never registered — its start-session may not have landed. Confirm with:

```bash
am robot agents --project <abs> --active   # should list YOUR name and each peer lane
```

If your name (or a peer's) is missing, that lane's start-session did not land — **do not assume the coordination leg is live.** Re-run start-session for the missing lane before relying on mail/reservations between you. Skipping this check is how the coordination leg silently goes unverified.

Identity notes:

- Agents get adjective+noun names (GreenCastle, BlueLake). Omit `name`/`--name` to auto-generate a valid one.
- `am macros start-session` auto-generates a fresh identity **per project**; you will have a different name in each project. Confirm yours via `am agent start`.
- The other macros (`macro_prepare_thread`, `macro_file_reservation_cycle`, `macro_contact_handshake`) and the fast `resource://` reads are self-described by the server; catalog in [TOOLS.md](references/TOOLS.md) and [RESOURCES.md](references/RESOURCES.md).

## File Reservations — Reserve Before Editing

The discipline, not the syntax (syntax: `am file_reservations --help` or the `file_reservation_paths` tool):

1. **Reserve before the first write.** Glob patterns are fine (`src/auth/**/*.ts`). Set a real `ttl_seconds` and put the bead id in `reason`.
2. **Check `conflicts` in the response.** On conflict: wait for TTL expiry, message the holder, or share with `exclusive=false`. Never write into a conflicted path.
3. **Release when done** (`release_file_reservations` / `am file_reservations release <abs> <me>`). Don't squat on leases across unrelated work.

## Beads Integration

Use bead IDs as your threading anchor. BR remains authoritative; mail carries the lease, notification, and discussion side channel.

```
1. Pick work:        br ready --json → choose bd-123
2. Reserve files:    file_reservation_paths(..., reason="bd-123")
3. Announce:         send_message(..., thread_id="bd-123", subject="[bd-123] Starting...")
4. Work:             Reply in thread with progress
5. Record evidence:  br update bd-123 --notes "Validation: tests, commit, CI, or handoff proof"
6. Complete:         br close bd-123, release_file_reservations(...), final message
```

**Bead ID (often bd-###) goes in:** thread_id, subject prefix, reservation reason, commit message

**Do not infer durable state from mail silence.** A missing reply is not proof that a bead is abandoned, blocked, or complete. Check `br show <id> --json`, `bv --robot-insights`, git state, and CI evidence before changing work state.

## Quick Troubleshooting

| Error | Fix |
|-------|-----|
| "sender_name not registered" | Call `macro_start_session` first |
| Pane looks spawned but coordination is silent | A pane can look spawned yet never have registered. Run `am robot agents --project <abs> --active` — if the lane is absent, its start-session didn't land; re-run it |
| "FILE_RESERVATION_CONFLICT" | Wait, coordinate, or use `exclusive=false` |
| "CONTACT_BLOCKED" | Use `request_contact`, wait for approval |
| Server unreachable | `am robot health` (works CLI-only, direct SQLite) or `health_check()` (MCP). `curl …:8765/health` only resolves if the HTTP MCP server is running; CLI-only deploys have no `:8765` listener. Start the server with `am` |
| Guard blocks commit | Set `AGENT_NAME` env var; emergency bypass: `AGENT_MAIL_BYPASS=1 git commit` |

Deeper diagnostics (doctor check/repair), the pre-commit guard (`install_precommit_guard`), the human-overseer web UI, and FTS5 search syntax are all self-described by the server/CLI — see [RECOVERY.md](references/RECOVERY.md) and [ADVANCED.md](references/ADVANCED.md).

## References

| Topic | Reference |
|-------|-----------|
| All MCP tools | [TOOLS.md](references/TOOLS.md) |
| Workflow patterns | [WORKFLOWS.md](references/WORKFLOWS.md) |
| MCP resources | [RESOURCES.md](references/RESOURCES.md) |
| Cross-project setup | [CROSS-PROJECT.md](references/CROSS-PROJECT.md) |
| Doctor & recovery | [RECOVERY.md](references/RECOVERY.md) |
| Installation | [INSTALL.md](references/INSTALL.md) |
| Fix MCP config | [FIX-MCP-CONFIG.md](references/FIX-MCP-CONFIG.md) |
| Product bus, build slots, internals | [ADVANCED.md](references/ADVANCED.md) |

## Validation

```bash
am robot health                     # PRIMARY check — CLI/direct SQLite, works without the HTTP server
am agent start --json               # cockpit; flags a missing :8765 listener under mcp_endpoint=fail
curl http://127.0.0.1:8765/health   # ONLY if the HTTP MCP server is up (am serve-http); CLI-only deploys have no :8765 listener
am                                  # start server if needed
```

---

**Fork maintenance.** `am` is Bo's fork (`boshu2/mcp_agent_mail_rust`). To pull upstream fixes, use the fork-sync factory in `~/dev/mcp_agent_mail_rust`: `make fork-status` → `make fork-preview` → `make fork-sync` (its `AGENTS.md` § "Upstream sync"; never rebase main by hand). Divergence facts are owned by **FORKS-MAP F-3**.
