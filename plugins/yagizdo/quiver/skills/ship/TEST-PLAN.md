# Test Plan -- /ship

**Trigger:** `/ship "<description>"` and `/quiver:ship "<description>"` in a project with no `.claude/ship/roadmap.md` (Init: questions, phase split, save); bare `/ship` in a project with a roadmap (run or resume the next phase); `/ship <phase-id>` (run, resume, or unblock that phase); `/ship --verify` (re-run the build, test, and smoke checks of the current phase); `--seed <spec.md>` (read by Init only)

**Setup (Init):** (a) A directory made with `git init` and nothing else -- no commit, no file. Pass a description as $ARGUMENTS. (b) The same, plus a committed file under `.claude/ship/` (e.g. `.claude/ship/keep.md`). (c) A directory that is not a git repository. (d) A repository with no description, no `--seed`, and no source files.

**Setup (one phase):** Run Init in setup (a) with a description small enough for one phase and nothing to look up: "a Python module `add.py` with one function `add(a: int, b: int) -> int` that returns a + b, and `test_add.py` with three unittest cases (2+3=5, -1+1=0, 0+0=0). Standard library only, no CLI, no file or network I/O, runs on whatever python3 is installed. Local use only, nothing published. Starting fresh, no prior decisions. Tests: python3 -m unittest. No run command." Before approving, add a local remote so a push would show: `git init --bare ../remote.git` and `git remote add origin ../remote.git`; `git ls-remote origin` prints nothing. Approve the one-phase split; the phase starts in the same turn.

**Setup (research):** Init plus one phase run on a description with an open technical choice, e.g. "a Node 22 CLI that saves a full-page screenshot of a URL; pick the browser library for me", once in a directory holding only `.git/` and a README, once in a directory that holds source files.

**Setup (fresh session):** (a) A description that splits into one phase of at least 8 tasks, e.g. a Python CLI with eight subcommands named in the description, each its own module and tests. (b) The one-phase setup above, in a new session (under 30% of the window, under 8 tasks).

**Setup (lost continuation):** From a phase whose build finished: edit its file back to `stage: build` while the plan in `plan:` reads `status: completed` -- the state a turn leaves when it ends on `/work`'s summary. Separately: a phase with `stage: review` and a `review-*.md` in `.claude/reports/` whose `- **Branch**:` is the current branch and whose `- **HEAD at review**:` is `git rev-parse --short HEAD`.

**Setup (review and fix):** Build the review fixture with `bash tests/eval/review-golden/build-fixture.sh <dir>` (branches `main` and `feature`, three planted defects, five baits; on `feature` when it finishes). By hand, in the formats `skills/ship/SKILL.md` `# State Files` defines, write a roadmap with one phase `in-progress`, its phase file with `stage: review`, `branch: feature`, `fix_rounds: 0`, and `plan:` pointing at a one-task plan in `.claude/plans/` whose frontmatter carries `status: completed`, `test_command: python3 -m pytest`, `build_command: none (no build step)`, and `run_command: none`. Run bare `/ship`. Variants, each from the first review's report: (Critical) change one confirmed finding's tier to Critical in the saved report, set `stage: fix` and `review_report:` to that report, run `/ship`; (cap) set `stage: fix` and `fix_rounds: 1` with a report that still carries a confirmed finding, run `/ship`.

**Expected behavior:**

*Gather and routing*
1. The five gather blocks exit 0 in a repository with commits, in one with no commit (the `git log` block prints `NO_COMMITS`), and in a non-git directory, where Step 0 prints the no-repository line and continues.
2. `--resume` or `--execute` prints the one line saying the flag is not needed, then routes as usual.
3. `/ship <token>` naming no phase prints the `No phase "<token>"` line with the phase list and terminates; `/ship <id>` on a `done` phase prints `> Phase <id> is already finished.` with the last line of its final report.
4. With every phase `done`, ship prints one line per phase and names `/quiver:create-pr` when the branch has no pull request. With only phases waiting on a `blocked` one, it prints the stopped line for each blocked phase and terminates.

