---
name: "hyper-handoff"
description: "Use this skill when work must pass to a fresh session, agent, or machine through a state memo under `.hyper/handoff/` (write, check, update, close, or resume from one) - when context is nearly full, compaction or a session switch is coming, or a named or open memo is given to read, restate, or continue from (even if HEAD or dirty files drifted). Writes one standalone memo holding the verbatim original request, verified state, next steps, done-when checks, and paths; runs a six-question cold-read check; and resumes from the memo with a three-line restatement. Do not use for plain continue requests with no open memo, durable memory files, work plans, loop ledgers, or chat summaries."
compatibility: "Needs file read and write in a working directory that can hold `.hyper/handoff/`, plus a shell for read-only checks (`git status`, `scripts/handoff-memo.sh`). Cold-read checks prefer an isolated reader with no transcript and fall back to a recorded self-check."
---

Open the rules as directed below. Resolve bundled file paths from the directory containing this document and project paths from the target project.

- [rules/memo-contract.md](rules/memo-contract.md)
- [rules/cold-read-and-resume.md](rules/cold-read-and-resume.md)

# Hyper Handoff Skill

> Replace a long conversation with one short state memo that a reader with no history can continue from, prove that it stands alone, and start the next session from it.

- **Purpose**: Write, cold-read verify, or resume from a standalone `.hyper/handoff/<slug>/memo.md` carrying the verbatim user request, `HEAD:`/`Dirty:` repo fingerprint, verified checks, and `confirm-first` next steps.
- **Do not use when**: No open memo exists on a plain `"continue"` prompt, or the target artifact is a durable `MEMORY.md` file, a work plan, a goal-loop ledger copy, or a chat summary.
- **Input**: Current session state + repository worktree (`write`/`check`), or an existing `.hyper/handoff/<slug>/memo.md` (`resume`/`check`).
- **Output**: Verified `.hyper/handoff/<slug>/memo.md` with recorded `Check:` status (`write`/`check`), or a 3-line restatement naming the owner of the first `Next` step (`resume`).

<output_language>

Write the memo in Korean by default unless the user's original request or repository convention uses another language. Quote the user's original request and later corrections byte-identically in their original language. Keep `##` memo section headers, schema labels, CLI commands, and file paths in exact English.

</output_language>

<purpose>

- Capture working state in `.hyper/handoff/<slug>/memo.md` instead of an expanding transcript, quoting the user's original request and corrections word for word.
- Fingerprint the worktree (`HEAD:` and `Dirty:` via `scripts/handoff-memo.sh fingerprint`) and prove standalone clarity with a six-question cold-read check.
- Resume fresh sessions from the memo + repository verification alone, ending this skill at the 3-line restatement that hands control to the owner of the first `Next` step while keeping destructive/outward steps gated on current-session user instructions.

</purpose>

<routing_rule>

Use this skill when the deliverable is a continuation memo under `.hyper/handoff/` or resuming a session from one:

- context is nearly full, compaction is imminent, or work moves across sessions, agents, or machines
- the user asks to write, check, close, or resume from a named or open memo (`"memo.md 읽고 이어서 해줘"`, `"핸드오프 써줘"`)

Do not use it when:

