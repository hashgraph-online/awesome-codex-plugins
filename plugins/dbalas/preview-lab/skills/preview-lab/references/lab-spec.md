# Review lab spec (v4)

The contract that `assets/lab.html` (the base template) already fulfills. `pl.mjs init` copies the template into each lab, and `pl.mjs brand` writes its two `BRAND` blocks. Read this spec only when the user asks for a change outside branding, and keep the result compliant. Never keep a second copy of the lab.

## Hard rules

- One file: `index.html` with inline CSS and JS, vanilla only. No dependencies, CDNs or build step. Stay under 56 KB.
- Keep `<meta name="preview-lab-spec" content="4">` in `<head>`.
- Read data from `window.PL_DATA` when it exists (a file made by `pl.mjs export`: screenshots inlined, no server, no history; **Send** becomes **Copy feedback**). Otherwise read it with `fetch('manifest.json', {cache:'no-store'})`. Fetch it again on `visibilitychange` → visible and re-render while keeping drafts, so items the agent adds appear without a reload. Track the open item by id, not by index.
- Escape every manifest string before it goes into HTML.
- No network requests besides the lab's own files. Project fonts and logos are allowed only as inline data or as public URLs the project already uses.

## Branding and text (baked in, not in the manifest)

Branding lives only inside the two `/* BRAND:START … BRAND:END */` blocks, so `pl.mjs upgrade` can carry it over. Edits anywhere else make the lab `customized`, and `upgrade` then needs `--force`.

- **CSS block**: tokens `--bg --fg --surface --muted --line --accent --on-accent --ok --warn --bad --radius --font`, as a full light set (`:root`) and a full dark set (`:root[data-theme=dark]`).
- **JS block**: `const BRAND = {…};` as one line of JSON with `name`, `logo`, `lang` and `copy`, so `pl.mjs brand` can read it back. Every piece of interface text is a key of the `STR` table defined right after the block, and `copy` overrides any of them. New text must be added to `STR`, never hard-coded.
- The feedback markdown is for the agent and stays in English whatever the lab language.

**Theme**: a header toggle that cycles **System → Light → Dark**. System is the default and follows `prefers-color-scheme`. Store the choice in `localStorage['pl:theme']`. `data-theme` on `<html>` always holds the resolved `light` or `dark`, so the dark tokens are defined only once.

## manifest.json (written only by pl.mjs; read-only for the lab)

```json
{ "previewLab": "4", "project": "acme-web", "root": "/path/to/checkout", "repo": "/path/to/.git", "labHash": "…",
  "title": "Checkout", "subtitle": "…", "mode": "visual|complete", "round": 2,
  "categories": [ { "id": "flow", "label": "Checkout flow", "description": "…" } ],
  "devices": [ { "label": "Mobile", "w": 390, "h": 844 } ],
  "items": [ { "id": "cart", "title": "Cart", "category": "flow", "route": "/cart", "note": "what changed",
      "shots": [ { "label": "mobile", "src": "shots/cart--mobile-1a2b3c4d.png", "scale": 2, "captured": true } ],
      "url": "http://localhost:3000/cart", "capture": { "…": "recipe replayed by pl.mjs recapture" },
      "recommendations": [ { "id": "r1", "type": "ux|ui|a11y|responsive|consistency|branding|copy|perf", "severity": "high|medium|low", "text": "…", "area": { "x": 40, "y": 20, "w": 30, "h": 8 }, "shot": "mobile" } ],
      "previous": { "round": 1, "status": "changes", "comment": "…", "areas": [] },
      "added": 2, "updated": 2 } ],
  "history": [ { "round": 1, "title": "…", "subtitle": "…", "categories": [],
      "items": [ { "id": "cart", "title": "Cart", "shots": [], "url": "…", "previous": {}, "added": 1, "updated": 1 } ],
      "feedback": { "submittedAt": "ISO", "general": "…", "items": [ { "id": "cart", "status": "approved", "comment": "", "areas": [], "accepted": [] } ] } } ] }
```

