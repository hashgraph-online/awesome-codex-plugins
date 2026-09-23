---
name: retrospective
description: "Audit whether prior learnings actually fired, then install mechanisms for this run's recurrences. No finding without an install path and a firing test. Triggers: retrospective, reflect, what did we learn, patterns, post-mortem, why does this keep happening."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
kernel:
  kind: state_transition
  version: 3
  side_effects: writes_repo
  confirmation: on_side_effect
  produces:
    - kernel.retrospective-result/v2
---

<skill id="retrospective">

<purpose>
This skill was redesigned 2026-09-03 because it was measurably not working.

A follow-through audit of every retrospective, chronicle, plan and report in the Vaults counted
**24 promised fixes: 15 live, 9 dead or never built.** The worst mistake class, unverified claims
reaching a human, had been written up **11 separate times**, and both of its proposed fixes were
still unbuilt. Meanwhile `improvement-gate.sh`, the hook that enforced "every run improves the
system that does the work", was retired 2026-07-28 and nothing ever replaced it.

The old version of this skill was not badly reasoned. Its nine lenses were sharp. It failed for
one structural reason: **every output was a ledger row, and a ledger row enforces nothing.** A
lesson written to a ledger that nothing reads at the moment of action is a gravestone with better
formatting.

So version 3 inverts what this skill is for.

| | v2 | v3 |
|---|---|---|
| primary question | what did we learn | did the last learnings actually fire |
| output | ledger rows | installed mechanisms, or an explicit accepted-no-mechanism row |
| when learning happens | here, at end of run | at error time, by `error-loop.py`; here only for what error time cannot see |
| a finding with no mechanism | acceptable | REFUSED, or recorded as explicitly accepted with a reason |

**This skill is no longer the primary learning mechanism, and must not be treated as one.**
Error-time closing belongs to `_meta/services/error-loop.py`, which opens a defect the moment a
gate we own fails and refuses the next commit until a lesson or a waive is recorded. That catches
the single instance while the cause is still warm.

What error-time closing structurally CANNOT see is recurrence across runs: the same mistake in
different clothes, three independent reinventions of one missing primitive, a guard that has been
quietly dead for six weeks. That, and only that, is what this skill is for.

Proportionality is a hard rule, not a preference. Aria has named the failure out loud:
"overengineering the fuck out of this". A retrospective longer than the work it describes is a
defect. If phase 0 finds nothing dead and phase 2 finds no recurrence, the correct output is four
lines saying so.
</purpose>

<on_start>
agentdb read-start
agentdb recall "<the run's concrete nouns: files, symbols, error text>"
for L in beliefs patterns anomalies questions; do tail -20 "_meta/ledgers/$L.jsonl" 2>/dev/null; done
python3 _meta/services/error-loop.py list      # anything still open from error time?
ls -t _meta/reports/retrospective-*.json 2>/dev/null | head -3
</on_start>

<!-- ============================================================ -->
<!-- PHASE 0 - MANDATORY. Audit the last promises BEFORE making new ones. -->
<!-- ============================================================ -->
<phase id="0_followthrough" name="Did the last learnings fire?" mandatory="true">

A run that adds a new promise while an old one lies dead has made the problem worse, so this
phase runs first and cannot be skipped.

1. Read the previous retrospective's `mechanisms[]` and the last 20 rows of each ledger.
2. For each promised mechanism, resolve a verdict. **LIVE requires two facts: the file exists AND
   something invokes it.** Prove the second with a grep, never by reading the file.
   - wired into a `settings.json` hook chain, or
   - a `jobctl` registry entry that `launchctl list` actually shows loaded, or
   - a git hook, or
   - a script another live script calls.
3. Any mechanism whose file exists but which nothing invokes is **DEAD**, not live. Say so in
   those words. A file nobody runs is indistinguishable from a file nobody wrote.
4. Any mechanism that was retired: find its replacement and verify the replacement is LIVE. A
   retirement with no live successor is a **REGRESSION** and outranks every new finding this run.
5. Count: promised, LIVE, DEAD, NEVER BUILT. That ratio is the headline of the report.

OUTPUT: `followthrough[]`, one row per prior mechanism with `{name, verdict, invoked_by, evidence}`,
plus the four counts. A phase 0 with no counts did not run.

STOP CONDITION: if anything is DEAD or a REGRESSION, fixing or formally retiring it takes priority
over every new lesson below. Report that and act on it first.
</phase>

<!-- ============================================================ -->
<!-- PHASE 1 - EVIDENCE. What happened, not the tidy story of it. -->
<!-- ============================================================ -->
<phase id="1_evidence" name="Gather the run's real evidence">

Reason from artifacts, never from recollection. Pull `git log` and the diff, reverted commits and
abandoned branches, failed test runs, guard refusals, escalations, receipts and verdicts, and the
`error-loop.py` entries opened this run.

Guard refusals are the highest-signal item in that list and the most commonly discarded. A hook
that refused something recorded a mistake a machine could already see; that is a finished
experiment, free of charge.

OUTPUT: a quotable evidence list. Anything not traceable to a commit, a log line, a receipt or a
recorded decision is marked `inference`, never `finding`.
</phase>

<!-- ============================================================ -->
<!-- PHASE 2 - RECURRENCE. The only thing error time cannot see.  -->
<!-- ============================================================ -->
<phase id="2_recurrence" name="What is this the Nth instance of?" mandatory="true">

Single instances were already handled at error time. This phase looks ACROSS runs, which is the
one thing no error-time hook can do.

1. For each finding, search the ledgers, chronicles and agentdb for prior instances. Search the
   CONCEPT from a second vocabulary, not just the words this run happened to use: the error code,
   the table name, the route, the domain noun. A negative grep is evidence about your pattern, not
   about the world.
