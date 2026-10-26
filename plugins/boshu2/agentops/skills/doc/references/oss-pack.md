# OSS Doc Pack — scaffold/audit open-source documentation

> Scaffold and audit the standard documentation pack for an open-source release. This is optional reference guidance for the Doc skill's OSS mode; it absorbed the former `/oss-docs` skill. Output contract: `CONTRIBUTING.md`, `CHANGELOG.md`, `AGENTS.md`, and the rest of the OSS doc tiers.

## Overview

This mode helps prepare repositories for open source release by:
1. Auditing existing documentation completeness
2. Scaffolding missing standard files
3. Generating content tailored to project type

A request can ask to audit (which OSS docs exist or are missing), scaffold
(create the requested missing standard files, or one named file), refresh
(update existing docs within the accepted request;
existing authorization is sufficient) or validate (check docs against the
style guidelines below).

---

## Audit and project type

Run `bash "<skill-dir>/scripts/audit-oss-docs.sh" --json` with the audited
repository as the working directory (`<skill-dir>` is defined in
[SKILL.md](../SKILL.md)); it audits the current directory. It reports the project
type, the detected languages and per-tier presence scores as JSON. Use the type
it reports; it checks operator markers before `cmd/`, because operators also
have `cmd/`. Its types are `operator`, `helm`, `cli-go`, `cli-python`,
`cli-node`, `cli-rust`, `library-go`, `library-python`, `library-node`,
`library-rust` and `unknown`.

The script checks three tiers by file presence only:

- **Tier 1 (required):** `LICENSE`, `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- **Tier 2 (standard):** `SECURITY.md`, `CHANGELOG.md`, `AGENTS.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.
- **Tier 3 (enhanced):** `docs/QUICKSTART.md`, `docs/ARCHITECTURE.md`, `docs/CLI_REFERENCE.md` (or `docs/CRD_REFERENCE.md` for an operator), `docs/CONFIG.md`, `docs/TROUBLESHOOTING.md`, `examples/`.

Why each file matters, a Tier 4 for specialized docs, and an adoption order:
[oss-documentation-tiers.md](oss-documentation-tiers.md).

---

## Scaffold

### Template Selection

| Reported type | Focus |
|---------------|-------|
| `cli-*` | Installation, commands, examples |
| `operator` | K8s CRDs, RBAC, deployment |
| `library-*` | API reference, examples |
| `helm` | Values, dependencies, upgrading |
| a service (caller-stated; the script has no service type) | API, configuration, deployment |

Per-type content templates: [oss-project-types.md](oss-project-types.md).

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

````markdown
# Agent Instructions

This project uses **<tool>** for <purpose>. Run `<onboard-cmd>` to get started.

## Quick Reference

```bash
<cmd1>              # Do thing 1
<cmd2>              # Do thing 2
```
````

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
- Update or overwrite existing content outside the authorized request, including through a refresh
- Generate code documentation (see [code/API guidance](default-mode.md))
- Generate the README hero/landing page (see [README craft](readme-craft.md))
- Create CI/CD files (out of scope — configure CI/CD separately)

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Generated docs feel generic | Project signals too sparse | Add concrete repo context (commands, architecture, workflows) |
| Existing docs conflict | Legacy text diverges from current behavior | Reconcile with current code/process and mark obsolete sections |
| Contributor path unclear | Missing setup/testing guidance | Add explicit quickstart and validation commands |
| Open-source handoff incomplete | Session-end workflow not reflected | Add landing-the-plane and release hygiene steps |
