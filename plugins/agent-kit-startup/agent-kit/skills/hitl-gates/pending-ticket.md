# Pending operator ticket (ask id `ticket`)

Procedure page for the Ground Control bucket (ADR `2026-10-08_countdown-coming-home-generic-lane.md` point 3; ask id `ticket` added to ADR `2026-09-19_headless-hitl-transport-and-live-tui.md` point 2 by its 2026-10-15 amend). Linked from `/start-project`, `/backlog-add`, `/continue-plan`, `/run-plan` and `/run-plan-all`. Labels and fallback rules: [SKILL.md](./SKILL.md).

## What a ticket is

A headless run started with `--land-on-gate` (or fired by `agent-kit countdown`) that stopped at an unanswered gate, was stopped by the operator, or failed leaves two things:

- an entry in `.cursor/context/gate-exit.json` (gitignored; `pending[]` holds the stamp, Ask id, labels, branch and PR/MR URL; `skipped[]` holds the Countdown fires refused while it waited);
- a note `.cursor/gate-exit/<stamp>.md` on a pushed `gate-exit/<stamp>` branch, usually with a PR/MR against the base.

The gate the note names is still unanswered. The ticket belongs to the operator; the agent never triages it alone.

## Detect (preflight)

1. Read `.cursor/context/gate-exit.json`. Absent, or `pending` empty: silent skip, no Ask, no mention.
2. Otherwise run `agent-kit ground-control status --json` (read-only) for each ticket's headline, branch state and review URL. CLI unavailable: use the marker fields alone.
3. Unreadable marker: one-line warning and continue. Never edit or delete the file by hand.

The ticket Ask is off the default path. It fires only while a ticket is pending, and then before the command's own entry Ask, like the API-limit pre-flight. Broad Intake (`/start-project`, `/backlog-add`) also lists each pending ticket as an `include` finding.

## Ask (id `ticket`)

One ticket per Ask, oldest stamp first. Question: "Pending operator ticket `<stamp>`: <headline>. What now?"

Labels, exact and in this order: `Read the ticket` / `Accept` / `Discard` / `Later`.

Numbered-list fallback (path 1):

```text
HITL_GATE: ticket | Read the ticket | Accept | Discard | Later
1. Read the ticket
2. Accept
3. Discard
4. Later
```

| Reply | Effect |
|-------|--------|
| `Read the ticket` | Print the note (`git show origin/gate-exit/<stamp>:.cursor/gate-exit/<stamp>.md`; else the marker fields) and the PR/MR URL, then Ask again with the same four labels |
| `Accept` | Run `agent-kit ground-control accept <stamp>`. Exit 0: ticket cleared. Exit 2: the branch is not merged into the base yet; say so, the ticket stays pending (the operator merges the PR/MR, the agent never does). Then continue the command |
| `Discard` | Run `agent-kit ground-control discard <stamp>` (closes the PR/MR when `gh`/`glab` is authenticated, deletes the branch, clears the entry). Exit 3: report it, the ticket stays. Then continue the command |
| `Later` | Leave the ticket pending and continue to the command's entry Ask. Do not Ask about it again in this command run |

Skip or cancel means stop: the command does not continue. `Accept` and `Discard` close the ticket only. The gate the note names is answered in a live session (`/continue-plan` or `/run-plan`) through its own Ask, never from this one and never with an inferred reply. Never merge the gate-exit PR/MR and never `/git-prod` from this procedure.

## Unattended dispatch

When nobody can answer (a `/run-plan-all` per-plan Task, a headless run started with `--no-hitl`, a Countdown fire), do not Ask and do not block: report the pending stamps in the worker return or run summary as `Pending tickets: <stamp>, ...` and continue. A Countdown fire already refuses to start while a ticket is pending.

## HANDOFF provenance

Record a triage only with its Ask id and reply (`ticket` + operator reply + label, or the `HITL_REPLY: ticket | ...` line in a headless run). Never write a ticket as accepted or discarded without that reply (`errors/2026-08-14_handoff-fabricated-hitl-provenance.md`).
