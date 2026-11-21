# Memo Contract

Use this rule before writing or revising any memo. It owns when to write, where the file lives, the required sections and their budget, what stays out, the secret rule, and revision.

## 1. When to Write

Write at a natural boundary, not at the last token. A memo written while the session still has room is better than one squeezed in at the limit.

- Write when the context is nearly full, before a compaction, before the session, agent, or machine changes, or when the user asks.
- Rewrite after each verified step of a long job when the user wants the work to survive a sudden stop. One memo per piece of work; a rewrite replaces the file.
- Do not write for a task that finishes in the current turn. There is nothing to carry.
- Leave room for the write itself. Gathering facts, writing the memo, and the stand-alone check all use context, and a memo started at the limit may not finish.
- Switching sessions is not free: the next session re-reads the memo and the files it points to. Switch when the context or the user requires it, not after every small step. When no verified step fits between two switches, report that instead of writing another memo.

## 2. Where It Lives

- Path: `.hyper/handoff/<slug>/memo.md`. The slug is a lowercase hyphenated name for the work, taken from the user's words or the branch name.
- `.hyper/` must be git-ignored. Check with `git check-ignore -q --no-index .hyper/`; when it is not ignored, add `.hyper/` to the repository's ignore file as part of this write and say so in the report. Register it before taking the fingerprint: the ignore edit is itself a dirty entry, so a fingerprint taken first goes stale the moment the memo is written.
- Because the path is normally ignored, a push or clone does not carry the memo. When the trigger is a move to another machine, the report says so, gives the memo's absolute path, and names the two ways to move it without performing them: copy the `.hyper/handoff/<slug>/` directory, companion files included, to the same path on the other machine, or paste the memo text into the new session, which saves it at that path before resuming. Committing the memo is the user's call, never the default, and the memo never holds a secret value, only where the value lives.
- Outside a git repository, use the same relative path in the working directory.
- One slug is one line of work. Keep one memo file per slug and revise it in place; a different piece of work gets its own slug. The history of earlier memos is not kept: the point is that the current state is enough. A data file the memo points to (section 4) may sit beside it.
- Several open memos: a path named by the user wins; otherwise match the current branch or worktree against `Where`; if more than one still matches, list them (slug, `Written`, `Now`) and ask once. Never pick silently by newest.

## 3. Required Sections

Section names are English and verbatim. Fill every section; write `none` where nothing applies, so a reader knows it was considered.

|Section|Holds|Rule|
|---|---|---|
|Header lines|`Format` (`hyper-handoff/1`, or `legacy` when the line is absent), `Slug`, `Revision`, `Status` (`open` or `closed (<date>: <reason>)`), `Written` (date and time), `Written by` (agent and machine), `HEAD:` (`<sha> (<branch>)`, `none (no commits)`, or `none (not a git repository)`), `Dirty:` (`clean`, or the count and the `git status --porcelain` paths; past 20, the count and a short digest of that output), `Resumed:` (the time a session resumed it, or `none`), `Check`|The fingerprint is taken in the worktree named in `Where` at write time. The check line has one spelling, `Check:`, with `pass`, `unverified-standalone: <question numbers>`, `self: pass`, `self: fail: <question numbers>`, or `skipped by user`|
|`## Original request`|The user's request, quoted verbatim|Never paraphrased, shortened, or translated|
|`## Corrections`|Each later user instruction that changes or narrows the request, and each standing preference or steering instruction about how to work (what to use, what not to touch, what to report), quoted verbatim, with its date|`none` when there were none|
|`## Now`|What is being done and why, in at most five sentences|Names the one outcome the work is moving toward|
|`## Done`|Finished items and established findings, each with the check that proved it or the word `unverified`|One line per item; a finding keeps its exact value and where it was observed|
|`## Next`|Ordered steps; the first is a concrete action with the exact command or file|At most eight steps; later ones may be coarser. A step that is destructive or reaches outside the working tree carries the tag `confirm-first`, so the reader sees the gate before reaching it; the tag adds no authority|
|`## Plan and done-when`|The plan source (a path or `none`), every completion requirement the request and corrections state, and the checks that must pass before the work is called finished|At least one condition a command or a look at a file can confirm|
|`## Where`|Repository path, branch, worktree, machine, pull requests, services, state directories, the old session's record, and state the work depends on that lives outside the repository|Pointers only; each resolves or is marked `external`; state that will not survive the session or the move is named as such|
|`## Decisions and dead ends`|Decisions the user made (who, when), approaches that failed and must not be repeated, and workarounds that were needed|Each dead end names why it failed; a workaround names the command that worked|
|`## Open questions and risks`|What is unknown, what could break, what waits on the user|`none` when empty|

