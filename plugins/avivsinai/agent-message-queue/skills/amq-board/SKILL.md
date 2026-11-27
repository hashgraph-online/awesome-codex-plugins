---
name: amq-board
version: 0.172.0 # x-release-please-version
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
affects the answer. A STALE first line means sync before acting.

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

For a continuously published board, run `amq-board sync --watch --notify lead,alt
--as floor`. The watch goes on after a failed pass, tries again each minute, and
ends on Ctrl-C or TERM, or when the project was replaced. Each new floor problem
is sent once after every pass; a board that stops being published is reported by
the existing stale notice after the liveness window.
Each line is one problem for the lead to act on: dispatch what is ready,
ask the seat once, then replace it. It is not proof that a process stopped.

Each roster seat carries one context line: the prompt size of the newest
counted response of the worker's mapped sessions, with its age, and the 5 h
cache-read share when the window holds cache reads. pi records no cache
reads, so a pi seat shows no share. The line is a measured fact for judging
how full a seat's context is; the board sets no threshold and gives no
advice.

`seat_stalled`, `seat_at_limit`, `account_near_cap`, `ready_not_started`,
`in_progress_not_worked`, `reply_overdue` and `source_failed` are the kinds.
`source_failed` means the source's `read_failed` fact: its read in this
pass failed (for several homes, at least one home read failed). The
problem's `source` field names the failing
provider, and its incident identity ignores error prose. A retained card does
not change a failed current read to a successful one. Each source reports one
of these states:

| State | Meaning | Floor problem |
| --- | --- | --- |
| ok | The read supplied a current list | no |
| ok with limits | Partial or capacity-limited; the coverage names the limit | no |
| read failed | `read_failed` is true; the read of this source failed in this pass | yes, `source_failed` |
| unavailable or disabled | The source has no home or is turned off; shown, not read | no |

`account_near_cap` fires when an account's freshest cap reading shows 90
percent or more used. A reading stays current until its future reset time;
without one, its timestamp must be inside the 15-minute bound. The
newest fact for a cap decides before the threshold, so an older 95-percent
reading beside a newer half-used one raises nothing. It is
the account's fact: no mapped worker or card is needed. Codex reports the
pre-limit figures; Claude Code and pi publish nothing before the limit, so
they give no line.
`reply_overdue` covers overdue agent replies, owner questions and owner
rulings. The sender reads the thread before taking a default or closing a
ruling. The command exits 0 on an empty list, 6
on problems, and 1 on a stale or absent snapshot. A seat whose harness records
no activity cannot produce `in_progress_not_worked` without that evidence.

`amq presence list` shows all stored notes with their `note_at` age or
`(age unknown)`. An old Note timestamp does not remove a roster record there.
The Floor alone hides notes older than `liveness_window`, and `note_at` tracks
text changes rather than activity. All read-only board faces label stale
published input instead of reading sources or refreshing. Text/HTML explicitly
say every number is old; JSON/pane carry `stale` (also `false` when fresh) and
`published_age_seconds`; retro refuses over-age input.

An unclosed request older than `obligation_max_age` (14 days by default) expires, as in `amq thread open`. It leaves Needs you and the overdue check. Set `obligation_max_age` to `0` to disable expiry.

## Retro

Old history is refused: sync before acting on the report.

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
