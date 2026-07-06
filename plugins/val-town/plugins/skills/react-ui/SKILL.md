---
name: react-ui
description: Use when building any val with a user interface — dashboards, web apps, landing pages, forms, admin tools, anything users see in a browser. Covers JSX/React conventions, Twind/Tailwind styling, React version pinning, the view-source link requirement, and what to avoid (template-string HTML, external assets).
triggers: [react, jsx, tsx, ui, frontend, component, dashboard, page, app, twind, tailwind, styling, css, html]
---

# React UI

For any val that renders a UI, prefer to build it with React components in `.tsx` files, unless the user states otherwise. The `templates/react-hono-starter` template is set up for this — start there with `remix_val` instead of building from scratch.

## File conventions

Put markup, styles, and scripts in real files — avoid template literal strings (e.g. `new Response(\`<html>...</html>\`)`). Code in template strings has no syntax highlighting, no linting, no type checking, and is unreviewable.

- `.tsx` — React/JSX components, any UI with logic or interactivity
- `.html` — purely static markup
- `.ts` — server code and scripts

Build UI **component by component** in `.tsx` files. Compose small components rather than rendering one giant page.

## Styling: Twind + Tailwind

Prefer Twind to apply Tailwind utility classes at runtime — no build step required. Add the script to your HTML shell:

```html
<script src="https://cdn.twind.style" crossorigin></script>
```

Then use Tailwind classes directly in JSX:

```tsx
<div className="flex items-center gap-4 p-6 rounded-lg bg-white shadow">
  <h1 className="text-2xl font-bold">Hello</h1>
</div>
```

Avoid inline `<style>` tags, CSS-in-JS objects, or separate `.css` files, unless the user says otherwise.

## View source link

Every UI val should expose a way for users to see and remix its source. Both parts are required:

1. Backend route:
   ```ts
   import { parseVal } from "https://esm.town/v/std/utils/index.ts";
   app.get("/source", (c) => c.redirect(parseVal().links.self.val));
   ```
2. Visible link in the frontend:
   ```tsx
   <a href="/source">view source</a>
   ```

## React version pinning

A common error — `"Cannot read properties of null (reading 'useState')"` — means a React sub-dependency is loading a different React version. Pin all React-related imports to 18.2.0:

```ts
import SomeLib from "https://esm.sh/some-lib?deps=react@18.2.0,react-dom@18.2.0";
```

## Assets

Do not use external images or hosted assets that may break. Prefer:

- Emojis or unicode symbols
- Inline SVG
- Icon fonts via CDN (Lucide, Font Awesome)

## Surfacing client-side errors

To send browser errors back to val logs (visible via `get_logs`), include this script in your HTML shell:

```html
<script src="https://esm.town/v/std/catch"></script>
```

## Verifying changes

After editing a UI val, call `fetch_val_endpoint` to confirm the page renders without error, then check `get_logs` for any client-side errors. Don't report the change as done without both.
