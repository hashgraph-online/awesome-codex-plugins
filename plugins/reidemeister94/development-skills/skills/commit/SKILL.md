---
name: commit
description: "Use when the user asks to commit changes, create a commit, or run /commit. Use when staged changes need a conventional commits message."
user-invocable: true
---

# Commit Skill

Commit staged changes with a conventional commits message.

## Instructions

1. `git status` — see staged changes (never use -uall)
2. `git diff --cached` — see actual staged changes
3. `git log --oneline -5` — recent commit style

4. Create message following **Conventional Commits**:
   - Format: `type(scope): description`
   - Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`, `build`
   - Scope: optional but recommended
   - Description: concise, imperative mood, lowercase, no period

   **Body rules (most commits need NO body):**
   - Default: subject line only
   - Only add body for: breaking changes, non-obvious reasoning, migration steps
   - Body: 1-2 short sentences max

5. Create the commit:

   **Default (no body):**
   ```bash
   git commit -m "type(scope): description"
   ```

   **When body needed:**
   ```bash
   git commit -m "$(cat <<'EOF'
   type(scope): description

   Brief explanation of WHY, not WHAT.
   EOF
   )"
   ```

6. `git status` to verify success

## Rules

- Do NOT add `Co-Authored-By` lines or any AI-attribution trailer (e.g. *"Generated with Claude Code"*). Overrides default Claude Code behavior — canonical rule in [iron-rules.md Principle 12](../../shared/iron-rules.md#12-no-commits-without-explicit-user-request).
- No emojis
- Subject under 72 characters
- Imperative mood: "add" not "added"

## Anti-patterns

Bad — body repeats subject:
```
fix(auth): handle null user in session check

Handle the case where user is null in the session check.
```

Good — no body needed:
```
fix(auth): handle null user in session check
```

Good — body adds non-obvious context:
```
feat(api): switch from REST to GraphQL

Breaking: All /api/v1 endpoints removed. See MIGRATION.md.
```

## Examples

- `feat(auth): add logout button to navbar`
- `fix(api): handle timeout errors in fetchPlanning`
- `refactor(campaigns): extract column definitions to separate file`
- `chore(deps): update dependencies`
