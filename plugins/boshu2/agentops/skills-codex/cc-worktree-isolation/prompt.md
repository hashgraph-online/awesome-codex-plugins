# Codex Execution Profile — cc-worktree-isolation

Read the sibling `../SKILL.md` first — it is the authoritative methodology (phases, constraints, rubric, troubleshooting). This profile translates it to the Codex runtime, where the Claude-native levers (`claude --worktree`, `isolation: worktree` agent frontmatter, the `EnterWorktree`/`ExitWorktree` tools, `WorktreeCreate`/`WorktreeRemove` hooks) do **not** exist. On Codex, isolation is done with plain `git worktree` plus disciplined file ownership.

## Steps

1. **Decide the shape.** Confirm work is actually parallel and contended (multiple writers, one repo). If it is single-agent sequential work, stop — use a plain branch, no worktrees.

2. **Assign disjoint file ownership BEFORE spawning.** List every planned writer and the exact file set each owns. If two writers share any file, merge them into one worker. Do not proceed until every writer has a non-overlapping file set. This is the load-bearing step — worktrees only prevent *accidental* collision, not legitimate co-editing.

3. **Choose the base ref deliberately.** Decide where each worktree branches from: `origin/<default-branch>` (clean baseline — workers will NOT see uncommitted local changes) vs. current `HEAD` (carries local changes forward). Pick on purpose; do not default blindly.

4. **Create one worktree per writer.** For each worker: `git worktree add <path> -b <branch> <base-ref>` (e.g. `git worktree add ../wt-ag-123 -b work/ag-123 origin/main`). Use a stable naming scheme tied to the unit of work (bead/issue id).

5. **(Monorepo) Restrict each checkout to the relevant subtree.** In each worktree enable sparse checkout so a worker can only touch its subtree: `git -C <path> sparse-checkout init --cone && git -C <path> sparse-checkout set <subtree>...`. This makes touching unrelated code structurally impossible and speeds checkout.

6. **(Optional) Write an audit trail.** Append create/remove events to `.claude/worktree-audit.log` (or a repo-local log) with timestamp + path, so cleanup can be verified later.

7. **Run + coordinate.** Dispatch each worker into its own worktree path. If swarm members might still converge on a shared path, layer agent-mail file reservations on top — worktrees stop the filesystem clobber, reservations prevent two workers *choosing* the same file.

8. **Commit inside each worktree.** Each worker commits its own branch in its own working directory. Verify no two workers report the same branch.

9. **Merge back in a deterministic order.** Merge worker branches into the canonical branch in a fixed order (e.g. dependency order). Any merge conflict here is a Phase-2 ownership failure — note it for next time.

10. **Clean up and verify zero orphans.** For each worktree: ensure work is committed/merged, then `git worktree remove <path> && git branch -d <branch>`. Confirm with `git worktree list` (only the canonical tree remains) and `git branch` (no orphaned worker branches). Refuse to force-remove a worktree with uncommitted or unmerged work without explicit operator confirmation.

## Guardrails

- **One writer per file, always.** Isolation defers a conflict to merge time; it does not authorize two agents to co-edit one file. Enforce disjoint ownership upfront.
- **Never use `claude -p` (or `--print`) for workers.** This is operator/flywheel infrastructure — `claude -p` bills the API per token, not the Max subscription, and is banned for Claude workers. On Codex use `codex exec`; for Claude turns use NTM panes or spawned subagents on the subscription.
- **Base ref is a decision.** `fresh`/`origin` workers will not see uncommitted local changes — push first or branch from HEAD if they need them.
- **Cleanup is not automatic.** Do not delete a worktree or branch that still holds uncommitted files or unmerged commits without confirming the work is safe. Force-discard only after operator sign-off.
- **Read-only by default for anything irreversible.** Propose merge/remove plans; do not destroy branches or worktrees with real work silently.
- **Stay in-repo.** Only operate on worktrees registered to the current repo (`git worktree list`); do not enter or remove unrelated trees.

## See Also

- `../SKILL.md` — full methodology, critical constraints, quality rubric, examples, troubleshooting table.
- `cc-hooks` — governance-hook authoring (Claude runtime).
- `agent-mail` — file reservations that complement worktrees for swarm coordination.
- `ntm` / `vibing-with-ntm` — spawning the parallel workers that consume this isolation.
