# Punch List

> The enforced to-do for this shift. The clock-out gate (a Stop hook) blocks ending the session
> while any item in the **Items** list below is an open `- [ ]`. Everything above that heading is
> the contract — binding for the duration of the shift. Only the Items list changes: tick boxes to
> `- [x]` as work finishes.
> Owner-approved active work belongs here. Known later work belongs in `drafting-table.md`;
> unresolved owner decisions belong in `parking-lot.md`; timed Hunt orders belong in
> `work-orders.md`.

## Never idle, never ask, never wait

- During a shift, asking the user is denied — park, don't ask. A decision that is genuinely the
  owner's goes in `parking-lot.md` in plain language, with the most sensible production-grade
  default chosen so work continues. Never block the run waiting for an answer.
- There is always a next concrete edit. A walkthrough cycle that finds nothing new is success, not
  idleness.

## How the shift ends (and only these ways)

- **Done** — every box in the Items list is `- [x]`. The ticks are the truth; no magic phrase ends it.
- **Stop-work order** — `STOP` exists (the Nightshift Stop skill, or
  `touch "$NS/STOP"` on POSIX, or
  `New-Item -ItemType File -Force "$NS\STOP"` in native Windows
  PowerShell). Open boxes stay
  open as the record of where work stopped.
- **Quitting time** — past `deadline`, the gate clocks the shift out. Belongs to
  open-ended work: start NOTHING new past the whistle, finish the unit in hand, then clock out.
- **Orderly clock-out** — if a shift must end with work in hand, commit it as a `wip:` commit
  (repository mode) or write an artifact receipt (artifact mode), plus
  one handover line in `shift-log.md`, then stop.

## The standard — what "done" means

- Production-ready, best effort, every time. No stubs, no "future feature", no "documented for
  later", no trivial-only edits. If you can do it now, do it now.
- Effort is never a reason to defer. "This deserves a focused session" — this IS the focused
  session. Size, difficulty, or hours already spent never justify a stub, a narrowed scope, or
  splitting an item for later. Only correctness does.
- Run the item gate (the `## Gates` block below) right before each commit or artifact receipt; it must be green to tick.
- No suppression — fix root causes. No lint disables without a written reason next to them.
- One conventional commit per item in repository mode; one artifact receipt per item in artifact mode under `$NS/receipts/` (`runtime/write-receipt.sh`, or `runtime/windows/write-receipt.ps1` on native Windows). Local only. Never fake a tick.

## Site discipline

- **Deletion is not completion** — never remove an item or edit this contract to end the shift. If
  either is ever altered, restore it, then tick only after the item is complete.
- **History is append-only on shift** — no `reset --hard`, no `rebase`, no `commit --amend`, no
  force operations. The night's receipts must survive to morning.
- **Pushing is the owner's** — commit locally; the owner reviews and pushes. Push only where an
  item explicitly says to.

## Immutable

Everything above the Items heading is the contract. It binds the agent for the shift — never
modify, trim, or reword it. The owner may edit the `## Gates` block anytime, so re-read it each
item. Only the Items list changes.

## Gates

<!-- Nightshift Setup fills this from your stack, or leaves it empty (no automated checks).
     Item gate: runs every item, right before its commit or artifact receipt — must be green to tick.
     Site inspection: the heavier batch (coverage, dead code, Sonar), every N items or H hours. -->

_None configured._

## Items

<!-- Empty until you promote work here from drafting-table.md — while this is empty the gate stays
     inert. One top-level open checkbox per task (a dash, a space, then a bracketed space), each
     with its own sub-bullets, a Verify line, and a Commit line (repository) or receipt (artifact). Tick to a bracketed x when done.
     drafting-table.md carries the exact shape. Keep the illustration out of this file: any
     bracketed-space checkbox here, even in a comment, counts as an open item. -->
