---
name: verify-generation
description: Use on every generative step. Runs 3 to 5 verification rounds with the full suite (tests plus the matching verifier agents), fixes every finding between rounds, records the rounds in progress, stops on a passing round, and refuses to call a step done while findings remain.
---

# Verify a generation

## Goal

No generative output reaches the owner without having survived the full verification suite, so the owner's past corrections are enforced before they can be repeated. The suite has two halves, deterministic tests that catch what code can catch and verifier agents that judge what code cannot, and a round is both halves against the current output. Rounds repeat because a fix in one place breaks another, and because a verifier in fresh context may see on the second read what it missed on the first. The step stops when a round passes, with at least three rounds so a pass is confirmed, and never after round five. Findings are fixed in the artifact only, never by changing a test, a verifier or a memory entry, since those are the owner's corrections and the artifact is the thing under review. Every round is recorded in progress with its evidence, so the report can show the owner what was checked and the next context can resume if this one is lost. Findings that survive round five are reported as unfinished work, never hidden, because an owner who sees an unresolved finding can decide and an owner who does not will meet it as a correction.

## Objective

Identify the artifacts the step produced or changed and select every verifier whose trigger matches them, plus the memory-conformance verifier that runs on everything. Run a round: the full test suite, then each selected verifier in fresh context with only the inputs its file lists, collecting every FAIL with its location. Fix every finding in the artifact, citing the rule or fact id each fix applies. Record the round in the progress table with the test result, the verifiers run, the findings and the fixes. Repeat until a round passes on or after round three, or until round five has run. Report the rows and the verdict, and list any findings that remain as open items, with the step marked not done.

## Tasks

1. Identify the artifacts the step produced or changed, by path. A step that touched several files verifies all of them together, because a rule about consistency across files cannot be checked one file at a time.
2. Load `memory/verification.md` and `verifiers/INDEX.md`. Select every active verifier whose trigger matches an artifact path or kind, plus `verifiers/memory-conformance.md`, which runs on everything. Record the selection in the progress table so the report shows what was checked.
3. Run a round. First `python -m pytest -q tests`, and record pass or the failing test names. Then run each selected verifier in fresh context with the artifact paths, the rule texts it names and the examples it names, and collect every FAIL with its quoted location and rule id. A round is both halves; a round that skipped either is not a round.
4. Fix every finding in the artifact. Do not touch tests, verifiers or memory to make a finding go away; if a finding looks wrong, task 7 says what to do. Cite the rule or fact id each fix applied, so the progress table shows the memory being used.
5. Record the round in the table in `memory/progress.md`: step, round number, tests result, verifiers run, findings, fixed. Write the row before starting the next round, so a lost context can resume from the table.
6. Repeat from task 3. Stop after a round with zero findings once at least three rounds have run, or after round five whatever the result. A clean round one or two is followed by another full round, not by stopping.
7. If findings remain after round five, list them under open items in `memory/progress.md` with the verifier and the location, and report the step as not done. A FAIL the agent believes is wrong goes to `memory/open-questions.md` as a `Q` entry for the owner, with the finding quoted.

## Instructions

- **The full suite is both parts, every round.** The tests catch what code can catch, cheaply and identically each time; the verifiers judge what code cannot. Skipping the tests because nothing mechanical changed misses the fix that broke a count; skipping the verifiers because the tests passed misses everything the tests cannot see. A round that ran one half is recorded as half a round and does not count toward the minimum.
- **A verifier runs as a separate agent that sees only what its file lists.** In Claude Code, launch the `verifier` agent from `.claude/agents/` with the verifier path and the artifact paths in the task message. Elsewhere, start a fresh context with the verifier file as the system prompt and the artifact paths as the message. Never run a verifier inside the generating context, and never pass it the plan, the conversation or an explanation of the artifact; the verdict is worth exactly as much as the verifier's independence.
- **A FAIL the agent disagrees with is still a finding.** Fix the artifact if the fix is harmless, which it usually is. If the fix would make the artifact worse by the agent's reading, record the disagreement as a `Q` entry in `memory/open-questions.md`, quoting the finding and the reason, and list it under open items; the owner settles it as feedback. Every other unresolved finding goes under open items in `memory/progress.md`. A round is never marked clean by overruling a verifier, because the verifier is the owner's proxy and the agent is the party under review.
- **Each round is a full run against the current output.** Re-checking only the last round's findings misses what the fixes broke, which is the most common second-round finding. The tests are cheap and the verifiers are fresh each time, so there is no saving to be had by narrowing a round.
- **Cite the rule or fact ids each fix applied.** The progress table and the report name the ids, so the owner can see that the memory was used and which entries earned their place. A fix that cites no id is either a judgment call the agent made alone, which the report should say, or a sign that a fact is missing, which is feedback for the owner.
- **The stopping condition is a passing round, within the bounds.** A round passes when the test suite is green and every selected verifier returns PASS with no findings. The step is not done before round three, because a single clean read by a fresh-context verifier is weak evidence and the extra rounds are cheap. The step never runs past round five; after that the findings are reported, not chased, so the owner decides.

## Checklist

- [ ] **Verifiers were selected by trigger from the index, plus memory-conformance.** Every active verifier whose trigger matches an artifact ran in every round, and none was dropped because it was slow or inconvenient. The selection is recorded in the first row for the step.
- [ ] **At least three rounds ran and at most five, and the step ended on a passing round or was reported as not done.** A clean round before round three was followed by a full round, not by stopping. Round five was the last whatever it found.
- [ ] **Every round is recorded in `memory/progress.md` with its evidence.** Each row names the step, the round number, the test result, the verifiers run, the findings with locations, and the fixes with the ids they applied. The row was written before the next round started.
- [ ] **No test, verifier or memory file changed during the rounds.** `git status` after the step shows changes to the artifact and to `memory/progress.md` only, plus a `Q` entry in `memory/open-questions.md` for a disputed finding. A finding was never made to disappear by editing its check.
- [ ] **Unresolved findings are reported, never hidden.** Anything still failing after round five is under open items with its verifier and location, and the report marks the step not done. A disputed FAIL has a `Q` entry.

## Output

The progress table rows for the step and a one-line verdict: clean after round N, or unresolved findings listed with their verifier and location and the step marked not done.

## Runtime behavior

- Runs inside the main request after every generative step, before the output is shown to the owner or used by a later step, so downstream work never builds on an unverified artifact.
- Reads memory and runs tests; fixes go to the artifact, and the only repo files it writes are `memory/progress.md` and, for a disputed finding, `memory/open-questions.md`. It never edits `tests/`, `verifiers/` or any other memory file.
- Launches verifiers in fresh context, one agent per verifier per round, and waits for all of them before fixing, so the fixes address the full set of findings at once.
