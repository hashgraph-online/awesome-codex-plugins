---
name: debug
description: Use for bugs, unexpected behavior, regressions, or failing tests you did not write.
---
# Debug

If `topology=multi-module` (triage announcement or coordinator spec/plan declaration), read `../references/multi-module.md`. Investigate read-only across repos; fix inside the task's registered module only; defer commits until integration passes.

1. **Reproduce.** Minimal deterministic repro. No repro → no fix.
2. **Root-cause.** Ask "why" until one cause explains *all* symptoms. Symptoms != cause.
3. **Regression test first** (red), then fix at the root (green). Use `tdd`.

## Don't
- Guess. Read the code and the full error.
- Change two things at once.
- Stop at the first plausible cause.

3 failed hypotheses → re-read from scratch. Done = repro + regression test + root cause named + green.