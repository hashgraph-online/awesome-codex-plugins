# Adding Skills

This repo is built so agents can add skills without hand-wiring every adapter.
The only canonical source for a skill is `skills/<skill-name>/`.

## Skill Directory

Create one directory per skill:

```text
skills/
  <skill-name>/
    SKILL.md
    references/
    scripts/
    assets/
```

Only `SKILL.md` is required. Add `references/`, `scripts/`, or `assets/` when
they make the skill easier to use or keep the main instructions concise.

## Frontmatter Contract

Use lowercase hyphen-case for `name`, and make it match the directory name.
Marketplace plugin IDs are generated from the grouping rules in
`scripts/marketplace-utils.mjs`.

```yaml
---
name: example-skill
description: Use when doing a specific workflow that benefits from repeatable agent guidance.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Example Skill
  category: Developer Tooling
  tags: example,workflow,agents
---
```

Rules enforced by validation:

- `name` must match the folder name.
- `description` must be useful and at least 40 characters.
- `metadata.version` must be `MAJOR.MINOR.PATCH` semver.
- `metadata.displayName`, `metadata.category`, and `metadata.tags` are required.
- Tags must be lowercase hyphen-case and cannot be duplicated.
- `metadata.tags` can be a comma-separated string or a YAML list.
- Display names should omit the `LVTD` prefix.
- `SKILL.md` must include a top-level Markdown heading.
- `SKILL.md` must use LF line endings.
- Executable files in `scripts/` must have an executable bit.

## Writing The Skill

Keep the first screen focused on when to use the skill and the workflow the
agent should follow. Move long examples, checklists, reference tables, and
provider-specific details to `references/` when they would bury the core
instructions.

Prefer deterministic scripts over prose for repeated mechanical checks. Keep
scripts local to the skill directory and document when the agent should run
them.

## Generated Artifacts

Do not edit these paths by hand:

```text
.claude-plugin/
.agents/
plugins/
dist/
```

Run this after changing any skill:

```bash
npm run build
```

The build regenerates:

- `dist/registry.json`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `plugins/<plugin-name>/`

`dist/` is ignored. Marketplace artifacts under `.claude-plugin/`, `.agents/`,
and `plugins/` are committed so marketplace installs work directly from GitHub.

## Final Check

Run the full check before opening a PR:

```bash
npm run check
```

This command validates source skills, rebuilds generated files, validates
marketplace artifacts against the canonical `skills/` folders, and fails if
committed generated marketplace artifacts are stale.

## PR Checklist

- Source skill is added or updated under `skills/<skill-name>/`.
- Marketplace grouping rules are updated when the skill should ship in a
  generated plugin.
- Generated marketplace artifacts are regenerated with `npm run build`.
- `npm run check` passes.
- Any workflow changes are reflected in this guide and `AGENTS.md`.