- An item has `shots`, a `url`, or both. With both, show shots first and add a **Live** tab.
- `scale` is the device pixel ratio of a shot. The 100% view shows it at `naturalWidth / scale`.
- Approved items never reach the next round: `pl.mjs round` removes them.
- `history`: every finished round, archived by `pl.mjs round` with its items, shots and the feedback that was sent (no `feedback` if none was). Only the last 5 are kept by default. The lab shows each one read-only.
- `added` / `updated`: the round in which the item was added or visually changed. When it equals the round on screen (and that round is above 1), tag the item **New** or **Updated**.

## Layout

**Header (sticky, one row)**: brand or logo; title and subtitle (truncated, never wrapped); a `complete · beta` badge in complete mode; progress (`x / n reviewed` plus a bar); theme toggle; **Copy as prompt**; and the primary **Send** button.

**Round bar** (top of the content), one wrapping row:
- a round selector once `history` exists: the current round first, then each past round with its send date (`Round 2 · sent 19 Nov`). Switching rounds replaces the whole content (title, sections, cards, notes, filters, detail).
- on a past round, a short "read-only" note
- the **filters**, each with its count: All and To review always; New, Updated, Changes and Approved once they match at least one item

**Notes for this round** (`general`), right under the round bar: one field for everything at once (overall impressions, other screens, states or sizes to see next). It belongs to its round. The detail toolbar has a **Notes** button that opens the same field in a small dialog and shows a dot when it has text. On a past round it is plain read-only text.

**Past rounds** are read-only: the verdict buttons are disabled, fields are read-only, areas cannot be drawn or deleted, and **Send** is hidden. **Copy as prompt** copies that round's feedback.

**Footer**: one quiet line, "Made with ♥ · Preview Lab", linking to https://github.com/dbalas/preview-lab.

**Grid**: one section per category, in manifest order, with a heading and count. Items without a known category go into a final "Other" section. Cards use an auto-fill grid (about 250px minimum) and show:
- a thumbnail: the first shot cropped from the top, but wide or small images (components) shown whole; a scaled, non-interactive iframe for url-only items
- below the thumbnail (never over the screenshot): the title with the status badge on its right, then a **New** or **Updated** tag, a route chip and the view count
- a notes count (comment and areas)
- a recommendations pill (count, colored by the most severe one) when the item has any

**Detail**: a native `<dialog>` that fills the viewport, opened by a card, by `#<item-id>` in the URL, or from the strip. A round close button sits fixed in the top-right corner (`Esc` also closes).
- **Stage**: view tabs (shot labels, plus Live), prev/next buttons, the image with an area overlay, and a thumbnail strip of every item as a scroll-snap carousel with status dots. View tabs never shrink; the toolbar sits to their right and wraps to its own row when space runs out.
- **Panel**:
  - title, New/Updated tag, category and route chips, and the note
  - a **Last round** box when `previous` exists (status, comment, area notes)
  - the verdict: two large buttons, **Approve** (`--ok`) and **Changes** (`--warn`), each tinted in its color with an icon, a one-line hint and its key (`A`, `C`); the chosen one fills with its color; pressing it again clears it
  - recommendations, when the item has any: a heading with `x / n applied` and **Apply all**, then one card each (severity stripe and badge, type, text, checkbox). Cards with an `area` carry `R<n>`, matching a dashed, numbered marker on their view (`shot`, else the first); hovering either lights up both, clicking a marker flashes its card, clicking `R<n>` switches to that view. Ticking sets Changes. Read-only on past rounds.
  - a comment field
  - an area list (numbered, editable note, delete)
  - a footer with `i / n` and a **Next** button
- On narrow screens (860px and below) the panel stacks under the stage and the whole detail scrolls as one page, with the toolbar and footer sticky.
- On phones (600px and below): one card per row; the header keeps logo, title, theme and Send; the detail toolbar stays on one row; keyboard hints are hidden.

