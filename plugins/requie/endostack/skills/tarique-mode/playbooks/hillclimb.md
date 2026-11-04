# Hillclimb

You are responsible for a single metric and for keeping the experiment honest. Subagents make the attempts while you set direction, review their diffs, and make the keep-or-revert calls. If the job is one defect or one slow path rather than a sustained climb, use [bug-fix.md](bug-fix.md) or [perf-issue.md](perf-issue.md).

Every attempt changes exactly one thing, gets measured, and is then either kept or undone. Two untested changes are never piled together, because a combined result cannot tell you which change helped. A win claimed from reading the code does not count (`principle-prove-it-works`).

1. **Understand the target and its workload.**
   - Run the `how` skill on the code you are going to optimize.
   - List the properties of the workload that could change the result, such as data volume, length of history, starting state, and concurrency. Choose a case in which the user's complaint actually shows up. If you cannot reproduce the complaint with any case, get a reproduction working before you try to improve anything.
   - Settle on one metric and on whether higher or lower is the goal.
   - Define a stopping condition that a command can evaluate. It needs both a target and a minimum attempt count, so that a single fortunate early result cannot end the climb. A typical form is "beats baseline by N% or more, after M or more attempts". Take N and M from the user if they gave them, and agree on them with the user if not.
2. **Build a harness, show that it detects the problem, and freeze it** (`principle-build-the-lever`).
   - Run several realistic workloads that differ from each other. The symptom must appear in the target case, and the easier cases must come out measurably different from it in the expected direction. If they do not, change the workload or the metric until they do.
   - Run the `benchmark-checklist` skill over the harness, and freeze it only after it passes. The harness must report how many errors occurred and how much work it did, so that a run which did nothing is obvious instead of looking fast.
   - After freezing, a single repeatable command prints the metric. It takes enough samples to rise above noise, reporting a median over several runs and never one run.
   - Before making any change, record the baseline and one passing run of the regression gate, meaning the tests that must keep passing throughout.
3. **Start a decision log** using the `show-me-your-work` skill. Use a tab-separated file with one row per attempt and these columns: id, hypothesis, change, before, after, delta, test result, verdict (kept or reverted), note. Do not commit it. Read it again before starting each attempt.
4. **Base every hypothesis on a mechanism** drawn from what you learned in step 1. "Parse config later, since it currently blocks first paint" is a usable hypothesis; "add some caching" is not. When the metric is about performance, rank hypotheses with the ladder in step 2 of [perf-issue.md](perf-issue.md). Use its ranking only, and keep your own stopping condition.
5. **Test a single hypothesis in each iteration.**
   - A subagent makes the change, running on the `hillclimb` model role (`fast` by default, adjusted under the policy in [../SKILL.md](../SKILL.md)) with a narrow scope. Review the diff it produces; do not write the change yourself (`principle-guard-the-context-window`). When several hypotheses are independent of each other, spawn them in parallel, giving each its own worktree (`principle-separate-before-serializing-shared-state`).
   - Use the frozen harness to measure the metric before and after, and run the regression gate.
   - The change stays only if the metric improves by more than the noise and the gate still passes. In every other case, undo it completely. A change that "might help" is undone too.
   - Commit each change you keep separately, adding the changed files by name. Do not add everything at once, since a stray file can slip an unrelated edit or a secret into history.
   - Add the attempt to the log whether you kept it or not.
   - Finish each iteration with a check before starting the next one (`principle-sequence-verifiable-units`). For runs nobody is watching, take the wake-up mechanism from [autonomous-run.md](autonomous-run.md) and ignore that playbook's stopping rule.
   - If a speedup works by removing a validation, an authorization check, or a bounds check, it is a regression no matter how good the number looks. Undo it.
6. **Do not give up at the first plateau.** When progress stalls or several attempts in a row are rejected, try a different category of change, combine attempts that nearly worked, read the source again, or try a bolder idea before you conclude anything. The number ranks below correctness and simplicity: when a gain changes what the code does, undo it, and when a simplification costs nothing on the metric, retain it (`principle-laziness-protocol`).
7. **End the climb** once the stopping condition is met, or once every idea left would cost more than it could gain. Do not relax the stopping condition so that you meet it. Do not stop while there are still untested hypotheses that would be cheap to try. If you are out of ideas, tell the user that plainly.
8. **Wrap up** using [opening-a-pr.md](opening-a-pr.md), with the kept commits in the order you made them.

## Reply

State the metric and the target. Give the baseline value, the final value, and the percentage change between them. Give the number of iterations and how many were kept and how many reverted. Add a line for each kept change, the path to the decision log, and the idea you would try next.
