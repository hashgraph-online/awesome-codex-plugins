---
name: plugin-scanner
description: Scan AI agent skills, plugins, MCP servers, and agent tooling for prompt injection, unsafe commands, secret exposure, and supply-chain risks before installing or trusting them.
license: Apache-2.0
---

# Plugin Scanner

Use HOL's local `plugin-scanner` when a user asks to inspect an AI agent skill, plugin, MCP server, agent package, or repository before installation or use.

The scanner is shipped by the open-source `hol-guard` Python package. Scanning runs locally and does not require Guard Cloud.

## When to use this skill

Use this skill when the user asks to:

- scan or audit a `SKILL.md` before installing it;
- inspect an MCP server or agent plugin for security risks;
- check a third-party agent repository before trusting it;
- look for prompt injection, credential exposure, unsafe commands, or suspicious package/install behavior;
- validate a skill/plugin repository in CI or before publishing it.

## Safety rules

- Never execute code from the target repository just to scan it.
- Never run its install scripts, package lifecycle hooks, or arbitrary shell commands.
- Never read `.env` files, credential stores, private keys, or unrelated user secrets.
- Prefer scanning a local path or a repository the user has already chosen to inspect.
- Treat scanner findings as security evidence, not a guarantee that a package is safe.
- Ask before installing `hol-guard` if `plugin-scanner` is not already available.

## Workflow

### 1. Check for the scanner

```bash
command -v plugin-scanner
```

If it is not installed, explain that `plugin-scanner` is provided by HOL Guard and, with user approval, install it in an isolated CLI environment:

```bash
pipx install hol-guard
```

If `pipx` is unavailable, point the user to the HOL Guard installation instructions rather than silently changing their Python environment.

### 2. Scan the target without executing it

For a repository or directory:

```bash
plugin-scanner scan PATH --format markdown
```

For machine-readable results:

```bash
plugin-scanner scan PATH --format json
```

For Agent Skill / plugin structure validation:

```bash
plugin-scanner lint PATH
plugin-scanner verify PATH
```

Use the narrowest target path that contains the material the user asked to inspect.

### 3. Interpret findings

Summarize:

1. the target that was scanned;
2. the highest severity finding;
3. concrete files/rules involved;
4. whether the scanner found prompt-injection, secret/exfiltration, command-execution, dependency/install, or MCP-specific risks;
5. the recommended next action.

Do not claim "safe" solely because no finding was returned. Say that no covered issue was detected by the current scan.

## Common prompts

- "Scan this skill before I install it."
- "Check this MCP server for prompt injection or suspicious commands."
- "Audit this agent plugin repository."
- "Verify this SKILL.md and tell me what is risky."
- "Run a security check on this AI tool before we add it to our project."

## Source

- HOL Guard / plugin-scanner: https://github.com/hashgraph-online/hol-guard
- Distribution companion: https://github.com/hashgraph-online/hol-guard-plugin