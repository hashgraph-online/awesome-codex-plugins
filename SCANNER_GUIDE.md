# Plugin Quality Guide

All plugins submitted to **Awesome Codex Plugins** must pass the HOL AI Plugin Scanner. This guide shows you how to achieve a passing score and fix common issues.

## Minimum Requirements for Listing

| Requirement | Threshold |
|-------------|-----------|
| **Scanner Score** | ≥ 80 / 130 |
| **Severity** | No critical or high findings |
| **CI Gate** | Scanner must run in your repo's GitHub Actions |

## Quick Start

### Install the Scanner

```bash
# With pipx (recommended)
pipx install plugin-scanner

# With pip
pip install plugin-scanner

# Or run without installing
pipx run plugin-scanner scan . --format text
```

### Run a Scan

```bash
# Basic scan — full report
plugin-scanner scan . --format text

# Quick lint — faster, checks common issues
plugin-scanner lint . --format text

# Verify readiness for marketplace
plugin-scanner verify . --format text

# JSON output for CI parsing
plugin-scanner scan . --format json --output report.json

# SARIF output for GitHub Advanced Security
plugin-scanner scan . --format sarif --output results.sarif
```

### Understanding Your Score

```bash
$ plugin-scanner scan . --format text

╔══════════════════════════════════════════════════════════════════╗
║  HOL Plugin Scanner                                              ║
╚══════════════════════════════════════════════════════════════════╝

✅ Manifest Validation        31 / 31
✅ Security                   36 / 36
✅ Operational Security       20 / 20
✅ Best Practices             15 / 15
✅ Marketplace                15 / 15
⚠️  Skill Security             12 / 15   (3 points: 1 elevated skill step)
⚠️  Code Quality               10 / 10

──────────────────────────────────────────────────────────────────
Score: 119 / 130 (91.5%)
──────────────────────────────────────────────────────────────────

✅ PASSED: Score ≥ 80, no high/critical findings
```

## CI Integration (Required)

Your plugin repo must have the scanner running in CI. Add this to `.github/workflows/hol-scanner.yml`:

### Standard Gate (Recommended)

```yaml
name: HOL Plugin Scanner

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

permissions:
  contents: read
  security-events: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: HOL Plugin Scanner
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: scan
          min_score: 80
          fail_on_severity: high
          format: sarif
          upload_sarif: true
```

### Strict Gate (90+ Score, No Medium+ Findings)

```yaml
name: HOL Plugin Scanner — Strict

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

permissions:
  contents: read
  security-events: write

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: HOL Plugin Scanner
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: scan
          min_score: 90
          fail_on_severity: medium
          format: sarif
          upload_sarif: true
```

### Lint Gate (Fast PR Checks)

```yaml
name: HOL Plugin Scanner — Lint

on:
  pull_request:
    branches: [main, master]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: HOL Plugin Linter
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: lint
          fail_on_severity: high
```

### Auto-Submit to Registry (On Main Branch)

```yaml
name: HOL Plugin Scanner + Registry Submit

on:
  push:
    branches: [main, master]

permissions:
  contents: read
  security-events: write

jobs:
  scan-and-submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - name: HOL Plugin Scanner
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: scan
          min_score: 80
          fail_on_severity: high

      - name: Submit to HOL Registry
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: submit
          min_score: 80
          submission_enabled: true
          submission_score_threshold: 80
```

## Scoring Categories

### Manifest Validation (31 points)

What it checks:
- `plugin.json` exists and is valid JSON
- Required fields: `name`, `version`, `description`, `repository`, `license`, `interface.displayName`, `interface.shortDescription`, `interface.composerIcon`
- `name` is kebab-case (e.g., `my-plugin`, not `myPlugin`)
- `version` follows semver
- `repository` is a valid GitHub URL

**Common fixes:**
```json
// ✅ Good
{
  "name": "hol-data-sync",
  "version": "1.2.0",
  "description": "Sync data from HOL services to local storage",
  "repository": "https://github.com/yourname/hol-data-sync",
  "license": "Apache-2.0",
  "interface": {
    "displayName": "HOL Data Sync",
    "shortDescription": "Sync HOL data locally",
    "composerIcon": "./assets/icon.svg"
  }
}

// ❌ Bad: missing fields, bad name format, no interface
{
  "name": "holDataSync",
  "version": "1.0",
  "repository": "github.com/yourname/repo"
}
```

### Security (36 points)

What it checks:
- `SECURITY.md` exists with vulnerability disclosure policy
- `LICENSE` file exists (MIT, Apache-2.0, etc.)
- No hardcoded secrets in any file (API keys, tokens, passwords, AWS credentials)
- No `ghp_`, `sk-`, `AKIA`, `AIza` patterns
- MCP remotes are hardened (no wildcard `*` origins, no `http://` without localhost)

**Common fixes:**

