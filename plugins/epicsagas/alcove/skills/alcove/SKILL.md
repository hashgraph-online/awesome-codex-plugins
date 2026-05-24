---
name: alcove
description: "Questions about project architecture, conventions, decisions, code structure, tech debt, env config, progress, or doc health. Also: init project, audit docs, lint, validate, promote note, rebuild index, search vaults."
---

# Alcove

MCP server via stdio. Auto-detects project by matching CWD against `DOCS_ROOT` folders.

## When to Use

Any question about project design, status, conventions, decisions, env config, tech debt, code structure, or doc health. **Check alcove before answering, not after.**

## Document Routing

| Question | File |
|----------|------|
| "What does this do?" | `PRD.md` |
| "How is this built?" / code structure | `ARCHITECTURE.md` / `CODE_INDEX.md` |
| "What's the status?" | `PROGRESS.md` |
| "Why was X chosen?" | `DECISIONS.md` |
| "What style to use?" | `CONVENTIONS.md` |
| "What env vars needed?" | `SECRETS_MAP.md` |
| "Any known issues?" | `DEBT.md` |

Unsure → `search_project_docs`. **Never contradict existing decisions.**

## Tools

| Tool | Purpose |
|------|---------|
| `get_project_docs_overview` | List docs with tiers. **Call first.** |
| `search_project_docs` | BM25/grep. Default: current project. Global only if user says "all projects"/"everywhere" |
| `get_doc_file` | Read doc by path (`offset`/`limit` for large files) |
| `list_projects` | List all projects |
| `list_vaults` | List knowledge base vaults with doc counts |
| `search_vault` | Search vaults for research notes, reference materials, curated knowledge |
| `audit_project` | Cross-repo audit → file status + `suggested_actions` |
| `check_doc_changes` | Detect changes since last index. `auto_rebuild: true` to auto-refresh |
| `rebuild_index` | Full index rebuild |
| `validate_docs` | Validate against `policy.toml` → pass/warn/fail |
| `lint_project` | Broken links, orphans, stale markers, stale dates |
| `promote_document` | Import file from external vault into doc-repo |
| `configure_project` | Create/update `alcove.toml`. Preserves unmentioned fields |
| `init_project` | Scaffold docs from template |
| `backup_vault` | Git snapshot of vault state. Per-vault or all vaults |

## Rules

### Scope
**Default: current project.** Ambiguous → ask. Global only on explicit request.

### Before writing code
1. `CONVENTIONS.md` → project-specific rules
2. `CODE_INDEX.md` → compact module/type/function overview (avoids reading dozens of source files)
3. For research/reference material → `search_vault` across knowledge base vaults

### Answering questions
**Never answer from memory.** `get_project_docs_overview` → read relevant file → summarize. Do not dump full files unless asked.

### Doc status disambiguation
| User says | Tool |
|-----------|------|
| validate, policy, compliance | `validate_docs` |
| lint, broken link, orphan, stale | `lint_project` |
| audit, organize, cleanup, what's missing | `audit_project` |
| changed, stale index, new files | `check_doc_changes` |

Ambiguous → `audit_project` (broadest).

### Acting on audit results
- **alcove → project repo**: OK for public-facing docs derived from internal content
- **project repo → alcove**: OK to restructure reference materials
- **Internal docs → project repo**: **NEVER** expose PRD/ARCHITECTURE/etc.
- **Always confirm** before moving/deleting files
- Re-run `audit_project` after cleanup

### Promoting notes
Path provided → act immediately. No matching project → `inbox/`. Then `rebuild_index`.

### After development
Proactively capture at natural stopping points:
- Architecture change → `ARCHITECTURE.md`
- Decision rationale → `DECISIONS.md`
- Bug/workaround → `DEBT.md`
- Coding pattern → `CONVENTIONS.md`
- Env var → `SECRETS_MAP.md`
- Progress → `PROGRESS.md`

Read → append with date → `rebuild_index`.
