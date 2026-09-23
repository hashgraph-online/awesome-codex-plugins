# Runtype Skills

[![skills.sh](https://skills.sh/b/runtypelabs/skills)](https://skills.sh/runtypelabs/skills)

Official agent skills for the [Runtype](https://runtype.com) platform — install them in Claude Code, Cursor, Copilot, and 35+ other AI coding agents.

## Install

**All skills:**

```bash
npx skills add runtypelabs/skills
```

**Pick specific skills** (repeat `--skill` once per skill; comma lists and globs are not supported):

```bash
npx skills add runtypelabs/skills --skill tool-design --skill tool-design-interface
```

**Browse what's available:**

```bash
npx skills add runtypelabs/skills --list
```

## Skills

### Runtype platform

Start with `runtype`; it routes to the focused skill for the job.

| Skill | Description |
|-------|-------------|
| [`runtype`](skills/runtype/) | Scope a Runtype project or set up platform access; route implementation to the relevant Runtype skill. |
| [`runtype-build-product`](skills/runtype-build-product/) | Build or modify Runtype-hosted AI products, agents, flows, and surfaces using current platform instructions. |
| [`runtype-admin`](skills/runtype-admin/) | Inspect, debug, or manage a live Runtype account through MCP or CLI; mutate only within the requested scope. |
| [`runtype-persona`](skills/runtype-persona/) | Embed, style, or debug Runtype Persona widgets and browser-side chat integrations. |
| [`runtype-external-agents`](skills/runtype-external-agents/) | Connect externally executed agents (Flue, Cloudflare Agents SDK, Vercel AI SDK, LangGraph, custom loops) to Runtype traces, evals, or surfaces; not Runtype-hosted execution. |
| [`runtype-templates`](skills/runtype-templates/) | Create, validate, or package distributable Runtype FPO templates and their setup requirements. |
| [`runtype-sdk-marathon`](skills/runtype-sdk-marathon/) | Build source-controlled Runtype workflows with the SDK or CLI, including Marathon tasks and playbooks. |

### Tool design

Framework-agnostic guidance for designing the tools an AI agent calls. Start with `tool-design`; it routes to the focused guide.

| Skill | Description |
|-------|-------------|
| [`tool-design`](skills/tool-design/) | Design or audit an AI agent toolset; route naming, schemas, output, errors, execution, and security to focused guides. |
| [`tool-design-interface`](skills/tool-design-interface/) | Design agent-facing tool names, descriptions, and parameter schemas; diagnose incorrect tool selection or inputs. |
| [`tool-design-output`](skills/tool-design-output/) | Design agent tool results, including pagination, partial success, context size, and actionable next steps. |
| [`tool-design-errors`](skills/tool-design-errors/) | Design actionable agent tool errors, ambiguity handling, retry guidance, and fallback behavior. |
| [`tool-design-execution`](skills/tool-design-execution/) | Design agent tool execution: async jobs, idempotency, timeouts, transactions, and compensation. |
| [`tool-design-composition`](skills/tool-design-composition/) | Compose and expose agent toolsets: task-level operations, batching, discovery, dry runs, and versioning. |
| [`tool-design-security`](skills/tool-design-security/) | Design tool identity, credential injection, authorization, tenant scope, and audit boundaries. |

Skill descriptions above mirror each skill's `SKILL.md` frontmatter; update both together.

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