*Init*
5. In Init setup (a), ship prints a 1-2 sentence summary, dispatches no `quiver:code-navigator` (the root holds nothing), and asks the project questions in one `AskUserQuestion` call, leaving out any the description answers. A partial answer is asked once more.
6. It shows the phase table (ID, Phase, Goal, Done when, Depends on) with 2-5 checkable done criteria per phase and an out-of-scope line, then one approval question. "Change something" redraws the table and asks again; "Start over" returns to the project questions.
7. On approval it writes `.claude/ship/roadmap.md` (headings `## Goal`, `## Phases`, `## Now`, `## Next`; every row `pending`), `.claude/ship/decisions.md` (`D<n>.` entries with `(user, <date>, phase init)`, the resolved `test_command`, `build_command`, and `run_command` among them), and one `.claude/ship/phases/<id>-<slug>.md` per phase with `status: pending` and `stage: questions`. Each file is read back. It prints `> Saved <N> phases under .claude/ship/. Starting phase <id> -- <name>.` and starts that phase in the same turn, with no second `/ship`: no `No phase` line for the description, and the phase's questions come next.
8. Before the first write, `.claude/ship/` is appended to `.git/info/exclude` once: `git check-ignore .claude/ship/roadmap.md` reports it ignored and `git status --short` lists nothing under `.claude/ship/`. In setup (b) no entry is added. In setup (c) the files are written and no `.git` is created.
9. Setup (d) prints `> Tell me what to build: /ship "<...>"` and terminates.

*One phase, end to end*
10. Bare `/ship` sets the phase `in-progress` in its file and in the roadmap row and sets `## Now`, then runs every stage in one turn up to the final report.
11. The phase asks at most two question rounds: the phase questions (none when nothing qualifies, and then nothing is printed) and at most one batch after research. No third batch. Technical details the user would not weigh are recorded under `## Decisions` as `(agent, <date>)`, not asked. In the one-phase setup, research prints `> Nothing to look up -- every technical choice is already set.` and dispatches nothing.
12. The spec lands at `.claude/specs/<date>-<project>-<phase-id>-<slug>.md` with `- **Status:** Approved in advance by the phase questions (<date>)`; the plan lands at `.claude/plans/<date>-<project>-<phase-id>-plan.md` with `spec_source:`, the three command fields, a `## Global Constraints` section carrying the out-of-scope line as "Do not build ..." entries, and `**Provides:**` lines only on tasks another task names by symbol. Neither write asks for approval. When the plan path exists, the `-2` name is used and the first plan and its ledger are untouched.
13. The plan reviewer is dispatched once; no question from `skills/plan/SKILL.md` Step 7 is asked.
14. The build stage invokes `work` through the Skill tool with `<plan path> --auto`. Ship creates no branch and dispatches no implementing agent. The moment `/work`'s Phase 5d summary prints, in the same turn, ship records `branch:`, writes `stage: verify`, prints `> The code is written. Checking that it builds, passes its tests, and starts.`, and runs the checks.
15. The verify stage prints one evidence line each for build and tests (or a skipped reason) and `Smoke: skipped -- no run command` when `run_command` is `none`; a zero-test run is `skipped`, never `pass`. The three lines are written under `## Measurements`.
16. Every status line and every question in the run is plain language: none names a stage (`questions-2`, `split`, `fix`), a verdict token, or a rule code.
17. Nothing leaves the machine: `git ls-remote origin` shows the same refs as before the run, and the final report says nothing was pushed and no pull request was opened.

*Research*
18. In the research setup, research runs after the phase questions and prints one `> Looked up <N> questions -- ...` line whose counts add up to N. An `answered` question is not asked and lands under `## Decisions` with its evidence line; a `narrowed` one is asked in the follow-up batch with the recommended option first; a `needs-measurement` one becomes a "measure <what> on the target first" step in the plan task that needs it.
19. In a root with nothing but `.git/`, `.claude/`, and Markdown files, `quiver:code-navigator` is not dispatched; `quiver:stack-researcher` still is.

*Fresh session*
20. Every run writes one `- <date> context: ... | tasks: <N> | choice: <here|fresh|not asked>` line under `## Measurements`; when the transcript cannot be read it reads `context: unknown (<reason>)` and ship prints the task-count-only line.
21. Setup (a) shows the fresh-session question with both options naming the current effort; setup (b) asks nothing and records `choice: not asked`.
22. "Stop and continue in a fresh session" writes `stage: build`, prints `> Saved. Next: /clear, then /ship.`, and terminates. After `/clear`, bare `/ship` prints `> Picking up phase <id> (<name>) where the last run stopped.` and starts the build with no question asked again.

