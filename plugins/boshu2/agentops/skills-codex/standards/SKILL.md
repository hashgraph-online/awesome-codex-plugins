---
name: standards
description: "Run standards."
---
# Standards Skill

Language-specific coding standards loaded on-demand by other skills.

## Purpose

This is a **library skill** - it doesn't run standalone but provides standards
references that other skills load based on file types being processed.

## Standards Available

| Standard | Reference | Loaded By |
|----------|-----------|-----------|
| Skill Structure | `references/skill-structure.md` | vibe (skill audits), doc (skill creation) |
| Python | `references/python.md` | vibe, implement, complexity |
| Go | `references/go.md` | vibe, implement, complexity |
| Rust | `references/rust.md` | vibe, implement, complexity |
| TypeScript | `references/typescript.md` | vibe, implement |
| Shell | `references/shell.md` | vibe, implement |
| YAML | `references/yaml.md` | vibe |
| JSON | `references/json.md` | vibe |
| Markdown | `references/markdown.md` | vibe, doc |
| SQL Safety | `references/sql-safety-checklist.md` | vibe, pre-mortem (when DB code detected) |
| LLM Trust Boundaries | `references/llm-trust-boundary-checklist.md` | vibe, pre-mortem (when LLM code detected) |
| Race Conditions | `references/race-condition-checklist.md` | vibe, pre-mortem (when concurrent code detected) |
| Codex Skills | `references/codex-skill.md` | vibe (when `skills-codex/` or converter files detected) |
| Behavioral Discipline | `references/behavioral-discipline.md` | implement, review, vibe, pre-mortem |
| Test Pyramid | `references/test-pyramid.md` | plan, pre-mortem, implement, crank, validation, post-mortem |
| SKILL.md Tier-Caps | `references/skill-tier-caps.md` | vibe (skill line-cap audits), doc, plan |
| External-Source Attribution | `references/external-source-attribution.md` | doc (when absorbing external corpora), heal-skill |

## How It Works

Skills declare `standards` as a dependency:

```yaml
skills:
  - standards
```

Then load the appropriate reference based on file type:

```python
# Pseudo-code for standard loading
if file.endswith('.py'):
    load('standards/references/python.md')
elif file.endswith('.go'):
    load('standards/references/go.md')
elif file.endswith('.rs'):
    load('standards/references/rust.md')
# etc.
```

## Domain-Specific Checklists

Specialized checklists for high-risk code patterns. Loaded automatically by `$validate` and `$pre-mortem` when matching code patterns are detected:

| Checklist | Trigger Pattern | Risk Area |
|-----------|----------------|-----------|
| `sql-safety-checklist.md` | SQL queries, ORM calls, migration files, `database/sql`, `sqlalchemy`, `prisma` | Injection, migration safety, N+1, transactions |
| `llm-trust-boundary-checklist.md` | `anthropic`, `openai` imports, prompt templates, `*llm*`/`*prompt*` files | Prompt injection, output validation, cost control |
| `race-condition-checklist.md` | Goroutines, threads, `asyncio`, `sync.Mutex`, shared file I/O | Shared state, file races, database races |
| `codex-skill.md` | Files under `skills-codex/`, `convert.sh`, `skills-codex-overrides/` | Codex API conformance, prohibited primitives, tool mapping |
| `behavioral-discipline.md` | Execution, review, or plan-validation tasks with ambiguity or broad blast radius | Hidden assumptions, overbuilding, drive-by edits, weak verification |

Skills detect triggers via file content patterns and import statements. Each checklist's "When to Apply" section defines exact detection rules.

## Deep Standards

For comprehensive audits, skills can load extended standards from
`vibe/references/*-standards.md` which contain full compliance catalogs.

| Standard | Size | Use Case |
|----------|------|----------|
| Tier 1 (this skill) | ~5KB each | Normal validation |
| Tier 2 (vibe/references) | ~15-20KB each | Deep audits, `--deep` flag |
| Domain checklists | ~3-5KB each | Triggered by code pattern detection |

## Integration

