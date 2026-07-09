# Project Map Kind Selection

Use this reference only when choosing the kind is ambiguous.

## Quick Rules

| Kind | Use For | Typical Evidence |
| :--- | :------ | :--------------- |
| `feature` | User-facing or business-named capability | route, page, menu, domain docs, tests, APIs |
| `flow` | Multi-step process across files or states | orchestrator code, state machine, UI steps, tests |
| `surface` | Page, route, modal, menu entry, external interface | router, page component, menu config |
| `component` | UI component, control, composite widget, tightly coupled UI hook | component source and usages |
| `module` | Business module, coordinator, service, state owner | module source, imports, tests |
| `utility` | Function, hook, adapter, parser, formatter, script | source signature and usages |
| `pattern` | Reusable implementation approach not owned by one file | representative implementations |
| `contract` | API, DTO, schema, event, config shape, type boundary | schema, type, OpenAPI, handler, client |
| `domain` | Business area that groups entries | multiple entries, routes, docs, module roots |
| `glossary-term` | User phrase to code-name mapping | user wording, code symbols, routes, APIs |

## Tie Breakers

- If users would ask "where is this feature?", prefer `feature`.
- If the core value is the sequence of steps, prefer `flow`.
- If the entry is mostly a route/page/modal entry point, prefer `surface`.
- If a reusable implementation has UI, prefer `component`; if it coordinates business behavior, prefer `module`; if it is a small callable helper, prefer `utility`.
- If there is no single owning file and the value is a repeatable recipe, prefer `pattern`.
- If the main risk is semantic drift across API/schema/types, prefer `contract`.
- If the entry mainly helps translate user words into code search terms, prefer `glossary-term`.

## First-Version Scope

Support all kinds, but keep `domain` and `glossary-term` lightweight. Do not let them turn cataloging into a broad project analysis task.
