# Craft: design systems (type design_system)

How to make a design system people and agents can build from with confidence. Pages built on it
copy its values exactly, so every value has to be the real one.

## Build from the real sources

- Start from what the brand already has: its code (stylesheets, theme files, a component library),
  its style guide, its site, its decks. List the whole inventory first (colors, text styles,
  spacing, radii, shadows, components, logos, icons), build all of it, and say in your reply what is
  left.
- **Exact values.** Copy hex codes, sizes, line heights and radii as the source has them, never
  rounded to a grid or swapped for a framework default. Code beats screenshots; never invent a
  value.
- Keep the source's names where they make sense (`brand.500`, `space.4`), so people recognise them.
- Nothing to build from? Make a small first system and say so: six to ten colors, five to seven
  text styles, four spacing steps, three radii, a paragraph of guidelines and no components.

## Guidelines as a brand book

`guidelines` is the first thing people and agents read. Write it as a short brand book:

- A paragraph on the brand's character and who it speaks to.
- **Content:** voice and tone, with two or three real examples of do and don't (a button label, an
  error message).
- **Visual foundations:** how color is used (which token for what, the one accent), which text
  style for what, spacing and layout, imagery.
- **Iconography and logos:** the icon set and its sizes, the logo's clear space and what never to do
  with it.
- **Usage rules that name tokens:** "Primary actions use `color.accent` on `color.bg`; one primary
  button per view."
- What a page has to provide itself, such as its own link to the fonts.

## Every token with a reason

- Give every token a `$description` that says where it is used ("Text on `bg` and `surface`"), not
  what it is.
- Alias the semantic tokens to the palette (`"accent": {"$value": "{color.brand.500}"}`), so pages
  use `--<prefix>-color-accent` and never a raw palette step.

## Contrast in every theme

- Every text color has 4.5:1 contrast on each background its description names, in the light
  theme and in `themes.dark` (3:1 for text 24 px and up, control borders, focus rings and icons).
  Check each pair, and pick a shade that passes rather than one that nearly does.
- Status colors differ in lightness, not only in hue, so they read for color-blind people.
- When a pair the brand really uses fails, keep it as the source has it, and say so in its
  `$description` and in your reply.
- Design the dark theme; don't invert the light one. Surfaces get lighter as they rise, and accents
  lift a little so they keep their contrast.

## Copy real assets

- Logos, icons and images are copied from the source into the assets as files, never redrawn or
  approximated. With no logo to copy, use the name in plain type and say so.
- Fonts other pages will load are Google Fonts or system stacks. A font file in the assets shows on
  the design system's own site only, so give it a fallback stack and say so.

## Components

- Each component's examples show its real states (default, hover, focus, disabled, error), one
  example per state, with classes such as `.is-hover`, not with explanations.
- The first sentence of a component's description says what it is for; then when not to use it.
- No AI tropes in the examples either: no gradient washes, emoji, or cards with a colored left
  border.

## Changing a design system

- Read it first and change only what was asked, keeping every other token and word as it is.
- Renaming or removing a token breaks the pages built on it. Mark it `$deprecated` with what to use
  instead, and remove it only when asked.