Skills that use standards:
- `$validate` - Loads based on changed file types
- `$implement` - Loads for files being modified
- `$review` - Loads for change-quality and blast-radius checks
- `$doc` - Loads markdown standards
- `$review` - Loads for root cause analysis
- `$refactor` - Loads for refactoring recommendations

## Examples

### Vibe Loads Python Standards

**User says:** `$validate` (detects changed Python files)

**What happens:**
1. Vibe skill checks git diff for file types
2. Vibe finds `auth.py` in changeset
3. Vibe loads `standards/references/python.md` automatically
4. Vibe validates against Python standards (type hints, docstrings, error handling)
5. Vibe reports findings with standard references

**Result:** Python code validated against language-specific standards without manual reference loading.

### Implement Loads Go Standards

**User says:** `$implement ag-xyz-123` (issue modifies Go files)

**What happens:**
1. Implement skill reads issue metadata to identify file targets
2. Implement finds `server.go` in implementation scope
3. Implement loads `standards/references/go.md` for context
4. Implement writes code following Go standards (error handling, naming, package structure)
5. Implement validates output against loaded standards before committing

**Result:** Go code generated conforming to standards, reducing post-implementation vibe findings.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Standards not loaded | File type not detected or standards skill missing | Check file extension matches reference; verify standards in dependencies |
| Wrong standard loaded | File type misidentified (e.g., .sh as .bash) | Manually specify standard; update file type detection logic |
| Deep standards missing | Vibe needs extended catalog, not found | Check `vibe/references/*-standards.md` exists; use `--deep` flag |
| Standard conflicts | Multiple languages in same changeset | Load all relevant standards; prioritize by primary language |

## Reference Documents

- [references/common-standards.md](references/common-standards.md)
- [references/behavioral-discipline.md](references/behavioral-discipline.md)
- [references/examples-troubleshooting-template.md](references/examples-troubleshooting-template.md)
- [references/go.md](references/go.md)
- [references/json.md](references/json.md)
- [references/markdown.md](references/markdown.md)
- [references/python.md](references/python.md)
- [references/rust.md](references/rust.md)
- [references/shell.md](references/shell.md)
- [references/skill-structure.md](references/skill-structure.md)
- [references/standards-index.md](references/standards-index.md)
- [references/typescript.md](references/typescript.md)
- [references/sql-safety-checklist.md](references/sql-safety-checklist.md)
- [references/llm-trust-boundary-checklist.md](references/llm-trust-boundary-checklist.md)
- [references/race-condition-checklist.md](references/race-condition-checklist.md)
- [references/codex-skill.md](references/codex-skill.md)
- [references/test-pyramid.md](references/test-pyramid.md)
- [references/yaml.md](references/yaml.md)
- [references/skill-tier-caps.md](references/skill-tier-caps.md)
- [references/external-source-attribution.md](references/external-source-attribution.md)

## Local Resources

### references/

- [references/codex-skill.md](references/codex-skill.md)
- [references/behavioral-discipline.md](references/behavioral-discipline.md)
- [references/common-standards.md](references/common-standards.md)
- [references/examples-troubleshooting-template.md](references/examples-troubleshooting-template.md)
- [references/go.md](references/go.md)
- [references/json.md](references/json.md)
- [references/llm-trust-boundary-checklist.md](references/llm-trust-boundary-checklist.md)
- [references/markdown.md](references/markdown.md)
- [references/python.md](references/python.md)
- [references/race-condition-checklist.md](references/race-condition-checklist.md)
- [references/rust.md](references/rust.md)
- [references/shell.md](references/shell.md)
- [references/skill-structure.md](references/skill-structure.md)
- [references/sql-safety-checklist.md](references/sql-safety-checklist.md)
- [references/standards-index.md](references/standards-index.md)
- [references/test-pyramid.md](references/test-pyramid.md)
- [references/typescript.md](references/typescript.md)
- [references/yaml.md](references/yaml.md)
- [references/skill-tier-caps.md](references/skill-tier-caps.md)
- [references/external-source-attribution.md](references/external-source-attribution.md)

### scripts/

- `scripts/validate.sh`

