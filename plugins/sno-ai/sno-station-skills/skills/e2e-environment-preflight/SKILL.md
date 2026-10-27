---
name: e2e-environment-preflight
description: "Check external services, hosts, browser sessions, model endpoints, and agents before an end-to-end run. MANUAL-ONLY: load when a caller names it. NEVER auto-load from context for ordinary testing or debugging."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# e2e-environment-preflight — the gate that runs before the first row

**Never auto-triggered.** Named callers only:

| Caller | Moment |
|---|---|
| A requirements document or test plan | once end-to-end proof is required and the document names an external system |
| A task brief | before staffing any end-to-end journey |
| `e2e-red-triage` | when a red turns out to be environmental and owes a new check |

This skill is self-contained: the trigger and the three artifacts.

Terms: the **owner** is whoever owns the work, usually the user; a **row** is one acceptance check in the test plan; a **journey** is one end-to-end scenario made of rows; a **red** is a row that failed or gave no answer; the **suite** is all the rows of a journey.

**Each repository binds this locally.** A repo-level `e2e-environment-preflight` names its own systems, its
own primer directory, its own evidence paths, and its own configuration decisions. This file is
the contract; the local one is the address book. If the repository has no local binding, the
first journey that needs one writes it.

## The trigger, as an operational test

> The preflight is required when **any acceptance row's evidence comes from a system outside the
> repository under test** — a running service, a host, a browser session, a live model endpoint,
> an installed agent. Rows whose evidence is produced entirely by code in the repository do not
> trigger it.

The test plan or requirements document states the answer as one of two literal forms:

    External systems: none — <scope fact>
    External systems: <name>, <name> — preflight required

A library with no external systems answers `none` and never sees this skill again. **A plan that names a system for
which no primer exists does not pass** — that refusal is how the first primer for a system gets
written, without anyone having to remember to write it.

## Why this exists

The three classes that reliably burn days — anything with a login, anything driving a browser,
anything driving another agent — share one property: **when they break they produce nothing
rather than an error, and the nothing appears far from the cause.** A revoked credential still
reads as valid locally. A missing profile looks like an empty result. A dead actor looks like a
slow one.

So an hour goes into attributing an absence, and goes again next month on the next system.
The preflight moves that cost to the front, where it is paid once and mechanically.

Three reasons it is a gate and not a checklist: **you cannot tell a
product defect from a setup defect** once the suite is running; **every mid-run fix invalidates
the rows already passed**, so the suite stops being one observation and becomes N observations
of N environments; and **fix-one-rerun is a serial loop with a full suite inside it** — twelve
missing preconditions found one at a time cost twelve suite runs, found together they cost one
repair pass.

**No row starts while any check is red. Amber is red.** A check going red at row 14 stops there:
the run is void, rows 1–13 do not carry over, repair happens outside the run, and the preflight
runs again from the top.

## Two stages, in this order

Checking before the configuration is settled is checking against nothing. These are defaults; a project may choose otherwise and record it in its local binding.

**Stage A — settle the decisions.** Some preconditions cannot be checked because nobody has
said what correct means. A product with several valid configurations has no wrong setting to
detect; run the suite against whichever one happened to be set and it measures an arbitrary
configuration and answers a question nobody asked.

The sorting test is one sentence: **if two defensible answers would make the same row pass and
fail, it is the owner's decision.** Everything else the agent settles from the approved plan, the repository, or a written ruling — handing those up is noise, and noise makes the real questions
get skimmed.

Always the owner's, and most often forgotten: **the ceilings** — wall-clock, spend, and which
hosts may be destroyed. Ask with a recommendation derived from a measured sample. Without a
recorded ceiling the budget check cannot be green or red at all, and an executor invents one,
silently changing what *pass* means.

**Onboarding is part of this and is the part that gets skipped.** A run of a real flow starts
where a real user starts. If the product has a first-run path, the preflight names which path the run
takes. A suite that begins after onboarding has excluded the part most likely to break for a new
user, and it keeps passing while every new user fails.

Collect the owner's set from the whole plan first and ask in **one** exchange, each item with
options, downstream consequence, and your recommendation. Answers become configuration-of-record
in the preflight artifact — a configuration that lives only in a chat window cannot be reproduced
and cannot be cited.

**Stage B — derive the checks.** The standing floor — the checks every run needs whatever the plan says, such as the credential and absent-variable checks below — always applies. The project half is read
off the approved plan, never invented: every actor (service, agent, or process) named alive during the test, every artifact path
in an evidence requirement, every capability a planted defect needs. A precondition no row needs
is not added; a row whose preconditions were never extracted is a defect in the plan.

**A plan cannot name a precondition its author does not know exists.** That is what the primer supplies, and it is why Stage B depends on one.

## Artifact 1 — the system primer

One per external system, one per repository, re-derived on a version change. Contents:

