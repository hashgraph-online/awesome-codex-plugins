---
name: align-docs
description: "Use when user wants project docs (AGENTS.md, .agents/rules, docs/, README) aligned with the codebase, or the agent context compatible with both Claude Code and Codex CLI. Captures session discoveries; --clean consolidates obsolete chronicles/plans into ATLAS.md. Triggers on /align-docs, convert agent context."
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, AskUserQuestion
---

# Align Docs — one canonical agent context

Claude Code, Codex CLI, and every other agent read the same canonical context from the repo, without duplication. Convert structure where missing, capture what the session learned, then reduce every docs/agents file **and project memory** to the most critical, non-trivial **domain · infrastructure · company · project-specific** facts in the fewest words that stay clear. Everything else is noise — removed. The repo is the only context teammates share: anything load-bearing outside it is invisible to them and lost.

Regardless of the project's current status, proceed with the following steps and relentlessly reduce and simplify CLAUDE.md, AGENTS.md, and the additional docs and rules until they converge to the principles and structure expressed below.

## Target architecture

```
repo/
├── CLAUDE.md                  # single line: @AGENTS.md
├── AGENTS.md                  # canonical context, ≤70 lines, references rules by path
├── .agents/rules/             # single source of truth — path-scoped rule files
├── .claude/
│   ├── rules → ../.agents/rules   # symlink; Claude auto-loads
│   └── CLAUDE.md                  # gitignored — personal per-project (Claude)
└── .gitignore                 # ignores .claude/CLAUDE.md and AGENTS.override.md
```

| Agent | Discovery |
|-------|-----------|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` import; `.claude/rules/*.md` auto-loaded recursively (symlinks OK), gated by `paths:` frontmatter |
| Codex CLI | Native `AGENTS.md` walk-up; at most ONE file per directory; precedence `AGENTS.override.md > AGENTS.md`; no imports — agent must `Read` rule files when in scope |

## Step 0 — Root & mode

`root=$(git rev-parse --show-toplevel 2>/dev/null) || root=.` — all paths below resolve under `$root`.
`$ARGUMENTS` contains `--clean` / `clean` → read `references/clean-mode.md` and follow it (runs Steps 1-7, then deep consolidation).
Any free-text beyond the flags is a **project directive** (e.g. *"drop principles X-Y-Z because …"*) — carry it into Step 3.

## Step 1 — Inventory

```bash
ls -la CLAUDE.md AGENTS.md .claude/rules .agents/rules MEMORY.md 2>&1
wc -l AGENTS.md CLAUDE.md 2>&1
grep -nE "\.claude/CLAUDE\.md|AGENTS\.override\.md" .gitignore 2>&1
ls ~/.claude/projects/*/memory/ 2>&1   # pick the dir matching this project
```

Report what exists, what's missing, what's over budget. Then diff docs against disk: structure trees vs `ls`, versions vs manifests, README tables (skills/agents/shared) vs directories, every referenced path exists, links resolve.

## Step 2 — Structure (idempotent)

- **`CLAUDE.md`** — overwrite with exactly one line, no trailing prose: `@AGENTS.md`
- **`.agents/rules/`** — create if missing. One topic per file, descriptive name. Every file starts with scope frontmatter (else it loads into Claude's context every session):

```yaml
---
paths:
  - "src/**"