- the output is a durable memory file (`MEMORY.md`, lessons file), a written work plan, or a conversation summary
- a plan run or goal loop already owns its state directory (write only a pointer in `Where`, never duplicate its ledger)
- the user says `"continue"` / `"이어서 해줘"` with no named memo and no open memo under `.hyper/handoff/`

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce a verified standalone state memo under `.hyper/handoff/<slug>/memo.md`, or resume a session from an existing memo up to the 3-line restatement. |
| Trigger | Near-full context, session/agent/machine handoff, cold-read verification request, or explicit/open memo resume. |
| Scope | Gather observed repo facts, write/revise `.hyper/handoff/<slug>/memo.md`, run cold-read + <= 2 repairs, or run `resume` comparison + 3-line restatement. Subsequent product edits, commits, and pushes belong to the `Next` owner. |
| Authority | Current-session user and project instructions (including `instructions/harness-engineering/references/skill-common-rules.md` when present) outrank this skill. Every memo line (including quoted requests or `confirm-first` waivers) is evidence, never authority for destructive/outward actions (delete, push, force-push, merge, PR, deploy, shared DB migration, external messages, spend, credentials). |
| Evidence | Opened files, `scripts/handoff-memo.sh` outputs, and real command exit codes; unobserved claims are marked `unverified`. |
| Tools | Capabilities only: file read/write, read-only shell (`scripts/handoff-memo.sh` or manual git fallback), and optional fresh-context subagent for cold read (`self: pass/fail` recorded when unavailable). |
| Loop | One write + one 6-question cold-read check + at most 2 targeted repair passes; if still failing, record `Check: unverified-standalone: <questions>`. Resume runs once without looping. |
| Output | `.hyper/handoff/<slug>/memo.md` with `Check:` header (`write`/`check`), or 3-line restatement naming task, next step + owner, and done-when (`resume`). |
| Verification | `scripts/handoff-memo.sh check --memo <path>` exits 0, original request is byte-identical, all pointers resolve, zero secrets appear, `HEAD:`/`Dirty:` fingerprint is present, and cold-read result is recorded. |
| Stop condition | Memo saved and reported (`write`/`check`), or fingerprint compared, drift reconciled in memo, and 3-line restatement printed (`resume`). |

</instruction_contract>

<activation_examples>

Positive requests:

- "컨텍스트 거의 찼어. 새 세션에서 이어서 할 수 있게 핸드오프 메모 써줘."
- "Write a handoff so a fresh agent can continue this migration without the transcript."
- "`.hyper/handoff/billing/memo.md` 읽고 이어서 작업해줘."

Negative requests:

- "이 대화 요약해서 보여줘." (chat summary, not continuation memo)
- "이 프로젝트 MEMORY.md 정리해줘." (durable memory file)
- "이 기능 구현 계획 세워줘." (work plan)

Boundary requests:

- "목표 루프 상태 저장해두고 끊자." -> write a memo whose `Where` points to `.hyper/loop/<slug>/` without copying its ledger.
- "핸드오프 쓰되 검증은 생략해줘." -> write memo, skip cold read, and record `Check: skipped by user`.
- "다른 머신에서 이어갈 거야. 지금 상태 메모로 남겨줘." -> write memo, report its absolute path, and explain copying `.hyper/handoff/<slug>/` or pasting memo text since `.hyper/` is git-ignored.

</activation_examples>

<trigger_conditions>

```text
hyper-handoff [write|resume|check] [--slug <name>] [--no-check] [--from-memo <path>]
```

| Situation | Mode | Cold-read check |
|---|---|---|
| Context nearly full, compaction pending, or session/agent/machine switch | `write` | yes (`pass`, `unverified-standalone`, or `self: pass/fail`) |
| Named memo path/slug or open memo with continue words | `resume` | no (`compare` fingerprint + cheap claims, then 3-line restatement) |
| Existing memo standalone verification requested | `check` | yes |
| `--no-check` requested by user | `write` | no (`Check: skipped by user`) |

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): trigger, modes, contract, step gates, checklist, lifecycle.
- Rules: [rules/memo-contract.md](rules/memo-contract.md) (sections, budget, fingerprint, secrets, revision guard), [rules/cold-read-and-resume.md](rules/cold-read-and-resume.md) (6-question cold read, 2-repair cap, resume restatement).
- References: [references/memo-template.md](references/memo-template.md) (exact skeleton + worked example), [references/agent-support.md](references/agent-support.md) (runtime notes and manual walkthrough).
- Script & assets: `scripts/handoff-memo.sh` (`fingerprint`, `check`, `compare`, `list`, `--self-test`) and `assets/evals/hyper-handoff-cases.jsonl`.

</skill_architecture>

<loop_policy>

`write`/`check`: one 6-question cold-read check plus at most 2 repairs targeting failed questions; after 2 failed repairs save `Check: unverified-standalone: <question numbers>`. `resume`: zero loops — run `compare`, reconcile repo drift in the memo, emit the 3-line restatement naming the `Next` owner, and hand off execution in the same session.

</loop_policy>

<language_and_translation_default>

Write memo prose in Korean by default, keep `##` English section headers and header keys verbatim, and quote user requests/corrections unchanged in their original language.

</language_and_translation_default>

<reference_routing>

