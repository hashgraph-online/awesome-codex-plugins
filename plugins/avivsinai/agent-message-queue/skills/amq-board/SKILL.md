---
name: amq-board
version: 0.168.3 # x-release-please-version
description: "Read the AMQ fleet board when asked for current work, check the floor for stalled seats, measure request history in a retrospective, or classify recent requests on demand."
metadata:
  short-description: Fleet board and on-demand request labels
  compatibility: claude-code, codex-cli
---

# AMQ board

## Read the board

```sh
amq-board                          # text
amq-board --json                   # published model, including source coverage
amq-board --html --out board.html  # one static page
```

Read the source ages and coverage for this project. On first initialization run
`amq-board sync --init`. When a fresh view is requested, or the last source read
is over ten minutes old, run `amq-board sync` in this project and read the
published view again. Name any stale, unavailable or incomplete source that
affects the answer.

The Requests section lists questions, review requests, and todos. Each
recipient has an observation: a direct reply (a message whose last ref is
the request), then later messages in the same thread as secondary context,
or "not assessed" when the recipient's session is unknown. The headline
counts only recent requests to the owner with no direct reply observed. The
Requests section counts requests to agents with no direct reply as the
agents' bookkeeping, with its coverage notes.

## Check the floor

After `amq-board sync`, run `amq-board check` (`--json` for the same rows).
For scheduled notices, create a dedicated `floor` observer, then run
`amq-board check --notify lead,alt --as floor`. Both recipients regularly
receive each new incident once, with the observer's original problem text.
Failed pairs retry; a stale board tells of `board_stale` and retains the set.
Never use a working seat as the sender because its unread notice affects
later stall analysis. Every distinct handle resolves live before sending.
This is an explicit optional broadcast; plain check output is unchanged.
Each line is one problem for the lead to act on: dispatch what is ready,
ask the seat once, then replace it. It is not proof that a process stopped.

`seat_stalled`, `seat_at_limit`, `ready_not_started`,
`in_progress_not_worked` and `reply_overdue` are the kinds. `reply_overdue`
covers overdue agent replies, owner questions and owner rulings. The sender
reads the thread before taking a default or closing a ruling. The command exits 0 on an empty list, 6
on problems, and 1 on a stale or absent snapshot. A seat whose harness records
no activity cannot produce `in_progress_not_worked` without that evidence.

An unclosed request older than `obligation_max_age` (14 days by default) expires, as in `amq thread open`. It leaves Needs you and the overdue check. Set `obligation_max_age` to `0` to disable expiry.

## Retro

Run `amq-board retro` every two weeks, or after a bad day.
The lead takes the worst number and assigns one fix to an owner.
A rule nobody needed in the period is a candidate for removal.

## Classify recent requests

When the caller asks for request labels, follow
[classify recent requests](references/classify.md). Report the classifier and
supporting quote for each judgment.

## Report

Describe labels as one model's opinions, with the classifier name and its
quote. Keep observations and opinions apart. Lead with the requests to the
owner; report the agents' count as their bookkeeping, with its coverage
notes. Never present either count as unfinished work.