---
```

- **Symlink** — `mkdir -p .claude; [ -e .claude/rules ] || ln -s ../.agents/rules .claude/rules`; commit it (git stores symlinks natively on Unix).
- **`.gitignore`** — append `.claude/CLAUDE.md` and `AGENTS.override.md` if missing. Tell the user: personal notes → `.claude/CLAUDE.md` (Claude, auto-loaded) or `~/.codex/AGENTS.md` (Codex, user-global); `AGENTS.override.md` *replaces* shared `AGENTS.md` — avoid unless scoped to a subdirectory.

## Step 3 — `AGENTS.md` (≤70 lines)

Prepend `references/agents-template.md` verbatim at the top (replace a similar existing block) — **unless** the block is headed by an `<!-- align-docs:principles-customized … -->` marker line, which makes it authoritative: preserve it, never revert to the template. Then, in this order and nothing else — no section headings or decoration:
- Project scope (1-2 sentences)
- Single fewest-words list of the most critical, non-trivial domain·infra·company·project facts (safety rules, test commands; tables/commands beat prose)
- Rules index table at the bottom — one row per file in `.agents/rules/`: `Rule | Scope (paths:) | Topic`

If it's in a rule file, reference — never duplicate.

**Project directive (Step 0).** Asks to drop/alter/add principles → judge the rationale critically (Principle 0): sound → apply it to the principles block, prepend a `<!-- align-docs:principles-customized: <one-line reason> — see docs/chronicles/NNNN -->` marker line above the block, and record the WHY in a chronicle so later runs preserve it; unsound → push back and ask, don't apply.

## Step 4 — Capture session discoveries

Cold invocation (no prior work this session) → state **"CAPTURE: NONE"**. Else harvest what this session learned that it lacked at the start:

- **Non-inferable only** — domain·infra·company·project-specific, not derivable from the code. No structure/architecture overviews.
- **Idempotent** — write only facts not already on disk.
- Critical always-read fact → `AGENTS.md` line; topic with depth → `.agents/rules/<topic>.md` + index row. **Never memory.**

## Step 5 — Memory sweep

Memory is per-machine: teammates share only the repo, so facts parked there diverge per person and get lost. Read every project-memory file (Claude auto-memory `~/.claude/projects/<project>/memory/`, repo `MEMORY.md` if present):

- Critical, non-trivial domain·infra·company·project fact → move to `AGENTS.md` or `.agents/rules/<topic>.md`, delete from memory.
- Machine-specific (env paths, personal tooling) → gitignored `.claude/CLAUDE.md` / `~/.codex/AGENTS.md`.
- Leave memory ≈ empty: only what fits neither home.

## Step 6 — Total cleanup

Not just `AGENTS.md` ≤ 70 lines: audit **every** docs/agents file — `AGENTS.md`, `CLAUDE.md`, `.agents/rules/**`, READMEs, `docs/**`. Every line passes one gate: *most critical, non-trivial fact the next agent must read — domain·infra·company·project-specific — in the fewest words?* Keep it at its right home (always-read → `AGENTS.md` · topic depth → rules file · WHY → chronicle · HOW → plan), else delete.

- Fix misalignments found in Step 1 (structure, versions, paths, README tables, index rows — including files added in Steps 4-5). Chronicle bodies are immutable — touch only if they reference incorrect content.
- Remove noise: entries referencing nonexistent things · duplicates (keep once, link from others) · empty sections/placeholders · generic content the agent already knows from general training.
- **Preserve all load-bearing content** (safety rules, domain glossary, test commands, rules index) — shrink the expression, never the function.

## Step 7 — Verify & gates

```bash
wc -l AGENTS.md CLAUDE.md
[ "$(cat CLAUDE.md | tr -d '[:space:]')" = "@AGENTS.md" ] && echo "CLAUDE.md OK"
readlink .claude/rules && diff <(ls .claude/rules/) <(ls .agents/rules/) && echo "symlink OK"
git check-ignore -v .claude/CLAUDE.md AGENTS.override.md
```

Report: AGENTS.md line count · rule files vs index rows · symlink status · gitignore entries · memory residue. STOP and fix if any invariant fails:

- `CLAUDE.md` is not exactly `@AGENTS.md`.
- `AGENTS.md` exceeds 70 lines — trim further.
- A rule file lacks `paths:` frontmatter (else it loads every session).
- A rule file is absent from the `AGENTS.md` index table — index by textual row, never `@import` (Codex has no imports).
- A domain·infra·company·project fact survives only in memory / `MEMORY.md` — move it into `AGENTS.md` or `.agents/rules/`.
- `AGENTS.override.md` committed beside `AGENTS.md` (two sources of truth) — or `.claude/CLAUDE.md` committed. Never commit either.
