---
name: create-agents-md
description: Generate or rewrite an AGENTS.md file — a high-signal-density operational checklist for AI coding agents.
argument-hint: Generates project-specific AGENTS.md with constraints, conventions, and gotchas that prevent costly agent mistakes.
disable-model-invocation: true
when-to-use: "user wants to generate an AGENTS.md operational checklist -- '/create-agents-md', 'create agents.md', 'generate agents file', 'write AGENTS.md'"
---

# Gather Context

```
!`git remote -v 2>/dev/null || echo "NO_GIT"`
```

```
!`git log --oneline -5 2>/dev/null || echo "NO_GIT"`
```

---

# Instructions

**Before starting**, use tools to gather project context silently (do not show results to the user):
1. Glob `**/*` (max depth 2, exclude `.git/`, `node_modules/`, `.build/`, `vendor/`, `target/`) -- project file structure
2. Read `AGENTS.md`, `README.md`, `CLAUDE.md` -- existing docs (skip if missing)
3. Glob `**/*ci*.yml`, `**/*ci*.yaml`, `**/Jenkinsfile`, `**/.travis.yml`, `**/Makefile` (max depth 3) -- CI config
4. Glob for linter configs in root: `.eslintrc*`, `.prettierrc*`, `biome.json`, `rustfmt.toml`, `.swiftlint.yml`, `.rubocop.yml`, `.editorconfig`, `.clang-format`

Treat missing files as empty. Proceed regardless.

You are an AGENTS.md architect. Your goal is **maximum signal density** — every line must be project-specific, non-obvious, and action-guiding. No generic advice. No README duplication. No rules already enforced by tooling.

```
┌───────────┐     ┌───────────┐     ┌───────────┐     ┌───────────┐
│ 1. GATHER │ ──► │ 2. ANALYZE│ ──► │ 3. GENERATE│ ──►│ 4. SAVE   │
│ Shell data │     │ Detect    │     │ Write      │     │ Write file│
│ from above │     │ project   │     │ AGENTS.md  │     │ Verify &  │
│            │     │ type &    │     │ sections   │     │ report    │
│            │     │ read cfgs │     │            │     │           │
└───────────┘     └───────────┘     └───────────┘     └───────────┘
```

Use the `find` output to understand project type, language, build system, and structure — regardless of whether it's Node, Rust, Go, Python, Ruby, Swift, Java, C++, Elixir, or anything else. Do not rely on hardcoded manifest names.

Silently determine which case applies:

- **Branch A — No project detected:** If the directory has no recognizable source files, manifests, or config → tell the user this doesn't appear to be a project directory. **Stop here.**
- **Branch B — Existing AGENTS.md:** If `cat AGENTS.md` returned content → enter **rewrite mode**. Aggressively trim generic advice, deduplicate against README.md and CLAUDE.md, tighten language to imperative form. Then proceed to AGENTS.md Generation using the existing content as a starting point.
- **Branch C — No AGENTS.md:** Proceed to AGENTS.md Generation and create from scratch.

---

# AGENTS.md Generation

Analyze all gathered context -- project structure, file types, configs, CI/CD, linter configs, README, CLAUDE.md, git history -- and generate an AGENTS.md.

**Deduplication rule (highest priority):** Read CLAUDE.md carefully. If a rule, convention, validation command, or location is already documented in CLAUDE.md, do NOT repeat it in AGENTS.md. Agents read both files. AGENTS.md exists only for information that CLAUDE.md does not cover.

**Available sections** -- use only the ones that have content after deduplication. Omit any section that would be empty or fully covered by CLAUDE.md:

1. **Must-follow constraints** — Hard rules not covered by CLAUDE.md that cause build failures, test failures, or broken deployments if violated. Use inline labels for grouping (e.g., "Branching:", "Safety:", "ASCII-first:") instead of sub-headings. *Exclude:* anything already in CLAUDE.md, or enforced by a linter/formatter config file.

2. **Validation before finishing** — Exact commands an agent must run before considering work complete. *Exclude:* commands already listed in CLAUDE.md's Testing section.

3. **Repo-specific conventions** — Naming patterns, file organization rules, import conventions unique to this codebase. *Exclude:* conventions already documented in CLAUDE.md (e.g., timestamp format, retention policy, commit format).

4. **Important locations** — Key files and directories that agents need to know about but wouldn't discover by casual browsing. *Exclude:* obvious paths and any paths already listed in CLAUDE.md.

5. **Change safety rules** — What to check before modifying specific areas of the codebase. *Exclude:* safety rules already documented in CLAUDE.md (e.g., SYNC contract).

6. **Known gotchas** — Non-obvious traps, quirks, or environment-specific issues that waste agent time. *Exclude:* issues documented in README or CLAUDE.md.

**Section rules:**
- Every bullet must be specific to THIS project. If you could copy-paste it into any repo, delete it.
- Use imperative language: "Run X", "Never Y", "Always Z" -- no hedging ("consider", "you might want to").
- Omit sections that have no content after deduplication -- do not pad with filler or "No constraints" lines.
- Do NOT duplicate content from README.md or CLAUDE.md. When in doubt, omit.

---

# Quality Gates

Before saving, verify:

**BLOCKING** (fix before saving):
- Every bullet is specific to this project -- no generic advice that applies to any codebase.
- No content duplicated from README.md or CLAUDE.md.
- No rules already enforced by linter/formatter config files detected in context.
- All language is imperative -- no "consider", "might", "should consider", "you may want".
- No empty or filler sections -- omit sections with no unique content.

**WARNING** (review and trim):
- File exceeds 80 lines -- AGENTS.md should be a concise checklist, not documentation.
- Any section has more than 7 bullets -- merge or remove the least critical.

---

# Anti-Patterns

- **Don't** include generic advice like "write clean code" or "follow best practices".
- **Don't** duplicate the README or CLAUDE.md -- agents read both files already.
- **Don't** hedge with "you might want to" or "consider doing" -- be direct.
- **Don't** keep empty sections -- omit them entirely.
- **Don't** list linter rules -- the linter already enforces them.

---

# Save & Verify

1. Write the generated AGENTS.md to the project root.
   **Verify:** Read back the file and confirm it matches what was generated.
2. Count total lines and sections used.
   **Verify:** Check line count < 80. Confirm no empty sections remain.

---

# Output

> **AGENTS.md {created | rewritten}**
> **Sections:** {count of sections included}
> **Lines:** {line count}
> **Signal check:** {pass | warnings}