```markdown
<!-- SECURITY.md -->
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

Please open a GitHub issue with the `[security]` label or email security@yourdomain.com.

We will respond within 48 hours and release a patch within 7 days for critical issues.
```

```json
// ✅ Good: Secure MCP remote
{
  "mcp": {
    "remotes": [
      {
        "name": "hcs-server",
        "url": "https://hcs-server.example.com/mcp",
        "origin": "https://hcs-server.example.com"
      }
    ]
  }
}

// ❌ Bad: Dangerous MCP remote
{
  "mcp": {
    "remotes": [
      {
        "name": "any-server",
        "url": "http://localhost:3000/mcp",
        "origin": "*"
      }
    ]
  }
}
```

### Operational Security (20 points)

What it checks:
- GitHub Actions are SHA-pinned (not floating tags like `@v4`)
- No `permissions: write-all` or overly broad permissions
- Dependabot is configured (`.github/dependabot.yml` exists)
- Dependency lockfiles present (`package-lock.json`, `requirements-lock.txt`, `yarn.lock`, `pnpm-lock.yaml`)

**Common fixes:**

```yaml
# ✅ Good: SHA-pinned, minimal permissions
name: CI
on: [push, pull_request]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-node@1d0ff469b7ec7b3cb9d8673fde0c81c44821de2a  # v4.1.0

# ❌ Bad: Floating tags, broad permissions
name: CI
on: [push]
permissions: write-all
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Best Practices (15 points)

What it checks:
- `README.md` exists with clear description
- `skills/` directory exists with valid `SKILL.md` files
- `SKILL.md` has proper frontmatter (`name`, `version`, `description`, `author`)
- `.codexignore` file exists (lists files to exclude from plugin bundle)

**Common fixes:**

```markdown
<!-- SKILL.md frontmatter -->
---
name: data-fetcher
version: 1.0.0
description: Fetch data from HOL services with caching
author:
  name: Your Name
  email: you@example.com
---

# Data Fetcher Skill

This skill provides commands to fetch and cache data from HOL services.

## Commands

- `fetch [topic]` — Fetch data for a topic
- `cache-clear` — Clear the local cache
```

```
# .codexignore
node_modules/
.git/
.env
*.log
```

### Marketplace (15 points)

What it checks:
- `marketplace.json` is valid JSON if present
- `source` paths are safe (no `..` or absolute paths)
- `category` is valid

### Skill Security (15 points)

What it checks:
- Cisco AI scan is clean (no malicious patterns)
- No elevated `exec` or `eval` in skill steps
- Skills are analyzable (not obfuscated)

**Common fixes:**

```markdown
<!-- ❌ Bad: Elevated skill with dangerous commands -->
```bash
curl -s https://example.com/install.sh | bash
sudo rm -rf /tmp/data
```

```markdown
<!-- ✅ Good: Safe skill with validated input -->
```bash
# Verify URL is from allowed list before fetching
if [[ "$URL" =~ ^https://(api\.example\.com|cdn\.example\.com)/ ]]; then
  curl -s "$URL" -o /tmp/safe-download
fi
```

### Code Quality (10 points)

What it checks:
- No `eval()`, `new Function()`, `Function()` in JavaScript
- No shell command injection patterns
- No `child_process.exec` with unsanitized input

**Common fixes:**

```javascript
// ❌ Bad: eval with user input
const result = eval(userInput);

// ✅ Good: Use a safe parser or whitelist
const allowedCommands = { 'add': (a, b) => a + b, 'subtract': (a, b) => a - b };
const result = allowedCommands[command]?.(a, b);
```

## Troubleshooting

### Scanner fails with "Plugin not found"

Make sure you're running from the plugin root directory (where `.codex-plugin/plugin.json` exists).

```bash
cd my-plugin/
plugin-scanner scan . --format text
```

### Score is stuck below 80

Check the scanner output for specific findings. Each finding has a severity and explanation. Fix high-severity items first.

### SARIF upload fails in GitHub Actions

Make sure your workflow has `security-events: write` permission:

```yaml
permissions:
  contents: read
  security-events: write
```

## Getting Help

- **Scanner repo:** [hashgraph-online/hol-guard](https://github.com/hashgraph-online/hol-guard)
- **GitHub Action:** [hashgraph-online/ai-plugin-scanner-action](https://github.com/hashgraph-online/ai-plugin-scanner-action)
- **Registry:** [hol.org/registry/plugins](https://hol.org/registry/plugins)
- **Issues:** Open an issue in this repo with the `[scanner]` label
- **Security issues:** Email security@hol.org

## Badges

Add the HOL Guard badge to your plugin repo once you achieve a passing score:

```markdown
[![HOL Guard](https://img.shields.io/badge/HOL%20Guard-Verified-green)](https://hol.org/guard)
```

Or show your score:

```markdown
[![HOL Guard Score](https://img.shields.io/badge/Score-95%2F130-brightgreen)](https://github.com/hashgraph-online/hol-guard)
```
