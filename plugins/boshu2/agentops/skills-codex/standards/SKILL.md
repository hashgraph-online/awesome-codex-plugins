---
name: standards
description: Provide repo coding standards.
---
# Standards Skill

Language-specific coding standards loaded on-demand by other skills.

## Purpose

This is a **library skill** - it doesn't run standalone but provides standards
references that other skills load based on file types being processed.

## Standards Available

| Standard | Reference | Loaded By |
|----------|-----------|-----------|
| Skill Structure | `references/skill-structure.md` | validate (skill audits), doc (skill creation) |
| Python | `references/python.md` | validate, implement, complexity |
| Go | `references/go.md` | validate, implement, complexity |
| Rust | `references/rust.md` | validate, implement, complexity |
| TypeScript | `references/typescript.md` | validate, implement |
| JavaScript | `references/javascript.md` | validate, implement |
| Shell | `references/shell.md` | validate, implement |
| YAML | `references/yaml.md` | validate |
| JSON | `references/json.md` | validate |
| Markdown | `references/markdown.md` | validate, doc |
| SQL Safety | `references/sql-safety-checklist.md` | validate, pre-mortem (when DB code detected) |
| LLM Trust Boundaries | `references/llm-trust-boundary-checklist.md` | validate, pre-mortem (when LLM code detected) |
| Race Conditions | `references/race-condition-checklist.md` | validate, pre-mortem (when concurrent code detected) |
| Codex Skills | `references/codex-skill.md` | validate (when `skills-codex/` or converter files detected) |
| Behavioral Discipline | `references/behavioral-discipline.md` | implement, review, validate, pre-mortem |
| Test Pyramid | `references/test-pyramid.md` | plan, pre-mortem, implement, crank, validation, post-mortem |
| SKILL.md Tier-Caps | `references/skill-tier-caps.md` | validate (skill line-cap audits), doc, plan |
| External-Source Attribution | `references/external-source-attribution.md` | doc (when absorbing external corpora), heal-skill |
| Migration-Owner Discipline | `references/migration-owner.md` | implement, plan, review, pre-mortem (when writing a breaking migration / retirement / `--fix`) |
| Agentic-Workflow Evidence | `references/agentic-workflow-evidence.md` | plan, implement, review, pre-mortem (empirical basis — Finster 2026 — for the workflow discipline) |

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
`validate/references/*-standards.md` which contain full compliance catalogs.

| Standard | Size | Use Case |
|----------|------|----------|
| Tier 1 (this skill) | ~5KB each | Normal validation |
| Tier 2 (validate/references) | ~15-20KB each | Deep audits, `--deep` flag |
| Domain checklists | ~3-5KB each | Triggered by code pattern detection |

## Integration

Skills that use standards:
- `$validate` - Loads based on changed file types
- `$implement` - Loads for files being modified
- `/review` - Loads for change-quality and blast-radius checks
- `$doc` - Loads markdown standards
- `/review` - Loads for root cause analysis
- `$refactor` - Loads for refactoring recommendations

## Examples

### Validate Loads Python Standards

**User says:** `$validate` (detects changed Python files)

**What happens:**
1. Validate skill checks git diff for file types
2. Validate finds `auth.py` in changeset
3. Validate loads `standards/references/python.md` automatically
4. Validate verifies against Python standards (type hints, docstrings, error handling)
5. Validate reports findings with standard references

**Result:** Python code validated against language-specific standards without manual reference loading.

### Implement Loads Go Standards

**User says:** `$implement ag-xyz-123` (issue modifies Go files)

**What happens:**
1. Implement skill reads issue metadata to identify file targets
2. Implement finds `server.go` in implementation scope
3. Implement loads `standards/references/go.md` for context
4. Implement writes code following Go standards (error handling, naming, package structure)
5. Implement validates output against loaded standards before committing

**Result:** Go code generated conforming to standards, reducing post-implementation validate findings.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Standards not loaded | File type not detected or standards skill missing | Check file extension matches reference; verify standards in dependencies |
| Wrong standard loaded | File type misidentified (e.g., .sh as .bash) | Manually specify standard; update file type detection logic |
| Deep standards missing | Validate needs extended catalog, not found | Check `validate/references/*-standards.md` exists; use `--deep` flag |
| Standard conflicts | Multiple languages in same changeset | Load all relevant standards; prioritize by primary language |

## Reference Documents

- [references/architecture-terms.md](references/architecture-terms.md)
- [references/common-standards.md](references/common-standards.md)
- [references/behavioral-discipline.md](references/behavioral-discipline.md)
- [references/examples-troubleshooting-template.md](references/examples-troubleshooting-template.md)
- [references/cli-wireup-template.md](references/cli-wireup-template.md) — Reproducible cobra subcommand template (noun + verb, injectable Options, ~10 min/cycle)
- [references/go.md](references/go.md)
- [references/json.md](references/json.md)
- [references/markdown.md](references/markdown.md)
- [references/python.md](references/python.md)
- [references/rust.md](references/rust.md)
- [references/shell.md](references/shell.md)
- [references/skill-structure.md](references/skill-structure.md)
- [references/standards-index.md](references/standards-index.md)
- [references/typescript.md](references/typescript.md)
- [references/javascript.md](references/javascript.md)
- [references/sql-safety-checklist.md](references/sql-safety-checklist.md)
- [references/llm-trust-boundary-checklist.md](references/llm-trust-boundary-checklist.md)
- [references/race-condition-checklist.md](references/race-condition-checklist.md)
- [references/codex-skill.md](references/codex-skill.md)
- [references/test-pyramid.md](references/test-pyramid.md)
- [references/yaml.md](references/yaml.md)
- [references/skill-tier-caps.md](references/skill-tier-caps.md)
- [references/external-source-attribution.md](references/external-source-attribution.md)
- [references/migration-owner.md](references/migration-owner.md) — One fail-closed owner per breaking migration: warn→alias→hard-error staging, atomic format-preserving `--fix`, refuse ambiguous both-forms-present, marker-last ledger writes
