---
name: preview-lab
description: >-
  Fast UI/UX review loop. Puts the screenshots, screens and components you choose into a per-project
  review lab styled like the project, lets the user approve or ask for changes, comment and mark areas,
  and returns that feedback straight to the session, round after round. Captures screenshots with the
  installed Chrome, keeps itself clean, and works in local, remote and cloud sessions. Use when the user
  asks to review, preview, QA or give feedback on UI, screens, components or visuals, or says
  "preview lab", "review lab" or "visual review". Two modes, visual (default) and complete
  (beta, adds UX, UI and accessibility recommendations).
license: MIT
---

# Preview Lab

`$SKILL` = this file's directory. `$PL` = `node "$SKILL/scripts/pl.mjs"` (Node 18+, zero dependencies; run it from the project root). Mutating commands answer with one JSON line; only `init` and `status` print paths. If `node` is missing, tell the user Preview Lab needs it and stop.

## Ground rules

- **What to show is the caller's decision.** This skill never chooses, filters, suggests or adds captures. Show exactly the items you, the calling agent, decide to provide. If the user asks to see something, capture it with your own judgment.
- **One lab per checkout, reused.** Its code (`index.html`) starts as the base template, is branded once with `$PL brand`, then reused. Git worktrees of the same repo keep separate items but share the branding.
- **Always clean.** The lab lives outside the project (`~/.preview-lab/<project>-<hash>/`; `PREVIEW_LAB_HOME` replaces `~/.preview-lab`) and holds only its code, `manifest.json`, the shots the manifest references and the latest feedback. `pl.mjs` deletes everything else, and deletes labs whose checkout is gone. A successful `add` also empties the inbox, so keep nothing there you want to reuse. Never write lab files anywhere else. If the home folder is not writable, `init` falls back to `<project>/.preview-lab/` (git-ignored) and says so.
- **The user's prompt wins.** Mode, grouping, language, location (`init --in-project`), layout changes: map them onto pl commands, the items JSON or lab code edits.
- **Mode**: `visual` (default) collects feedback only. Use `complete` (beta) when the user asks for a complete, full or expert review, an audit, recommendations, or what you would improve: you also write `recommendations` per item. Set it with `"mode"` at the top of the items JSON, and read `references/complete-mode.md` before you start.

## 1. Open the lab

```bash
$PL init     # {lab, inbox, index: unbranded|ok|outdated, round, items, pendingFeedback, server?, customized?}
```

- `pendingFeedback: true`: the last feedback was never acted on. Run `$PL feedback` and deal with it first.
- `index: unbranded`: brand it with `$PL brand`. Do not open `index.html` for this (it is over 50 KB).
  ```bash
  $PL brand                        # prints {brand: the current values, copyKeys: every text of the lab, in English}
  $PL brand "<inbox>/brand.json"   # or pipe it with -; answers {ok, index, warnings?}
  ```
  ```json
  { "name": "Acme", "logo": "<svg…> or an image URL", "lang": "es", "font": "Inter, system-ui, sans-serif", "radius": "8px",
    "light": { "bg": "#…", "fg": "#…", "surface": "#…", "muted": "#…", "line": "#…", "accent": "#…", "on-accent": "#…", "ok": "#…", "warn": "#…", "bad": "#…" },
    "dark": { "bg": "#…", "surface": "#…", "…": "same tokens" },
    "copy": { "send": "Enviar feedback" } }
  ```
  - Every key is optional and keeps its current value when left out. `{}` keeps the neutral look and marks the lab as branded.
  - `copy` overrides lab texts by key (see `copyKeys`): use it to put the lab in the session's language and voice. `null` removes an override.
  - Take the brand from, first match wins: design docs (`DESIGN.md`, brand guidelines), design tokens (Tailwind theme, CSS variables, theme files), the live UI. If there is none, send `{}`.
  - Mapping: `on-accent` is the text color the app puts on its accent buttons; `ok`, `warn` and `bad` are its success, warning and error colors (leave them out if it has none); `radius` is the radius of its buttons and inputs; `logo` is the mark only (inline SVG or image URL; `currentColor` takes the accent), or empty for the initial of `name`.
  - `warnings` (all listed at once) flag pairs that are hard to read in the lab. They are advice: the project's real brand values win. To clear one, adjust the lab-only tokens first (`surface`, `line`, `muted`) and leave brand colors alone, or keep it and move on.
- `index: ok`: reuse it as is. To restyle or retranslate later, run `brand` again. Edit `index.html` itself only for something `brand` cannot do (a layout change the user asked for, a bug), following `references/lab-spec.md`.
- `index: outdated`: run `$PL upgrade`. It keeps the brand blocks. If it answers `CUSTOMIZED`, note the custom edits, run `$PL upgrade --force`, then re-apply them.

## 2. Put items in

Write one JSON file (into `inbox`, or pipe it with `-`) and add it:

