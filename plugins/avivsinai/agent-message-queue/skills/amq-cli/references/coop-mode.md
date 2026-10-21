# Co-op Mode Protocol

## Roles

- **Initiator** = whoever starts the task (agent or human). Owns decisions and receives updates.
- **Leader/Coordinator** = coordinates phases, merges, and final decisions (often the initiator).
- **Worker** = executes assigned phases and reports back to the initiator.

The initiator assigns roles for the task. A provider or model name does not
determine authority or ownership.

## Phased Flow

| Phase | Mode | Description |
|-------|------|-------------|
| **Research** | Parallel | Both explore codebase, read docs, search. No conflicts. |
| **Design** | Parallel -> Merge | Both propose approaches. Leader merges/decides. |
| **Code** | Split | Divide by file/module. Never edit same file. |
| **Review** | Parallel | Both review each other's code. Leader decides disputes. |
| **Test** | Parallel | Both run tests, report results to leader. |

```
Research (parallel) -> sync findings
    v
Design (parallel) -> leader merges approach
    v
Code (split: divide files/modules)
    v
Review (parallel: each reviews other's code)
    v
Test (parallel: both run tests)
    v
Leader prepares commit -> user approves -> push
```

## Key Rules

1. **Initiator rule** — reply to the initiator and ask the initiator for clarifications
2. **Workspace ownership** — follow the repository's branch and worktree rules;
   do not switch, stash, or overwrite another participant's work
3. **Code phase = split** — divide files/modules to avoid conflicts
4. **File overlap** — if same file unavoidable, assign one owner; other reviews/proposes via message
5. **Coordinate between phases** — sync before moving to next phase
6. **Leader decides** — initiator or designated leader makes final calls

## Stay in Sync

- After completing a phase, report to the initiator and await next assignment
- While waiting, safe to do: review partner's work, run tests, read docs
- If no assignment comes, ask the initiator (not a third party) for next task

## Progress protocol

When work starts, reply with `kind=status` and an ETA. Use `urgent` only for
work that must interrupt the current activity.

Reply to the initiator, preserve the existing thread, send status at start and
phase boundaries, and finish with changes and verification.

- **Blocked**: send `kind=question` to the initiator with options and a recommendation.

## Modes of Collaboration (Modus Operandi)

- **Leader + Worker**: leader decides, worker executes; best default.
- **Co-workers**: peers decide together; if no consensus, ask the initiator.
- **Duplicate**: independent solutions or reviews; initiator merges results.
- **Driver + Navigator**: driver codes, navigator reviews/tests and can interrupt.
- **Spec + Implementer**: one writes spec/tests, the other implements.
- **Reviewer + Implementer**: one codes, the other focuses on review and risk detection.

## Communication

- Use AMQ messages to coordinate between phases and report to the initiator
- Don't paste code blocks — reference file paths (shared workspace)

## Interrupts

- Urgent messages labeled `interrupt` trigger an interrupt notice when wake is
  running. The label never enables Ctrl+C by itself; real SIGINT requires the
  explicit destructive opt-in `--interrupt-cmd ctrl-c`.
- Input injection can activate a focused permission or approval dialog. Payload
  text alone may match single-key shortcuts, so removing Enter is not safe.
- `--defer-while-input` reduces collisions with recent typing but cannot detect
  modal state; an idle dialog looks like an idle composer.
- For an AMQ-enforced zero-input watcher, run `amq wake --inject-mode none` or
  `amq coop exec --require-wake --wake-inject-mode none <agent>`. This mode
  writes notices to wake stderr, turns urgent interrupts into one bell plus the
  output notice, and rejects `--inject-via`, `--inject-arg`, and `--inject-cmd`.
  A directly started wake uses its configured stderr. `coop exec` sends wake
  diagnostics to the private `agents/<agent>/.wake.log`, not the TUI composer.
- A new wake started with `--baseline-existing` (which `coop exec` adds) leaves
  messages already in `inbox/new` unread and notifies only for later arrivals.
  `wake repair` keeps the dead generation's suppression floor instead, so mail
  delivered while the notifier was down still notifies. When `coop exec`
  reuses a live owner-bound wake, it does not re-baseline that wake, so a
  pending backlog can still notify. See
  [wake operations](https://github.com/avivsinai/agent-message-queue/blob/main/docs/wake-operations.md).

## Message Handling

- `amq drain --include-body` — process incoming messages
- `amq send --to <partner>` — send work/findings to partner
- `amq send --to <partner> --wait-for drained --wait-timeout 60s` — block on a single-recipient handoff
- `amq receipts list --me <agent> --msg-id <msg_id>` — inspect delivery history
- `amq receipts wait --me <agent> --msg-id <msg_id> --stage drained` — wait for receipt arrival
- `amq reply --id <msg_id>` — reply in thread

## Spec Workflow

The spec workflow is a skill-managed protocol that uses standard AMQ kinds plus labels (`workflow:spec`, `phase:*`) on thread `spec/<topic>`.

Canonical spec phases are:
`Research -> Discuss -> Draft -> Review -> Present -> Execute`

For the full spec protocol, see the amq-spec skill's `spec-workflow.md`.
