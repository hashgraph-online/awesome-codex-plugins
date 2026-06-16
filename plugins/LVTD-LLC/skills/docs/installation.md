# Installation

LVTD skills are plain folders that contain a `SKILL.md` file. Use the `skills` CLI to install them from GitHub, a direct skill URL, any git URL, or a local checkout.

For Claude Code and Codex, this repo also ships native marketplace artifacts at
the repository root.

## Claude Code Marketplace

```text
/plugin marketplace add LVTD-LLC/skills
/plugin install django@lvtd-skills
/reload-plugins
```

Claude Code exposes the installed skills under the plugin namespace, for
example `/django:django-htmx`.

## Codex Marketplace

```bash
codex plugin marketplace add LVTD-LLC/skills
codex plugin add django@lvtd-skills
```

Codex exposes the installed skills under the plugin namespace, for example
`$django:django-htmx`.

Start a new Codex thread after installing or updating plugins so the newly
installed skills are available in context.

## Marketplace Contents

This repository ships:

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/<plugin-name>/
```

Plugin IDs:

- `cookiecutter`
- `django`
- `nonfiction-book-writing`
- `rust`

Plugin IDs group related source skills. Direct installs through the `skills` CLI
still use canonical skill directory names such as `django-htmx`.

If you installed an older per-skill marketplace plugin, uninstall that plugin ID
and install the matching grouped plugin. For example, replace
`django-htmx@lvtd-skills` with `django@lvtd-skills`.

The previous `calibredb@lvtd-skills` and `make-product-viral@lvtd-skills`
marketplace plugins are no longer generated. Uninstall those marketplace plugin
IDs and install the skills directly with the `skills` CLI instead:

```bash
npx skills add LVTD-LLC/skills --skill calibredb
npx skills add LVTD-LLC/skills --skill make-product-viral
```

## Install With The Skills CLI

```bash
npx skills add LVTD-LLC/skills --skill <skill-name>
```

Example:

```bash
npx skills add LVTD-LLC/skills --skill django-htmx
```

The command installs `django-htmx` from the `LVTD-LLC/skills` repository. The CLI will prompt for the target agent and scope if they are not provided.

## Source Formats

```bash
# GitHub shorthand
npx skills add LVTD-LLC/skills --skill django-htmx

# Full GitHub URL
npx skills add https://github.com/LVTD-LLC/skills --skill django-htmx

# Direct path to a skill in the repository
npx skills add https://github.com/LVTD-LLC/skills/tree/main/skills/django-htmx

# Any git URL
npx skills add git@github.com:LVTD-LLC/skills.git --skill django-htmx

# Local checkout
npx skills add . --skill django-htmx
```

## Codex

Direct skill install:

```bash
npx skills add LVTD-LLC/skills --skill django-htmx -g -a codex
```

Restart Codex or start a new session if your runtime only discovers skills at launch.

## Claude Code

Direct skill install:

```bash
npx skills add LVTD-LLC/skills --skill django-htmx -g -a claude-code
```

If your Claude Code setup uses project-local skills, install into that project's skill directory instead.

## OpenClaw

```bash
npx skills add LVTD-LLC/skills --skill django-htmx -g -a openclaw
```

Use project scope instead of `-g` when you want the skill committed with a project.

## Hermes And Other Agents

For Hermes or another agent runtime, let the CLI prompt for the agent target or pass the relevant `--agent` value:

```bash
# Let the CLI prompt for the target agent
npx skills add LVTD-LLC/skills --skill django-htmx

# Hermes Agent
npx skills add LVTD-LLC/skills --skill django-htmx -g --agent hermes-agent

# Another supported agent identifier
npx skills add LVTD-LLC/skills --skill django-htmx --agent <agent-name>
```

The required contract is intentionally small:

- The target directory must contain one folder per skill.
- Each skill folder must contain a `SKILL.md`.
- The `SKILL.md` frontmatter should include `name` and `description`.

## Local Development

```bash
# Install one skill from the current checkout
npx skills add . --skill django-htmx
```

## Bulk Install

Use `--all` to install every skill to every selected agent without shell-specific wildcard quoting.

```bash
npx skills add LVTD-LLC/skills --all
```
