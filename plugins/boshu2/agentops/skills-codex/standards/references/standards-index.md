# Standards Index

JIT loading map for validation agents. Load only what you need based on file types.

## Extension to Standard Map

| Extension | Standard File | Size |
|-----------|---------------|------|
| `.py` | `skills/validate/references/python-standards.md` | 32k |
| `.go` | `skills/validate/references/go-standards.md` | 28k |
| `.rs` | `skills/validate/references/rust-standards.md` | 40k |
| `.ts`, `.tsx` | `skills/validate/references/typescript-standards.md` | 24k |
| `.sh`, `.bash` | `skills/validate/references/shell-standards.md` | 20k |
| `.yaml`, `.yml` | `skills/validate/references/yaml-standards.md` | 16k |
| `.json` | `skills/validate/references/json-standards.md` | 12k |
| `.md` | `skills/validate/references/markdown-standards.md` | 8k |

## Universal Standards (Always Load)

| Standard | File | Purpose |
|----------|------|---------|
| **Vibe-Coding** | `skills/validate/references/vibe-coding.md` | Trust calibration, metrics, failure patterns |
| **Common Standards** | `skills/standards/references/common-standards.md` | Cross-language patterns: error handling, testing, security, docs, organization |
| **Behavioral Discipline** | `skills/standards/references/behavioral-discipline.md` | Assumptions, simplicity bias, blast-radius control, verification discipline |
| **Skill Structure** | `skills/standards/references/skill-structure.md` | Anthropic-compliant skill structure, frontmatter, quality checklist |

**Always load vibe-coding.md first**, then common-standards.md and behavioral-discipline.md for universal patterns.

## Pattern Files (Load When Relevant)

| Pattern Type | File | When to Load |
|--------------|------|--------------|
| Go patterns | `skills/validate/references/go-patterns.md` | Go architecture review |
| General patterns | `skills/validate/references/patterns.md` | Design review |
| Report format | `skills/validate/references/report-format.md` | Writing vibe reports |
| Codex skill standard | `skills/standards/references/codex-skill.md` | Codex skill files, converter output, `skills-codex/` |

## JIT Loading Pattern for Agents

```markdown
## Step 1: Detect File Types

Scan the target files to identify languages:
- Use Glob to find files
- Note extensions present

## Step 2: Load Relevant Standards

For each language detected, use Read tool:

Tool: Read
Parameters:
  file_path: "skills/validate/references/<language>-standards.md"

Only load standards for languages actually present in the review.

## Step 3: Apply Standards

Reference the loaded standards when validating code.
Cite specific sections: "Per python-standards.md section 3.2..."
```

## Example: Mixed Python/Go Review

```
Files detected: src/main.py, pkg/handler.go, scripts/deploy.sh

Load (3 standards only):
1. Read("skills/validate/references/python-standards.md")
2. Read("skills/validate/references/go-standards.md")
3. Read("skills/validate/references/shell-standards.md")

Skip: typescript, yaml, json, markdown (not present)
```

## Context Budget

| Agent Model | Context Budget | Max Standards |
|-------------|----------------|---------------|
| haiku | ~100k | 3-4 standards |
| opus | ~200k | All if needed |

Keep agents lean. Load only what's needed.

## JIT Loading Order

1. **vibe-coding.md** (universal — trust calibration, failure patterns)
2. **common-standards.md** (universal — cross-language error handling, testing, security, docs, organization)
3. **behavioral-discipline.md** (universal — assumptions, simplicity, scope control, verification)
4. **Language standards** (per detected extensions)
5. **Pattern files** (if architecture/discovery review)