```json
{ "title": "Checkout redesign", "subtitle": "…", "mode": "visual",
  "categories": [ { "id": "flow", "label": "Checkout flow" } ],
  "viewports": { "mobile": [390, 844], "desktop": [1440, 900] },
  "items": [
    { "id": "cart", "title": "Cart", "category": "flow", "route": "/cart", "note": "what changed",
      "url": "http://localhost:3000/cart", "capture": { "schemes": ["light", "dark"] } },
    { "id": "promo", "title": "Promo field", "category": "flow", "capture": { "url": "http://localhost:6006/iframe.html?id=promo", "viewports": ["desktop"], "selector": "#root > *", "padding": 16 } },
    { "id": "empty", "title": "Empty cart", "shots": [ { "label": "mobile", "src": "empty-mobile.png" } ] } ] }
```

```bash
$PL add "<inbox>/items.json"    # validates everything, captures, then commits; on any error nothing changes
$PL recapture [id...]           # replay the stored capture recipes (all items, or the given ones)
$PL remove cart promo
```

An item needs at least one of:

| Field | Meaning |
|---|---|
| `shots` | Images you already have from any tool (simulator, device, design export). `src` is relative to the JSON file; files in `inbox` are moved in. |
| `capture` | A recipe pl runs with the installed Chrome, Edge or Chromium. Stored on the item so `recapture` can replay it. |
| `url` | Adds a **Live** tab that embeds the running page, with responsive tools. Keep that server running during the review. |

`capture` fields, all yours to choose (there are no default sizes or URLs):

| Field | Meaning |
|---|---|
| `url` | Page to capture. Defaults to the item's `url`. |
| `viewports` | Names from the top-level `viewports`, or an inline `{ "label": [w, h] }`. One shot per viewport. |
| `schemes` | `["light"]`, `["dark"]` or both. Dark shots are labeled `<viewport> dark`. |
| `fullPage` | Capture the whole scrolling page. |
| `selector`, `padding` | Capture one element: use this for components. Pick the tightest element that holds the whole component, and pad it (about 16 px) so its edges show. |
| `actions` | Steps before the shot, for states: `{"click": sel}`, `{"hover": sel}`, `{"type": [sel, "text"]}`, `{"press": "Escape"}`, `{"scroll": sel or y}`, `{"wait": ms or sel}`. |
| `wait` | Milliseconds, or a selector to wait for, after load (default 500). |

- Re-adding an id updates it. Passing `shots` or `capture` replaces those views and the old files are deleted.
- Shot files are named by content hash, so identical pixels are not a change. After a code change, `$PL recapture` on everything is safe: the answer lists `changed` ids and only those lose their approval.
- `fullPage`, `selector` and `actions` need Node 22+. Without a browser, capture with your own tools and pass `shots`.
- `devices` (top level, `[{label, w, h}]`) overrides the lab's responsive presets.
- **Categorization (default)**: group items into 2–6 sections in flow order (flow steps, pages, component families, states), unless the user asks for something else. Declare every `category` id in `categories`; items with an unknown one land in a final "Other" section.

## 3. Review

Start the lab the way your harness can wait for it:

| Your harness… | Run |
|---|---|
| wakes you when a background command exits (Claude Code: `run_in_background`) | `$PL serve --open` in the background. On Send it prints the feedback and exits 0 (2 = timeout). |
| does anything else, or you are not sure | `$PL serve --open --detach` (drop `--open` if you cannot open a browser; `--port N` if 4747 is taken, otherwise a free port is picked). It returns at once: give the user the URL and end your turn. When they say they sent it, run `$PL feedback`. |
| runs where the user's browser cannot reach `127.0.0.1` (cloud or remote session, strict sandbox), or `serve` fails | `$PL export <file>`: this round as one self-contained HTML file. Deliver it the way your harness hands files to the user. They open it, review, press **Copy feedback** and paste the text into the chat. |

Never leave a blocking `serve` in the foreground: a tool-call timeout would kill it.

`serve` prints `PREVIEW_LAB_URL`. Tell the user the URL in one line (`URL#<item-id>` opens one item), then wait. A lab tab left open from the last round reloads by itself, and `--open` only opens a new tab when none reconnects. `$PL stop` ends a running server. The lab's **Copy as prompt** button gives the same feedback text for pasting into the chat.

## 4. Act, then iterate

The feedback (`$PL feedback` or the serve output) is short markdown:
- statuses: `approved` or `changes` (none = not reviewed)
- areas: `<view> @ x, y, w×h` in % of the whole shot image (full height for full-page shots), measured from its top-left corner, plus a note; areas on the live page include the device size. To see what one points at, open `<lab>/shots/<id>--<view>-*.png`.
- `General`: the round's notes for everything, which may ask for other screens, states or sizes; capture those with your judgment
- `Apply rec`: accepted recommendations; `Declined recs`: do not suggest those again

Plan in a few lines, then implement. For the next round:

```bash
$PL round          # archives this round (read-only in the lab's round selector); approved items leave; the rest keep their feedback as "Last round"; round +1
$PL recapture      # visually changed items are tagged Updated
$PL add …          # new items are tagged New
$PL serve --open
```

The lab keeps the last 5 past rounds with their screenshots (`$PL round --keep N` changes that; `0` keeps none). `$PL reset` empties the lab and its history but keeps its code. `$PL clean` deletes anything unreferenced, including the inbox.