*Lost continuation*
23. With `stage: build` and a plan reading `status: completed`, `/ship` adds a `## Log` line, records `branch:`, and starts at the checks; `/work` is not invoked again.
24. With `stage: review` and a report matching the branch and `HEAD`, `/ship` records the report in `review_report:` and starts the fix stage; no second review runs.

*Review and fix*
25. The review stage applies the keep-local rule to `.claude/reports/` and invokes `quiver:review` through the Skill tool with `--base <default branch> --run-checks --plan <plan path> --output .claude/reports`. After its Step 4b summary prints, in the same turn, ship records `review_report:`, writes `stage: fix`, and continues.
26. On the fixture, only findings carrying `Verification: confirmed` go into the fix plan at `.claude/plans/<date>-<project>-<phase-id>-fix-plan.md`, whose frontmatter carries `review_source: <report path>`, `review_iteration: 1`, and `status: active`, one task per finding naming its report ID and title. The README sentence and the `app/ledger.py` comment, when the review lists them as `refuted-by-verification`, are not in it, and `git diff` after the fix round shows no change to `README.md` or that comment.
27. `/work <fix plan> --auto` runs, and after its Phase 5d summary ship sets `fix_rounds: 1`, runs the build, test, and smoke checks again, records them under `## Measurements`, and reviews once more in the same turn; that review covers only the changes since the first report.
28. In the Critical variant, ship asks one question for the finding, options in the order "Fix it", "Leave it and list it", "Stop this phase here". "Stop this phase here" sets `status: blocked` in the phase file and the roadmap row, writes the final report, and terminates; `/ship 1` later resumes the phase at its recorded stage. A finding whose fix would change specced behavior gets "Leave it and list it" first.
29. In the cap variant, ship fixes nothing, writes `stage: done`, and the final report lists the confirmed finding as open. No third `/work` run and no third review happen in any setup.

*Done and re-entry*
30. The phase is `done` only when every check line from the last verify is a pass or a skip and no Critical finding is left unaddressed; otherwise `blocked` with the reason. The roadmap row, `## Now`, and `## Next` are updated, and decisions that apply beyond the phase are appended to `decisions.md` with `phase <id>`.
31. The final report is written under `## Final Report` and printed, covering the eight items the done stage lists, and names `/quiver:create-pr` for the pull request without running it. With a second phase ready, ship then prints `> Phase <id> is done. Starting phase <next id> -- <name>.` and that phase's questions follow in the same turn; a phase that ends `blocked` starts nothing and the run ends.
32. `/ship --verify` on a finished phase prints the three check lines, records them under `## Measurements`, and terminates with `stage` and `status` unchanged.
33. Without git, the review and fix stages are skipped; the final report says the branch was not reviewed and names `/quiver:review --base <default branch> --run-checks --plan <plan path>`.
34. A phase the done stage left `blocked` on a failing check carries `stage: verify`. After the test is fixed by hand, `/ship <phase-id>` re-runs the checks and continues to the review of the new changes; it does not stop again on the old check line. `/ship --verify` on that phase records the three lines and leaves it `blocked`.
35. With `stage: fix`, `fix_rounds: 0`, and `fix_plan:` naming a plan reading `status: active` (a fix round that stopped partway), `/ship` asks no question again, writes no `-2` fix plan, and invokes `/work <fix_plan> --auto` on the recorded plan.
36. A phase the done stage left `blocked` on a Critical from the review after the fix round carries `stage: verify`. With no code change since, `/ship <phase-id>` asks one question for that finding, options in the order "I fixed it", "Leave it and list it", "Keep it stopped", before it runs anything. "Keep it stopped" leaves `status: blocked` and terminates. "Leave it and list it" records the answer under `## Decisions`, and the final report lists the finding as open. A phase stopped through the fix stage's "Stop this phase here" (`stage: fix`) gets the fix stage's question instead, not this one.
37. After any fix round, the `## Log` carries one `fix: not fixed: <task numbers or none>` line. Then hand-set the phase file to `stage: fix`, `fix_rounds: 1`, `review_report:` naming a report with no Critical, `fix_plan:` naming a plan whose `review_source:` report lists a Critical that task 1 names, passing check lines, and the log line `fix: not fixed: 1`. `/ship <phase-id>` goes straight to the done stage and sets `status: blocked` with that Critical as the reason. With `fix: not fixed: none` it sets `done`; with no such line it sets `blocked`, and the next `/ship <phase-id>` asks the "I fixed it" question for that Critical. With `fix: not fixed: none` and a `review_report:` that lists the same Critical again (same ID and title, reported as a regression), it sets `blocked`: the fix-plan task closes only the first review's Critical.