`Format` is the first header line and names the memo format version. This release writes `hyper-handoff/1`; the number after the slash changes only when a section is renamed or removed. A memo without the `Format` line is read as `legacy`: it is read, not rejected, and the rest of this contract applies as written. A reader that meets a major version it does not know reports that version and the parts it could not interpret, and does not guess at them.

## 4. Budget

- Aim for at most 100 lines excluding the quoted request and corrections. This is this skill's own default, chosen so the memo is read in full, not a figure from any study.
- A longer memo means the writer is copying instead of pointing. Move detail to the file it belongs in and keep a path.
- The quoted request is never cut to fit. If it is very long, keep it whole and shorten everything else.
- Exact results the remaining work needs in full, such as a list of outcomes, measurements, or identifiers, are not shortened to fit. Save them in a file beside the memo and point to it, or point to the record that already holds them.

## 5. What Stays Out

The memo is a brief for the work that remains, not a history of the session and not a summary of it. A line stays only when the remaining work needs it; how long something took, or how often it came up, is not a reason to keep it.

- Transcripts, tool output, diffs, and logs. Keep the one line that matters and a pointer narrow enough to fetch only the needed part: a file with a line range, or a command with a filter.
- A copy of a plan or of a plan run or goal loop state. Point to the plan file and to the state directory, and write in `Next` that the work resumes by that run's own resume rule.
- Reasoning narratives and feelings about the work. Keep conclusions and the reason for a decision.
- Anything the reader can read faster from the repository than from the memo, such as file contents or the full list of changed files. Give the command that produces it.

## 6. Secrets and Personal Data

- Never write a secret, token, password, key, or personal data value into the memo. Write where it lives (for example `the value is in the project's secret store under NAME`) and that it was not copied.
- If the user's own request contains a secret, quote the request with the value replaced by `[redacted]` and say so in the header. This is the one allowed edit to the verbatim rule.

## 7. Facts, Not Recall

- Gather branch, worktree, `HEAD`, dirty set, changed files, last test result, and running processes with commands in the current repository. Do not write them from memory of the conversation. The fingerprint is `git rev-parse HEAD` and `git branch --show-current` for `HEAD:`, and `git status --porcelain` for `Dirty:`, both run in the worktree named in `Where`.
- A line that cannot be checked is marked `unverified`. A reader trusts an honest `unverified` more than a confident guess.
- Dates are absolute. Write `2026-11-09`, never `yesterday`.
- Name things by their identifier, not by a word that only made sense in the conversation: not "the bug" or "that file", but `login redirect loop in src/auth/redirect.ts`.
- Keep the exact value the next steps depend on, not a description of it: the error line as printed, the measured number, the command that worked. Keep observations apart from ideas that were not tested; an untested idea is marked `unverified`.
- For work that reads a large input, record which parts were read and what they showed, so the next session does not read them again.
- State outside version control cannot be rebuilt from the repository: uncommitted changes when the machine changes, installed dependencies, applied migrations, running processes, temporary files. Name each one the work depends on in `Where` and say whether it survives.

## 8. Revising and Lifecycle