- **The containment model, first, before any command.** What contains what. Most environment
  mistakes are made at this layer: someone who has not been told a namespace exists will never
  think to ask which one they are in, and will read an identifier off a directory path. A reader
  given the containment model predicts the traps instead of memorising them.
- **The identifier table — every value carries the command that re-derives it**, marked
  last-observed rather than stated. Prefer the command over the value.
- **Failure shape per dependency**: when this breaks, is it loud or quiet? The quiet ones are the
  entire reason the file exists.
- **A version binding and a void list** — what invalidates the document. Bind to the system's
  version, never to a date: a dated document rots silently, a version-bound one announces it.

**No bare value that has no command.** An accurate document quotes an identifier, the identifier moves, and the next reader inherits a false fact
that reads as surveyed truth. Your file will do this to its next reader unless the command is
preferred.

## Artifact 2 — the runner

One script per system. The primer exists so the runner is **derived from** it rather than
invented, which means every check carries five fields: the command, the expected observable, the
failure calibration, the person or team responsible for it, and the artifact field it writes.

- **A prose condition is not a check.** "The service is healthy" is an intention, and an executor
  satisfies an intention by believing it. Name the literal string, exit code, field value, count
  or deadline — and separately name what makes it red.
- **Reports every failure at once**, never stopping at the first; stopping recreates the serial
  loop the gate exists to replace.
- **Checks; never repairs.** A step that installs or fixes makes its own check pass by
  construction and hides that the environment was not ready. Repair is separate and explicit,
  after which the runner starts again from the top.
- **Exits nonzero if anything is red.**
- **Emits one artifact**: every check, its command, its observed output, its verdict, with a sha256 of its contents recorded in the run's results if the project keeps them, so a result can be traced to the
  world it ran in. A suite whose artifact is missing or stale did not pass this gate.
- **A check nobody has watched go red is not a check.** Break the precondition once, see it go
  red, restore, record it. Where breaking it is unsafe, say so in the calibration field and name
  what would have to exist to calibrate it.

**The baseline and the mutations allowed anyway.** Rows themselves change the environment — they
kill children, cut networks, plant stale records. So each row declares its own disposable
mutations before it runs; a declared mutation is expected, is reverted, and voids nothing.
Anything outside that allowlist — a dependency changed, a credential rotated, a host rebooted —
voids the run.

**The two rules that keep being skipped are one rule.** A credential check that reads a variable
has checked nothing; only a real call that returned a real response passes. And some variables
must be **absent**, enumerated by name and asserted empty, because a key that overrides the intended login path silently changes which account and model the entire run used.

**Acquiring a credential and using one are different things.** An interactive first-time login
does not fail this gate: the credential persists and refreshes, and every call after it is made
with no human present. What is not automatable is *recovery after revocation* — and that is the
gate working, not a hole in it. Record it as a bounded, named, human repair.

## Artifact 3 — the red scoreboard

**This is what the gate is for.** Every red gets exactly one bucket, appended to a journey-scoped
scoreboard beside the preflight artifact:

| Bucket | Meaning |
|---|---|
| `source` | a product defect — the only kind that counts as a win |
| `environment` | a precondition wrong or unset |
| `stuck` | no verdict at all: hang, timeout, empty, silent absence |
| `harness` | the test itself was wrong |

    {"row":"<row-id>","bucket":"source","note":"…","owed_check":null}

Four buckets, exhaustive, one per red, no "other". The rule that turns the scoreboard into a
ratchet:

> **An `environment` or `stuck` red must name the preflight check that should have caught it. If
> no such check exists, it is written before the journey closes** — `owed_check` carries the new
> check's id.

Report the four counts at the end of every run. Rising `source` with falling `environment` and
`stuck` is the gate working. Flat `environment` across two journeys means the ratchet is not
being applied — a process defect, not bad luck.

## Anti-patterns — any one fails the gate

These are defaults; a project may choose otherwise and record it in its local binding.

| | Anti-pattern | Why it is fatal |
|---|---|---|
| P1 | Asserting a variable is **set** instead of that the call **works** | set-and-wrong is the common case, not the edge case |
| P2 | Asking a human to paste a credential during the run | a missing credential is a design defect, not a question |
| P3 | Skipping a check because it passed last run | the environment changed; that is why it is a gate |
| P4 | A check that passes when its input source is missing | it must report SOURCE MISSING, never CLEAR |
| P5 | Installing or repairing inside the check | the check then measures itself |
| P6 | Starting with a known-amber item | amber is red; there is no third state |
| P7 | A preflight derived from imagination rather than the approved plan | it checks what no row needs and misses what every row needs |
| P8 | Counting a mocked dependency as ready | a mock proves nothing about the real system it stands in for |
| P9 | Choosing a configuration default silently | the run then measures an arbitrary setting |
| P10 | Asking the owner one decision at a time, or asking what is derivable | N rounds instead of one, and noise makes the real questions get skimmed |
| P11 | Starting the flow after onboarding because onboarding is "setup" | the first-run path is where new users break, and it stays untested forever |
