---
name: improve-loom-for-my-repo
description: >
  Use at the END of a session in which loom's code tools were used, when the
  user asks to improve loom, report what it got wrong, or asks "why did loom
  miss that". Harvests THIS session's own transcript — where loom answered,
  where you fell back to grep or whole-file reads, what you couldn't trust —
  and turns each gap into a reproducible finding the loom maintainers can
  act on. First sessions count most. NOT for filing bugs about repos loom
  doesn't index, and NOT for gaps this session did not actually hit.
disable-model-invocation: true
---

# improve-loom-for-my-repo — turn this session into fixes

Evidence rule: **if this session's transcript does not support a claim,
drop the claim.** No remembered grievances from other sessions, no
speculative "loom could also…" ideas. Every finding must cite the moment it
came from: what was asked, which loom call ran (or should have), what came
back.

Stop before Step 1 when either precondition fails, and say which:

- The repository is indexed: `code.repos` lists it, or a `loom_code_*` call
  this session answered with an `as_of` for it. Misses in an unindexed repo
  are not loom defects.
- This session holds at least one real miss: a loom call that answered
  wrong, abstained, or was not used where it should have answered.

## Step 1 — harvest four lists from the transcript

1. **Where loom answered.** Each loom call that settled a question, and
   what you did NOT have to read because of it.
2. **Every fallback.** Each Grep/rg/Glob/whole-file Read you ran — with
   what you were actually trying to learn, which loom op *should* have
   answered it, and why it didn't. A fallback made out of habit while an op
   would have worked is labelled *discoverability*, not *capability* — they
   get different fixes.
3. **Right but unusable.** Output that was correct but you couldn't read or
   trust: a count you couldn't interpret, an abstention you couldn't act
   on, a ranking you didn't believe, a stale `as_of`.
4. **First-run friction** (first session with loom only): token setup,
   namespace confusion, indexing wait, the first output nobody explained.

## Step 2 — localize each gap to a defect class

Classify against loom's pipeline so the fix lands in the right subsystem:
`ingest` (file/symbol never indexed — prove with a grep hit that has no
`code.symbol` result), `scip` (callers wrong/missing while the fast tier
has the symbol — check the row's `tier`), `rank` (right unit exists but
lost — **only real if you can write the labeled triple: the exact query,
the unit that should have led, and what led instead; that triple is the
fix's test, without it the finding is an opinion**), `serve` (budget cut
the answer, annotation wrong, disclosure missing), or `docs/skill`
(discoverability).

## Step 3 — the report

Header: loom server version (`/v1/health`), namespace, `as_of` commit,
corpus size (`code.index_status`). Per finding: severity (HIGH = wrong
output a user would act on; MEDIUM = missing capability; LOW = polish),
class, and a minimal reproduction runnable without this repo's private
context — for rank findings, the labeled triple verbatim. Order by
evidence strength × impact.

Every `rank` triple should be offered as a candidate fixture row for
`bench/fixtures/code_intel_qa.jsonl` — user feedback arriving pre-shaped
as a red test is the whole point of this skill.

## Step 4 — one report, no duplicates

Before filing, search for each finding among existing issues
(`gh issue list --repo ClickHouse/loom --state all --search "<symbol or
query>"`). A finding that is already reported becomes a comment on that
issue with this session's reproduction, not a new issue. Drop a finding
this session repeated itself; one report per session.

Destination: paste the report verbatim (do not summarize it into an
impression) into a GitHub issue on ClickHouse/loom titled
`<namespace>: <top finding>`, or hand it to the user to file. Filing or
commenting is the user's call: show the report first.
