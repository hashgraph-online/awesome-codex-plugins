# Handoff format canon

Load for handoff prep and before any "ready for handoff" claim. Covered here: spec card structure (3-5 bullets, deliverable + value), the spacing constants, frame-name clearance (at least 24px), caption layout (badge + title HUG, body + triggers AUTO + FILL), dashed-border captions with no amber, the right-side annotation pattern and its note card component, screen-count anti-inflation, the 4-lens critique (dev, designer, PM, CEO), one locale per file, no AI-stuffed prose.

Codified from review rounds on production handoffs. The `figma-handoff-gate` skill enforces it.

## Terms

- **Spec card:** the card that summarizes one screen or one major component in 3-5 bullets. Still used in new work.
- **Caption:** the content of a spec card, laid out as badge + title, then body + trigger list (see "Caption layout"). The caption layout and caption visual rules still apply. Only the old placement, a caption row below the screens, is deprecated.
- **Note card:** one `HandoffNote` instance in the right-side annotation column, one per behavior or state (see "Annotation pattern"). New work documents screen behavior with note cards.
- **Handoff panel:** a panel of handoff text placed inside a section (see the section bounds item of the checklist). The internal-canon slop signatures at the end of this file apply to its bullets too.

## Spec card structure

- 3-5 bullets MAX per card
- Each bullet = `deliverable + value` (what was built + why it matters)
- NO internal jargon: ticket codes (`TICKET-123`), internal tool names ("the v2 validator"), registry or rule codes, internal canon names
- NO `@user_NNN` placeholders: use realistic names in the file's language (see "Project locale and sample names"), or strip
- NO AI-stuffed verbose explanations
- One spec card per screen / per major component

### Good bullet examples

- "Avatar fills from pravatar.cc: diverse, deterministic by ID"
- "Two-gate review (slop check + handoff gate) before any 'ready' claim"
- "iOS HIG tinted-bg alpha 0.18, never 1.0 (fixes a contrast bug)"

### Bad bullet examples (auto-fail)

- "Fixed the overflow caused by the v2 validator missing the TICKET-123 registry entry": internal jargon
- "Tested with @user_001 / @user_002": placeholder leak
- "Made it more polished and intuitive": AI hype copy
- "Updated the design": no value, no specificity

## Frame layout

### Spacing canon

Current pattern since 2026-05-25: annotations anchored to the right of each screen.

When annotations sit **to the right of each screen** (canonical pattern, see "Annotation pattern" below), the cluster is `[screen][gap][annotation column]`. Spacing rules:

| Token | Value | What it gaps |
|---|---|---|
| `SCREEN_TO_ANNOTATION_GAP` | **80px** | Right edge of screen to left edge of annotation column |
| `CLUSTER_TO_CLUSTER_GAP_H` | **160px** | Right edge of annotation column to left edge of next screen |
| `ROW_GAP_V` | **200px** | Bottom of cluster row to top of next cluster row |
| `SECTION_TITLE_CLEARANCE` | **48px** | Section title baseline to top of first cluster row |
| `FRAME_NAME_CLEARANCE` | **24px** | Auto-rendered frame label above frame to previous row content |

**Legacy floor (older sections without annotation anchoring):** sections built before this pattern used at least 80px between any two frames. Still valid for atlases without per-screen annotations, but new work uses the table above.

**Why generous V > H:** vertical scan beats horizontal scan for dev reading. 200px V keeps each row a discrete "thought". 160px H is enough to break clusters without wasting canvas.

### Old caption-row pattern (deprecated for new work)

- The old "screen row, caption row, screen row" sandwich is retired for new sections.
- New work: annotations LIVE WITH the screen (right side, same row), not BELOW the row.
- Reference case (field note, 2026-05): an 80px row gap with 87-105px captions jammed in, so the caption bottom overlapped the next row by ~40px. The root fix is the anchor pattern (annotations as right-side neighbor), not bigger row gaps with bottom-anchored captions.

### Frame-name clearance

- **At least 24px gap above the first frame** for label readability (caught in a late review round)
- Frame name visible without zooming
- Section title NOT overlapping frame content

### Caption layout (critical fix)

```
[Spec card frame]
├── HUG horizontal: [badge] [title]      ← compact, no FILL inside HUG
└── AUTO vertical: [body]                 ← FILL works here
                   [trigger list]         ← FILL works here
```

WRONG: badge + title + body + triggers all in one HUG horizontal frame with FILL on text = caption FILL-in-HUG overflow.

