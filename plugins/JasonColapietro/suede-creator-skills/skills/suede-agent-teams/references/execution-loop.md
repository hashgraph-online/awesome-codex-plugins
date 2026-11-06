# Model Tiering


Assign the least capable model that can still do the role correctly. Cost and latency compound across a roster; do not default every lane to the most capable model.

- **Mechanical tasks** (isolated function, single file, a complete spec with no judgment call): cheapest capable model.
- **Integration and judgment tasks** (multi-file coordination, pattern-matching against the existing codebase, non-trivial debugging): standard model.
- **Architecture, design, and review roles** (RFC authoring, code grading, security-sensitive review, release verification): most capable model available.

When a lane's task complexity is ambiguous, default up a tier rather than down; a cheap model returning `NEEDS_CONTEXT` or a wrong answer costs more in re-dispatch than starting at the right tier.

## Builder Dispatch Protocol

A dispatched builder reports one of four states before its output reaches review. Handle each before the lane proceeds to the next roster stage:

- **Done**: proceed to the next stage in the roster.
- **Done with concerns**: the builder finished but flagged a doubt. Read the concern. If it touches correctness or scope, resolve it before review; if it is a pure observation, note it in the handoff and proceed.
- **Needs context**: the builder is missing information the lane map should have supplied. Provide it and re-dispatch the same builder; do not silently guess on its behalf.
- **Blocked**: the builder cannot proceed. Diagnose why before re-dispatching: a context gap gets more context, a reasoning gap gets a more capable model, an oversized task gets split into smaller lanes, and a wrong plan escalates to the human (see Escalation Protocol). Never re-dispatch the same builder unchanged and hope for a different result.

A builder that asks a clarifying question mid-task gets an answer before it continues; do not let it guess past an open question to hit a deadline.

## Continuous Team Loop

Use the smallest loop that can finish the work, but escalate deliberately when
the task is broad, risky, release-bound, or the user asks for max agent teams.

Choose the loop:

- **Sequential:** default for normal scoped work.
- **Continuous PR:** use when strict CI, PR review, branch hygiene, or public
  release control matters.
- **RFC/DAG:** use when the work needs decomposition, design decisions, or dependency ordering before implementation. Run **RFC Mode** first to capture problem statement, proposed solution, alternatives, risks, and decision record before spawning builders.
- **Exploratory parallel:** use when several independent approaches, audits, or
  surface checks can run without touching the same files.
- **Recovery:** use after a failed check, repeated defect, blocked release,
  drifted claim, or loop churn.

For max-agent work, escalate through this roster only as needed:

```text
Scout -> Planner -> Builder lane(s) -> Design reviewer -> Visibility grader
-> Code grader -> Code reviewer -> Release verifier -> Handoff writer
```

Wrap the roster with these gates:

1. **Loop selection:** name why the loop is sequential, continuous PR, RFC/DAG,
   exploratory parallel, or recovery.
2. **Team contract:** objective, target, constraints, lane map, dependency
   order, done signal, and ship gate.
3. **Planning quality gate:** atomic tasks, observable acceptance criteria,
   named files/surfaces, must-have requirements, release/account boundaries.
4. **WIP ownership gate:** each builder owns explicit files or surfaces; any
   collision is sequenced.
5. **Execute wave:** parallel lanes only when outputs do not collide.
6. **Quality/eval gate:** run the relevant source, copy, design, code,
   visibility, build, screenshot, API, or live checks. A failing check earns
   up to three genuinely different fixes: each attempt must change the
   diagnosis or the strategy. Stop early when the same root cause repeats and
   escalate the repeating cause to the user.
7. **Adversarial review:** ask how the result fails in production, release,
   published statements, abuse, accessibility, mobile, or handoff.
8. **Consensus review:** merge multiple review lenses into blockers, accepted
   caveats, fixes now, and follow-ups.
9. **Release lock:** build/deploy/live/API/App Store/iOS/published-statement accuracy is
   owned by release verifier before any public completion claim.
10. **Evidence handoff:** capture changed files, commands, screenshots or URLs,
    verification, caveats, blockers, status, and next action.

Loop stall protocol: (1) freeze all lanes except the one that failed, (2) assign a diagnosis-only lane (no fixes, root cause only), (3) write a gap plan with a single acceptance criterion, (4) execute only the gap, (5) re-run the original failing check. Do not widen until that check passes.
