---
name: alcove
description: "HTTP API-based documentation server (always running). Questions about project architecture, conventions, decisions, code structure, tech debt, env config, progress, or doc health. Also: init project, audit docs, lint, validate, promote note, rebuild index, search vaults."
---

# Alcove

HTTP API-based documentation server (always running). Auto-detects project by matching CWD against `DOCS_ROOT` folders.

## Prerequisites

The alcove API server must be running. Check and start with:

```bash
alcove api status   # check if server is running
alcove api start    # start if not running
```

Resolve URL and token once at the start of every session:
```bash
eval $(alcove api env)
# sets ALCOVE_URL=http://127.0.0.1:<port>  (always)
# sets ALCOVE_TOKEN=<token>                (only if configured)
```
All commands below use `$ALCOVE_URL`. If `$ALCOVE_TOKEN` is set, add `-H "Authorization: Bearer $ALCOVE_TOKEN"` to every request.

## Arguments

| Arg | Action |
|-----|--------|
| `verify` / `rag status` | 1) `alcove api status` — check daemon is running<br>2) `eval $(alcove api env)` — resolve URL + token<br>3) `curl -s $ALCOVE_URL/health` — print health response |

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

Unsure → search via API. **Never contradict existing decisions.**

## API Reference

### Search & Discovery

Use the search endpoint. Project is auto-detected from CWD.

```bash
# Search current project (default)
curl -s '$ALCOVE_URL/search?q=QUERY'

# Search with options
curl -s '$ALCOVE_URL/search?q=QUERY&limit=10&mode=hybrid'

# Search a specific project
curl -s '$ALCOVE_URL/search?q=QUERY&project=PROJ'

# Search across all projects
curl -s '$ALCOVE_URL/search?q=QUERY&limit=20'

# POST search (JSON body)
curl -s -X POST $ALCOVE_URL/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"q": "QUERY", "limit": 10, "project": "proj", "mode": "hybrid"}'
```

Response: `{"query": "...", "results": [...], "mode": "...", "truncated": false}`

### Project Operations

```bash
# List projects
curl -s $ALCOVE_URL/projects

# Init project
curl -s -X POST $ALCOVE_URL/projects \
  -H 'Content-Type: application/json' \
  -d '{"project_name": "myproj", "project_path": "/abs/path"}'

# Project docs overview (with sizes and classification)
curl -s $ALCOVE_URL/projects/PROJECT/docs

# Audit doc health
curl -s $ALCOVE_URL/projects/PROJECT/audit

# Validate against policy.toml
curl -s $ALCOVE_URL/projects/PROJECT/validate

# Configure project settings
curl -s -X PUT $ALCOVE_URL/projects/PROJECT/config \
  -H 'Content-Type: application/json' \
  -d '{"core_files": ["PRD.md", "ARCHITECTURE.md"]}'

# Read a doc file
curl -s '$ALCOVE_URL/docs/PRD.md?project=PROJECT'
curl -s '$ALCOVE_URL/docs/reports/weekly.md?project=PROJECT&offset=0&limit=2000'

# Index code structure
curl -s -X POST $ALCOVE_URL/index-code \
  -H 'Content-Type: application/json' \
  -d '{"source_path": "/abs/path/src", "language": "rust", "project": "PROJECT"}'
```

| Action | Method | Endpoint |
|--------|--------|----------|
| List projects | GET | `/projects` |
| Init project | POST | `/projects` |
| Project docs overview | GET | `/projects/{name}/docs` |
| Audit project | GET | `/projects/{name}/audit` |
| Validate docs | GET | `/projects/{name}/validate` |
| Configure project | PUT | `/projects/{name}/config` |
| Read doc file | GET | `/docs/{path}?project=name` |
| Index code | POST | `/index-code` |

### Index & Maintenance

```bash
# Update index — incremental (changed/added/deleted files only), all projects
curl -s -X POST $ALCOVE_URL/index

# Update index — single project only
curl -s -X POST $ALCOVE_URL/projects/PROJECT/index

# Check changed files since last index
curl -s '$ALCOVE_URL/changes?auto_rebuild=true'

# Lint docs
curl -s '$ALCOVE_URL/lint?project=PROJECT'
```

| Action | Method | Endpoint |
|--------|--------|----------|
| Update index (all projects) | POST | `/index` |
| Update index (single project) | POST | `/projects/{name}/index` |
| Check changes | GET | `/changes?auto_rebuild=true` |
| Lint project | GET | `/lint?project=name` |

### Vault Operations

```bash
# List vaults
curl -s $ALCOVE_URL/vaults

# Search vaults
curl -s '$ALCOVE_URL/vaults/search?q=QUERY&vault=*&limit=20'

# Backup vault
curl -s -X POST $ALCOVE_URL/vaults/backup \
  -H 'Content-Type: application/json' \
  -d '{"vault_name": "myvault"}'

# Promote document into doc-repo
curl -s -X POST $ALCOVE_URL/promote \
  -H 'Content-Type: application/json' \
  -d '{"source": "/abs/path/notes.md", "project": "PROJECT", "copy": true}'
```

| Action | Method | Endpoint |
|--------|--------|----------|
| List vaults | GET | `/vaults` |
| Search vault | GET | `/vaults/search?q=...` |
| Backup vault | POST | `/vaults/backup` |
| Promote doc | POST | `/promote` |

### MCP Proxy (Legacy)

The JSON-RPC proxy remains available for MCP clients:

```bash
curl -s -X POST $ALCOVE_URL/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"TOOL_NAME","arguments":{}}}'
```

### Health Check

```bash
curl -s $ALCOVE_URL/health
# → {"status": "ok", "version": "x.y.z", "docs_root_configured": true, "projects": N}
```

## Rules

### Scope
**Default: current project.** Ambiguous → ask. Global only on explicit request.

### Before writing code
1. `CONVENTIONS.md` → project-specific rules
2. `CODE_INDEX.md` → compact module/type/function overview (avoids reading dozens of source files)
3. For research/reference material → search vaults via `GET /vaults/search?q=...`

### Answering questions
**Never answer from memory.** Call `GET /projects/{name}/docs` → `GET /docs/{path}?project=name` for the relevant file → summarize. Do not dump full files unless asked.

### Doc status disambiguation
| User says | Endpoint |
|-----------|----------|
| validate, policy, compliance | `GET /projects/{name}/validate` |
| lint, broken link, orphan, stale | `GET /lint?project=name` |
| audit, organize, cleanup, what's missing | `GET /projects/{name}/audit` (runs both validate + lint) |
| changed, stale index, new files | `GET /changes?auto_rebuild=true` |

Ambiguous → call `audit_project` (broadest).

### Acting on audit results
- **alcove → project repo**: OK for public-facing docs derived from internal content
- **project repo → alcove**: OK to restructure reference materials
- **Internal docs → project repo**: **NEVER** expose PRD/ARCHITECTURE/etc.
- **Always confirm** before moving/deleting files
- Re-run validate + lint after cleanup

### Promoting notes
Path provided → act immediately: `POST /promote` with the source path. No matching project → `inbox/`. Then `POST /index`.

### After development
Proactively capture at natural stopping points:
- Architecture change → `ARCHITECTURE.md`
- Decision rationale → `DECISIONS.md`
- Bug/workaround → `DEBT.md`
- Coding pattern → `CONVENTIONS.md`
- Env var → `SECRETS_MAP.md`
- Progress → `PROGRESS.md`

Read → append with date → `POST /index`.
