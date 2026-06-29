# Contributing to Awesome Codex Plugins

Thanks for helping grow the Codex plugin ecosystem!

## How Submissions Work

You add a single line to `README.md`. That's it. A maintainer-verified generator mirrors your plugin bundle from your source repo and regenerates the catalog files (`plugins.json`, `marketplace.json`). You never need to copy plugin files into this repo yourself.

```
Your PR:  README.md (+1 line)
Generator (CI):  plugins/<owner>/<repo>/  ←  fetched from your GitHub repo
                  plugins.json            ←  regenerated from README
                  marketplace.json        ←  regenerated from README
```

## Adding a Plugin

> **Important: Read this entire guide before opening a PR. Submissions missing required items will be asked to fix them.**

### Step 1: Set up scanner CI in your plugin repo (required)

Your plugin repo must have the **HOL AI Plugin Scanner** running in CI before you submit. This is not optional. We verify this during review.

Add this file to your plugin repo at `.github/workflows/hol-plugin-scanner.yml`:

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
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
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

Wait for the CI to pass on your repo's main branch, then copy the workflow run URL.

### Step 2: Run the scanner locally and check your score

The release metadata below is synced automatically from the latest published HOL scanner release.

```bash
pipx install --force "plugin-scanner==2.0.928"
plugin-scanner scan . --format text
```

Expected reviewed wheel SHA256: `d76a77ca08aaac90ca956d0cde46767a31cc28f662e3ef32cbdcbfec6d7b4a43`

If you want to verify the exact wheel before install:

```bash
rm -rf .hol-plugin-scanner-dist
python3 -m pip download --only-binary=:all: --no-deps --dest .hol-plugin-scanner-dist "plugin-scanner==2.0.928"
python3 -m pip hash .hol-plugin-scanner-dist/*.whl
```

You need a score of **80/130** or higher with **no critical or high severity findings**. Save the output to include in your PR description.

### Step 3: Verify your plugin repo has the required files

Your plugin repo must contain:
- `.codex-plugin/plugin.json` (valid manifest)
- `SECURITY.md` (vulnerability disclosure policy)
- `LICENSE` (MIT or Apache-2.0 recommended)
- `README.md` (clear description)
- No hardcoded secrets, no dangerous MCP commands
- SHA-pinned GitHub Actions (if using Actions)
- Dependency lockfiles (`package-lock.json` or equivalent)

### Step 4: Add your entry to README.md and open a PR

1. **Fork** this repository
2. **Add your entry** to the appropriate section in `README.md` (alphabetical order by display name)
3. **Submit a PR** with:
   - Your scanner score (or link to the passing CI run on your plugin repo)
   - The public GitHub URL of your plugin repo

**Do not copy plugin files, `plugins/` directories, `plugins.json`, or `marketplace.json` into your PR.** The generator pulls your bundle from your source repo and regenerates all catalog files automatically. PRs that include manually-committed bundles will have those files stripped before merge.

## README Entry Format

Add your plugin as a single line in the appropriate category section:

```markdown
- [Plugin Name](https://github.com/<owner>/<repo>) - One-line description of what it does.
```

Rules:
- One plugin per line
- Alphabetical order within each category
- Description must be a single sentence
- Link must point to the GitHub repository root

## Scanner Requirements (Mandatory)

All plugins submitted to this list **must pass the HOL AI Plugin Scanner**.

### Minimum Requirements

- **Score:** ≥ 80/130
- **Severity:** No critical or high findings
- **CI:** Scanner workflow must be running in your plugin repo's GitHub Actions (see Step 1 above)
- **PR description:** Must include scanner score or a link to the passing CI run

### Run the Scanner Locally

The commands below stay pinned to the same reviewed scanner release used in the submission guide.

```bash
# Install the current reviewed release
pipx install --force "plugin-scanner==2.0.928"

# Scan your plugin
plugin-scanner scan . --format text

# Or lint for quick fixes
plugin-scanner lint . --format text

# Verify install readiness
plugin-scanner verify . --format text
```

Expected reviewed wheel SHA256: `d76a77ca08aaac90ca956d0cde46767a31cc28f662e3ef32cbdcbfec6d7b4a43`

### Required in Your Plugin Repo

Your plugin repository must include:

1. **`.codex-plugin/plugin.json`** — Valid manifest with required fields
2. **`SECURITY.md`** — Vulnerability disclosure policy
3. **`LICENSE`** — MIT or Apache-2.0 recommended
4. **`README.md`** — Clear description of what the plugin does
5. **No hardcoded secrets** — Scanner will flag API keys, tokens, passwords
6. **No dangerous MCP commands** — No `rm -rf`, `sudo`, `curl | sh`, `eval`, `exec` patterns
7. **SHA-pinned GitHub Actions** — If you use Actions, pin to commit SHAs
8. **Dependency lockfiles** — `package-lock.json` or `requirements-lock.txt`

