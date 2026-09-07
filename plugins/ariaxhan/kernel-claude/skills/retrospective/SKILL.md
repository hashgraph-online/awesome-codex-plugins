---
name: retrospective
description: "Turn a finished run into a change to what you know: surprises, belief updates, preserved anomalies, named primitives, bounded architecture mutations. Writes the beliefs/patterns/anomalies/questions ledgers. Triggers: retrospective, reflect, what did we learn, patterns, synthesis, post-mortem."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
kernel:
  kind: state_transition
  version: 2
  side_effects: writes_repo
  confirmation: on_side_effect
  produces:
    - kernel.retrospective-result/v1
---

<skill id="retrospective">

<purpose>
"What went well / badly / next time" extracts operational hygiene, not intelligence. The better
question: **what did this work teach us that we did not know we were learning?**

This is not a summary artifact, it is a memory-update process:

`evidence -> surprises -> belief changes -> patterns -> unresolved anomalies -> reusable
primitives -> new questions -> bounded architecture mutations`

Each run CHANGES the accumulated model, rather than adding one more markdown gravestone. It does
that by comparing against prior runs and writing four evolving ledgers, so a lesson learned twice
is caught, a pattern with enough evidence is promoted, and a belief that no longer holds is retired.

Anti-convergence rule, load-bearing: models are eager to explain everything. Sometimes the
highest-value move is keeping a weird result alive, unexplained, until three future runs reveal
what it means. Do not resolve an anomaly you cannot yet explain; preserve it.

Every phase below emits an artifact. A phase that produced only prose did not run.
</purpose>

<on_start>
agentdb read-start   # prior learnings seed the analysis
agentdb query "SELECT id, type, insight, evidence, hit_count, load_count, ts, last_hit FROM learnings ORDER BY ts DESC"
for L in beliefs patterns anomalies questions; do tail -40 "_meta/ledgers/$L.jsonl" 2>/dev/null; done
ls -t _meta/reports/retrospective-*.json 2>/dev/null | head -3   # compare, do not re-derive
</on_start>

<!-- ============================================================ -->
<!-- PHASE 1 - EVIDENCE. The raw material, not opinion about it.  -->
<!-- ============================================================ -->
<phase id="1_evidence" name="Gather the run's real evidence">
Reason from what happened, never from the tidy story of it. Pull `git log`, the diff, reverted
commits and abandoned branches, commit messages, failed test runs, escalations, receipts and
verdicts, and the AgentDB learnings from the query above.

OUTPUT: a quotable evidence list. A claim that cannot be traced to a commit, a log line, a receipt
or a recorded decision is marked `inference`, not `finding`.
</phase>

<!-- ============================================================ -->
<!-- PHASE 2 - INTELLIGENCE. What did we learn without noticing?  -->
<!-- ============================================================ -->
<phase id="2_intelligence" name="Extract what you did not know you were learning">
Run the lens that BITES for this run, not all nine. Three are mandatory: surprise, belief-update,
anomaly. Answer in one or two lines with evidence, and emit the named artifact. A lens with no
artifact is narration: drop it from the report rather than padding it.

<lens id="surprise" mandatory="true">
What surprised me? What should have surprised me and did not? Where was my prediction most wrong?
What looked hard but was easy, or easy but hard?
OUTPUT: `intelligence.surprises[]` entries, each `prediction -> reality -> evidence`. A surprise
that contradicts a stored belief also goes to the belief-update lens.
</lens>

<lens id="belief_update" mandatory="true">
What do I believe less now? What got stronger? Which assumption survived only because nobody
tested it? What would "me before this run" reject that I now think is true?
OUTPUT: one `beliefs.jsonl` write per answer (`op: create|modify|weaken|retire`) with confidence
and the contradicting or confirming evidence, plus `agentdb learn pattern "<belief>" "<evidence>"`
when it should fire during future work rather than only at the next retrospective.
</lens>

<lens id="anomaly" mandatory="true">
What result does not fit my explanation? What happened once that deserves investigation rather
than dismissal? What did the system do that nobody designed? Where did two supposedly equivalent
approaches diverge?
OUTPUT: an `anomalies.jsonl` entry with `preserve_until_condition`. Never an explanation you had
to reach for. See the anti-convergence rule.
</lens>

<lens id="hidden_knowledge">
What do I now know how to do that I could not easily explain? What did I repeatedly notice before
I had words for it? What knowledge lives only in commits, debugging and rejected attempts and
would vanish if everyone forgot it tomorrow?
OUTPUT: `agentdb learn gotcha|pattern "<what>" "<why>"`, so it fires at the moment of action.
</lens>

