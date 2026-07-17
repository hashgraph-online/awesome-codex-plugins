---
name: research
description: Answer a bounded question with current cited
---
# Research

Answer one bounded question with current evidence. Research informs a caller;
it does not select work, approve a plan, mutate lifecycle state, or decide what
happens next.

## Contract

1. State the question, decision it informs, scope, non-goals, and evidence
   required for a useful answer.
2. Search the smallest relevant local sources. For changing external facts,
   use current primary sources.
3. Verify structural or semantic-search leads against authoritative content.
4. Separate observation, inference, contradiction, and unknown.
5. Lead with the answer and cite every load-bearing claim.
6. Report unchecked scope and stop.

Use the current agent inline by default. Parallel readers or alternate runtimes
are optional execution choices only when the caller authorizes them. Prior
research, CASS, MS, codebase recon, and pattern mining are advisory sources,
not required phases.

## Commit-level citation for code claims

A claim about what code does cites the commit it was observed at, plus
file:line — code moves, and a citation without a revision decays silently into
a claim about a repository that no longer exists. For the working tree, record
the current HEAD and whether the cited file carries uncommitted changes. The
named failure mode is the floating citation: a path and line that resolved
when written, drifted after a refactor, and now lends false authority to a
stale answer. A reader must be able to run `git show <commit>:<path>` and see
the cited lines; a code claim that cannot survive that replay is reported as
unverified, not asserted.

## Done means observable capability

Research is done when its capability flags are answerable, not when effort
feels sufficient. At the start, derive from the bounded question a short list
of capability statements — "can name the module that owns X, with citation",
"can state whether Y is reachable from Z, or that this is unknown". The stop
condition: every flag is either satisfied with evidence or explicitly reported
unknown with what was searched. Hours spent and files read are not flags. The
named failure mode is effort-shaped doneness — stopping because the search was
long, and shipping an answer whose load-bearing claim was never actually
established. If a flag stays unsatisfiable inside scope, say so and stop;
widening the question mid-search is a new question, and the caller owns it.

### Multiple caller-supplied reports

When the caller supplies several reports for one bounded question, synthesize
them as evidence inside this same Research invocation:

1. Build a source ledger before comparing claims. Preserve each report's path or
   supplied identifier, title, author/runtime when known, and revision or date
   when supplied. Assign a short local label without replacing that identity.
2. Extract each load-bearing claim with its source label and original evidence
   reference. Normalize wording only for comparison; never merge citations or
   make agreement erase provenance.
3. Group comparable claims into **agreement**, **contradiction**, and **unknown**.
   Agreement means independent reports support the same claim. Contradiction
   preserves the conflicting claims and evidence. Unknown means the reports do
   not establish the fact or the underlying source was not checked. Reports that
   repeat one upstream source are agreement in wording, not independent
   corroboration; preserve that shared provenance.
4. Verify load-bearing claims against authoritative content when the bounded
   question requires it. A report's conclusion is advisory, not authority.
5. Produce one cited synthesis that states what the reports jointly support,
   where they disagree, and what remains unknown. Report checked and unchecked
   sources, then stop.

Do not recursively launch another Research pass, invent a synthesis umbrella,
or start a new runtime merely because multiple reports exist. Additional readers
remain caller-authorized execution choices, not part of this procedure.

## Output

For a quick question, return the cited answer directly. When the caller asks
for a durable artifact, write one report containing:

- question and scope;
- answer;
- evidence references;
- contradictions and unknowns;
- checked and unchecked areas.

For a durable synthesis of multiple reports, also include `source_ledger` and
`comparison` (`agreements`, `contradictions`, and `unknowns`) as defined by the
output schema. Single-report outputs may omit those optional fields.

Do not emit approval, confidence gates, retry instructions, owner, next action,
or delivery state.
