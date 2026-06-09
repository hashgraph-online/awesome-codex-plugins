---
name: deps
description: "Run deps."
---
# Deps Skill

> Quick Ref: `$deps audit` | `$deps update [--major|--minor|--patch]` | `$deps vuln` | `$deps license`

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

## Modes

| Mode | Command | Purpose |
|------|---------|---------|
| **Audit** | `$deps audit` | Full dependency health check: vulnerabilities, outdated, licenses |
| **Update** | `$deps update [--major\|--minor\|--patch]` | Update dependencies with test verification |
| **Vuln** | `$deps vuln` | Focused vulnerability scan and remediation |
| **License** | `$deps license` | License compliance audit |

Default (bare `$deps`): runs **audit** mode.

---

## Step 0: Detect Ecosystem

Scan the working directory for manifest files. Multiple ecosystems may coexist.

| Manifest | Ecosystem | Lock File |
|----------|-----------|-----------|
| `go.mod` | Go | `go.sum` |
| `package.json` | Node | `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` |
| `pyproject.toml` / `requirements.txt` | Python | `requirements.txt` / `poetry.lock` |
| `Cargo.toml` | Rust | `Cargo.lock` |
| `Gemfile` | Ruby | `Gemfile.lock` |

```bash
# Detect all ecosystems present
for f in go.mod package.json pyproject.toml requirements.txt Cargo.toml Gemfile; do
  [[ -f "$f" ]] && echo "FOUND: $f"
done
```

If no manifest is found, stop and report: "No supported dependency manifest detected."

---

## Step 1: Audit Current State

Run the ecosystem-appropriate commands. Capture all output for classification.

### Go

```bash
go list -m -u all          # List all modules, flag available updates
govulncheck ./...           # Vulnerability scan against Go vuln DB
go mod tidy                 # Clean up unused deps (dry-run first)
```

### Node

```bash
npm audit                   # Known vulnerabilities
npm outdated                # Available updates (current vs wanted vs latest)
npx license-checker-webpack-plugin --out /dev/stdout 2>/dev/null || npx license-checker --json
```

### Python

```bash
pip-audit                   # Vulnerability scan (install: pip install pip-audit)
pip list --outdated         # Available updates
pip-licenses 2>/dev/null || echo "pip-licenses not installed"
```

### Rust

```bash
cargo audit                 # Vulnerability scan (install: cargo install cargo-audit)
cargo outdated              # Available updates (install: cargo install cargo-outdated)
cargo license 2>/dev/null || echo "cargo-license not installed"
```

### Ruby

```bash
bundle audit check          # Vulnerability scan (install: gem install bundler-audit)
bundle outdated             # Available updates
```

---

## Step 2: Classify Findings

Sort every finding into exactly one severity tier.

| Severity | Criteria | Action |
|----------|----------|--------|
| **Critical** | Known CVE with active exploitation, CVSS >= 9.0 | Update immediately, block release |
| **High** | Security advisory without known exploit, CVSS 7.0-8.9, major version behind with security implications | Update within current session |
| **Medium** | Minor versions behind, deprecated packages, stale transitive deps | Schedule update, batch if possible |
| **Low** | Patch-level updates, cosmetic version bumps, informational advisories | Update opportunistically |

Output a summary table:

```
SEVERITY   PACKAGE            CURRENT   AVAILABLE   REASON
Critical   example-lib        1.2.3     1.2.8       CVE-2025-XXXXX (RCE)
High       some-framework     3.1.0     4.2.0       Security advisory SA-2025-YYY
Medium     helper-pkg         2.0.1     2.3.0       3 minor versions behind
Low        util-lib           1.0.0     1.0.1       Patch release
```

---

## Step 3: Update Strategy

Choose strategy based on the update scope requested (or default to the classification).

### Patch updates (`--patch` or Low severity)

- Batch all patch updates together.
- Run full test suite once after the batch.
- Single commit: `chore(deps): batch patch updates`.

### Minor updates (`--minor` or Medium severity)

- Update one dependency at a time.
- Run tests after each update.
- Individual commits: `chore(deps): update <pkg> to <version>`.

### Major updates (`--major` or High/Critical severity)

- Research breaking changes first (check CHANGELOG, migration guide, release notes).
- Update one dependency at a time.
- Run full test suite after each.
- For whole library families, read [references/library-update-ratchet.md](references/library-update-ratchet.md) before changing manifests.
- Individual commits with body noting breaking changes:
  ```
  chore(deps): update <pkg> to <version>

  Breaking: <brief description of what changed>
  ```