RIGHT: badge + title HUG horizontal, body + triggers in a separate vertical AUTO frame with FILL.

### Caption visual

- Subtle **dashed border** (1px, neutral color)
- NO amber/yellow slop (lesson from an early review round)
- NO heavy backgrounds, NO drop shadows
- Background: transparent OR very light neutral fill
- These rules cover spec card captions. The note card of the annotation pattern below has its own visual spec, including a small accent on its `Why:` / `Edge:` prefixes.

---

## Annotation pattern (cross-project canon, 2026-05-25)

This is the **default for any project handoff** (product screens, marketing pages, anything visual). Apply it unless the project explicitly opts out in its own agent instructions (`CLAUDE.md`, `AGENTS.md` or equivalent).

### Anchor + layout

- **Position:** right of the screen, vertical column, **top-aligned with screen top**
- **Gap from screen:** 80px (see `SCREEN_TO_ANNOTATION_GAP`)
- **Column width:** 320px (fits ~50 chars per line at 14/20 type)
- **Column auto-layout:** vertical AUTO, FILL height to match screen height when possible, otherwise HUG. FILL needs an auto layout parent (see `references/auto-layout-canon.md`), so it is possible only when the screen and the column sit together in a horizontal auto layout frame. A column placed free on the canvas next to the screen uses HUG.
- **Gap between note cards within column:** 16px

### Note card structure (per behavior, NOT per element)

One card per **behavior or state** the developer needs to understand. NOT one card per UI element. If the screen has 3 meaningful behaviors, 3 cards. Do not pad to 5.

```
┌─ note card ──────────────────────┐
│ [#] OPTIONAL_LABEL                │  ← step number + state tag (Default, Empty, Error...)
│                                   │
│ When [trigger / condition],       │  ← WHEN line, 1 sentence
│ [what happens].                   │  ← WHAT line, 1-2 sentences
│                                   │
│ Why: [intent]                     │  ← WHY, optional, only when non-obvious
│                                   │
│ Edge: [empty / error / loading]   │  ← EDGE, optional, only if state has variation
└───────────────────────────────────┘
```

Layout inside card: vertical AUTO, 12px gap, 16px padding all sides.

### Visual

- Background: `#16181D`, or the project's own dark tokens. The card is dark on purpose: when the handoff shows light mockups, note cards and panels are dark themed, which separates "the design" from "meta-content about the design".
- Stroke: 1px `#2A2E37`, **dashed** (3, 4)
- Radius: 12px
- Type:
  - Label (step + tag): 11/16, all-caps, weight 600, first accent color. Use the project's own accent. With no project accent, default to `#E5484D` (configurable).
  - WHEN + WHAT body: 14/20, weight 400, color `#FFFFFF`
  - WHY / EDGE: 13/18, weight 400, color `#C4C8D0`
  - "Why:" / "Edge:" prefixes: 13/18, weight 600, second accent color, prefix only. Use the project's second accent. With no second accent in the project, reuse the label accent (`#E5484D` by default, configurable).
- NO drop shadow. NO solid card colliding with a solid screen background: the dashed stroke is the separator.

### Copy voice: human, descriptive, dev-readable

**Default pattern:** `When [trigger], [outcome].` In a file written in another language, keep the same sentence shape in that language.

Subject + verb + condition. The developer understands it in one read, with no internal dictionary.

The human-authorship rule of `references/naming-canon.md` covers section and page names, free-form doc frames and comments. A note card keeps the schema below (its short all-caps label and the `Why:` / `Edge:` prefixes); its sentences follow this voice.

### Good copy (paste-ready voice)

- "When the user taps the back arrow, the call keeps running in the background."
- "When the channel has no members, the block disappears and the invite button moves up to the header."
- "If the user has no permission, the tap shows a toast instead of opening the screen."
- "When the message is from someone outside the group, the avatar shows a small badge."

### Bad copy (auto-fail)

- "Implements the empty state behavior": vague, no trigger, no outcome
- "User journey continues seamlessly": AI hype, "seamless" is blocked
- "Empty: hide block, show CTA": bullet shorthand, not a human sentence
- "This screen handles the case when...": preamble before the actual fact
- "The system intuitively manages the transition": AI vocabulary stack
- Anything with em-dashes (U+2014): banned canon-wide

### Schema (default fields)

