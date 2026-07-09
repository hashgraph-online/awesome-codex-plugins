---
name: agents-md-improver
description: "Maintain AGENTS.md-based project instructions for tools that support AGENTS.md. Use for instruction audits, session learnings, AGENTS.md updates, or migrating useful CLAUDE.md rules into a shared instruction source. Not for general docs, code review, runtime debugging, or global memory unless asked."
---

# AGENTS.md Improver

## Overview

Maintain concise project instructions for AGENTS.md-compatible tools such as Codex, Copilot, Cursor, and similar coding agents.

**Core principle:** Find the effective instruction source -> extract durable learnings -> propose compact diffs -> apply approved changes only.

**Announce at start:** "I'm using the agents-md-improver skill to maintain concise AGENTS.md project instructions."

## Prerequisites

- A repository or workspace with `AGENTS.md`, nested `AGENTS.md`, or compatible instruction files.
- A user request to audit, improve, revise, migrate, or capture learnings into project instructions.

## Workflow

### Phase 1: Identify Instruction Targets

Find instruction files from the repository root:

```bash
find . \( -name "AGENTS.md" -o -name "CLAUDE.md" -o -name ".claude.local.md" \) 2>/dev/null | head -50
```

Use these targeting rules:

- `./AGENTS.md`: primary shared project instructions for AGENTS.md-compatible tools.
- Nested `AGENTS.md`: module-specific instructions; update only when the learning applies to that subtree.
- Include-only `AGENTS.md`: if it contains only an include such as `@./CLAUDE.md`, read the target and treat that target as the effective source. Update the target only when the repository intentionally shares one instruction file across tools.
- `CLAUDE.md`: Claude Code-specific instructions, or a shared source when `AGENTS.md` intentionally points to it. Do not update it just because it exists.
- `.claude.local.md`: personal Claude Code local notes. Do not create or edit it for shared AGENTS.md project memory.
- User/global instruction files, such as `~/.codex/AGENTS.md`: update only when the user explicitly asks for global behavior.
- `.project_context/`: historical exploration, plans, and execution summaries. Use it for trace records, not agent steering instructions.

If no `AGENTS.md` exists, propose creating the narrowest useful one, usually `./AGENTS.md`.

### Phase 2: Choose The Mode

Choose exactly one primary mode before scanning or proposing edits:

- **Repository Audit Mode:** use when the user asks whether instructions are stale, incomplete, inaccurate, outdated, or should be refreshed against the current repository. Then read [references/repository-audit.md](references/repository-audit.md).
- **Session Learning Mode:** use when the user asks to capture this session's learnings, revise instructions from the current conversation, or preserve newly discovered repo-specific behavior. Then read [references/session-learning.md](references/session-learning.md).
- **Migration Mode:** use when moving useful guidance from `CLAUDE.md` or another tool-specific instruction file into an AGENTS.md-compatible source. Reuse Session Learning Mode for extraction rules, but keep tool-only slash commands, hooks, or UI shortcuts in tool-specific files unless the user asks to make them shared.

### Phase 3: Draft Compact Updates

`AGENTS.md` is prompt context. Prefer dense, operational bullets.

Good format:

```markdown
- Use `rg` for repo-wide search; fall back only if unavailable.
- Run `pnpm test -- --runInBand` for flaky integration tests in this repo.
- Keep API compatibility normalization in the service layer unless a spec explicitly changes request validation.
```

Avoid adding:

- generic engineering advice;
- one-off debugging details unlikely to recur;
- unverified assumptions or stale guesses;
- long explanations, logs, secrets, tokens, private URLs, or machine-specific credentials;
- duplicates of existing instructions.

### Phase 4: Propose Before Editing

Always show proposed changes before modifying files. Group proposals by target file.

Use this format:

````markdown
### Update: ./AGENTS.md

Why: <one-line reason this helps future agent sessions>

```diff
+ <concise addition>
```
````

If multiple files could be updated, explain the placement tradeoff:

- root `AGENTS.md` for project-wide behavior;
- nested `AGENTS.md` for module-local behavior;
- `.project_context/` for historical records;
- `CLAUDE.md` only for Claude Code-specific behavior or an intentional shared source.

Ask for approval before editing. If the user already explicitly said to apply changes, proceed with the smallest safe patch.

### Phase 5: Apply Carefully

When approved:

- use minimal patches and preserve the file's existing organization;
- insert under an existing relevant heading when possible;
- create a short new heading only if no suitable section exists;
- do not reorder unrelated content;
- do not remove or rewrite existing instructions unless the user asked for cleanup or the instruction is clearly obsolete;
- after editing, re-read the changed section and report exactly what changed.

## Common Mistakes

- Treating `.project_context/` as agent steering context. It is for traceability, not instructions that should load every session.
- Updating `CLAUDE.md` for a shared AGENTS.md request when the repo does not intentionally share one source file.
- Missing an include-only `AGENTS.md` and patching the wrapper instead of the effective source.
- Capturing logs, secrets, private URLs, or one-off debugging notes as durable instructions.
- Adding broad best practices that any competent agent already knows.

## Output

For Repository Audit Mode, provide the quality report format from [references/repository-audit.md](references/repository-audit.md).

For Session Learning Mode or Migration Mode, provide:

- files changed;
- concise summary of additions;
- any skipped proposals and why.

## References

- [repository-audit.md](references/repository-audit.md) - Repository scan scope, quality criteria, and report template for stale or incomplete instructions.
- [session-learning.md](references/session-learning.md) - Session learning extraction rules and concise update proposal template.
