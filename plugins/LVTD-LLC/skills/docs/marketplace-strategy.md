# Marketplace Strategy

Research date: 2026-06-08

## Executive Recommendation

Keep `skills/<skill-name>/SKILL.md` as the canonical source format and generate
host-specific marketplace artifacts from it.

The shared skill format is the most portable layer across Codex, Claude Code,
OpenClaw, and other agent clients. Marketplace and plugin formats should be
treated as adapters:

- Agent Skills catalog: first-class canonical source and public registry.
- Claude Code: generated `.claude-plugin/marketplace.json` plus plugin folders.
- Codex: generated `.agents/plugins/marketplace.json` plus Codex plugin folders.
- OpenClaw: publish individual skills to ClawHub, and add native OpenClaw
  plugins only when a skill needs runtime tools.

This lets skill authors write once, while users install through the native UI or
CLI of their preferred tool.

## Current Repo Assessment

The repo now has the right base shape for a generated marketplace:

- Each skill is a folder under `skills/` with a `SKILL.md`.
- `scripts/validate-skills.mjs` checks names, descriptions, frontmatter,
  metadata, headings, line endings, and executable script files.
- `scripts/build-registry.mjs` emits `dist/registry.json`.
- `scripts/build-marketplaces.mjs` emits Claude Code and Codex marketplace
  adapters from shared marketplace helper functions.
- `scripts/validate-marketplaces.mjs` verifies generated manifests, marketplace
  entries, plugin directories, and copied skill folders against the canonical
  `skills/` source.
- `npm run check` rebuilds and validates the catalog, then fails if committed
  marketplace artifacts are stale.
- The `skills` CLI can install individual skills from GitHub, a direct skill
  URL, any git URL, or a local checkout.
- CI runs the same `npm run check` command used locally.

Remaining gaps before this becomes a mature marketplace:

- The registry does not include source commit metadata yet.
- Frontmatter parsing is intentionally strict custom parsing instead of a full
  YAML parser.
- CI does not yet run native host validators such as Claude, Codex, or OpenClaw
  plugin validation CLIs.
- There are no prompt fixtures or behavioral smoke tests per skill yet.
- There is no supply-chain signing or provenance process for release artifacts.

## Best Practices

### 1. Preserve a Host-Neutral Skill Core

Use the Agent Skills shape as the canonical contract:

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/
    references/
    assets/
```

Every skill should have:

- `name`: matches folder name, lowercase hyphen-case, max 64 chars.
- `description`: says what the skill does and when to use it.
- Optional `license`, `compatibility`, and `metadata`.
- Main instructions kept concise, with large material moved to `references/`.
- Scripts only when deterministic execution is better than prose.

This aligns with the Agent Skills specification and with Claude Code and
OpenClaw skill discovery. Codex also uses the same basic `SKILL.md` style for
skills inside plugins.

### 2. Separate Canonical Metadata From Host Adapter Metadata

Keep the canonical metadata minimal and portable in `SKILL.md`:

```yaml
---
name: django-htmx
description: Build and review HTMX interactions in Django server-rendered projects.
license: MIT
compatibility: Designed for Codex, Claude Code, OpenClaw, and Agent Skills compatible clients.
metadata:
  category: Web Development
  tags: django,htmx,server-rendered-ui
  version: "0.1.0"
