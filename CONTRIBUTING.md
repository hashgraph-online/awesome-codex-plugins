# Contributing to Awesome Codex Plugins

Thanks for helping grow the Codex plugin ecosystem!

## Adding a Plugin

1. **Fork** this repository
2. **Add your entry** to the appropriate section in `README.md`
3. **Add your plugin bundle** under `plugins/<owner>/<repo>/`
4. **Follow the format** described below
5. **Submit a PR** with a clear description

## Plugin Bundle Requirements

Every plugin submission must include a bundle under `plugins/<owner>/<repo>/` with the following structure:

```
plugins/<owner>/<repo>/
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

## Additional Requirements

- Plugin must have a **public GitHub repository**
- Must be **functional** with a valid `.codex-plugin/plugin.json` manifest
- Must include an **icon** as described above
- Include a **description** that explains what the plugin does
- **One plugin per PR** (unless adding multiple related plugins)

## Categories

- **Development & Workflow** - Tools for coding, planning, and development workflows
- **Tools & Integrations** - External service integrations and utilities

## PR Checklist

Before submitting, verify:

- [ ] README.md entry is alphabetically sorted within its category
- [ ] Plugin bundle exists under `plugins/<owner>/<repo>/`
- [ ] `.codex-plugin/plugin.json` exists and is valid JSON
- [ ] `composerIcon` field is set in `plugin.json` interface section
- [ ] Icon file exists at the path referenced by `composerIcon`
- [ ] All links in the README entry are valid
- [ ] No placeholder or TODO values in plugin.json

## CI Checks

All PRs are automatically validated. The CI will check:

1. **Alphabetical order** - README entries must be sorted within each section
2. **Plugin manifest** - `plugin.json` must exist and contain required fields
3. **Icon presence** - `composerIcon` must point to an existing file
4. **Marketplace sync** - `plugins.json` and `marketplace.json` stay in sync with README
5. **Markdown links** - All URLs in README must be reachable

If CI fails, check the logs for specific errors and fix before re-pushing.
