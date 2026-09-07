---
name: debug
description: "Scientific debugging: reproduce, hypothesize, predict, isolate, fix root cause; every fix gets a regression test. Triggers: bug, error, fix, broken, not working, fails, crashed, unexpected, stack trace, regression, exception."
allowed-tools: Read, Bash, Grep, Glob
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="debug">

<purpose>
Debugging is forming and testing a THEORY that explains the bug.
Not random changes. Not guessing. Scientific method applied to code.
DEFECT (in code) → INFECTION (in state) → FAILURE (visible symptom).
The failure you see is NOT where the bug is. Binary search upstream.
Systematic methodology beats ad-hoc guessing. The process is the multiplier.
</purpose>

<prerequisite>Run `agentdb recall` with the exact error text, subsystem/library, failing
test, and known files/symbols. Recall again when the hypothesis changes or a new failure
appears; that is a new retrieval question. Reference on demand:
skills/debug/reference/debug-research.md.</prerequisite>

<steps>
1. **REPRODUCE**: get specific before touching code.
   - Document: exact input, expected output, actual output (full stack trace), environment, frequency.
   - "Sometimes fails" is not a reproduction. Get deterministic.
   - (gate: can reproduce consistently, OR have added targeted logging to wait for next occurrence)

2. **HYPOTHESIZE**: list 3 causes before pursuing any.
   - Read ALL error output first (anchoring bias mitigation).
   - Write each hypothesis to AgentDB. Prevents circular re-investigation.
   - (gate: 3 candidate hypotheses written; none pursued yet)

3. **ISOLATE**: binary search, O(log n) not O(n).
   - **Code**: call chain A→B→C→D→E fails → check midpoint C → recurse into failing half.
   - **Time**: `git bisect` between known-good and known-bad commit. ~10 tests for 1000 commits.
   - **Input**: large failing input → split in half → recurse to minimal reproduction case.
   - Instrument at boundaries: log inputs/outputs at each layer boundary.
   - Mock external dependencies to isolate which one causes failure.
   - (gate: failure localized to a specific function/commit/input subset)

4. **ROOT CAUSE**: the error line is the FAILURE. The DEFECT is upstream.
   - Ask: what assumption was violated? What invariant broke?
   - If you can't explain WHY it broke, you haven't found root cause.
   - Top causes by frequency: wrong input shape/type · off-by-one · missing null check · race condition · shared-state mutation · wrong comparison operator · variable scope · swallowed error · API contract mismatch · environment difference.
   - (gate: can state root cause in one sentence explaining the violated invariant)

5. **FIX**: root cause, not symptom.
   - Fix the DEFECT, not the FAILURE site. (Null check at crash site = symptom fix.)
   - Write regression test that fails before fix, passes after.
   - Run: original failing case + edge cases + full regression suite.
   - Commit fix + test together.
   - (gate: regression test green; original failing case passes)
</steps>

<anti_patterns>
Shotgun (random changes until it works) · fix-and-pray (never re-run the original case) ·
symptom fixing (null check at the crash site) · printf flooding (binary search first, then
targeted logging) · blame-the-framework (it's almost never the library) · unscoped
"investigate" (scope narrowly or use a subagent so the file reads don't fill context).
</anti_patterns>

<when_stuck>
Explain the problem in writing · re-read the error message (the answer is there most of
the time) · reduce to a minimal reproduction · ask "what changed?" (git log/diff, deps,
env) · search the exact error message in quotes · step away, bias accumulates. Re-run the
EXACT original failing case before declaring victory; "seems to work" is not evidence.
</when_stuck>

<escalation>
30+ min on one hypothesis with no evidence → abandon it. 3+ hypotheses rejected → step
back, re-examine assumptions. 2 failed fix attempts → invoke tearitapart; it may be a
design problem. Repeated failed corrections in one session → /clear with a minimal
reproduction. Bug only in production → add targeted monitoring, document, move on.
For 3+ plausible causes, spawn one fresh-context agent per hypothesis (evidence_for /
evidence_against / confidence); fresh context catches what a long session anchors past.
</escalation>

<on_complete>
agentdb write-end '{"skill":"debug","bug":"<description>","root_cause":"<what_broke>","fix":"<what_fixed>","test":"<regression_test_name>","learned":"<pattern_for_future>"}'
</on_complete>

</skill>