**Verification checklist:**
- [ ] Gather blocks exit 0 in all three directory kinds.
- [ ] Init writes the three state files in the `# State Files` formats and reads each back.
- [ ] `.claude/ship/` is excluded once in a fresh repository and not excluded when it holds a tracked file.
- [ ] A one-phase run reaches the final report in one turn with at most two question rounds.
- [ ] The fresh-session question appears only when recommended, and `/clear` then `/ship` continues at the build.
- [ ] A turn that ended on `/work`'s or the review's summary is recovered from the plan's `status` or the report's `Branch` and `HEAD at review` lines.
- [ ] Review is invoked as `quiver:review` with `--base`, `--run-checks`, `--plan`, and `--output .claude/reports`, and the run continues after its summary.
- [ ] Confirmed findings are fixed; refuted and unverified ones are left alone and listed.
- [ ] A Critical finding stops for the user; "Stop this phase here" leaves the phase `blocked`.
- [ ] `fix_rounds: 1` caps the loop: no second fix round.
- [ ] No push, no pull request, no comment.
- [ ] No status line or question names a stage, a verdict token, or a rule code (R12).
- [ ] Every review command this file and the skill print carries `--run-checks`.
- [ ] No `CLAUDE_PLUGIN_ROOT` references in `SKILL.md` (R4).
- [ ] No Unicode characters or emoji in `SKILL.md` or this file (R8).
- [ ] No inline `!` shell blocks beyond the five git blocks (R3); `bash tests/skills/test-shell-block-syntax.sh` passes.
- [ ] `when-to-use:` is a single-line double-quoted string (R10).
- [ ] `SKILL.md` names `skills/plan/SKILL.md`, `skills/brainstorm/SKILL.md`, `skills/verification/SKILL.md`, `skills/tdd/SKILL.md`, and `skills/local-files/SKILL.md` and restates none of them; `bash tests/skills/test-ship-plan-pointers.sh` and `bash tests/skills/test-ship-contract.sh` pass.

**Known gotchas:**
- A fix stage that finds no confirmed finding on a branch with a real defect points at the review's finding check (`/quiver:review` Step 3.3), not at ship. Ship fixes only findings carrying `Verification: confirmed`, so a check that never confirms makes ship fix nothing. Run `bash tests/eval/run-review-golden.sh --keep` first and read the `Verification:` lines in the report it names, and its `refuted by verification` notes, before debugging ship.
- The Skill tool does not return. Invoking `work` or `quiver:review` loads that file into the conversation; the only end signal is the callee's summary (`/work` Phase 5d, the review's Step 4b), and both end with "follow its continuation step". A turn that still ends on a summary is what Step 1's re-derivation recovers; it is not a defect when the next `/ship` resumes at the right stage.
- Use the qualified `quiver:review`. A bare `/review` resolves to a bundled command's alias and runs a different reviewer that writes no report, so Step 1 never finds one and the fix stage has nothing to read.
- A saved report location for `/quiver:review` does not move ship's report, because ship passes `--output .claude/reports`; it does point the second review's re-review detection elsewhere, and that review then covers the whole branch. More cost, same result.
- Fix rounds are counted in the phase file, not from the report's `Iteration` line: a phase started on an earlier phase's unmerged branch starts its first review as a re-review.
- The 30% and 8-task thresholds and the window sizes are unmeasured starting values. The `## Measurements` context line is how they get tuned; a run that skips writing it loses the data point. The transcript format is undocumented and written asynchronously, so `context: unknown` is an expected result, not a failure.
- The three-attempt fix cap lives in `/work`. Ship adds no retry; a task still failing after its third run is accepted and listed in the final report.
- Starting ship on a feature branch makes `/work --auto` continue on that branch. A phase whose dependency's branch is not merged continues on the current branch with one line saying so; ship never merges or rebases.
- An existing plan path is never overwritten: its basename keys `/work`'s ledger, and a rewrite under the same name would resume `complete` lines against tasks it never built.
- The "nothing to look up" setup uses a pure function with no I/O and no library on purpose. A realistic description leaves runtime behavior open even when it names every library and version, and research runs for it, correctly.
- Plugin auto-discovery needs a plugin reload after the skill is first installed.
