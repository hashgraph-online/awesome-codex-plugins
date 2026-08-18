---
name: audit-agent-onboarding
description: Use to lint a repo's agent onboarding files (AGENTS.md, CLAUDE.md, .claude/rules/*.md) for bloat, contradictions, duplication, stale or vague commands, missing sections, leakage, and secrets - or with --stats to view compression receipts. Read-only; reports findings and hands fixes to update-agent-onboarding.
---

# Auditing agent onboarding files

Static + cross-reference linter for instruction-file smells. **Read-only:** this
skill never writes files. It produces a findings report; applying fixes is
`update-agent-onboarding`'s job (content) or the user's (structure).

**Announce at start:** "Using audit-agent-onboarding to lint the onboarding files."

**Usage:** `audit-agent-onboarding [--stats]`

## `--stats`: compression receipts
Read `.aiboarding/state.json:receipts` and render a table: file, level, bytes and
lines before/after, percent saved, measured-at. Label token figures approximate
when the receipt does (they are byte/4 estimates unless a real tokenizer produced
them). Since instruction files load every session, per-session savings compound  - 
present "per-session saved × sessions" only as a clearly labeled estimate. Then stop.

## Linters
Run every check against `AGENTS.md`, `CLAUDE.md`, and any `.claude/rules/*.md`;
tag each finding **FAIL** (breaks agents or leaks something) / **WARN** (costs
quality or tokens) / **INFO** (improvement candidate).

1. **Size budget** - run `.aiboarding/tools/check-size-budget AGENTS.md` (plugin
   `templates/tools/` fallback if not installed). Its WARN/FAIL map directly.
2. **Codex-cap chain** - for monorepos, sum the byte sizes of every nested
   `AGENTS.md` on a leaf-to-root chain; a chain projected over 32768 bytes is a
   FAIL (Codex truncates silently at `project_doc_max_bytes`).
3. **Duplication** - CLAUDE.md restating imported `AGENTS.md` content (imports
   expand at launch; duplication doubles token cost). Sections restating the
   README near-verbatim: WARN, suggest the doc link instead.
4. **Contradictions** - conflicting instructions within or across files (e.g. two
   different test commands, contradictory guardrails). FAIL.
5. **Stale commands** - extract every backticked command; verify each resolves
   against package scripts, Makefile/justfile targets, CI workflows, or a binary
   on PATH. Unresolvable: FAIL with the source line.
6. **Vague commands** - imperative instructions without an executable invocation
   ("run the tests" with no command). WARN.
7. **Missing sections** - no `Agent Guardrails` or no `Verification Before
   Completion` content: WARN (these are the sections that prevent repeated agent
   mistakes).
8. **Skill leakage** - long procedural walkthroughs (roughly >15 lines of
   numbered steps for one task) that belong in a skill, not always-loaded
   context. INFO, name the candidate skill.
9. **Lint leakage** - formatting/style rules that belong in linter or formatter
   config, not prose. INFO.
10. **Rules extraction candidates** - sections both long and domain-scoped
    (testing minutiae, one subsystem's details) that fit `.claude/rules/<topic>.md`
    with a `paths:` scope, or a nested `AGENTS.md` for cross-agent visibility.
    INFO. Note the asymmetry honestly: `.claude/rules/` is Claude-only.
11. **Unsafe content** - secrets or credentials (key-shaped strings, `-----BEGIN`,
    bearer tokens, connection strings with passwords): FAIL, name the line, do not
    quote the secret itself. Destructive commands (`rm -rf`, `DROP TABLE`, force
    pushes) presented without confirmation framing: WARN.
12. **Wrapper integrity** - `CLAUDE.md` missing the `@AGENTS.md` line, or
    aiboarding marker fences unbalanced: FAIL.

## Report
Output findings ordered FAIL → WARN → INFO, each with file, location, one-line
rationale, and a concrete suggested fix. End with the one-line verdict and the
handoff: content fixes → offer to run `update-agent-onboarding` (its approval gate
still applies); compression fixes → `compress-onboarding`. Suggestions are never
auto-applied.