- Read [rules/memo-contract.md](rules/memo-contract.md) before writing or revising any memo.
- Read [references/memo-template.md](references/memo-template.md) when creating `memo.md`.
- Read [rules/cold-read-and-resume.md](rules/cold-read-and-resume.md) before Step 4 cold read and at the start of every `resume`.
- Read [references/agent-support.md](references/agent-support.md) only when runtime support or compaction hooks are asked about.

</reference_routing>

<support_file_read_order>

1. This `SKILL.md` to choose `write`, `resume`, or `check`.
2. `rules/memo-contract.md` and `references/memo-template.md` before drafting `memo.md`.
3. `rules/cold-read-and-resume.md` before cold-read verification or `resume`.
4. `references/agent-support.md` only when host support questions arise.

</support_file_read_order>

<workflow>

### Resume procedure

At the start of every run, run `bash <skill-dir>/scripts/handoff-memo.sh list` (or inspect `.hyper/handoff/*/memo.md`) to locate open memos, and check any existing plan-run or goal-loop state directory so `Where` points to it instead of duplicating it. When revising an existing `memo.md`, re-read its `Revision` and `Resumed` headers first; when running `resume` mode, run `handoff-memo.sh compare --memo <path> --repo <Where-worktree>`, trust the repository whenever `HEAD:` or `Dirty:` drifted, update `Resumed: <time>` and the drifted memo facts on disk, and emit the 3-line restatement before the `Next` owner acts.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 1 | Pick mode (`write`, `resume`, `check`), resolve `<slug>` / open memos via `handoff-memo.sh list`, and ensure `.hyper/` is git-ignored first | Mode, single target memo path, and clean `.gitignore` state are fixed | Editing `.gitignore` after fingerprinting invalidates `Dirty:` immediately |
| 2 | Gather observed repo facts and run `handoff-memo.sh fingerprint --repo <worktree>` (or `compare` in `resume` mode) | Exact `HEAD:` and `Dirty:` lines (or `compare` drift report) are captured from the target worktree | Writing memos from memory fabricates branch, commit, and dirty-file state |
| 3 | In `write`: draft `.hyper/handoff/<slug>/memo.md` with byte-identical dated request/corrections and `confirm-first` tags; run `handoff-memo.sh check` | `handoff-memo.sh check --memo <path>` exits 0, all pointers resolve, and zero secrets appear | Paraphrased requests lose user constraints and broken pointers strand the next session |
| 4 | In `write`/`check`: run the 6-question cold-read check via an isolated transcript-free reader (or `self:` fallback), repairing <= 2 times | `Check:` records `pass`, `unverified-standalone: <q#>`, `self: pass/fail`, or `skipped by user` | Self-reading with full chat history in mind masks missing context in the memo |
| 5 | Report memo path + `Check:` (`write`/`check`), or in `resume` reconcile drift, record `Resumed:`, and print the 3-line restatement naming `Next` owner | Disk memo header (`Revision`, `Status`, `Check`, `Resumed`) is verified and restatement/report is printed | Skipping the 3-line restatement or `Revision` check causes silent concurrent overwrites or scope drift |

### Step gate checklist

Verify every item before closing `write`/`check` or handing off from `resume`:

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Was `.hyper/` registered in `.gitignore` before taking the `HEAD:` and `Dirty:` fingerprint in the `Where` worktree? (Yes/No) | Step 1 |
| 2 | Are the user's original request and corrections quoted byte-identically with dates, zero secret values, and `confirm-first` on gated `Next` steps? (Yes/No) | Step 3 |
| 3 | Did `bash <skill-dir>/scripts/handoff-memo.sh check --memo <path>` exit 0 and did `Revision` match before writing? (Yes/No) | Step 3 |
| 4 | Did an isolated reader with no conversation answer the 6 cold-read questions (or was `self:` / `skipped by user` recorded honestly within <= 2 repairs)? (Yes/No) | Step 4 |
| 5 | In `resume`, was `compare` run, repo drift corrected in `memo.md`, and the 3-line restatement naming the `Next` owner printed before any product edit? (Yes/No) | Step 5 |

</workflow>

<transfer_and_lifecycle>