### Scanner Score Breakdown

| Category | Max Points | What to Check |
|----------|-----------|----------------|
| Manifest Validation | 31 | `plugin.json` valid, required fields, semver, kebab-case |
| Security | 36 | `SECURITY.md`, `LICENSE`, no secrets, hardened MCP remotes |
| Operational Security | 20 | Pinned Actions, no `write-all`, Dependabot, lockfiles |
| Best Practices | 15 | `README.md`, skills directory, `SKILL.md` frontmatter, `.codexignore` |
| Marketplace | 15 | `marketplace.json` valid, safe source paths |
| Skill Security | 15 | Cisco scan clean, no elevated findings, analyzable |
| Code Quality | 10 | No `eval`/`new Function`, no shell injection |

**Total: 130 points.** Aim for 80+ to qualify.

## Example Workflows

Add this to your plugin repo at `.github/workflows/scanner.yml`:

### Basic CI Gate (Recommended)

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

### Strict Security Gate (For High-Trust Plugins)

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

      - name: Submit to Registry if Eligible
        if: github.ref == 'refs/heads/main'
        uses: hashgraph-online/ai-plugin-scanner-action@v1
        with:
          plugin_dir: "."
          mode: submit
          min_score: 90
          submission_enabled: true
          submission_score_threshold: 90
```

### Lint-First Workflow (For Development)

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

## Plugin Repo Requirements

Your plugin source repo must be structured so the generator can find it:

```
your-plugin-repo/
  .codex-plugin/
    plugin.json        # Required - plugin manifest
  assets/
    icon.svg           # Required - plugin icon (SVG preferred, PNG acceptable)
  ...                  # Other plugin files (skills, commands, etc.)
```

### plugin.json

Must be valid JSON at `.codex-plugin/plugin.json` with at minimum:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "repository": "https://github.com/<owner>/<repo>",
  "license": "MIT",
  "interface": {
    "displayName": "My Plugin",
    "shortDescription": "Brief one-liner",
    "composerIcon": "./assets/icon.svg"
  }
}
```

**Required fields:**
- `name` - machine-readable plugin identifier
- `version` - semver version string
- `description` - what the plugin does
- `repository` - GitHub repository URL
- `license` - SPDX license identifier
- `interface.composerIcon` - path to the icon file (relative to plugin root)

### Icon

- **Format:** SVG preferred. PNG also accepted.
- **Size:** 512x512px recommended. Must read clearly at small sizes (32x32).
- **Location:** `assets/icon.svg` (or `assets/icon.png`)
- **Style:** Simple, distinctive. Avoid text-heavy designs.
- **File size:** Keep under 50KB. Optimize SVGs (no embedded raster images).

## Additional Requirements

- Plugin must have a **public GitHub repository**
- Must be **functional** with a valid `.codex-plugin/plugin.json` manifest
- Must include an **icon** as described above
- **Must pass the HOL Plugin Scanner** (score ≥ 80, no critical/high findings)
- **Must have scanner running in CI** (GitHub Action or equivalent)
- **One plugin per PR**

## Categories

- **Development & Workflow** - Tools for coding, planning, and development workflows
- **Tools & Integrations** - External service integrations and utilities

## PR Checklist

Before submitting, verify:

**In your plugin repo:**
- [ ] `.github/workflows/hol-plugin-scanner.yml` exists and CI passes on main
- [ ] `SECURITY.md` exists in your plugin repo
- [ ] `LICENSE` exists in your plugin repo
- [ ] `.codex-plugin/plugin.json` exists and is valid JSON
- [ ] Plugin Scanner score ≥ 80/130 (paste score or link CI run in PR description)

**In your PR:**
- [ ] README.md entry is alphabetically sorted within its category
- [ ] PR description includes your scanner score or CI link
- [ ] PR description includes the public GitHub URL of your plugin repo
- [ ] All links in the README entry are valid
- [ ] **No manually-committed plugin bundles, `plugins.json`, or `marketplace.json`** — the generator handles these

## CI Checks

All PRs to this repo are automatically validated. The CI will check:

1. **Alphabetical order** - README entries must be sorted within each section
2. **Plugin manifest** - For new README entries, the generator fetches your source repo and validates `plugin.json`, required fields, and icon presence
3. **Scanner verification** - PR description must include scanner score or CI link
4. **Markdown links** - All URLs in README must be reachable

## Getting Help

- Scanner docs: [HOL Guard](https://github.com/hashgraph-online/hol-guard)
- Scanner action: [ai-plugin-scanner-action](https://github.com/hashgraph-online/ai-plugin-scanner-action)
- Registry: [hol.org/registry/plugins](https://hol.org/registry/plugins)
- Issues: Open an issue in this repo with the `[scanner]` label