| Field | When to include | Format |
|---|---|---|
| **Label** (step + tag) | Always | `01 DEFAULT`, `02 EMPTY`, `03 ERROR`. State tag optional if only one state is shown. |
| **WHAT + WHEN** | Always | One block: `When X, Y happens.` Single paragraph, 1-3 sentences. |
| **WHY** (`Why:`) | Only when non-obvious | One sentence. Skip if obvious. Forcing this into every card = AI slop. |
| **EDGE** (`Edge:`) | Only when state varies | One line per variant: `Edge: When no network, button greys out and shows tooltip on tap.` |

**Card density target:** 30-100 words. More than 100 words = split into 2 cards or rewrite. Fewer than 20 words while the developer needs more = add WHY or EDGE.

### Component instance

When applying via `figma_execute`, use a single reusable `HandoffNote` component on the project's Components page with these properties:

- `label` (TEXT, default `"01 DEFAULT"`)
- `whenWhat` (TEXT, default placeholder)
- `why` (TEXT, default empty: when empty, the row hides through `showWhy`)
- `edge` (TEXT, default empty: when empty, the row hides through `showEdge`)
- `showWhy` and `showEdge` (BOOLEAN, default false): they hide the Why and Edge rows. An empty `why` or `edge` text does not hide its row on its own, so bind each row's visibility to its boolean and set it to false on any instance whose row has no text. The names follow the boolean property naming in `references/naming-canon.md`.

Then **instance** the component for each annotation. NEVER raw frames. The component is the canon; instances inherit fixes.

No prebuilt `HandoffNote` component and no generator script ship with these skills. Check the file first: if it already has an annotation component, use that one (its name may differ). If the file has no annotation component, build one once from the spec below, then reuse instances of it for every note. Every value in the table comes from the sections above.

