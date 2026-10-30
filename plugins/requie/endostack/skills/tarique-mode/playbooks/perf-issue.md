# Perf issue

Fix one measurable slowdown, with every change backed by before and after measurements that you plan, review, and check.

Use this for a single complaint: a sluggish interaction, command, render, or request. Sustained improvement of one metric goes to [Hillclimb](hillclimb.md). Explaining a live symptom goes to [Runtime forensics](runtime-forensics.md); explaining an existing capture goes to [Trace forensics](trace-forensics.md).

Inputs: the slow scenario, its surface (UI, CLI, service), and any target.

1. **Record a baseline trace** on the affected surface through its control skill. Validate it, and every later measurement, with the `benchmark-checklist` skill ([../../benchmark-checklist/SKILL.md](../../benchmark-checklist/SKILL.md)). Use synthetic or redacted data, since a trace of production data can capture secrets and personal records.
2. **Ground hypotheses** in how the code really runs with the `how` skill ([../../how/SKILL.md](../../how/SKILL.md)). Claim no ceiling you have not run. Climb this ladder from the cheapest rung and stop at the first that meets the target:
   1. Delete work nobody consumes.
   2. Cache work already done.
   3. Do less work.
   4. Defer it.
   5. Move it off the user's wait.
   6. Parallelize it.
   7. Make each unit cheaper.
3. **Let the trace drive the fix design.** When the fix spans more than one function, run the `architect` skill ([../../architect/SKILL.md](../../architect/SKILL.md)) before writing it. Spawn a subagent on the perf role from `~/.endostack/models.toml` (default `fast`, `strong` for the hardest), effort and speed per the router. Read its diff. For caching rungs, confirm the cache key includes user or tenant identity and the cache is bounded. Trace again, and confirm each attempt before the next ([principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md)).
4. **Compare traces by program,** for example JSON loaded into sqlite and diffed by query. An inconclusive result, or one from a different surface, fails and is reported as such.
5. **Put the figures in the PR description,** then follow [Opening a PR](opening-a-pr.md).

Done means the cheapest sufficient rung met the target on the real surface with a valid comparison.

**Reply** with the baseline, the post-fix figure, the difference, the rung used, and artifact paths.
