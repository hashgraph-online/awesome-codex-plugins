# Memo Contract

Use this rule before writing or revising any memo. It owns when to write, where the file lives, the required sections and their budget, what stays out, the secret rule, and revision.

## 1. When to Write

Write at a natural boundary, not at the last token. A memo written while the session still has room is better than one squeezed in at the limit.

- Write when the context is nearly full, before a compaction, before the session, agent, or machine changes, or when the user asks.
- Rewrite after each verified step of a long job when the user wants the work to survive a sudden stop. One memo per piece of work; a rewrite replaces the file.
- Do not write for a task that finishes in the current turn. There is nothing to carry.

## 2. Where It Lives

- Path: `.hyper/handoff/<slug>/memo.md`. The slug is a lowercase hyphenated name for the work, taken from the user's words or the branch name.
- `.hyper/` must be git-ignored. Check with `git check-ignore -q --no-index .hyper/`; when it is not ignored, add `.hyper/` to the repository's ignore file as part of this write and say so in the report.
- Outside a git repository, use the same relative path in the working directory.
- Keep one file. The history of earlier memos is not kept: the point is that the current state is enough.

## 3. Required Sections

Section names are English and verbatim. Fill every section; write `none` where nothing applies, so a reader knows it was considered.

|Section|Holds|Rule|
|---|---|---|
|Header lines|`Slug`, `Revision`, `Written` (date and time), `Written by` (agent and machine), `Check`|The check line is `pass`, `unverified-standalone: <failed questions>`, `self`, or `skipped by user`|
|`## Original request`|The user's request, quoted verbatim|Never paraphrased, shortened, or translated|
|`## Corrections`|Each later user instruction that changes or narrows the request, quoted verbatim, with its date|`none` when there were none|
|`## Now`|What is being done and why, in at most five sentences|Names the one outcome the work is moving toward|
|`## Done`|Finished items, each with the check that proved it or the word `unverified`|One line per item|
|`## Next`|Ordered steps; the first is a concrete action with the exact command or file|At most eight steps; later ones may be coarser|
|`## Plan and done-when`|The plan source (a path or `none`) and the observable conditions that mean finished|At least one condition a command or a look at a file can confirm|
|`## Where`|Repository path, branch, worktree, machine, pull requests, services, state directories|Pointers only; each resolves or is marked `external`|
|`## Decisions and dead ends`|Decisions the user made (who, when) and approaches that failed and must not be repeated|Each dead end names why it failed|
|`## Open questions and risks`|What is unknown, what could break, what waits on the user|`none` when empty|

## 4. Budget

- Aim for at most 100 lines excluding the quoted request and corrections. This is this skill's own default, chosen so the memo is read in full, not a figure from any study.
- A longer memo means the writer is copying instead of pointing. Move detail to the file it belongs in and keep a path.
- The quoted request is never cut to fit. If it is very long, keep it whole and shorten everything else.

## 5. What Stays Out

- Transcripts, tool output, diffs, and logs. Keep the one line that matters and a pointer to where the rest is.
- A copy of a plan or of a plan run or goal loop state. Point to the plan file and to the state directory, and write in `Next` that the work resumes by that run's own resume rule.
- Reasoning narratives and feelings about the work. Keep conclusions and the reason for a decision.
- Anything the reader can read faster from the repository than from the memo, such as file contents or the full list of changed files. Give the command that produces it.

## 6. Secrets and Personal Data

- Never write a secret, token, password, key, or personal data value into the memo. Write where it lives (for example `the value is in the project's secret store under NAME`) and that it was not copied.
- If the user's own request contains a secret, quote the request with the value replaced by `[redacted]` and say so in the header. This is the one allowed edit to the verbatim rule.

## 7. Facts, Not Recall

- Gather branch, worktree, changed files, last test result, and running processes with commands in the current repository. Do not write them from memory of the conversation.
- A line that cannot be checked is marked `unverified`. A reader trusts an honest `unverified` more than a confident guess.
- Dates are absolute. Write `2026-11-09`, never `yesterday`.
- Name things by their identifier, not by a word that only made sense in the conversation: not "the bug" or "that file", but `login redirect loop in src/auth/redirect.ts`.

## 8. Revising

- Increase `Revision`, update `Written` and `Check`, and re-run the check from `rules/cold-read-and-resume.md` after any change to `Now`, `Next`, or `Plan and done-when`.
- Move a finished `Next` step into `Done` with its proof. Drop a dead end that is no longer reachable.
- Never delete the original request or a correction.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| After a compaction, crucial information and the user's stated preferences can disappear; this is why the original request and corrections are copied verbatim | [Belcak et al., arXiv:2611.05306](https://arxiv.org/abs/2611.05306), Appendix A |
| The recap covers objective, facts, changes, verification, dead ends, and the remaining plan with the completion condition | same paper, Appendix G |
| The section list, the 100-line budget, the file location, and the secret rule are this package's own design | `instructions/skill/SKILL_AUTHORING.md` for the package shape only |

### Evidence grade

`LOCAL` - the contract is this package's design; only the verbatim-request reason comes from the cited paper.
