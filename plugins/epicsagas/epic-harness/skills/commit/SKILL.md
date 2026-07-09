---
name: commit
description: "Conventional Commits 1.0 generator. Stages relevant files, infers type(scope): description, never uses --no-verify."
---

# Commit — Conventional Commits Generator

## When to Trigger
- User wants to commit, save, or check in changes
- User asks to commit after completing a task
- Code changes are ready and user signals completion

## Process

1. **Gather context** — run in parallel:
   - `git status` — see what changed
   - `git diff HEAD` — see the actual diff
   - `git log --oneline -5` — match existing commit style

2. **Determine type**:
   | Type | When |
   |------|------|
   | `feat` | New feature or capability |
   | `fix` | Bug fix |
   | `refactor` | Code change, no behavior change |
   | `docs` | Documentation only |
   | `test` | Adding or correcting tests |
   | `build` | Build system or dependencies |
   | `chore` | Maintenance task |
   | `ci` | CI/CD configuration |
   | `style` | Formatting, whitespace |
   | `perf` | Performance improvement |

3. **Generate message**: `type(scope): description`
   - Lowercase type, optional scope
   - Imperative mood, no period, under 72 chars
   - Breaking changes: append `!` before `:`
   - Body only when diff needs extra context (max 3 bullet points)

4. **Stage and commit**:
   - `git add <specific files>` — prefer explicit files over `git add -A`
   - `git commit -m "type(scope): description"`
   - Execute automatically — no confirmation needed

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "I'll just use a generic message" | Generic messages make git history useless. | Spend 5 seconds analyzing the diff — the type and scope are obvious from the changes. |
| "The user didn't specify a format" | Conventional Commits is the project standard — guard will block non-CC messages anyway. | Always generate CC format. |
| "I'll commit everything together" | Unrelated changes in one commit make bisect and revert impossible. | If changes span multiple concerns, suggest splitting first. |

## Evidence Required

- [ ] `git status` checked before staging
- [ ] Only relevant files staged (not `git add -A` blindly)
- [ ] Message follows `type(scope): description` format
- [ ] Type accurately reflects the change (feat ≠ fix ≠ refactor)

## Red Flags
- Vague messages: "update code", "fix stuff", "changes"
- Wrong type: using `feat` for a bug fix, `fix` for a new feature
- Staging unrelated files
- Using `--no-verify` to bypass hooks
