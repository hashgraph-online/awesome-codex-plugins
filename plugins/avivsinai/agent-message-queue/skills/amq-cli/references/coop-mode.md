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

- After completing an assignment, send its closing reply (changes and verification) and stop
- When idle, set presence instead of messaging: `amq presence set --status available`.
  A message such as «done, my inbox is clear, I'm available» costs the initiator a
  full turn and tells it nothing that presence and the closing reply do not.
- While waiting, safe to do: review partner's work, run tests, read docs

## Progress protocol

Every message wakes its receiver, and a wake re-reads the receiver's whole
context. Send a message only when it changes what the receiver does now: a
question, a blocker, a verdict or result it waits for, or a correction.

Do not acknowledge an assignment or send an ETA unless the initiator asked for
one. Use urgent priority for a time-critical verdict or unblocking request.

Reply to the initiator on the existing thread, and finish with changes and
verification. Do not reply to a message that leaves you nothing to do or answer.

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

- To request an interrupt notice, check the receiving wake's interrupt enablement,
  priority and label with `amq wake config --me <handle>`. Use the configured
  priority and label. Sending a real interrupt to the process requires the
  separate, explicit `--interrupt-cmd ctrl-c` setting.
- The default wake is a plain doorbell, so input injection can activate a
  focused permission or approval dialog. Payload text alone may match
  single-key shortcuts, so removing Enter is not safe. The dialog guard is
  opt-in: `amq wake install-dialog-hook --harness claude|codex|cursor` (Codex
  also needs the entries trusted in `/hooks`); `amq coop exec` prints
  `dialog guard: plain` or `dialog guard: proper (<harness>)`.
- `--defer-while-input` reduces collisions with recent typing but cannot detect
  modal state; an idle dialog looks like an idle composer.
- Grok shows no signal AMQ can read for its approval prompt, and Cursor runs
  no hook for prompts it shows before any tool call, so a doorbell during
  such a prompt can answer it (known limit).
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

- `amq drain --for-turn` — process incoming messages
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
