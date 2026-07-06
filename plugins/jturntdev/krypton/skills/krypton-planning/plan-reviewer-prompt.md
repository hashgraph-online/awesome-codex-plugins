# Krypton Plan Reviewer Prompt

Use this template when dispatching a reviewer before or after a Krypton plan.

```text
MODE: PRE

You are reviewing a Krypton implementation plan before execution.

Plan file:
Original request:
Outcome contract:
Architecture slice:
Acceptance evidence requirement:
Known non-goals:
Unsafe paths or layers:

Check whether the plan is ready to execute.

Required checks:
- Expected outcome is explicit, not just a code change.
- Target-perspective output names who verifies the result and what they see, receive, do, or inspect.
- Acceptance evidence is stronger than tests, diffs, or "I built it".
- Architecture slice names source of truth, read/write path, contract boundary, owner files, unsafe files, displaced path, cutover, and evidence gate.
- Tasks are small, complete, and actionable.
- Parallel tasks have disjoint write scopes and an integration proof step.
- The plan avoids wrong owners, duplicate truth paths, missing displaced-path handling, missing cutover, and weak evidence gates.

Output:
- Mode: PRE
- Verdict: aligned | partially aligned | off-track
- Findings ordered by risk with severity: blocker | major | minor
- Smallest correction for each finding
- Recommended next gate
```
