
<skill id="git">

<purpose>
Git is the safety net. Every commit is a checkpoint you can return to.
Atomic commits, descriptive messages, feature branches for tier 2+.
Release gates, tagging, and the pre-ship chain live in skills/ship, not here.
Reference on demand: skills/build/reference/git-research.md.
</purpose>

<core_principles>
1. ATOMIC COMMITS: One logical change per commit. Never mix feature + refactor + fix.
2. CONVENTIONAL FORMAT: {type}({scope}): {description} - feat, fix, refactor, docs, test, chore
3. IMPERATIVE MOOD: "add feature" not "added feature" or "adding feature"
4. BRANCH PER FEATURE: Tier 2+ work gets feature/{name} or fix/{name} branch
5. COMMIT OFTEN: Every working state gets a commit. Max 30 min between commits.
</core_principles>

<workflow>
1. **Preflight**: `git status`; dirty at task start means stop and commit, stash, or
   discard first. Tier 2+: confirm you are NOT on main; `git checkout -b {type}/{name}`.
2. **Snapshot**: record HEAD (`git rev-parse HEAD`) to AgentDB before work, so a
   rollback target always exists.
3. **Commit**: stage specific files only, never `git add -A` / `git add .`. Message in
   conventional format, imperative mood. Forbidden: wip, update, misc, auto commit,
   Co-Authored-By, "Generated with". Never `--no-verify`; fix the gate (machine-only
   carve-outs are documented in CLAUDE.md <hook_carve_outs>).
4. **Scope check**: `git diff --stat {base}..HEAD` touches only contracted files;
   `git diff HEAD~1 | grep -i "key\|token\|secret\|password"` comes back clean.
5. **Push**: feature branches push freely after gates pass. main/master requires
   explicit user say-so. Releases (validate, review, tag) go through skills/ship.
</workflow>

<branch_strategy>
- main: always deployable. Never commit directly for tier 2+.
- feature/{name} new functionality · fix/{name} bug fixes · refactor/{name} restructuring.

Profile-gated workflow:
  local:             direct to main OK, branches optional
  github:            feature branches for tier 2+, PRs optional
  github-oss:        feature branches always, PRs REQUIRED before merge
  github-production: feature branches always, PRs + review REQUIRED
</branch_strategy>

<recovery>
- Committed too much / wrong message: `git commit --amend` (only if unpushed).
- Undo a pushed commit: `git revert {sha}`, never rewrite shared history.
- Lost work: `git reflog` finds orphaned commits; `git stash list` finds parked state.
- Wrong branch: `git cherry-pick {sha}` onto the right one, then revert/reset the stray.
- Force push: never bare `--force`; `--force-with-lease` only, never on shared branches.
- Mid-rebase/merge disaster: `git rebase --abort` / `git merge --abort` beats improvising.
</recovery>

<anti_patterns>
- Committing to main directly for multi-file changes
- "WIP" commits that never get squashed
- Mixing unrelated changes in one commit
- Force pushing to shared branches
- AI tool attribution in commit messages (Co-Authored-By, "Generated with", etc.)
- git add -A / git add . (catches unintended files)
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"git","commits":N,"atomic":true,"convention":"pass"}'
</on_complete>

</skill>