2. Count instances and list every date. **Two or more is a recurrence and demands a mechanism.**
3. Ask the question that generalizes: are these one mistake in different clothes? Three
   independent reinventions of one primitive that has no name yet?
4. Then run at most TWO further lenses, whichever bite for this run. Skip the rest; a lens with no
   artifact is narration.
   - **surprise**: where was my prediction most wrong? `prediction -> reality -> evidence`.
   - **belief-update**: what do I believe less now, and what contradicted it?
   - **anomaly**: what does not fit my explanation? Preserve it with a
     `preserve_until_condition`; do NOT resolve an anomaly you had to reach for an explanation
     for. Anti-convergence is load-bearing: a weird result kept alive unexplained for three runs
     is worth more than a tidy story now.
   - **abstraction**: what did I build manually that is secretly a reusable primitive?

OUTPUT: `recurrences[]` with `{class, instances[], dates[], prior_promises[]}` and at most two
lens artifacts.
</phase>

<!-- ============================================================ -->
<!-- PHASE 3 - MECHANISM. The gate. No install path, no finding.  -->
<!-- ============================================================ -->
<phase id="3_mechanism" name="Convert every recurrence into a machine" mandatory="true">

This phase is why the skill exists. Everything above is input to it.

**A recurrence leaves this phase in exactly one of two states. There is no third.**

1. **INSTALLED**, with all four fields filled and verified:
   - `failure_class`: what it refuses, stated as a class not an instance
   - `install_path`: the real file, and what invokes it, proven by grep
   - `refusal_condition`: exactly when it says no
   - `firing_test`: the one-line command that makes it fire, RUN, with its output pasted
2. **ACCEPTED**, explicitly: `{class, why_no_mechanism, who_accepted, revisit_when}`. An honest
   accepted row is a good outcome. A silent omission is not.

Rules that hold without exception:

3. Prose is never a mechanism. Adding a sentence to a CLAUDE.md, a skill, or a reference file
   does not count and must never be recorded as a fix. Every recurrence class in the audit that
   was "fixed" in prose recurred.
4. Prefer the machine that refuses at the moment of action over the one that reports afterwards.
   A gate at Stop is a retrospective wearing a hook's clothes; that is precisely how
   `improvement-gate.sh` died.
5. Derive authority from something the caller does not control: a pinned precedent commit, a canon
   document, the deployed artifact, a prior measurement. A gate that grades work against an
   expectation the caller supplies can never fail.
6. A new mechanism must COMPOSE with the existing ones, never short-circuit past them. Reaching
   for `continue` in a function that accumulates a verdict is the tell. A new fault state may
   displace the healthy state and nothing else.
7. Before recommending any checker, RUN it on the current tree. A gate that breaks the build on
   first run is worse than no gate.
8. Break it on purpose in an isolated copy and confirm the checker catches it. An unfired guard is
   a guess.

**Test discipline**, measured 2026-09-03: of about 40 test suites examined, 4 had any receipt of
ever catching a real defect, and roughly 36 were wired to nothing at all. So a test earns its keep
only when BOTH hold: something runs it without a human remembering to, and it names the specific
defect class it exists to catch, proven by failing against the broken state first. If you cannot
name the observed defect, do not write the test.

OUTPUT: `mechanisms[]`, every row INSTALLED with a pasted firing test or ACCEPTED with a reason.
A row that is neither is a defect in this report.
</phase>

<!-- ============================================================ -->
<!-- PHASE 4 - WRITE IT DOWN, SIZED TO THE CONSEQUENCE.           -->
<!-- ============================================================ -->
<phase id="4_record" name="Record, proportionally">

1. `_meta/reports/retrospective-<date>.json` as `kernel.retrospective-result/v2`, carrying
   `followthrough[]`, the four counts, `recurrences[]`, `mechanisms[]`, and the lens artifacts.
   `mechanisms[]` is what the NEXT run's phase 0 audits, so name each one exactly as installed.
2. Ledger writes only where the row will be read at a moment that matters. A belief nothing
   consults is not worth a line.
3. `agentdb learn` for anything that must fire during future work rather than at the next
   retrospective. Concrete nouns; a lesson nobody can recall is not stored.
4. Chronicle at the tier `_meta/services/chronicle-triage.sh` computes. Not the tier you feel.
5. Hard cap: if the report is longer than the work it describes, cut it. Nothing dead in phase 0
   and no recurrence in phase 2 means the whole output is four lines saying exactly that.

OUTPUT: the report path, the four counts, and the count of mechanisms installed versus accepted.
</phase>

<failure_modes>
Each of these actually happened. They are not hypotheticals.

1. **Ledger as gravestone.** A learning written where nothing reads it at the moment of action.
   24 promises, 9 dead. Fix: phase 3 or an explicit accepted row.
2. **Prose as fix.** The rule gets a better sentence and recurs anyway. Every prose-only class in
   the audit recurred.
3. **Enforcement at Stop.** The session has moved on and the nag competes with wrapping up.
   `improvement-gate.sh`, retired with no successor.
4. **Retirement without replacement.** Three hooks retired 2026-07-28 on a real argument; nothing
   took over their function. Phase 0 step 4 exists for this.
5. **The guard nobody invokes.** The file is perfect and no chain calls it. Phase 0 step 2 demands
   the grep for exactly this reason.
6. **Hardening that breaks the thing.** A launcher hardened to a root-owned path that was never
   installed left an "automated" pipeline unschedulable for nine days while its own status read
   OK. Always prove the good case still runs after adding a gate.
7. **The report longer than the work.** Buries the two facts that mattered and spends the reader's
   attention, the scarcest resource here.
</failure_modes>

</skill>
