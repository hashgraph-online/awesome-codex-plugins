# OSS Doc Pack — scaffold/audit open-source documentation (`/doc --mode=oss`)

> Scaffold and audit the standard documentation pack for an open-source release. This is the full contract behind `/doc --mode=oss`; it absorbed the former `/oss-docs` skill. Output contract: `CONTRIBUTING.md`, `CHANGELOG.md`, `AGENTS.md`, and the rest of the OSS doc tiers.

## Overview

This mode helps prepare repositories for open source release by:
1. Auditing existing documentation completeness
2. Scaffolding missing standard files
3. Generating content tailored to project type

(The legacy `/oss-docs audit`, `/oss-docs scaffold`, `/oss-docs validate` triggers route here.)

## Commands

| Command | Action |
|---------|--------|
| `audit` | Check which OSS docs exist/missing |
| `scaffold` | Create all missing standard files |
| `scaffold [file]` | Create specific file |
| `refresh` | Propose latest-pattern updates; write existing docs only after explicit user confirmation |
| `validate` | Check docs follow best practices |

---

## Phase 0: Project Detection

```bash
# Determine project type and language
PROJECT_NAME=$(basename $(pwd))
LANGUAGES=()

[[ -f go.mod ]] && LANGUAGES+=("go")
[[ -f pyproject.toml ]] || [[ -f setup.py ]] && LANGUAGES+=("python")
[[ -f package.json ]] && LANGUAGES+=("javascript")
[[ -f Cargo.toml ]] && LANGUAGES+=("rust")

# Detect project category
if [[ -f Dockerfile ]] && [[ -d cmd ]]; then
    PROJECT_TYPE="cli"
elif [[ -d config/crd ]]; then
    PROJECT_TYPE="operator"
elif [[ -f Chart.yaml ]]; then
    PROJECT_TYPE="helm"
else
    PROJECT_TYPE="library"
fi
```

---

## Subcommand: audit

### Required Files (Tier 1 - Core)

| File | Purpose |
|------|---------|
| `LICENSE` | Legal terms |
| `README.md` | Project overview |
| `CONTRIBUTING.md` | How to contribute |
| `CODE_OF_CONDUCT.md` | Community standards |

### Recommended Files (Tier 2 - Standard)

| File | Purpose |
|------|---------|
| `SECURITY.md` | Vulnerability reporting |
| `CHANGELOG.md` | Version history |
| `AGENTS.md` | AI assistant context |
| `.github/ISSUE_TEMPLATE/` | Issue templates |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR template |

### Optional Files (Tier 3 - Enhanced)

| File | When Needed |
|------|-------------|
| `docs/QUICKSTART.md` | Complex setup |
| `docs/ARCHITECTURE.md` | Non-trivial codebase |
| `docs/CLI_REFERENCE.md` | CLI tools |
| `docs/CONFIG.md` | Configurable software |
| `examples/` | Complex workflows |

Full tier definitions: [oss-documentation-tiers.md](oss-documentation-tiers.md).

---

## Subcommand: scaffold

### Template Selection

| Project Type | Focus |
|--------------|-------|
| `cli` | Installation, commands, examples |
| `operator` | K8s CRDs, RBAC, deployment |
| `service` | API, configuration, deployment |
| `library` | API reference, examples |
| `helm` | Values, dependencies, upgrading |

Per-type content templates: [oss-project-types.md](oss-project-types.md).

For a machine-readable tiered audit (project type + per-tier scores + totals as JSON), run the helper script: `bash skills/doc/scripts/audit-oss-docs.sh --json`.

---

## Documentation Organization

```
project/
├── README.md              # Overview + quick start
├── AGENTS.md              # AI assistant context
├── CONTRIBUTING.md        # Contributor guide
├── CHANGELOG.md           # Keep a Changelog format
├── docs/
│   ├── QUICKSTART.md      # Detailed getting started
│   ├── CLI_REFERENCE.md   # Complete command reference
│   ├── ARCHITECTURE.md    # System design
│   └── CONFIG.md          # Configuration options
└── examples/
    └── README.md          # Examples index
```

---

## AGENTS.md Pattern

```markdown
# Agent Instructions

This project uses **<tool>** for <purpose>. Run `<onboard-cmd>` to get started.

## Quick Reference

```bash
<cmd1>              # Do thing 1
<cmd2>              # Do thing 2
```

## Verification evidence

Run the documentation checks relevant to the created files and report their
commands, results, and unchecked scope. Doc does not commit, push, release, or
decide completion; repository policy and the caller own those transitions.

---

## Style Guidelines

1. **Be direct** - Get to the point quickly
2. **Be friendly** - Welcome contributions
3. **Be concise** - Avoid boilerplate
4. **Use tables** - For commands, options, features
5. **Show examples** - Code blocks over prose
6. **Link liberally** - Cross-reference related docs

---

## Mode Boundaries

**DO:**
- Audit existing documentation
- Generate standard OSS files
- Validate documentation quality

**DON'T:**
- Update or overwrite existing content without explicit user confirmation, including through `refresh`
- Generate code documentation (use `/doc gen` — the default doc mode)
- Generate the README hero/landing page (use `/doc --mode=readme`)
- Create CI/CD files (out of scope — configure CI/CD separately)

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Generated docs feel generic | Project signals too sparse | Add concrete repo context (commands, architecture, workflows) |
| Existing docs conflict | Legacy text diverges from current behavior | Reconcile with current code/process and mark obsolete sections |
| Contributor path unclear | Missing setup/testing guidance | Add explicit quickstart and validation commands |
| Open-source handoff incomplete | Session-end workflow not reflected | Add landing-the-plane and release hygiene steps |
