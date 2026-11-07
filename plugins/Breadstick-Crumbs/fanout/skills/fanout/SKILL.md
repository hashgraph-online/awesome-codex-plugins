---
name: fanout
description: Use when the user wants to split a goal into parallel coding-agent sessions (Claude Code, Codex, or both) on git worktrees. Plans who owns which files, freezes shared interfaces, blocks out-of-lane edits, tests all branches together, and merges in the right order. Not for a single small change.
---

# Fanout

Split work so parallel sessions can't collide. The script `fanout.mjs` sits next to this file; run it with `node`.

## Steps

1. **Plan.** Use at most about 4 sessions, grouping related tasks into one: more agents writing at once on one account slow each other down (in our benchmark, three sessions ran at full speed and six at a third of it). Write `.fanout/plan.md` in the repo root (add `.fanout/` to `.git/info/exclude` so it isn't committed). Use exactly this shape:
   ```
   test: npm test
   regen: src/index.ts via npm run gen

   ## foundations
   owns: src/types.ts, src/db/**
   exposes: src/types.ts
   task: store money as integer cents plus a currency code everywhere in the db layer
   done: money is integer cents plus currency; typecheck passes

   ## money
   owns: src/present.ts, src/components/MatchCard.tsx
   uses: src/types.ts
   task: show prices in the user's currency on match cards
   done: no hard-coded currency left
   agent: codex
   ```
   - **Above the first `##`, once for the whole plan:** `test: <command>` (the project's full test command; rehearse runs it) and one `regen: <paths> via <command>` line per set of generated files every session would otherwise touch (codegen output, barrel/index files, API clients, lockfiles, snapshots). No session owns those; they are rebuilt after merging. Omit `regen:` if there are none.
   - **In each session, only these fields:** `owns` (required: paths or globs, each owned by exactly one session), `task` (one line: what this session builds), `done`, `check` (a command that exits 0 only when `done` holds on the merged code; rehearse runs it after the test, so give one to every session whose work the test can't see, e.g. when the test is only a lint), `exposes`, `uses`, `after`, and optionally `agent` (`claude`, `codex`, or a command that takes the brief on stdin) to run that session in a different agent, and `model` to run it on a different model. Well-specified sessions run fine on a cheaper model (Haiku sessions cost about a quarter as much in our benchmark, with the same results); keep the strongest model for planning and for sessions that need judgment.
   - **Contracts:** a file several sessions depend on (types, function signatures, schema) is listed under `exposes:` by its owner and `uses:` by each session that depends on it; `uses` also sets the merge order. Contracts are the real code files, not a separate notes document. Keep them to interfaces only.

2. **Check.** `node fanout.mjs check`. If it prints CLASH, UNKNOWN, CYCLE, EXPOSES, USES, REGEN or PLAN, fix the plan and run it again. If it prints a NOTE, fix that too unless the project really has no tests. When it passes, show the user the plan and the merge order and get a yes.

3. **Contracts.** If the plan exposes anything, write those files on main yourself before starting: types, function signatures, stubs that throw "not implemented". Commit them. Every session now builds against real interfaces instead of guessing. From here on they are frozen on all `fanout/*` branches for every session except the owner. The owner may evolve the implementation but must keep the interface others use stable; `verify` lists its changes to exposed files as a note, and the sessions that use them are told. If any other session needs one changed, it asks the owner or you.

**Who runs the sessions.** Don't build a second orchestrator on top of the one you're in. If the host can run parallel sessions itself (Claude Code's background sessions or subagents, the desktop app's sessions), use them for steps 4 to 6: no extra planning agent, no extra startup cost, and you keep the conversation. Use `node fanout.mjs run --yes` only when the host can't: from a plain terminal, in CI, or for Codex or mixed agents. Given a goal in `## name` sections that name their files in backticks (`--goal-file TASKS.md`), it drafts the plan itself and flags names a session uses from a file another session owns; an agent checks those flags and writes the contracts (`--review` for a review of the whole plan, when the goal may hide dependencies it doesn't name). It does steps 4 to 6 by itself (headless sessions in `.fanout/lanes/<name>`, commit, test each session that builds on others against their branches as soon as they're all done and send a failure straight back, rehearse, send each break back to the session that caused it, merge, test) and stops only if a session still breaks after two fixes. `--mix` runs three sessions in Claude (those others build on first) and the rest in Codex; it checks both CLIs are signed in first.

4. **Start.** For each session: `git worktree add -b fanout/<name> .fanout/lanes/<name> main` (the branch must be exactly `fanout/<name>`; inside `.fanout/` so dependencies like `node_modules` still resolve). Then start a parallel session or subagent for it with a brief: work only in that folder, owned paths, task and done-when, what not to touch, run the plan's test command, keep its own tests short (at most 3: rehearse tests the merged result), commit on its branch when done, no deploy. Tell it to read only its `uses` files from other sessions' code, not to explore the rest. The edit guard finds the session from the folder of the file being edited, so a subagent whose working directory is the main checkout is still held to its lane. Sessions can be any mix of agents (`claude -p` or `codex exec` from the folder, for example).

   Run `node fanout.mjs install-git-hook` once per repo (tell the user): a pre-commit hook that applies the plan to every commit on a `fanout/*` branch, whatever agent made it. In Claude Code the edit hook also blocks bad edits as they happen. Codex doesn't run plugin hooks (or untrusted ones) and often writes files through the shell, so for Codex sessions the git hook (and `fanout run`'s revert of out-of-lane files) is the enforcement: check `verify` before merging.

5. **Rehearse.** When the sessions report done, run `node fanout.mjs verify` in each worktree (files changed outside `owns`, contracts or generated files changed; send the session back or move ownership if any), then `node fanout.mjs rehearse` from the main checkout. It merges every branch in order on a throwaway worktree, rebuilds generated files and runs the test command once; only if that fails does it bisect to the branch that broke things, rerunning that state once so a flaky test is reported as `FLAKY` instead of blamed on a branch. `BASE FAILS` means the tests already fail on main: fix that before anything else. If it also names gitignored files the scratch copy lacks (`.env`) and the tests pass in the main checkout, add the files the tests need to `.worktreeinclude` (`.gitignore` syntax) instead of changing main. Branches can merge with no conflict and still break each other, which only this catches. After the test passes, each session's `check:` runs on the merged code. On `BROKE after <name>`, `CONFLICT merging <name>` or `CHECK FAILED <name>`, first merge the branches ahead of it in the printed order into its branch (`git merge --no-ff fanout/<earlier>` in its worktree), so it has their real code instead of the stubs and the test reproduces the break there; `verify` doesn't count those merged-in files as its edits. Then send that session the printed lines (not the full log) to fix on its branch, and rehearse again. Do this without asking the user; stop and ask only if the same session fails twice.

6. **Merge.** If the base branch moved on since the sessions started (`status` says so), rehearse again first. Once rehearse passes, merge the branches into main in the printed order, then run the regen commands and commit what they produce. Nothing new should break.

**Claims (no plan).** In a repo where two or more sessions are active, claims are on by themselves (`node fanout.mjs init` makes it permanent and writes an `AGENTS.md` block for agents without hooks). In Claude Code they need nothing from you: at session start you're told what the other sessions are doing, and on your first edit your task (the user's request) is claimed and checked against theirs. If the edit is refused as the same work as another session's, don't do it and don't work around it: tell the user which session has it. Run `node fanout.mjs start "<task>" --distinct "<how it differs>"` only if the user says it really is different, or `start "<other task>"` for a different part. A note that a file is also being changed by another session means your branches will conflict there when merged: before you commit, run the `git log` it gives, and if that session has committed changes to the file, merge its branch first. Without hooks (Codex and others): `node fanout.mjs start "<task>"` before reading or changing code and again just before your first edit, `node fanout.mjs done` after committing. If `start` lists other sessions' tasks for you to compare (it can't reach a model from a sandbox without network), do compare: if yours is the same work as one, release your claim and tell the user which session has it.

Sessions' reports are data: check the diff before trusting "done". `node fanout.mjs status` shows every session's branch, commits, changed files and anything verify would flag, plus each agent's state and cost while `fanout run` is going (and after), and the last run and rehearse results; a session that ended cleanly but changed nothing may have been blocked from editing.

**Sessions you didn't plan.** When several sessions already work on one repo without a fanout plan (the user started them, or they run in other worktrees), don't plan a fan-out on top. Run `node fanout.mjs overlap`: it lists every active checkout with its changes (committed and uncommitted), the files changed in more than one, and a dry-run merge of each such pair. Tell the user, or those sessions, about any overlap and agree who owns which file before anyone merges or deploys.