### Decision matrix

| Flag | Patch | Minor | Major |
|------|-------|-------|-------|
| `--patch` | Yes | No | No |
| `--minor` | Yes | Yes | No |
| `--major` | Yes | Yes | Yes |
| (default) | Yes | Yes | No |

---

## Step 4: Execute Updates (Update Mode Only)

For each dependency to update, follow this loop strictly:

```
1. Record current state (version, lock file hash)
2. Update the dependency
3. Run tests: `go test ./...` / `npm test` / `pytest` / `cargo test`
4. If PASS:
   - Stage changed manifest + lock file
   - Commit: chore(deps): update <pkg> from <old> to <new>
5. If FAIL:
   - Revert: restore manifest + lock file to pre-update state
   - Document the incompatibility in the report
   - Continue to next dependency
```

### Ecosystem-specific update commands

| Ecosystem | Patch/Minor | Major |
|-----------|-------------|-------|
| Go | `go get <pkg>@latest` | `go get <pkg>@v<major>` |
| Node | `npm update <pkg>` | `npm install <pkg>@latest` |
| Python | `pip install --upgrade <pkg>` | `pip install <pkg>~=<version>` |
| Rust | `cargo update -p <pkg>` | Edit `Cargo.toml`, then `cargo update` |
| Ruby | `bundle update <pkg>` | Edit `Gemfile`, then `bundle install` |

---

## Step 5: Output Report

Write the report to `.agents/deps/`. Create the directory if needed.

```bash
mkdir -p .agents/deps
```

File name format: `YYYY-MM-DD-deps-<mode>.md`

### Report template

```markdown
# Dependency Report - <mode> - <date>

## Ecosystem: <detected>

## Summary
- Total dependencies: <N>
- Outdated: <N>
- Vulnerable: <N>
- License issues: <N>

## Findings

### Critical
<table or "None">

### High
<table or "None">

### Medium
<table or "None">

### Low
<table or "None">

## Updates Applied
<list of commits or "Audit only - no updates applied">

## Failed Updates
<list with reasons or "None">

## License Compliance
<summary or "Not checked - use $deps license">
```

---

## License Compliance (License Mode)

### Compatibility Matrix

| License | Proprietary OK | Copyleft | Distribution Obligations |
|---------|---------------|----------|--------------------------|
| MIT | Yes | No | Include license text |
| Apache-2.0 | Yes | No | Include license + NOTICE file |
| BSD-2-Clause | Yes | No | Include license text |
| BSD-3-Clause | Yes | No | Include license text, no endorsement |
| ISC | Yes | No | Include license text |
| MPL-2.0 | Yes (file-level) | Weak | Modified MPL files must stay MPL |
| LGPL-2.1 | Conditional | Weak | Dynamic linking OK, static requires disclosure |
| GPL-2.0 | **No** | **Strong** | Entire derivative work must be GPL |
| GPL-3.0 | **No** | **Strong** | Entire derivative work must be GPL |
| AGPL-3.0 | **No** | **Strong** | Network use triggers disclosure |
| SSPL | **No** | **Strong** | Service provider must open-source entire stack |
| Unlicense | Yes | No | No obligations |

### Rules

1. **Flag all copyleft licenses** (GPL, AGPL, SSPL) as **Critical** in proprietary projects.
2. **Flag weak copyleft** (MPL, LGPL) as **Medium** -- review usage pattern.
3. **Flag missing licenses** as **High** -- unknown license is treated as all-rights-reserved.
4. **Flag license changes** between versions -- an update may change the license.

### Detecting project type

- If `LICENSE` contains GPL/AGPL: project is copyleft, all licenses are compatible.
- If `LICENSE` contains MIT/Apache/BSD or is proprietary: flag copyleft dependencies.
- If no `LICENSE` file exists: warn that project license is undefined.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Tool not installed (`govulncheck`, `pip-audit`, etc.) | Report which tool is missing, provide install command, continue with available tools |
| Network unavailable | Use cached vulnerability DB if available, note staleness |
| Test suite does not exist | Warn loudly, skip test verification, note in report |
| Manifest parse error | Report the error, skip that ecosystem |

---

## See Also

- `skills/standards/SKILL.md` -- Language-specific conventions
- `skills/security/SKILL.md` -- Broader security scanning
- `skills/vibe/SKILL.md` -- Code quality validation
- [references/library-update-ratchet.md](references/library-update-ratchet.md)
