# VidSeeds.ai MCP connector skills

Workflow skills for agents using the hosted `vidseeds` MCP server (`https://vidseeds.ai/api/mcp`). Claude Code discovers each `*/SKILL.md` under this tree automatically when the plugin is installed.

## Skills

| Directory                                       | Use when                                                                 |
| ----------------------------------------------- | ------------------------------------------------------------------------ |
| [`vidseeds-setup`](vidseeds-setup/)             | First connect, `AUTH_REQUIRED`, PAT / `VIDSEEDS_PAT`, OAuth on Claude.ai |
| [`vidseeds-efficiency`](vidseeds-efficiency/)   | Seeds, daily MCP quota, async jobs, avoiding wasted calls                |
| [`vidseeds-thumbnails`](vidseeds-thumbnails/)   | Generate, edit, studio, apply to project, publish to YouTube             |
| [`vidseeds-projects`](vidseeds-projects/)       | YouTube → project → metadata → platform config                           |
| [`vidseeds-analytics`](vidseeds-analytics/)     | Channel intel, autopsy, discovery, keywords                              |
| [`vidseeds-local-video`](vidseeds-local-video/) | Local files, ffmpeg recipes, precision trim                              |
| [`vidseeds-publishing`](vidseeds-publishing/)   | Platform connections, preflight, confirm publish                         |

Read **`vidseeds-efficiency`** before long or expensive workflows.

## Authoring format

Each skill is `skills/<name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: vidseeds-example
description: Use when … (triggers the Skill tool)
---
```

Required keys: `name`, `description`. Use one-line `description` strings (avoid YAML `>-` block scalars).

## Content boundary

See [`../MAINTAINERS.md`](../MAINTAINERS.md). Do not document admin tools, internal paths, or provider routing.

## Sync with the MCP server

Skills are maintained in the **private monorepo** under `plugins/vidseeds-mcp/skills/`. When `lib/mcp/tools/**` changes, update skills and run `bun run check:mcp-plugin-skills` from the monorepo root.
