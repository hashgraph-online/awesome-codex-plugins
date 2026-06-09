# Convergence Criteria

## Purpose

Decide when the audit-fix-rescan cycle (`references/audit-fix-rescan-cycle.md`) is finished. Without explicit criteria, agents either stop at the first quiet pass (premature) or keep re-reading forever.

A pass *converges* when each criterion below holds. The cycle is *complete* when two consecutive passes both converge.

## Stop Criteria

All true on the same pass:

- [ ] No new HIGH or MEDIUM findings appear.
- [ ] All previously-deferred findings are resolved or filed as separate issues with a reason.
- [ ] Test suite is green on the post-fix tree.
- [ ] Static scanners are clean or only flag entries with recorded justifications.
- [ ] No regression filed during pass 3 of the most recent iteration is still open.

## Finding-Decay Signal

Track findings per pass. A healthy cycle decays monotonically:

```
pass 1: 12
pass 2:  4
pass 3:  1
pass 4:  0
```

Warning shapes:

- Flat curve (`12 → 11 → 10`): you are skimming. Slow down or narrow scope.
- Re-emergence (`12 → 4 → 9`): a fix introduced a new defect class. Roll back or scope-isolate it.
- Late spike on verify (`8 → 3 → 1 → 6`): pass 4 found something earlier passes missed. Promote whatever tool caught it into pass 1 of the next cycle.

## Signal-to-Noise Ratio

```
signal_ratio = real_bugs_fixed / (real_bugs_fixed + suppressed_false_positives)
```

- `signal_ratio > 0.6` on pass 1 → scanner is well-calibrated for this scope.
- `signal_ratio < 0.3` on pass 1 → mostly noise. Tighten scanner config or change scope first.
- `signal_ratio` on pass 2 should be ≥ pass 1. If it drops, you are pattern-matching instead of reading.

## Pre-Release Gate

Add to the stop criteria:

- [ ] Two consecutive passes meet the stop criteria.
- [ ] No HIGH severity findings remain unfixed.
- [ ] Scanner exit code is 0 in strict mode.
- [ ] Diff against merge base has been read end-to-end at least once.
- [ ] Bug-finding pyramid checks (BF4 chaos/negative, BF5 script functional, BF1 property — see `skills-codex/bug-hunt/SKILL.md`) are run or recorded as out-of-scope.

For non-release use, the stop criteria alone are enough.

## When Not to Converge

Stop the cycle and escalate if:

- The same defect class re-emerges across passes despite fixes (architectural, not local).
- Three countable failures accumulate on the same root cause (`references/failure-categories.md`).
- Test infrastructure is unreliable enough that pass 3 cannot give a clean signal — fix the test infrastructure first.

File the escalation in the audit report and stop. Convergence under unreliable signal is worse than an honest "did not converge".

---

> Pattern adopted from `multi-pass-bug-hunting` (ACFS skill corpus). Methodology only — no verbatim text.