<lens id="counterfactual">
Restarting with what I know now, what would I delete? What would I do 10x earlier? Which
constraint was actually useful? What almost worked, and under what changed condition might it win?
OUTPUT: a `questions.jsonl` entry with `candidate_experiment`, or an `anomalies.jsonl` entry when
the near-miss is unexplained.
</lens>

<lens id="abstraction">
What general principle hides inside this specific problem, and where else does it appear? What did
I build manually that is secretly a reusable primitive? What must be true for the lesson to
generalize?
OUTPUT: a named `patterns.jsonl` entry with `instances[]`, plus `intelligence.primitives_named[]`.
Under-evidenced generalizations go to `questions.jsonl`, not `patterns.jsonl`.
</lens>

<lens id="novelty_mining">
What side discovery is more interesting than the thing we built? What problem did solving this
expose underneath it? What capability now makes a previously impossible idea cheap?
OUTPUT: a `questions.jsonl` entry naming the next experiment and what would make it worth running.
</lens>

<lens id="negative_space">
What never became a problem despite expecting it to? What received suspiciously little attention?
What important thing is absent from our metrics? What would an outsider find bizarre here?
OUTPUT: either a `questions.jsonl` entry or a phase-3 architecture proposal. Absence with no
artifact is not a finding.
</lens>

<lens id="trajectory" note="highest long-term value">
Compare the last 5 runs, not this one. What keeps recurring? Which mistakes are one mistake in
different clothes? Which discoveries keep reappearing independently? What am I repeatedly building
around because the missing primitive has no name yet?
OUTPUT: `intelligence.recurrences[]` plus a `patterns.jsonl` promotion when the same structure was
invented independently 3+ times, which is the strongest promotion evidence a pattern can have.
</lens>
</phase>

<!-- ============================================================ -->
<!-- PHASE 3 - ARCHITECTURE. Questions that can mutate the system. -->
<!-- ============================================================ -->
<phase id="3_architecture" name="What should change about how the system is built" domain="software|architecture|infra">
For architecture, infra or agent-runtime work, ask questions that can MUTATE the system. Draw the
ones that bite; each answer must reach a proposal or a `questions.jsonl` entry.

- **Autonomy boundary.** What human intervention should have been deterministic? What decision was
  escalated that should have been local, or local that should have been gated? Where did autonomy
  add risk without speed, or a safety constraint add friction without protection?
- **Information and state.** What did an agent need but lack at decision time? What was retrieved
  repeatedly and should be persistent context, or loaded repeatedly and almost never useful? What
  became the real source of truth despite the architecture naming another one?
- **Verification and failure.** Where did an agent guess instead of verify? Where did verification
  cost more than the task? What failure was detectable earlier, or only by another agent? What did
  "done" actually mean, and could it have been mechanically checked?
- **Coordination.** Where did two agents duplicate work, or parallelism reduce quality? What
  coordination happened conversationally that should be protocol? What protocol do agents route
  around, which is the signal the protocol is wrong?
- **Intelligence vs structure** (the deepest lens). What rule belongs in code, what in prompting,
  what in evaluation? What behavior are we solving with ever-longer prompts? Where is intelligence
  compensating for missing structure, or structure for something models now handle? What model call
  could become retrieval, grep, cache or deterministic code?
- **Memory.** What should expire and what should compound? What did one agent learn that the others
  needed? What propagates globally vs stays task-local?
- **Proactivity and observability.** What could have run before anyone asked, on what trigger? What
  observability would have shortened this most? What can telemetry not currently explain?
- **Complexity honesty.** Which component earned its complexity? Which exists for a problem we no
  longer have? If we deleted one layer tomorrow, which would we test first?

<synthesis>
Force the answers into AT MOST 3 proposals; fewer is better. Each: `evidence | root cause | change |
expected benefit | new failure modes | reversibility | cost | confidence | what future evidence
would prove this wrong`.

ANTI-OVERENGINEERING GATE, mandatory, applied before any proposal is recorded:

> Is this a recurring architectural signal, or one unusual instance? Find evidence across previous
> runs (ledgers, prior retrospectives, git history) BEFORE recommending permanent infrastructure.
> One occurrence is an anomaly to preserve, not an architecture to build.

A proposal with no cross-run evidence is demoted to a `questions.jsonl` entry with a
"watch for recurrence" note. It does not become a build. This gate is the counterweight to the
model's eagerness to generalize from one dramatic instance.