---
```

Then generate host-specific metadata:

- Codex UI metadata: `agents/openai.yaml` inside skill folders when needed.
- Claude Code marketplace metadata: plugin `plugin.json` and marketplace entry.
- OpenClaw metadata: ClawHub publish metadata and any `metadata.openclaw.*`
  fields only when an OpenClaw-specific behavior is needed.

Avoid hardcoding Claude-only or Codex-only fields in every skill unless the
field is harmless for other clients.

### 3. Offer Individual Skills and Grouped Marketplace Plugins

The source catalog remains one directory per skill, so direct installs can stay
granular. Marketplace installs should use grouped plugins when related skills
are normally useful together.

Recommended distribution model:

- Direct skills CLI installs use canonical skill names such as `django-htmx`.
- Generated marketplace plugins group related skills, such as `django`, `rust`,
  `nonfiction-book-writing`, and `cookiecutter`.
- Keep grouped plugins generated from the same skill source, not hand-maintained
  copies.

Tradeoff:

- Direct installs maximize user choice and clearer updates.
- Grouped marketplace plugins reduce install friction for teams that want a
  complete baseline.
- Plugin IDs no longer need to match canonical skill names; skill namespaces
  make the bundled skill explicit after install.

### 4. Version Skills Independently

Root repo versioning is not enough once skills become marketplace entries.

Add per-skill versioning:

- Each skill has a semver in metadata.
- Generated marketplace entries expose that version.
- Registry records the source commit and content hash for each skill.
- Release notes can include both repo-level and skill-level changes.
- Generated marketplace plugin versions should follow the root catalog version
  in `package.json` so packaging-only fixes invalidate host plugin caches.

For Git-backed marketplaces, pin generated entries to release tags or commit
SHAs where the host supports it. Claude Code supports pinning plugin sources by
ref and SHA in marketplace entries. This repo's `Release` workflow creates the
tag and GitHub release automatically on `main`.

### 5. Generate Artifacts, Do Not Hand-Edit Marketplaces

Add a build step that emits host-specific marketplace artifacts at the repository
root so Git-backed installs work directly:

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/<plugin-name>/
  .claude-plugin/plugin.json
  .codex-plugin/plugin.json
  skills/<skill-name>/
dist/
  registry.json
```

The source of truth remains `skills/`. Generated plugin folders should be
disposable and regenerated by script; humans should not edit generated
marketplace manifests directly.

### 6. Validate at Three Levels

Validation should happen before publishing:

- Skill validation:
  - Agent Skills naming and frontmatter rules.
  - Required top-level heading.
  - Description length and trigger quality.
  - No CRLF line endings.
  - Optional `scripts/` have executable bit and local usage docs.
- Marketplace validation:
  - Claude Code: `claude plugin validate` against generated plugin folders.
  - Codex: Codex plugin validator against generated `.codex-plugin/plugin.json`.
  - OpenClaw: local validation plus `clawhub` publish dry-run if available.
- Behavioral validation:
  - Small prompt fixtures per skill.
  - Expected trigger and non-trigger examples.
  - Smoke tests for bundled scripts.

### 7. Treat Skills as Supply-Chain Artifacts

Third-party skills and plugins can run commands, call tools, load references,
and interact with secrets through the host agent. A marketplace needs a
security posture from day one.

Minimum controls:

- Require review for any skill that adds `scripts/`, hooks, MCP config, apps,
  or external network assumptions.
- Prefer read-only behavior by default.
- Declare required tools and credentials explicitly.
- Keep secrets out of skill text, prompts, logs, and test fixtures.
- Add content hashes to the registry.
- Publish signed GitHub releases or provenance attestations when practical.
- Add CODEOWNERS for skill domains.
- Run dependency and secret scans in CI.
- Keep marketplace entries pinned to release tags for stable channels.

### 8. Use Native Host Semantics

#### Claude Code

Claude Code supports both standalone skills and plugins. Plugins are better for
sharing, versioning, and marketplace distribution. Plugin skills are namespaced
as `/plugin-name:skill-name`, which avoids conflicts.

Recommended Claude output:

```text
.claude-plugin/marketplace.json
plugins/django/
  .claude-plugin/plugin.json
  skills/django-htmx/SKILL.md
  skills/django-q2/SKILL.md
```

Use a Git-backed marketplace repo where possible. Relative plugin paths such as
`./plugins/django` resolve relative to the marketplace root when the marketplace
is added from Git.

Because this repository publishes `.claude-plugin/marketplace.json` at the root,
`/plugin marketplace add LVTD-LLC/skills` can work directly without cloning and
building locally.

Installation flow:

```bash
/plugin marketplace add LVTD-LLC/skills
/plugin install django@lvtd-skills
/reload-plugins
```

#### Codex

Codex plugins package workflow guidance, skills, and optionally apps or app
templates. For this repo, start with skills-only Codex plugins and add apps only
when a skill genuinely needs a connected system.

Recommended Codex output:

```text
.agents/plugins/marketplace.json
plugins/django/
  .codex-plugin/plugin.json
  skills/django-htmx/SKILL.md
  skills/django-q2/SKILL.md
```

Codex marketplace entries should include installation policy, authentication
policy, and category. Plugin manifests should use strict semver, real author
metadata, and only include app/MCP paths when those files exist.

#### OpenClaw

