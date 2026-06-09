# Runtype Skills

[![skills.sh](https://skills.sh/b/runtypelabs/skills)](https://skills.sh/runtypelabs/skills)

Official agent skills for the [Runtype](https://runtype.com) platform — install them in Claude Code, Cursor, Copilot, and 35+ other AI coding agents.

## Install

**All skills:**

```bash
npx skills add runtypelabs/skills
```

**Pick specific skills:**

```bash
npx skills add runtypelabs/skills --list
```

## Skills

| Skill | Description |
|-------|-------------|
| [`runtype`](skills/runtype/) | Umbrella onboarding and routing skill for Runtype setup, capability scoping, and choosing the right focused workflow. |
| [`runtype-build-product`](skills/runtype-build-product/) | Build and validate hosted Runtype products with agents, flows, tools, surfaces, records, schedules, secrets, and evals. |
| [`runtype-admin`](skills/runtype-admin/) | Operate live Runtype accounts safely through MCP or Code Mode MCP: inspect resources, debug traces, logs, evals, and apply careful mutations. |
| [`runtype-persona`](skills/runtype-persona/) | Embed, theme, and debug Persona chat widgets, fullscreen assistants, client tokens, artifacts, and browser-side local tools. |
| [`runtype-templates`](skills/runtype-templates/) | Create, validate, and package distributable Runtype FPO templates with pending secrets and import readiness checks. |
| [`runtype-sdk-marathon`](skills/runtype-sdk-marathon/) | Use the Runtype SDK, CLI, Marathon, playbooks, sandboxes, and code-first stored/upsert/virtual workflows. |

## Validation

Run the repository skill lint before publishing:

```bash
node scripts/lint-skills.mjs
node scripts/smoke-install-skills.mjs
```

The lint checks frontmatter, description length, linked references, forbidden internal URLs, common secret leaks, semantic guardrails for drift-prone claims, and extra drift against the neighboring `../core` monorepo when it is present. The smoke test copies each skill into an isolated install directory and confirms standalone metadata and local references still resolve.

For the recommended private-source/public-publish workflow, see [Keeping Runtype Skills in Sync](docs/keeping-skills-in-sync.md).

## Authoring a New Skill

Create a directory under `skills/` with a `SKILL.md` file:

```
skills/
└── my-skill/
    ├── SKILL.md           # Required: frontmatter + instructions
    ├── scripts/           # Optional: executable helpers
    ├── references/        # Optional: API specs, schemas, docs
    └── examples/          # Optional: example inputs/outputs
```

### SKILL.md format

```yaml
---
name: my-skill
description: >-
  What it does and when to use it. Include trigger phrases.
  Max 1024 chars.
user-invocable: true
argument-hint: "[optional args hint]"
---

Instructions for the agent go here. Keep under 500 lines.
Move detailed reference material to references/ or scripts/.
```

### Best practices

- **Description**: Use imperative phrasing ("Use when..."), include specific trigger phrases
- **Size**: Keep SKILL.md under 500 lines / 5,000 tokens
- **Structure**: Move API specs, schemas, and long docs to `references/`
- **Scripts**: Bundle reusable helpers in `scripts/` instead of inlining
- **No secrets**: Never include API keys, internal URLs, or credentials

## License

[MIT](LICENSE)
