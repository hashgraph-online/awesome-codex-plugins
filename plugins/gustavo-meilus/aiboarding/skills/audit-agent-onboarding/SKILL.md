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
present "per-session saved × sessions" only as a clearly labeled estimate. For each
receipt, render optional `high_consequence_regions` evidence as location, category,
outcome (`preserved` or `rewritten`), and explicit opt-in status, without instruction
text. Render an empty array as `none`; when field is absent, render `not recorded`.
Keep existing level, byte, line, date, and token output unchanged. Then stop.

## Evidence-aware audit
Run `.aiboarding/tools/audit-onboarding-evidence <repo-root>` first (fallback:
the plugin's `templates/tools/audit-onboarding-evidence`). Capture its lines and
exit status. Exit `0` means no computed FAIL; `1` means computed validation FAIL;
`2` is an operational error: stop and report tooling failure, never render it as an
audit finding. Do not write onboarding files in either case.

Each finding has independent severity (`FAIL`, `WARN`, `INFO`) and provenance
(`computed`, `inferred`). Preserve validator provenance and render one report
ordered FAIL, WARN, INFO. Never upgrade model judgment to `computed`.

| Category | Evidence |
| --- | --- |
| Local size budget; Codex project-chain budget; wrapper integrity | Computed |
| Stale commands | Mixed: validator only for explicit paths, package scripts, Make/Just targets; infer unresolved context-dependent cases |
| Duplication; contradictions; vague commands; missing sections; skill leakage; lint leakage; rules extraction candidates; unsafe content | Inferred |

Then review inferred categories and unresolved command references across `AGENTS.md`,
`CLAUDE.md`, and `.claude/rules/*.md`:

1. **Duplication** - imported or README content restated meaningfully.
2. **Contradictions** - instructions whose scope or intent conflicts.
3. **Stale commands** - only commands validator cannot prove absent.
4. **Vague commands** - imperative guidance lacking usable invocation.
5. **Missing sections** - absent guardrail or verification guidance, not headings alone.
6. **Skill/lint leakage and rules extraction candidates** - ownership and scope need judgment.
7. **Unsafe content** - secrets and destructive-command framing need context; do not quote secrets.

## Report
Output findings ordered FAIL → WARN → INFO, each with provenance, file, location,
one-line rationale, and concrete fix. Example:

```text
FAIL [computed] wrapper-integrity CLAUDE.md:1 — missing @AGENTS.md import; add it.
WARN [computed] size-budget AGENTS.md:1 — 24001 bytes > budget 24000; compress it.
WARN [inferred] vague-commands AGENTS.md:8 — "run tests" lacks invocation; name command.
```

End with one-line verdict and handoff: content fixes → offer
`update-agent-onboarding` (approval gate applies); compression fixes →
`compress-onboarding`. Suggestions are never auto-applied.