OpenClaw has native skills and plugins:

- Skills are plain `SKILL.md` folders and can be installed from ClawHub, Git,
  or local paths.
- Plugins can ship skills, but native plugins are more appropriate when adding
  runtime tools, providers, channels, or hooks.

Recommended OpenClaw output:

- Publish each skill individually to ClawHub.
- Generate `openclaw` install docs and `clawhub skill publish` commands.
- Create native OpenClaw plugin packages only for tool-backed capabilities.

Example install commands:

```bash
openclaw skills install django-htmx
openclaw skills install ./skills/django-htmx --as django-htmx
```

For Git-based OpenClaw installs, publish a generated per-skill repository,
branch, or archive whose root contains that skill's `SKILL.md`; OpenClaw's Git
install path expects one skill at the source root.

### 9. Keep the Registry Useful Outside Any One Host

Expand `dist/registry.json` into a proper marketplace API surface:

```json
{
  "schemaVersion": 2,
  "name": "LVTD Skills",
  "repository": "https://github.com/LVTD-LLC/skills",
  "generatedAt": "2026-06-08T00:00:00.000Z",
  "skills": [
    {
      "name": "django-htmx",
      "displayName": "Django HTMX",
      "description": "Build and review HTMX interactions in Django server-rendered projects.",
      "version": "0.1.0",
      "license": "MIT",
      "category": "Web Development",
      "tags": ["django", "htmx", "server-rendered-ui"],
      "path": "skills/django-htmx",
      "entrypoint": "skills/django-htmx/SKILL.md",
      "sha256": "...",
      "hosts": {
        "codex": { "plugin": "django" },
        "claudeCode": { "plugin": "django" },
        "openclaw": { "slug": "django-htmx" }
      }
    }
  ]
}
```

That registry can drive:

- A website marketplace.
- Search and filtering.
- Generated install commands.
- Host-specific marketplace generation.
- Changelog and update checks.

## Implementation Roadmap

### Phase 1: Normalize and Enrich Skills

- Add `license`, `compatibility`, and marketplace `metadata` fields to each skill.
- Replace custom frontmatter parsing with a YAML parser.
- Validate Agent Skills naming rules, max description length, and optional
  metadata.
- Add registry fields for version, license, category, tags, file list, and hash.

### Phase 2: Generate Marketplace Adapters

- Add `scripts/build-marketplaces.mjs`.
- Generate Claude Code marketplace artifacts at `.claude-plugin/` and
  `plugins/`.
- Generate Codex marketplace artifacts at `.agents/plugins/` and `plugins/`.
- Link plugin skill folders back to canonical `skills/<skill-name>/` folders
  instead of copying skill files into each host adapter.
- Generate OpenClaw publish plan.
- Commit the generated root marketplace artifacts so Git-backed installs work
  directly.

### Phase 3: Add Host Validation to CI

- Validate core skills.
- Build all marketplace adapters.
- Validate generated Claude plugin folders.
- Validate generated Codex plugin folders.
- Run smoke prompts or script tests for skills with executable resources.

### Phase 4: Publish Channels

- Stable channel: GitHub releases and release tags.
- Preview channel: branch or prerelease tag.
- Claude Code marketplace: Git-backed `.claude-plugin/marketplace.json`.
- Codex marketplace: Codex plugin directory or private/team marketplace.
- OpenClaw: ClawHub skill publishing.
- Generic clients: `dist/registry.json` and release tarball.

### Phase 5: Build the Marketplace UI

- Static site reads `dist/registry.json`.
- Users filter by host, category, tag, and capability.
- Each skill page shows install commands for Codex, Claude Code, OpenClaw, and
  direct skill installation.
- Include trust metadata: version, release tag, hash, license, last scan, and
  whether the skill bundles scripts or external tool requirements.

## Sources

- [Agent Skills overview](https://agentskills.io/home)
- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [OpenAI Codex plugins and skills](https://openai.com/academy/codex-plugins-and-skills/)
- [OpenAI Help: Plugins in Codex](https://help.openai.com/en/articles/20001256-plugins-in-codex)
- [OpenClaw skills](https://docs.openclaw.ai/tools/skills)
- [OpenClaw plugins](https://docs.openclaw.ai/tools/plugin)
- [OpenClaw ClawHub](https://docs.openclaw.ai/clawhub)
