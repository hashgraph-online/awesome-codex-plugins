# Supercov plugin

Coverage, security and code quality for coding agents. The plugin gives your agent two skills: one measures coverage and code quality and turns the gaps into focused tests or fixes, the other scans for security vulnerabilities. It runs `npx supercov`, so it needs Node.js 22 or newer.

Coverage runs locally. Security and quality send source files to TypeSafe using the `TYPESAFE_API_KEY` environment variable.

## Install

Claude Code:

```text
/plugin marketplace add supercorp-ai/supercov
/plugin install supercov@supercov
```

Codex:

```bash
codex plugin marketplace add supercorp-ai/supercov
codex plugin add supercov@supercov
```

Gemini CLI:

```bash
gemini extensions install https://github.com/supercorp-ai/supercov
```

Other agents that read skills: `npx skills add supercorp-ai/supercov`.

## Commands

Claude Code and Gemini CLI also get four commands:

| Command | What it does |
| --- | --- |
| `/supercov:coverage [test command]` | Writes one test for code no test reaches, and reports coverage before and after |
| `/supercov:security [patch]` | Scans the repository, or a change, for security vulnerabilities |
| `/supercov:quality [patch]` | Ranks files by code smells, or checks what a change introduced |
| `/supercov:review [--base ref]` | Checks a branch or uncommitted change for security and quality problems |

See the [Supercov README](https://github.com/supercorp-ai/supercov#readme) and [supercov.com/docs](https://supercov.com/docs) for everything else.
