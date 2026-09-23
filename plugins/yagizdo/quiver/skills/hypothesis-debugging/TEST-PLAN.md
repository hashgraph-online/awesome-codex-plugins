# Test Plan -- /hypothesis-debugging

**Trigger:** `/hypothesis-debugging <description>` (and `/quiver:hypothesis-debugging`)

**Setup:**
- Any git repository with source code.
- A bug to investigate (real or simulated).

**Expected behavior:**
1. Skill gathers git context and parses user's bug description.
2. When a screenshot is attached, the skill describes the anomaly geometry in measurable terms before any hypothesis.
3. Skill generates 2-4 hypotheses based on symptoms and codebase scan, each carrying a Refutation entry that names what would be observed if it were wrong.
4. Skill tests hypotheses, dispatching agents conditionally (only when their specialization adds value).
5. A hypothesis is confirmed only by a local observation no rival hypothesis explains, with its Refutation entry checked first -- never by an upstream issue or doc match alone. The confirmation is quoted as a `confirmed by:` line.
6. If hypotheses fail, skill enters adaptive exploration (max 2 rounds) with targeted user questions via AskUserQuestion.
7. On confirmed root cause, skill generates fix proposals (simplest first) and dispatches fix-reviewer.
8. When the user questions the diagnosis, the skill re-audits it against local evidence (Step 5c) before discussing alternative fixes; a contradiction refutes the root cause and re-enters hypothesis testing.
9. After fix review, skill presents approved proposals to user via AskUserQuestion.
10. On user selection, skill writes a reproducing test and prints its `red:` line, applies the fix, runs the resolved test command and reports its evidence line -- or names the reason once when no command resolves.
11. If the run after the fix fails, skill reverses the code change, records the root cause as refuted, and re-enters Step 2 once; a second failure ends the run with the ruled-out list and, when the refutations point at one, a named design assumption with its evidence.

**Verification checklist:**
- [ ] Slash menu shows `/hypothesis-debugging`.
- [ ] Simple single-file bugs resolve without any agent dispatch.
- [ ] Complex multi-file bugs trigger code-tracer dispatch.
- [ ] Log/stack trace input triggers log-analyzer dispatch.
- [ ] Regression scenarios trigger regression-finder dispatch.
- [ ] Environment/config bugs trigger environment-checker dispatch.
- [ ] Every fix proposal passes through fix-reviewer before user sees it.
- [ ] No fix applied without user confirmation via AskUserQuestion.
- [ ] After a fix, the skill prints an evidence line with an exit code, or a none reason -- never a bare "run the tests".
- [ ] Before the fix is applied, a `red:` line names the reproducing test; after it, a pass line follows -- or one `skipped:` reason covers both when no command resolves.
- [ ] Adaptive exploration bounded to 2 rounds.
- [ ] Every hypothesis carries a Refutation entry; none reads "nothing in particular".
- [ ] Every tested hypothesis has a `refuted:` or `survived:` line quoting the check and what it showed; the root cause in Step 5a carries a `confirmed by:` line.
- [ ] A screenshot in the input yields a geometry description (edges, symmetry, size ratio) in the Step 1 summary, before the hypotheses.
- [ ] The recent-changes scan is file-scoped (`git log -n 20 -- <files>`), and a commit whose subject names the affected component is listed in the summary by hash.
- [ ] No root cause is declared confirmed on an upstream issue or doc match; the issue's precondition is shown present in the codebase first.
- [ ] Research (web, context7, issue trackers) happens after the Step 1 summary and names the hypothesis it tests.
- [ ] "Are you sure" or "is there nothing better" triggers a re-audit of the diagnosis (Step 5c) before any alternative fix is proposed.
- [ ] A failed post-fix run never gets a second patch on top of the first; the first change is reversed and the root cause is re-examined, at most once.
- [ ] The stop report names a design assumption only together with the evidence that undercuts it, never as a bare label.
- [ ] All user decision points use AskUserQuestion, not plain text.

**Known gotchas:**
- Agent dispatch decision tree runs once per hypothesis, not once globally. A single debugging session may dispatch different agents for different hypotheses.
- The fix-reviewer is dispatched in Step 6 (after proposals are ready), not in Step 3 (during hypothesis testing). Do not confuse the two dispatch points.
- Navigation detection (CodeGraph and LSP) runs once in Step 0.7 and is cached for the session; agents dispatched in Step 3c receive the cached flags.
- Step 5c is entered by user pushback, not by a refuted hypothesis; a refutation found there flows back through 3d like any other, so the Step 4 two-round bound still applies.