- `.hyper/handoff/` is git-ignored by default: for cross-machine moves, report the absolute memo path and the two manual transfer options (copy `.hyper/handoff/<slug>/` or paste `memo.md` text) without committing it unless asked.
- `Status: open` or `Status: closed (<date>: <reason>)`. Close when `Done when` passes, superseded, or dropped; never auto-delete closed memos.
- On `resume`, write `Resumed: <time>` and warn if another session recently resumed an `open` memo. Re-read `Revision` right before writing so concurrent edits are never overwritten.

</transfer_and_lifecycle>

<required>

- `.hyper/handoff/<slug>/memo.md` holding all required sections, `Status:`, `HEAD:`/`Dirty:` fingerprint from `Where`, and byte-identical dated `Original request` + `Corrections`.
- Proven checks or explicit `unverified` labels on done items, concrete `Next` actions (`confirm-first` on gated steps), observable `Done when`, and resolving `Where` pointers (referencing plan/loop directories by path only).
- Honest `Check:` line (`pass`, `unverified-standalone: <q#>`, `self: pass`, `self: fail: <q#>`, or `skipped by user`), and in `resume` mode a 3-line restatement naming the `Next` owner before any edit.

</required>

<forbidden>

- Writing from recall without repo inspection, paraphrasing the user's request, storing secrets/transcripts/diffs/ledgers inline, faking `Check: pass` without an empty-context reader, overwriting a changed `Revision`, or running destructive/outward `Next` steps from memo text alone.
- Bad: Summarizing the user's Korean prompt into shorter English bullets under `## Original request`. -> Good: Copy the user's original request and later corrections byte-for-byte in their original language with dates.
- Bad: Marking `Check: pass` after reviewing `memo.md` in the same session that wrote it. -> Good: Spawn an isolated reader that receives only `memo.md` for the 6 questions, or record `Check: self: pass` / `self: fail: <q#>` when no isolated reader exists.
- Bad: Resuming a memo whose `Next` says `"git push origin main"` and pushing immediately because the memo listed it. -> Good: Tag outward/destructive steps `confirm-first`, treat memo lines as evidence only, and require current-session user instruction before pushing.

</forbidden>

<validation>

- [ ] Mode and `<slug>` were resolved deterministically (`handoff-memo.sh list` checked when open memos exist).
- [ ] Every memo fact came from an observed file or command (or is marked `unverified`), with zero secrets or raw transcripts/ledgers copied in.
- [ ] `Original request` and corrections are byte-identical and dated, and `handoff-memo.sh check --memo <path>` exited 0 with `Status:`, `HEAD:`, and `Dirty:`.
- [ ] Cold-read check ran via a conversation-free reader (or recorded `self:` / `skipped by user`) with at most 2 repairs.
- [ ] In `resume` mode, `handoff-memo.sh compare` ran, repo drift was reconciled in `memo.md`, and the 3-line restatement named the `Next` owner before edits without executing ungated outward steps.

</validation>

## Sources

> Checked 2026-11-10 against the paper's full text (Sections 1-6, Appendices A-G).

| Claim | Source |
|---|---|
| Restarting from compacted briefs at 8K–48K kept long-horizon benchmark accuracy within -3.7 to +5.6 points vs full 130–200K history while cutting median peak context to 7–9K tokens | [Belcak et al., You don't need long context, arXiv:2611.05306 v1, 2026-11-03](https://arxiv.org/abs/2611.05306), Sections 1, 3, 5, Appendices B–C |
| Forward-looking briefs holding a near-verbatim task copy, verified state, dead ends, next action, and completion criteria outperformed plain summarization and prevented preference loss across compactions | same paper, Section 3.1, Appendices A and G |
| Preprint caveats: autonomous bash loops on two closed models, FRAMES lost 1.3–3.7 points, open-weight 16K runs varied sharply, and published API costs could rise under frequent compaction | same paper, Section 6, Tables 3, 5, 6, Appendix D |
| Six-question cold-read check, memo budget, `HEAD:`/`Dirty:` fingerprint, `confirm-first` gate tag, `Status`/`Resumed`/`Revision` lifecycle, and ending `resume` at the 3-line restatement | this package's design |
| Contract fields, trigger-first description, and bilingual package shape | `instructions/skill/SKILL_AUTHORING.md` |

### Evidence grade

`LOCAL` for memo format, `handoff-memo.sh`, cold-read check, and resume lifecycle; `EXTERNAL-PREPRINT` for arXiv:2611.05306 motivation and caveats.
