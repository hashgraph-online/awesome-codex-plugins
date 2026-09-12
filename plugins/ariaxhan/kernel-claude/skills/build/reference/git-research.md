# Git Workflow Reference: Research & Best Practices

Reference for git strategy, commit practices, and agent-specific git patterns.
Read on demand. Not auto-loaded.

## Sources

Atlassian Git Tutorials, GitFlow, GitHub Flow, GitClear 211M line analysis (2026),
GitHub Agentic Workflows (Feb 13, 2026), GitHub Copilot CLI GA (Feb 25, 2026),
Spec-Driven Development (Sep 2025), git-staabm (Feb 7, 2026), Graphite stacked PRs.

---

## Atomic Commits: The Foundation

An atomic commit is a single, self-contained logical change. It can be
applied or reverted without side effects.

GitClear (211M lines, 2026): AI-assisted development linked to:
- **4x growth in code cloning** - copy/paste exceeds "moved" code for first time.
- **41% increase in code churn** in AI-heavy teams.
- **48% increase in duplication** as models fail to modularize.
- BUT: Power users produce **4-10x more output** (causation unclear).
- Negative side effects **9x more likely** among heavy AI users.

Rules:
- One logical change per commit. Feature + refactor = two commits.
- Each commit compiles and passes tests independently.
- If you can't describe the commit in one line, it's too large.
- Format: {type}({scope}): {description} in imperative mood.
  Types: feat, fix, refactor, test, docs, chore, perf, ci.

---

## Branching Strategy

For KERNEL: feature branches per contract.

- main: always deployable. Never commit directly for tier 2+.
- {type}/{name}: feature/auth-middleware, fix/query-timeout, refactor/api-layer.
- Create branch before implementation. Push before session end.
- Delete branch after merge.

git checkout -b {type}/{name}
# ... work ...
git push origin {type}/{name}
# ... merge via PR or direct ...
git branch -d {type}/{name}

---

## Git Bisect: The Debugging Power Tool

When a regression exists (worked before, broken now), bisect finds the
exact commit in O(log n) steps.

git bisect start
git bisect bad                    # current (broken) commit
git bisect good {known_good_hash} # last known working commit
# git checks out midpoint; you test and mark good/bad
# repeat until culprit found
git bisect reset

For 1000 commits: ~10 tests instead of 1000. The debug skill's binary
search methodology applied to git history.

---

## Merge Conflict Resolution

- Never auto-resolve silently. Document in AgentDB and surface to user.
- For agent work: if conflict arises, checkpoint and stop. Orchestrator decides.
- Prefer rebase for linear history on feature branches.
- Prefer merge commits for main (preserves feature branch history).
- After resolving: run full test suite before committing the merge.

---

## Stash Protocol

- Stash before risky operations: git stash push -m "before {description}"
- Stash before switching branches with uncommitted work.
- Always name stashes (the default message is useless later).
- Check stash list periodically: git stash list. Clean up old stashes.

---

## Git Worktrees for Parallel AI Agents (2026)

Git worktrees are now essential for running multiple AI coding agents:
- Two agents editing the same working directory corrupts state.
- Each worktree is an isolated checkout sharing the same .git history.
- Enables 5-10+ agents working on different features simultaneously.

Commands:
```bash
git worktree add ../project-feature-a -b feature/auth
git worktree list
git worktree remove ../project-feature-a
```

Limitations:
- Disk space: 20-min session with 2GB codebase can use 9.82GB.
- Code is isolated but runtime (ports, databases) is shared.
- Human review becomes the bottleneck.

Tooling: Superset IDE (Mar 2026), Emdash, @johnlindquist/worktree CLI.

---

## Stacked PRs (2026)

Breaking large features into sequential, dependent PRs:
- Each PR targets the previous branch, not main.
- Merge happens bottom-to-top.
- Research: PRs with 200-400 lines have **40% fewer defects**.
- Small PRs (<200 lines) approved **3x faster**.

Critical constraint: Cannot use "squash and merge" on intermediate PRs.
Tools: Graphite, git-grok, Aviator, stack-pr.

---

## GitHub Agentic Workflows (Feb 13, 2026)

Markdown-based workflow authoring for AI-powered automation:
- Continuous triage (auto-label/route issues)
- Continuous documentation (align READMEs with code)
- Continuous test improvement
- CI failure analysis

Security model: Read-only by default, sandboxed execution, network isolation.
Critical: "Pull requests are never merged automatically; humans must review."

---

## Agent-Specific Git Patterns

Surgeon agent:
- git add {specific files} not git add -A (prevents accidental inclusions).
- Commit after each working state, not at the end.
- Include contract ID in commit body for traceability.
- Push to remote before checkpoint.
- **2026**: Use worktree for parallel work with other agents.

Adversary agent:
- git diff {base_commit}..HEAD --name-only to verify scope compliance.
- git log --oneline -{N} to verify commit granularity.

Scout agent:
- git log --format='%H' -- {file} | wc -l for change frequency.
- git shortlog -sn for contributor map.

Handoff:
- Push all branches before generating handoff.
- Document branch name, uncommitted changes, stash contents.

---

## KERNEL Integration

- Every contract includes BRANCH and BASE_COMMIT for traceability.
- Validator agent checks commit format before allowing merge.
- No AI attribution: never Co-Authored-By, never tool signatures.
- Tag milestones: git tag -a v{X} -m "{description}".

