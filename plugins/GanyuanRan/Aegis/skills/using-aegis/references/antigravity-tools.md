# Antigravity Tool Mapping

Use this reference when adapting Aegis skills to Google Antigravity CLI, IDE, or
app surfaces.

Antigravity is treated as a host surface for the Aegis Method Pack, not as an
Aegis runtime core. Host output remains evidence candidate material unless the
target project or a future runtime core gives it higher authority.

## Current Support Boundary

Google's public Antigravity materials describe:

- Skills
- MCP
- JSON Hooks
- plugins
- slash commands
- subagents
- global and workspace-specific customization
- Antigravity CLI `1.0.1` plugin discovery for skills and agents from
  installed plugin directories

The precise local file layout and plugin manifest contract for third-party
method-pack distribution are still host-version-dependent and must be verified
against the current Antigravity release before writing install instructions that
claim a canonical path.

## Skill Access

Prefer portable text requests until the current Antigravity surface has been
verified:

```text
Use the Aegis `systematic-debugging` skill for this failure.
```

Portable goal entry:

```text
Aegis goal: Fix the auth refresh bug without rewriting the auth system.
```

When Antigravity exposes slash commands for skills or plugins, those commands
may be used as host conveniences, but the portable text form remains the
cross-host Aegis contract.

## Conceptual Tool Mapping

| Skill references | Antigravity equivalent |
| --- | --- |
| `Read` / file reading | Antigravity filesystem read tool |
| `Write` / file creation | Antigravity filesystem write tool |
| `Edit` / file editing | Antigravity file edit / patch tool |
| `Bash` / shell commands | Antigravity terminal command tool |
| `Grep` / content search | Antigravity search tool or shell search |
| `Glob` / file discovery | Antigravity file discovery tool or shell glob |
| `TodoWrite` / task tracking | Antigravity task, artifact, or project tracking surface |
| `Skill` tool | Antigravity Skills / plugin skill activation |
| `Task` / subagent dispatch | Antigravity subagents when enabled |
| `WebSearch` / `WebFetch` | Antigravity web/search tools when enabled |

## Three Host Shapes

### Antigravity CLI

Use terminal-first commands and slash-command configuration when available. CLI
support for subagents means Aegis subagent-heavy skills can map more directly
than they did in transitional Gemini CLI, but verification still requires fresh
evidence from commands, tests, or explicit host output.

### Antigravity IDE

Use workspace-scoped Skills, MCPs, and JSON Hooks where possible while testing
or introducing Aegis to a project. Promote to global configuration only after
the discovery path, reload boundary, and workspace helper path have been
verified.

### Antigravity App

Use app / project artifacts as host-facing projections of Aegis drafts. Do not
relabel Aegis method-pack artifacts as authoritative Antigravity or Aegis
runtime decisions.

## Gemini CLI Transition Boundary

Gemini CLI remains a transitional compatibility reference for historical install
lineage, current Gemini CLI users, and enterprise / paid API key users. New
Google-host work should target Antigravity CLI, Antigravity IDE, or Antigravity
App, while Gemini CLI remains available as a transition path.