OUTPUT: `intelligence.architecture_proposals[]` and a `mutations[]` row per proposal with
`artifact_type: architecture` and `status: proposed`. Closes the loop `run -> evidence -> anomaly ->
root cause -> hypothesis -> cross-run evidence -> bounded mutation -> measure -> keep/revert`, with
the reverting evidence named in advance.
</synthesis>
</phase>

<!-- ============================================================ -->
<!-- PHASE 4 - LEDGERS. The memory this process actually updates.  -->
<!-- ============================================================ -->
<phase id="4_ledgers" name="Update the four evolving ledgers">
Four JSONL ledgers under `_meta/ledgers/`. Compare against them; never re-derive from zero.

- **`beliefs.jsonl`** - `{id, belief, confidence: 0..1, evidence[], first_seen, last_updated, status: active|weakened|retired, supersedes}`.
- **`patterns.jsonl`** - `{id, name, structure, instances[], confidence, status: watching|promoted|principle}`. 3+ independent instances is a promotion candidate (phase 5).
- **`anomalies.jsonl`** - `{id, observation, context, why_unexplained, seen_in[], preserve_until_condition}`. Never deleted to tidy up; retired only when an explanation is earned, and the explanation is recorded.
- **`questions.jsonl`** - `{id, question, why_interesting, got_more_interesting_when[], candidate_experiment}`. Where under-evidenced generalizations wait for their third data point.

Then the cross-run comparison, explicitly:

> What is genuinely NEW? What have we already learned before (recurrence, not discovery)? What
> CONTRADICTS previous learning? Which pattern now has enough evidence to promote? Which old
> principle should be WEAKENED or RETIRED?

A contradicted belief is weakened or retired WITH the contradicting evidence, never silently
overwritten. A lesson appearing for the Nth time is flagged as recurrence (a lesson learned twice
was not learned) and escalates toward an enforceable artifact rather than another note.

Periodically, not every run, ask the long-horizon question and record the answer as a belief:

> What architecture is the accumulated evidence trying to turn us into?

OUTPUT: the ledger writes themselves, each mirrored as a `mutations[]` row in the record.
</phase>

<!-- ============================================================ -->
<!-- PHASE 5 - HYGIENE + PROMOTION. The old machinery, kept.       -->
<!-- ============================================================ -->
<phase id="5_hygiene" name="Housekeeping and artifact promotion">
Demoted below intelligence, not removed. A promoted pattern that stays a sentence is honor-system;
an artifact fires on its own.

1. **Clusters, duplicates, contradictions** in AgentDB: group by theme, merge duplicates into the
   strongest form, resolve contradictions with evidence and archive the loser.

2. **Stale archival, with the protected-set subtraction (do not skip).** Flag only rows whose last
   recall, or `ts` when never recalled, is older than 30 days:
   `COALESCE(last_hit, ts) < datetime('now', '-30 days')`. `last_hit` alone is NOT sufficient to
   delete: an injection rule fires a learning without stamping it, and `agentdb learn`'s dedup path
   bumps `hit_count` and leaves `last_hit` null. Before archiving ANY row, subtract rows referenced
   by a `learning_id` in the project's injection rules, and rows with `hit_count >= 5`. Measured
   2026-08-27 in Vaults: the bare predicate named 22 rows, 11 protected, including the most-recalled
   row (`hit_count` 125). Archiving on the bare predicate is silent and irreversible. Reference:
   `_meta/services/agentdb-archive-guard.py`.

3. **Promote via the artifact ladder**, most enforceable form that fits, never defaulting to prose:
   - **Hook** for a safety property or mechanical check (I0.15). Put the check ON the path the work
     must take: a hook beside the path drifts, a hook on the chokepoint holds.
   - **Agent** for a recurring role with its own judgment.
   - **Skill** for a repeatable HOW.
   - **CLAUDE.md prose** last resort, only for context no mechanism can enforce.
   Scaffold means WRITE THE FILE this session. Promotion needs 2+ instances OR one quiet/expensive
   failure mode, and clears the same anti-overengineering gate as an architecture mutation.

4. **GitHub layer (non-local profiles only).** On `github`, `github-oss` and `github-production`,
   post the retrospective's verdict as a comment on the cycle's issue and the summary to the Agent
   Logs discussion, via `hooks/scripts/github-integration.sh`. AgentDB and the ledgers are the
   source of truth; GitHub is visibility. Never block on a GitHub API failure, and never auto-close
   an issue.

   <ask_user>
     Use AskUserQuestion when promotable patterns or prune candidates exist.
     Ask: "Found {N} promotable patterns and {M} architecture proposals. Scaffold / propose which?"
     Prune candidates (dormant skills/agents) always require explicit approval.
   </ask_user>