---

## Agentic Git Discipline (moved from SKILL.md 2026-05-28)

Agentic workflows introduce new git failure modes. Mitigate them:

**Pre-task snapshot**: Before any agent starts work, record the HEAD commit SHA in AgentDB.
If the task needs rollback, you know exactly where to return.

```bash
# Record before agent work
git rev-parse HEAD  # save this to AgentDB

# Rollback if needed
git reset --hard <saved-sha>
```

**Dirty-state check**: If `git status` shows uncommitted changes at task start, stop.
Prior agent left state. Commit, stash, or discard before proceeding — never silently overwrite.

**Branch-per-agent for tier 2+**: Each agent working on distinct features gets its own
branch. Merging branches (not rebasing) preserves intent and makes conflicts explicit.

**Squash before merge**: Agent commits tend to be fine-grained and mechanical.
Squash to one meaningful commit per feature before merging to main. Message should
describe the feature, not the implementation steps.

**No force-push to shared branches**: An agent force-pushing destroys another agent's
or human's commits silently. Use `--force-with-lease` only, never bare `--force`.

---

## Diff Sizing for AI Code Review (moved from SKILL.md 2026-05-28)

<!-- Sources: https://collinwilkins.com/articles/ai-code-review-best-practices-approaches-tools.html (2026-04-04),
     https://www.codeant.ai/blogs/good-code-review-practices-guide, https://codeintelligently.com/blog/ai-code-quality-guide-2026 (2026-05-10) -->

Diff size is the single biggest lever for AI code review quality:

- **50-200 lines**: optimal — AI catches logic errors, security issues, edge cases
- **200-500 lines**: acceptable — AI catches obvious issues, misses subtle interactions
- **500+ lines**: degraded — AI overwhelmed, misses important context, feedback generic
- **1000+ lines**: near-useless — context saturation, review becomes superficial

Rule: if a diff exceeds 500 lines, split the PR before requesting AI review.

**Team-level PR size target**: Set P50 PR size < 300 LOC as a team metric (median PR, not max).
Teams that track this and enforce it see 40-60% reduction in review time.
Track with: `git log --oneline -20 --shortstat | grep -E "changed"`.
The 500-line hard cap is the ceiling; 300-line P50 is the steady-state goal.

**AI review before human review**: Run AI review (~90 seconds) before requesting human review.
Developer fixes cheap issues first, humans see a cleaner diff and focus on intent and design.
Sequence: AI review → fix → human review. Not parallel.

---

## AI PR Transparency (moved from SKILL.md 2026-05-28)

<!-- Source: https://javaworldmag.com/evolving-code-reviews-with-ai-in-2026/ (2026-04-14) -->

When merging AI-assisted work, PR descriptions should answer three questions:

1. **What was the AI's role?** (generated scaffold, wrote tests, suggested approach, full implementation)
2. **What prompt or instructions drove it?** (as important as a commit message — reviewers evaluate the generation process, not just the output)
3. **What was the human contribution?** (reviewed, modified, architecture decisions, requirements)

Reviewers then focus on: design decisions, architecture fit, business logic correctness — not line-by-line syntax the AI already handled.

This is not ceremony — it's the minimum for a meaningful review of AI-assisted code. Without it, reviewers are auditing output with no context on how it was generated.

---

## Review Conventions (moved from SKILL.md 2026-05-28)

<!-- Sources: https://stackoverflow.blog/2026/03/26/coding-guidelines-for-ai-agents-and-people-too/,
     https://javaworldmag.com/evolving-code-reviews-with-ai-in-2026/ (2026-04-23) -->

**"Nit:" prefix for optional comments**: Prefix style-only feedback with "Nit:" to signal it's optional.
Prevents authors from treating cosmetic suggestions as blockers.

```
# Required (no prefix)
"Line 24: userId could be null here — add validation before the DB call"

# Optional (Nit prefix)
"Nit: 'x' would be clearer as 'userCount'"
```

Without the prefix, reviewers and authors waste cycles on non-critical changes.

**AI-first review sequence**: AI review catches style/logic issues BEFORE human review.
Sequence: AI review (90s) → author fixes cheap issues → human reviews cleaner diff.
Humans then focus on architecture, business logic, and intent — not nitpicks the AI already caught.
Never parallelize AI + human review: humans see a noisier diff and duplicate AI feedback.

---

## Tiered Review Risk (moved from SKILL.md 2026-05-28)

<!-- Sources: https://www.codeant.ai/blogs/good-code-review-practices-guide, https://codeintelligently.com/blog/ai-code-quality-guide-2026 (2026-05-14) -->

Not all changes warrant the same review depth. Route by tier to capture the 40-60% review time reduction without sacrificing judgment on critical changes:

- **Tier 1 — AI handles completely**: style, formatting, naming, simple logic, boilerplate, test assertions
- **Tier 2 — AI + quick human skim**: error handling, input validation, moderate business logic
- **Tier 3 — human required**: architecture decisions, security-sensitive paths, auth/payments/PII, anything affecting critical systems

The review time savings come from AI absorbing Tier 1 entirely — not from replacing Tier 3 judgment.
Complex architectural decisions and business logic in critical flows always need a human eye.
