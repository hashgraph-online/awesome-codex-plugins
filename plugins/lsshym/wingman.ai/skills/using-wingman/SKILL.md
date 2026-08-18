---
name: using-wingman
description: Use when starting a Wingman-enabled coding session, adapting Wingman across AI coding platforms, deciding which Wingman skill applies, or interpreting Wingman plugin-level instructions versus project-local instructions.
---

# Using Wingman

## Purpose

Use this as Wingman's entry router. Decide which Wingman skill, if any, applies before meaningful coding work, debugging, refactoring, review, or project explanation. This router is not a substitute for the specific skill body.

Wingman covers three recurring agent risks:

- project memory: load relevant context before meaningful work and sync durable outcomes afterward
- contract alignment: protect API, schema, type, event, config, domain, and UI boundaries when meanings may drift
- project maps: find existing capabilities before rebuilding, and catalog durable capability knowledge afterward

Small, isolated tasks can stay small. If no Wingman trigger clearly matches, continue normally.

## Instruction Priority

Wingman skills provide plugin defaults, but user control comes first. Follow the highest applicable instruction source:

1. Direct user instructions, including current-chat requests.
2. Project-local instructions from the active coding platform, such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, or equivalent files.
3. Wingman skills.
4. Default model behavior.

If a project-local instruction conflicts with Wingman, follow the project-local instruction. The user is in control.

## How to Access Wingman Skills

Use the current platform's skill mechanism:

- **Claude Code:** use the `Skill` tool. When invoked, follow the loaded skill directly instead of reading skill files manually.
- **Copilot CLI:** use the `skill` tool. Skills are auto-discovered from installed plugins.
- **Gemini CLI:** use `activate_skill`. Gemini loads skill metadata at session start and activates full content on demand.
- **Codex:** use the platform's native skill loading behavior. If a Wingman skill is already loaded in context, follow it directly.
- **Cursor:** use Cursor's plugin skill UI or slash-command surface where available. Hooks may load `using-wingman` automatically, but manual skill invocation should not depend on hooks.
- **Other environments:** use the platform's documented skill or instruction-loading mechanism.

## Platform Adaptation

Wingman skill bodies are platform-neutral. If a Wingman skill or wrapper mentions platform-specific tool names, adapt them to the current platform.

For tool mappings, read only the relevant reference when needed:

- Codex: `references/codex-tools.md`
- Copilot CLI: `references/copilot-tools.md`
- Gemini CLI: `references/gemini-tools.md`

## Using Wingman Skills

### Decision Rule

Check Wingman skill triggers before meaningful coding work, debugging, refactoring, review, or project explanation.

- If the user directly asks for a Wingman skill, use that skill before other work unless it conflicts with higher-priority instructions.
- If a situational skill clearly matches, use it before acting.
- If only this router matches, decide the next skill and then follow that skill body.
- If no trigger clearly matches, continue normally.

### Skill Priority

When multiple Wingman skills apply:

1. Explicit user-requested skills.
2. `memory-load` before work that needs project context.
3. `data-contracts` or `project-map-find` before implementation when contract or existing-capability triggers apply.
4. `memory-sync` or `project-map-catalog` after meaningful work when durable context or project capability knowledge should be recorded.

Explicit workflow skills still require direct user request unless listed by the user.

## Repository Memory State

Wingman memory follows a repository-scoped opt-in model:

```text
memory capability installed
  = Wingman plugin provides memory skills
  != repository memory enabled

repository memory disabled
  = no .wingman/memory/

repository memory enabled
  = .wingman/memory/brief.md and .wingman/memory/context.md exist

repository memory partial / broken
  = .wingman/memory/ exists but required entry files are missing
```

For ordinary tasks, only invoke `memory-load` or `memory-sync` when repository memory is enabled.

If repository memory is disabled, do not announce or run `memory-load` / `memory-sync` for ordinary work. Continue normally. Mention disabled memory only when the user asks about memory, asks for history or consistency with previous work, explicitly requests memory loading or syncing, or asks to run `memory-setup`.

If repository memory is partial / broken, do not treat the partial files as authoritative memory. Report the missing entry files only for explicit memory requests or tasks that require memory consistency. `memory-setup` is the explicit repair/enable path.

When repository memory is enabled, current memory has priority over history. Use `memory-load` / `memory-sync` for the detailed routing, status, and conflict rules.

Situational skills:

- `memory-load`: use before non-trivial work where durable project context may matter and repository memory is enabled.
- `memory-sync`: use after meaningful work that should be recorded as durable context and repository memory is enabled.
- `data-contracts`: use when data, schema, type, API, event, config, or UI boundary meanings may drift.
- `project-map-find`: use before rebuilding something that may already exist, when locating existing features/pages/modules/components/contracts, or when deciding whether to reuse, extend, wrap, reference, avoid, or create a capability.
- `project-map-catalog`: use after creating or identifying a durable project capability, flow, surface, component, module, utility, pattern, contract, domain, or business concept that future agents should be able to find.

Explicit workflow skills:

- `memory-setup`: initialize Wingman memory files.
- `memory-clean`: clean, compact, prune, deduplicate, reduce memory, or resolve stale/conflicting memory rules only when the user explicitly asks.

Run explicit workflow skills only when the user directly asks for them.

Slash-prefixed forms such as `/project-map-catalog`, `/project-map-find`, or `/memory-setup` are conceptual invocation aliases for skills. Specific platforms may namespace or display them differently, such as `/wingman:memory-setup` in Claude Code.

## Wingman Red Flags

These are signs that a Wingman skill may be needed:

| Thought | Check |
|---------|-------|
| "This is just a field rename." | If it crosses API, schema, type, UI, event, or config boundaries, use `data-contracts`. |
| "I'll create a new component/helper." | If an existing capability or implementation may already exist, use `project-map-find` first. |
| "No need to read memory for this change." | If repository memory is enabled and the work touches business rules, state transitions, permissions, quotas, billing, field mappings, debugging, or refactoring, use `memory-load`. |
| "The work is done; I can just report back." | If repository memory is enabled and the result creates durable context, decisions, or contract knowledge, use `memory-sync`; if it creates findable project capability knowledge, use `project-map-catalog`. |
| "The memory folder is missing, so I'll initialize it." | Do not run `memory-setup` unless the user directly asks for it. |
| "Memory looks too long; I'll clean it now." | Do not run `memory-clean` unless the user asks; during `memory-load`, only warn or stop by pressure severity. |

## Safe Editing

- Preserve existing code during real file edits.
- Do not write placeholder comments such as `// ... existing code ...` into files to stand in for unchanged code.
- Use abbreviated snippets only in chat explanations, examples, or change summaries.
- Keep edits scoped to the user request and the surrounding project design.

## Language

Wingman's published plugin instructions are English by default. Generated memory and user-facing output may adapt to the project memory language or the user's current language.

## Platform Wrappers

Different platforms use different names for persistent instructions and startup behavior. Keep Wingman's canonical behavior in skills; platform wrappers may add their own hooks or manifests to invoke those capabilities.
