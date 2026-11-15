# Methodology Skills

Boss agent methodology skills use platform-discoverable skill bundles.

## Required Layout

Use this layout for every agent-invocable methodology skill:

```text
skill/skills/<domain>/<name>/SKILL.md
```

Examples:

- `skill/skills/pm/requirement-penetration/SKILL.md`
- `skill/skills/architect/tech-research/SKILL.md`
- `skill/skills/shared/tech-stack-detection/SKILL.md`

Do not add flat methodology files such as `skill/skills/pm/example.md`. They are easy for humans to read but are not reliably discoverable by the platform Skill loader.

维护规则：不要新增平铺 `.md` 方法论文件；所有可被 agent 调用的方法论都必须使用 bundle 布局。

## Agent Declarations

Every `Skill(skill: "<domain>/<name>")` call in `skill/agents/boss-*.md` must be declared in that agent's frontmatter:

```yaml
available_skills:
  required:
    - <domain>/<name>
  optional:
    - <domain>/<name>
```

The declaration and the actual calls must stay in sync:

- Declared skills must exist at `skill/skills/<domain>/<name>/SKILL.md`.
- Referenced skills must be listed in `available_skills`.
- Declared skills should be referenced by the prompt so the agent knows when to load them.

## Call Form

Use this canonical call form in agent prompts:

```text
Skill(skill: "<domain>/<name>")
```

Avoid alternate forms such as `Skill({ skill: "<domain>/<name>" })`; keeping one form makes cross-platform prompts and contract tests simpler.

## Shared Skills

Put reusable methodology in `skill/skills/shared/<name>/SKILL.md` only when two or more agents can use it without agent-specific assumptions.
