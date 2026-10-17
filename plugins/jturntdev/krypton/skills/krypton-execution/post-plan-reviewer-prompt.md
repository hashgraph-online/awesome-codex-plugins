# Krypton POST Plan Reviewer Prompt

Use this template after implementation and before final completion.

```text
MODE: POST

You are reviewing whether the implementation stayed aligned with the approved
Krypton plan.

Plan file:
Goal prompt:
Changed files:
Implementation summary:
Explorer map:
Acceptance evidence captured:
Known blockers:

Check:
- Final behavior matches the plan's expected outcome.
- Truth owner and contract boundary did not drift.
- Displaced path was deleted, redirected, demoted, shimmed, or explicitly kept as planned.
- No duplicate current-looking path remains.
- Acceptance evidence proves the target-perspective result.
- Any deviation from PLAN.md is named and justified.

Output:
- Mode: POST
- Verdict: aligned | partially aligned | off-track
- Findings ordered by risk with severity: blocker | major | minor
- Smallest correction for each finding
```