| Part | Spec |
|---|---|
| Component | Named `HandoffNote`, placed on the project's Components page |
| Size | Fills the 320px annotation column. Height follows the content. |
| Layout | Vertical auto layout, 12px gap, 16px padding on all sides |
| Surface | Fill `#16181D`, stroke 1px `#2A2E37` dashed (3, 4), radius 12px, no drop shadow (or the project's own dark tokens) |
| Label row | Step number + state tag (`01 DEFAULT`). 11/16, all-caps, weight 600, accent color. Bound to the `label` property. |
| Body row | The WHEN + WHAT sentence. 14/20, weight 400, `#FFFFFF`. Bound to the `whenWhat` property. |
| Why row | `Why:` prefix at 13/18 weight 600 in the second accent, then the text at 13/18 weight 400, `#C4C8D0`. The prefix is its own text node; only the text node next to it is bound to the `why` property, so setting the property never overwrites the prefix. Row visibility bound to `showWhy`; hidden when there is no text. |
| Edge row | `Edge:` prefix at 13/18 weight 600 in the second accent, then the text at 13/18 weight 400, `#C4C8D0`. The prefix is its own text node; only the text node next to it is bound to the `edge` property. Row visibility bound to `showEdge`; hidden when there is no text. |
| Copy pattern | `When [trigger], [outcome].` One block of 1-3 sentences. Why only when non-obvious. Edge only when the state varies. |
| Density | One card per behavior or state. 30-100 words per card. |

The spec fixes size, line height, weight and color. For the font family, use the project's UI typeface.

### Annotation column wrapper

The column is itself a small reusable: `HandoffNoteColumn` (vertical AUTO, 16px gap, fixed width 320, height HUG, or FILL under the condition in "Anchor + layout"). It hosts N `HandoffNote` instances. Same rule as the card: build it once if the file has none, then reuse it.

### Migrating existing handoff sections

When the canon updates:

1. Find existing handoff frames with the old caption-below pattern.
2. Move captions to the right-side column, instantiate `HandoffNote` per behavior.
3. Rewrite copy to the WHEN + WHAT voice (strip bullet shorthand, add subject + verb).
4. Re-space row gaps to 200px V / 160px H using the new canon values.
5. Re-run `figma-handoff-gate` to verify.

## Screen count integrity

- Components / banners / sheets / modals categorized **SEPARATELY** from screens
- Number screens only: NN-name pattern
- "12 screens" must be 12 actual screens
- Banners listed under "Banners (3)"
- Sheets under "Sheets (5)"
- Components under "Components (Z)"
- This is the anti-inflation rule: never let sheets, banners or components raise the screen count.

## State variants live in Component sets

- Hover / disabled / loading / error states go in Component variant sets
- NOT as raw delivered frames
- Spec card lists variants by axis: "State=Default|Hover|Disabled"

## 4-lens pre-ship critique (mandatory)

Before declaring done, simulate reading through each lens:

1. **Dev lens**: Can I implement this? Are tokens specified? Are state behaviors clear? Are edge cases mapped?
2. **Designer lens**: Is hierarchy clear? Is spacing consistent? Are components on-system?
3. **PM lens**: Does this match the user story? Are flows complete? Are dependencies called out?
4. **CEO lens**: Does this match the product narrative? Is copy on-brand? Is the value visible at a glance?

Each lens catches a different gap class. Single-lens review = ~50% miss rate.

Stamp the critique: state in your reply what each lens found, or that it found nothing, so the critique stays in the transcript.

## Project locale and sample names

Project-specific rules live in the project's `figma-map.md` (default `docs/figma-map.md`), or in the agent's own memory system if it has one. Two of them recur:

- **One locale for the Figma source.** A project may fix the language of the Figma file. Field example: one production project keeps the Figma source English-only, and the second language exists only as app localization. Follow the project's rule and do not mix locales in one handoff.
- **No `@user_NNN`.** Use realistic names in the file's language. If the project defines personas, use the persona names.

## Reports & comms

When the handoff is also a stakeholder report:

- **No self-corrections exposed**: do not bullet your own audit/fix history
- **Value first**: each bullet = deliverable + value, not process or internal canon
- Cut, do not soften: "I audited and fixed X" becomes a plain description of the fix's value to the reader

## Pre-ship checklist (handoff-gate enforces)

- [ ] Annotations live in a right-side column per screen (NOT below the row): see "Annotation pattern" above
- [ ] `SCREEN_TO_ANNOTATION_GAP` = 80px (screen right edge to annotation column left edge)
- [ ] `CLUSTER_TO_CLUSTER_GAP_H` = 160px (cluster to next cluster, horizontal)
- [ ] `ROW_GAP_V` = 200px (cluster row to next cluster row, vertical)
- [ ] Annotation copy uses the `When X, Y happens.` voice: human sentence, not bullet shorthand
- [ ] Annotation cards instantiate the `HandoffNote` component (NOT raw frames)
- [ ] No em-dashes in annotation copy
- [ ] Legacy floor still allowed for sections without per-screen annotations: frames spaced at least 80px apart
- [ ] First frame has at least 24px clearance for the name label
- [ ] Captions use the badge + title HUG / body + triggers AUTO + FILL pattern
- [ ] Captions visual: dashed border, no amber
- [ ] Spec card bullets: deliverable + value, no jargon, no placeholders, no AI-stuff
- [ ] Screen count not inflated (sheets/banners/components separate)
- [ ] State variants in Component sets, not raw frames
- [ ] 4-lens critique done (the work was read through the dev, designer, PM and CEO lenses), or its stamp recorded (what each lens found, stated in your reply)
- [ ] One project-appropriate locale (English-only when the project fixes the Figma source to English)
- [ ] No `@user_NNN` placeholders
- [ ] No internal jargon leaks
- [ ] **Section bounds discipline:** every child of a Figma SECTION sits within `(0, 0)` to `(section.width, section.height)`. Sections do NOT auto-grow: after appending or moving children, call `section.resizeWithoutConstraints(maxX + PAD, maxY + PAD)`. Handoff panels go INSIDE the section at `(60, 60)`, never at negative coordinates.

## Internal-canon slop signatures (when card copy surfaces on canvas)

When spec card / handoff panel bullets appear on the canvas (not just in repo docs), additional slop signatures betray AI generation. Strip these from visible copy and keep them in repo docs only:

- **Internal canon codes:** `Axis N`, `Phase X`, `Session [A-Z]`, internal rule ids such as `ABC-RULE-*`. Exception: when the code IS the canonical artifact the developer looks up (for example a business rule id such as `RULE-001`), keep it.
- **Process leaks:** `carve-out`, `delivery`, `scope boundary`, `per the second-pass Q3 default`, `review-2 parlay`, `body copy frozen in review 2`
- **Marker-tag leaks:** `TODO_MARKER`, `sharedPluginData['<namespace>']...`
- **Backticked node ids in body bullets:** the node id belongs once in the card subtitle, not littered through bullets. Use plain prose: "the item unavailable state" instead of "Error variant `123:456`"
- **"Half-promises" deferring to future sessions:** "Phase X will cover this", "deferred to a future pass", "out of scope for this pass"

Field note, 2026-05: the designer flagged handoff notes that read as AI-generated because they carried so much very technical detail. Write plain dev-note prose, with a citation only when the citation is the artifact the developer needs.
