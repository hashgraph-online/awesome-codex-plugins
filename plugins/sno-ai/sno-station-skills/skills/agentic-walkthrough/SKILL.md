---
name: agentic-walkthrough
description: "Prove that a reported run caused its intended real effect. Walk the executor path from entry to effect, capture one observable per hop, and report a result a no-op could not produce."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Agentic Walkthrough — take the program's seat

The stance is the whole method. You are not a reviewer standing outside the code with a
checklist; you are the thing the source describes — the job, the stage, the handler — and
you run it in your head, hop by hop, exactly as it would run, noticing every switch you pass
and every place your output goes. Only then do you turn to the real system and make it show
you that what you just walked actually happened. The principle: BE the executor, then make the
executor prove itself.

Ordinary debugging starts from a failure — an error, a red test, a wrong number. This starts from
the opposite and much quieter case: **everything reports success and you still do not know whether
the work happened.**

That case is real and it is not rare. A stage that cannot do its work can still report `done`. A
job can start, finish, write a trace, and pass its own verification while touching nothing. No
test suite catches this, because no assertion in the suite is false.

Three moves, in order. How far to take each is your judgment — often the first cannot finish
without the ones after it.

## 1. Walk the path — be the program, read, don't run

Put yourself where the code sits and go hop by hop from entry point to effect. You are reading,
not executing, which is the whole point: a live run cannot show you the branch it never took.

Three questions at each hop are usually enough:

- **What switch controls this hop, and what is its value right now?** A config key, an env var, a
  feature flag, a job type, a default argument.
- **If that switch is off, does it fail loud or continue quiet?** Quiet defaults are where these
  bugs live. Loud failures are already visible — you are hunting the silent ones.
- **What does this hop actually do — which line?** If you cannot name the line, you have not
  shown the hop does anything.

**The last hop is the one everyone skips and it is usually the decisive one: is this output
visible to whatever consumes it downstream?** A stage that runs perfectly and writes where nothing
reads is indistinguishable from a stage that never ran. Check the reader's path, not the writer's
— they are frequently not the same file, the same directory, or the same database.

Where to start and how deep to go is judgment. Go where the switches are dense, or where the
evidence gets thin.

## 2. Probe every hop that has to be real

The walk tells you which hops matter. A probe is how you make one of them prove itself.

**Keep each probe narrow: one observable that only the real thing could have produced.** A broad
health check is worth little here, because everything passes it — that is the whole problem. The
walk already told you what this hop is supposed to do; probe exactly that.

These classes come up again and again, and each fails in a way that looks fine from the caller's
side. Treat them as places to look, not a checklist to complete.

- **Stored state — the rows themselves.** Take a concrete failing case and pull out the actual
  record behind it. A log says a write happened; only the row can distinguish a correct write from
  one that hit the wrong record, wrote the wrong value, or was counted but never committed.
  Landed → the defect is downstream. Did not land → the write logic is wrong, and nothing built on
  top of it is worth tuning. **Expect to need the product's own accessor** — encryption, a key
  held elsewhere, a custom codec. A generic CLI failing to open the store is normal, not a wall.
- **Database identity.** Which file did the process actually open — resolve the real path — and is
  it the same one the reader queries? Path resolution usually consults several sources in an order
  nobody remembers, and the first one wins.
- **Model and API calls.** Did a request actually leave? How many, to which endpoint, under which
  model or account? Then the part usually skipped: **does the response contain what the caller
  assumes?** A 200 with an empty body sails through an `if (ok)` check. Zero calls is the loudest
  possible answer and the easiest one to miss.
- **Accelerator and environment setup.** A path that silently falls back to CPU still finishes,
  just differently. Ask which device the work actually landed on, not whether setup returned
  without error. Same shape for any "configure, then hope" step.
- **File input and output.** Did the bytes land where the consumer looks? A temp directory that
  gets cleaned, a relative path resolved from a different working directory, an output written
  somewhere nothing reads — all of these leave a successful write behind.
- **Child processes and third-party services.** Did it actually start, is the thing you matched
  actually it, is it listening, and did it stay up — or exit a second later while the parent
  carried on?

## 3. Report a number, not an impression

This is the one part worth being strict about, because it is what separates a gate from a reading
exercise.

**Finish with a number a no-op could not have produced, plus the line where each action happens.**
*N rows changed, M requests sent, and here is where I can see those N rows differ.*

- **Zero is a failure of the walk, not a result.** It means you found the path broken.
- **"The walk went well" is not a finding.** Neither is a summary with the numbers dropped.
- **If you cannot name the line, that action is not proven to run.**

## Before any absence becomes a finding, check your instrument

Most wrong conclusions here come from a check that could never have said anything else. **Prove
your check could have produced the other answer** — feed it a case you know is positive and watch
it fire. Shapes this actually takes:

- `grep -c` against a path that does not exist returns `0`, identical to a real file with no
  matches. Confirm the path exists before the count means anything.
- A process match can match the wrong process: a wrapper, a script that names your target as an
  argument, or your own shell.
- A progress check can range over the wrong quantity and read as stalled while the job is healthy.
- **Timestamps are asymmetric.** An *unchanged* modification time is strong evidence nothing
  touched the file. A *changed* one is evidence of almost nothing — opening a store,
  checkpointing, or migrating a schema all touch the file without doing the work you are after.
<!-- reminders:start -->
<!-- reminders:end -->
