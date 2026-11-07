# Build Best Practices

Rules that keep Bifrost work safe, correct, and maintainable. Each rule states the why and shows a good/bad example against the real SDK. The `references/` files teach *how* to use a surface; these files say *what not to get wrong* while using it.

Read the file for every area the change touches, before writing code:

| Read | When the change involves |
|---|---|
| `security.md` | Any workflow, form, app, agent, or table/file policy. Always read this one first. |
| `workspace.md` | Any change to the Workspace or to something it shares with Solutions: finding what exists, who depends on it, duplicates, centralizing |
| `workflows.md` | Python workflows, tools, data providers, scheduled/webhook/topic subscribers |
| `integrations.md` | `integrations.get()`, OAuth, or any call to an external API |
| `data.md` | Tables, table/file policies, claims, managed files, configs, secrets |
| `apps.md` | Any V2 App UI: layout, navigation, routing, states, theming, identity in the browser |

The ordering inside each file is by consequence: rules that cause data exposure or cross-tenant access come first, polish last.

Where a rule names a CLI flag or SDK signature, confirm it in `../generated/` before use; the generated appendices win when they disagree with an example here.