**Areas**: dragging on the image draws a box stored as x/y/w/h in % on the current view label; a plain click marks a small box around the point. The new area's note gets focus and the status becomes Changes if none is set. Typing a comment also sets Changes if none is set. Approve moves to the next item after about 180ms. Areas on the Live tab are labeled `Live <w>×<h>` and only drawn at that device size.

**Tools**:
- For shots: **Fit** and **100%** (true size, see `scale`).
- For the Live tab: device presets from `devices` (or Mobile 390×844, Tablet 820×1180, Laptop 1280×800, Desktop 1440×900), a custom width, rotate, zoom (Fit, 50%, 75%, 100%), an **Annotate** toggle that puts the area overlay over the page, and an **Open ↗** link for pages that refuse to be embedded. Scale the iframe with `transform`, and size it only after the dialog is open.

**Keyboard and touch**: `←` `→` move between items, `1`–`9` switch views, `A` `C` set the status, `Esc` blurs a field or closes the dialog. Ignore shortcuts while typing. A sideways swipe on the empty stage moves between items (on the image it draws).

## State and submit

- Keep drafts of the current round in `localStorage` under a key that includes project and round. Past rounds read their state from `history[].feedback` and never write. Wrap every access in try/catch, and merge defaults into stored drafts so drafts from an older template cannot break anything.
- **Send** asks for confirmation when items are still unreviewed, then POSTs to `feedback` (relative URL):

```json
{ "project": "…", "mode": "visual", "round": 2, "submittedAt": "ISO", "general": "…",
  "items": [ { "id": "cart", "title": "Cart", "status": "approved|changes|", "comment": "…",
               "areas": [ { "shot": "mobile", "x": 42.1, "y": 18.5, "w": 30, "h": 8.2, "note": "…" } ], "accepted": ["r1"] } ],
  "markdown": "<feedback.md text>" }
```

- On 200: clear the drafts and show a full-screen "sent" state that polls `manifest.json` every 2 seconds and reloads when it answers again. The server stops after a send, so an answer means the next round is being served, and the same tab carries on.
- On failure: copy `markdown` to the clipboard and tell the user to paste it into the chat. **Copy as prompt** does the same thing at any time. When the clipboard is blocked, show the text in a dialog to copy by hand.

### markdown (token-lean; omit empty parts)

```
# Preview Lab feedback: <project> · round <n> (<mode>)
<a> approved · <c> changes · <u> unreviewed
**General:** …
**Approved:** Title, Title
## <Title> [<id>] — <status>
<comment>
- Area 1 (<view> @ x <x>%, y <y>%, <w>×<h>%): note
- Apply rec r1 [type/severity]: text
```

Write a `##` block only for items marked Changes, or that have a comment, areas or accepted recommendations.

## Quality bar

- One control system: buttons, selects and text inputs share height (`--h`, or `--hs` in toolbars), border, radius and vertical centering.
- Meet WCAG AA contrast in both themes, and keep cards, fields and borders clearly separated from the background in dark mode.
- Badges, chips, `kbd` and controls are inline-flex and vertically centered. Scrollbars are thin and themed everywhere. Text on a status color uses `--surface`, never plain white or black.
- Show visible `:focus-visible`, label every control, and follow `prefers-reduced-motion`.
- Avoid horizontal scrolling at 360px wide.
- Keep `[hidden]{display:none!important}`: cards set their own `display`, which would otherwise override `hidden` and break the filters.
- Center the stage content with auto margins, not `place-items:center`, so content larger than the stage stays scrollable. The prev/next buttons sit outside the scrolling area.
- Use calm motion (150–250ms) and hover lift on cards.
- Size the stage image with explicit viewport-based `max-width`/`max-height`; percentage sizing inside a shrink-to-fit parent collapses to 0.
