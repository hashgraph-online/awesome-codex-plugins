---
name: create-skill
description: Use when the user wants to persist a preference, skill, or knowledge. Use when it would aid future val development to store a memory of how best to build something.
triggers: [skill, preference, knowledge, memory]
---

Skills in Val Town instruct Townie and other AI agents using the Val Town MCP server how to write idiomatic vals that respect a user's preferences and knowledge.

In any val, a user can create a `/skills/<name>/SKILL.md` file, e.g. `/skills/design/SKILL.md`. 
Townie and the Val Town MCP server index skills with that directory/file structure across all of a user's vals. 
A user may choose to centralize their skills in one val or co-locate skills across multiple vals.

## Frontmatter

A skill markdown file must have frontmatter:

- `name`: kebab-case name of the skill; contains lowercase letters, numbers, and hyphens
- `description`: helps the agent decide when the skill is relevant. **A good skill description is critical for agent discovery**
- `triggers`: (optional) is a list of keywords to tip off the agent

The `description` and `triggers` fields enable skill discovery, i.e. tells the user's AI agent (e.g. Claude Code, Codex, Cursor) when to use it. 
The more specific the better, including key terms that should trigger use (which can also be enumerated in `triggers`). 
Skills without frontmatter will be silently skipped, so Townie/MCP will not be able to access them.

## Best practices

The [Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) offer skill authoring best practices, including:

- Be concise. The context window is a public good
- Always write in third person
- Default assumption: AI agents are already very smart
- Be as specific as possible (e.g. code is better than plain english where possible)
- Improve skills based on usage and testing

## Example

```md
---
name: design
description: Use when styling a val's UI. Use for frontend vals that return JSX or HTML
triggers: [css, styling, layout, theme]
---

- Use `.css` files, avoid inline styles and Tailwind
- Locate React components in a `/components` directory, one component per file
- Use a sans-serif web-native font stack, no external fonts
- ...
```

## Remixing

A new skill can be created by remixing another user’s skill and customizing the `SKILL.md` file.
There is a remix button in the val.town UI, and a `remix_val` tool in the Val Town MCP server to do so.
