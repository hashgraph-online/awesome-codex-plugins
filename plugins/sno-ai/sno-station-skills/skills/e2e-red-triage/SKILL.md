---
name: e2e-red-triage
description: "Classify one unexpected end-to-end test failure as a product defect or an environment fault needing a new preflight check. MANUAL-ONLY: load when the suite runner names a specific failure. NEVER auto-load from context."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# e2e-red-triage — for the reds the preflight could not have predicted

Terms are as in `e2e-environment-preflight`: a **row** is one acceptance check in the test plan, a **red** is a row that failed or gave no answer, a **journey** is one end-to-end scenario made of rows, the **suite** is all the rows of a journey, and **preflight** is the set of environment checks that must be green before the first row runs.

**Never auto-triggered, and normally never needed.** One caller — the agent running the suite —
and one moment:

> The `e2e-environment-preflight` checks were **all green**, and a row went **red anyway** — or produced a
> null, an empty, a zero, or a silence nobody can yet explain.

If preflight was not green, the suite should not have started. If a red is an ordinary product
failure with a clear cause, fix it and move on; this is not the ceremony for an ordinary bug.
This is the residual after the gate has done its work — a small fraction, and one
that shrinks every time move 3 is honoured.

## Why this needs its own protocol

The preflight handles the failures somebody could enumerate in advance. What is left is the class
where **the failure produced nothing rather than an error, and the nothing appeared far from its
cause.** One null can mean five different things across five runs of the same suite; "no results" can mean the query matched nothing or the search never ran.

The hours such a red costs are spent **attributing an absence** — arguing about what a missing
thing meant, from evidence that never contained the answer. Guessing feels faster than
instrumenting and is not: a wrong guess costs a full suite run to disprove, and a *plausible*
wrong guess is worse than an implausible one because it stops the search.

The deeper version, and the one worth carrying: **the failure is usually a two-part outcome
collapsed into one verdict.** An HTTP 202 "accepted" means the request was queued, not that the work was done, and both caller and monitor read it as success until someone looks. A cleanly stopped service records
an exit code that looks like a crash. In each case the evidence was there, in plain
words, and nobody split it.

**So the first question is never "why did it fail" — it is "what are the two halves of this
result, and which half am I looking at?"**

## The three moves, in order

These are defaults; a project may choose otherwise and record it in its local binding.

### 1. Do not guess. Enter diagnosis.

Stop proposing causes. Write down first the two things this result could be a collapse of:
succeeded versus reached, stopped versus crashed, empty versus unreadable, absent versus
never-asked, zero-matches versus source-missing.

### 2. The first change makes the absence name itself. Not the product.

**The first commit after this kind of red does not touch product behaviour.** It changes whatever
produced the empty so that it says *why* it is empty — in the artifact, as a field, not in a log
line, which is read only by someone who already suspects the answer.

    result: null
    →  result: {value: null, because: "<the reason, as a code>"}

Then re-run. Only now diagnose. This inverts the usual instinct and that is the point:
instrumenting first looks slower for one iteration and is faster from the second onward, because
every future occurrence of this absence becomes a single read instead of an investigation.

Two shapes to watch for here, because both report health while broken:

- **A check that passes when its input source is missing.** A count over a path that does not
  exist returns zero — the same zero a real path with no matches returns. Before any "it is
  absent" claim, prove the place you looked at is real, then look.
- **A condition that can no longer fire.** An alarm testing an absolute count rather than a delta
  switches itself off permanently the first time the count moves.

Feed every new check a known-wrong input and watch it go red. Instruments fail toward "healthy".

### 3. The exit condition: come back with a durable check.

**A diagnosis is not the end. The finding becomes a new preflight check for that system and a line in that system's primer (see `e2e-environment-preflight`), or this red is not closed.**

Invoke `e2e-environment-preflight` to write it, and record the red in the red scoreboard described in `e2e-environment-preflight`, with its bucket and the new check's id:

    {"row":"<row-id>","bucket":"environment","note":"…","owed_check":"<check-id>"}

This is the only mechanism that makes the residual shrink. Without it the same class of absence
is rediscovered every campaign and the gate never gets stronger — the process runs, everyone is
diligent, and the hours are spent again. **Hitting the wall is allowed; coming back with nothing
durable is not.**

## Classify before you close

Every red gets exactly one bucket — `source`, `environment`, `stuck`, `harness`. Be honest about
`stuck`: a run that produced no verdict at all is not a pass and not a skip, and burying it is how
a campaign reports coverage it never had.

The counts are the point. A journey whose reds are mostly `source` found bugs. One whose reds are
mostly `environment` or `stuck` measured its own setup, and the fix for that is upstream in the preflight — never another round here.
