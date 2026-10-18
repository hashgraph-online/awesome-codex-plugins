# The Game Codex: the format

`games/<id>/CODEX.md` is plain Markdown that reads well on GitHub, plus a few conventions that
`homie-studio codex <id>` turns into a page in the game's own look. Everything in it is shown as text:
HTML in it is escaped, and an HTML comment (`<!-- … -->`) is a note for you that never shows.

## Frontmatter: the look

```yaml
---
eyebrow: The Ashen Reach            # a small label over each section's heading
tagline: Outrun the fire. Carry the last ember home.
cover: hero/wide.jpg                # behind the title: a picture in the game's folder
palette:
  bg: "#120c0a"                     # the page
  ink: "#f6e7d3"                    # the text
  accent: "#f4b23c"                 # headings, the title
  accent2: "#7ad38a"                # eyebrows, links, the tab bar's Build tab
  danger: "#ff5a4e"                 # danger tags
  good: "#5fdc8b"                   # good tags, ticks
  gold: "#f2c14e"                   # rare tags, the Ready to try box
fonts:
  display: Press Start 2P           # a Google Fonts family name, or a .woff2/.ttf in the game's folder
  body: Inter
  mono: JetBrains Mono
pixel: true                         # pictures keep hard pixel edges when scaled
try: Arrow keys or WASD to run, Space to dash. Open a second tab to see two runners in one room.
---
```

Every key is optional. A colour that is missing comes from the game's landing theme (game.json
`landing.theme`), then the studio's `site/theme.json`. Colours are `#hex`, `rgb()` or `hsl()`; a font is a
family name of letters, digits and spaces, or a file; anything else is left out with a warning. A light
`bg` draws a light page.

## The body

- `# Name` is the title (else game.json's name). The paragraph under it is the pitch.
- Every `## Section` is a tab, in the order written. The usual ones, which `codex` counts as decided once
  they have something in them: **Concept**, **World**, **Characters**, **Art direction**, **Controls**,
  **Rooms and players**, **Music and sound**, **Milestones**, **Open questions**, with **Latest** first.
  Name others freely (Items, Classes, Levels, Story, Death, Quests…); they are tabs too.
- The **Build status** tab is added by itself, from the game's progress feed.

## Cards: `### Name` under any section

```markdown
## Creatures

Wisps chase whoever holds the ember; moths only fight back.

### Cinder Wisp
![Cinder Wisp](art/cinder-wisp.png)
`M-01` `danger: Aggressive · 6 tiles` `gold: Rare at night`
*Level 1–3 · the burning floor*
Drifts toward whoever holds the ember; touching it costs a spark.
- **Where:** everywhere the grass is burning
- **Health:** 2 hits
- **Drops:** a short speed boost
```

- The first picture is the card's art (a sprite or a portrait; small pictures stay crisp with `pixel: true`).
- A line of only `` `code` `` chips: one like `M-01` or `C-12` is the card's id; the rest are tags. A tag's
  colour comes from `good:`, `danger:`, `gold:` or `info:` in front, else from its words (aggressive,
  boss, enemy are danger; passive, ally, player are good; rare, elite, legendary are gold).
- A line in italics is the card's subtitle (level, place, class).
- A list where every item is `**Key:** value` (or `Key: value`) is the card's stats, in the mono font.
- Anything else is the card's text.

Text before the first `###` of a section is its introduction.

## Tables, checklists, the decision log, pictures

```markdown
## Controls

| Action | Phone | Computer | TV and phones |
| --- | --- | --- | --- |
| Run | drag from the lower left | WASD or arrows | each phone is a pad |
| Dash | tap the right side | Space | the pad's A |

## Milestones

- [x] Step 1: a working copy of the starter plays in two browsers
- [ ] Step 2: the valley, the wisps and hand-offs, checked with two browsers

## Latest

- 2026-10-01: Rounds go to 90 seconds; the valley needs time to cross.
- 2026-09-30: Pixel art at 16 px, scaled 4x, no smoothing.
```

- Under **Latest**, a list item that starts with a date is a decision; the page shows them newest first.
- A picture on a line of its own is a figure; several in a row are a gallery. Pictures come only from
  inside the studio (a path from the game's folder, or from the studio's root) and are embedded in the
  page: png, jpg, webp, gif or svg, up to 2.5 MB each and 10 MB in all. A web address is not loaded.
- **Open questions** are drawn as numbered question cards.

## Keeping it true

- One codex per game; change it, never replace it.
- A changed decision: change its section, add a dated line under Latest, redraw (`codex <id>`), and update
  the artifact if there is one.
- The codex is the person's plan, not a public page: it is not served
  with a game's files, and on the site only at `/_studio/codex/<id>/` for the owner.