- Increase `Revision`, update `Written` and `Check`, and re-run the check from `rules/cold-read-and-resume.md` after any change to `Now`, `Next`, or `Plan and done-when`.
- Revise by editing, not by rewriting from the previous memo. Carry lines that are still true unchanged and re-check changed facts against the repository. A memo rewritten from a memo loses a little more each time.
- Move a finished `Next` step into `Done` with its proof. Drop a dead end that is no longer reachable.
- Never delete the original request or a correction.
- Close with `Status: closed (<date>: <reason>)` when the done-when conditions are met, the memo is superseded, or the user drops the work. A closed memo is kept unless the user asks to delete it, and it is never resumed unless the user names it.
- On resume, write `Resumed: <time>` in the header. A memo that shows a recent `Resumed` from another session and is still open is reported to the user before continuing.
- Re-read the header right before writing. If `Revision` changed since this session read it, another session wrote: do not overwrite, re-read and edit, or stop and report.

## Sources

> Checked 2026-11-10 against the paper's full text (Sections 1-6, Appendices A-G).

| Claim | Source |
|---|---|
| The compactions that kept accuracy best were briefs chosen for the work still to do, not faithful accounts of the trace; a plain summary weighs every fact alike and over-weights repeated stretches (sections 5 and 8) | [Belcak et al., arXiv:2611.05306 v1](https://arxiv.org/abs/2611.05306), Appendix A |
| Those compactions held a verbatim or near-verbatim copy of the task, the current activity with intent and next steps, a plan decomposed from the task, the requirements for calling the task complete, and pointers to the artifacts that hold relevant information (section 3: `Original request`, `Now`, `Next`, `Plan and done-when`, `Where`) | same paper, Appendix A |
| The recap prompts ask for the objective, established facts with exact values and with observations kept apart from unverified ideas, applied changes with verification status, the checks run, dead ends, workarounds and commands already tried, the remaining plan with the next action and the completion condition, and a narrow command for any truncated output; their task-specific slots add which state persists across conversations, input coverage, and the checks required before completion (sections 3, 5, and 7) | same paper, Appendix G |
| In human-in-the-loop work a compaction can lose crucial information and the user's stated preferences, and has to keep what follow-up work after the user's steering may need (`Corrections`). The paper reports this as common experience; its own experiments ran without a human | same paper, Appendix A |
| A compaction is lossy, compacting a history that already holds a compaction loses more, and a task that needs exact past outcomes fails under a fixed compaction budget; the paper's proposed remedy, which it did not evaluate, is a kept record read selectively (sections 4 and 8, the session record in `Where`) | same paper, Section 3.1 |
| The harness triggered compaction at a threshold below the context limit to leave room for the compaction turn, and ended a run whose compaction did not finish in that room (section 1) | same paper, Section 2.4.1, Appendix C |
| Total work can grow under tight compaction: on Terminal-Bench 2.1 one model's mean total length was 72K tokens at a 24K limit against 28K with full history, and one open-weight model fell from 53.0% to 3.6% on SWE-bench Verified at a 16K limit, which the paper puts down mostly to verbose steps leaving little room for progress between compactions (section 1) | same paper, Table 5, Appendix D |
| Own design, not from the paper and not tested against it: the section names and their order, the 100-line budget, the file location, the secret rule, the `unverified` marker, re-checking state with commands while writing (the paper's compaction turn runs none), carrying the request inside the memo (the paper's harness supplies the task again, so its recap does not repeat it), the `HEAD:`/`Dirty:` fingerprint, the `confirm-first` tag, the `Status` and `Resumed` lifecycle, and the rule against overwriting an unread `Revision` | this package; `instructions/skill/SKILL_AUTHORING.md` for the package shape only |

### Evidence grade

`LOCAL` for the contract's shape, names, and numbers: they are this package's design. `EXTERNAL-PREPRINT` for the rows that cite the paper: one unreviewed arXiv v1, measured on its own harness and models with no human in the loop, and not on the agents that run this skill.