</phase>

<!-- ============================================================ -->
<!-- PHASE 6 - RECORD.                                             -->
<!-- ============================================================ -->
<phase id="6_record" name="Emit the mutation record">
Write `_meta/reports/retrospective-{date}.json` per schemas/kernel.retrospective-result.v1.schema.json:
- identity: {created: ISO 8601, session, scope} - REQUIRED, no top-level `date`.
- analyzed: learnings/clusters/merged/archived/contradictions_resolved counts.
- mutations[]: every artifact touched AND every ledger write -
  {op: create|modify|remove|promote|weaken|retire, artifact_type: hook|agent|skill|prose|learning|belief|pattern|anomaly|question|architecture, path, reason, evidence, reinforced, status: applied|scaffolded|proposed|rejected}.
- intelligence: {surprises[], belief_updates[], anomalies_preserved[], primitives_named[], recurrences[], architecture_proposals[]} - empty arrays allowed, missing keys are not.
- project_fit: missing[] and dormant[] as arrays of STRINGS.

```bash
"${CLAUDE_PLUGIN_ROOT:-.}/orchestration/manifest/kernel-manifest" validate _meta/reports/retrospective-{date}.json
agentdb write-end '{"did":"retrospective","new_beliefs":N,"weakened":N,"anomalies_preserved":N,"patterns_promoted":N,"architecture_proposals":N,"mutation_record":"_meta/reports/retrospective-{date}.json"}'
```
</phase>

<output_format>
## Retrospective, {date} - {what this run was}

### What is genuinely new
{discoveries, vs what turned out to be recurrence of a known lesson}

### Surprises
{prediction vs reality, with evidence}

### Belief updates
{believe less / believe more / retired, each with its evidence and ledger id}

### Preserved without understanding
{anomalies kept alive on purpose, and the condition under which to revisit}

### Reusable primitives named
{what was built manually that is secretly a primitive, with the name given to it}

### Trajectory
{what recurs across the last 5 runs; the mistake in different clothes; the unnamed primitive}

### Architecture proposals (<=3, or none)
{each: evidence | root cause | change | benefit | new failure modes | reversibility | cost | confidence | disproving evidence - all past the anti-overengineering gate}

### Ledger writes
- beliefs +{N} / weakened {N} / retired {N} · patterns +{N} / promoted {N}
- anomalies +{N} preserved · questions +{N}

### Hygiene
- Merged {N}, archived {N} (protected-set subtracted), contradictions resolved {N}
- Artifacts promoted: {pattern} -> {hook|agent|skill} at {path}

### Mutation record
- `_meta/reports/retrospective-{date}.json` (validated)
</output_format>

<seeds note="founding entries from the 2026-09-01 refusal-runtime session; the ledgers start here">
beliefs:
- "Autonomy comes from mechanical refusal on a chokepoint, not from better reasoning." conf 0.9 -
  234 systems: every one that ran unattended had a scorer outside the agent's authority.
- "A rule beside the path drifts; a rule on the path holds." conf 0.9 - two guards in a whole stack
  had ever refused anything; both sat on chokepoints. The gate beside the path denied 0 of 1,179.
- "Knowing a failure class does not prevent committing it; only a check does." conf 0.85 - an author
  shipped three self-authorization defects hours after writing three documents against them.
- "Frequency is not consent: never expand authority from a count of past behaviour." conf 0.9.
- "Storage is not retrieval: a lesson recorded and not fired at the moment of action is a cost."
  conf 0.8 - an agentdb learning was relearned as new 81 days after it was written.

patterns (watching -> promote on the 3rd independent instance):
- "theatre has three kinds: by design (vacuous assertion), by wiring (real check never installed),
  by starvation (installed check, no data)." 3 instances (TBS, tooling, lane-ledger).
- "the human-at-the-wheel corpus is an oracle: (situation, response, verdict) answers both what to
  do next and whether output is good." 1 strong instance; watch for reuse.
- "seed the real defect into the instrument in an isolated copy before trusting it." recurring
  (test-capability.sh, instrument-breaker, instruction-surface-check).

anomalies (preserved, not explained):
- "catcher ratio held near 1-in-3 mechanical across four independent defect censuses AND on the
  session author's own 8 mistakes. Why that ratio? Unknown. Preserve until a fifth census."

questions:
- "what architecture is the accumulated evidence trying to turn us into?" - revisit at 5+ runs.
- "objective generation is unbuilt in all 234 systems and in ours. Genuinely hard, or just gated on
  a grader nobody had? Watch whether the corpus-grader makes it cheap."
</seeds>

</skill>
