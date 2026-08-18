# Live Mode

Interactive browser variant mode for **designer-skill**: select elements in the running app, request design actions, and hot-swap HTML+CSS variants via the dev server's HMR.

## MCP entry point

1. `load_project_context` — confirm PRODUCT.md (and DESIGN.md when present).
2. `get_command({ verb: "preview" })` — load this file as the authoritative contract.
3. `dispatch_intent` — when the user describes live iteration in natural language.

Live helper scripts (`scripts/live*.mjs`) ship in a future release. Until then, use **browser MCP tools** for navigation, snapshots, and visual verification after applying variants in source.

## When to use

- Compare 2–3 distinct directions on one element or section before committing
- Iterate with the user in the browser without rewriting the whole page
- Validate spacing, hierarchy, and motion on the real DOM (not a static mock)

## Prerequisites

- Dev server with HMR (Vite, Next.js, Nuxt, SvelteKit, Bun) **or** a static HTML page in the browser
- `PRODUCT.md` at project root (or `.agents/context/` / `docs/`)
- `.designer-skill/live/config.json` when the live helper is available (see `project-init.md` Step 6)

## Core workflow

Execute in order:

1. **Boot** — start the designer-skill live helper when scripts are available.
2. **Open** — navigate the browser to the **app URL** that serves the target page (not the helper port).
3. **Poll** — long-poll for events: `generate`, `steer`, `accept`, `discard`, `exit`.
4. **Generate** — load the action's reference via `get_command`; plan three distinct directions; write all variants in one edit.
5. **Steer** — apply user corrections; reply and poll again.
6. **Accept / discard** — promote the chosen variant into source; strip temporary scaffolding (see cleanup below).
7. **Ship gate** — `anti_slop_checklist` before declaring done.

## Harness poll policy

| Harness | Strategy |
|---|---|
| **Cursor** | One-shot poll in a background terminal; restart after each event |
| **Claude Code** | Background task poll |
| **Codex** | Foreground blocking poll (stdout must return to the session) |

No recap, no tutorial output, no pasting full PRODUCT/DESIGN bodies into chat.

## Register and identity

Infer **brand** vs **product** register from PRODUCT.md (SKILL.md preflight). **DESIGN.md wins visual decisions; PRODUCT.md wins strategic/voice decisions.** When DESIGN.md is missing, extract identity from CSS variables, computed styles, and sibling components — identity preservation is the default.

For freeform generation (no named sub-command), follow SKILL.md design laws plus the register tone. Named actions map to `get_command` verbs (`layout`, `color`, `amplify`, etc.).

## Source markers (designer-skill namespace)

All live-mode plumbing uses the `designer-skill` prefix:

| Marker | Purpose |
|---|---|
| `data-designer-skill-variant="N"` | Variant wrapper |
| `data-designer-skill-css="SESSION_ID"` | Inline variant styles |
| `data-designer-skill-variants` | Outer wrapper |
| `<!-- designer-skill-variants-start ID -->` | Scaffold start |
| `<!-- designer-skill-carbonize-start/end SESSION_ID -->` | Temporary accept stitch |
| `<!-- designer-skill-param-values SESSION_ID: {...} -->` | Accepted parameter snapshot |
| `node_modules/.designer-skill-live/<id>/` | Temp Svelte component sessions |

Freeform actions use `action: "freeform"`.

## Accept cleanup (carbonize)

When a variant is accepted with temporary inline CSS:

1. Locate the carbonize block between `designer-skill-carbonize-start/end` comments.
2. Retarget `@scope` rules to semantic classes on the accepted HTML.
3. Unwrap `data-designer-skill-variant` shells and delete dead variant rules.
4. Remove param-value comments and helper `<style>` blocks.
5. Run `detect_antipatterns` on the edited file before ship gate.

## Fallback without live helper

When live scripts are unavailable:

1. Implement 2–3 variant directions as source branches or temporary classes.
2. Use browser MCP (`browser_snapshot`, `browser_take_screenshot`) after each change.
3. Let the user pick a direction; merge into production markup.
4. `detect_antipatterns` on touched files; then `anti_slop_checklist`.

## CSP (dev only)

During init, dev CSP may allow the live helper origin. Patch shape uses `__designerSkillLiveDev` appended to `script-src` and `connect-src`. Set `cspChecked: true` in `.designer-skill/live/config.json` once handled.

## Config schema

`.designer-skill/live/config.json`:

```json
{
  "files": ["index.html"],
  "insertBefore": "</head>",
  "commentSyntax": "html",
  "cspChecked": false
}
```

Framework-specific `files` / `insertBefore` values are detected during `project-init` Step 6.
