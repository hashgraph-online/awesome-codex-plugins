# Craft: designs (type design)

How to make artboards that look designed rather than generated. Each board is shown alone at its
exact size, so every pixel on it is a choice.

## Design system first

- Before choosing any look, look for the person's design system: `list_artifacts` with
  `type: "design_system"`, or the one they name. Read it with `get_design_system`, put its `css` in
  a `<style>` in the shared head and each of its `font_links` as a `<link>`, and design with its
  tokens and components. Use its exact values, never near ones.
- When they name a brand or product whose real source you can reach (a style guide, a repository,
  files they share), take colors, type, spacing and assets from that source, not from memory.
  Never recreate another company's distinctive design.
- With neither, make a small system for this design and keep to it: one or two Google Fonts chosen
  for the subject (Inter for text is a safe neutral), a ground color, a text color and at most two
  accents of similar strength, four or five type sizes, and one spacing step (8 px) and its
  multiples. Define them as CSS custom properties in the shared head so every board uses the same
  ones.
- Commit to one look you can name in a few words ("quiet editorial, black on cream"), and say it in
  your reply with your assumptions.

## No filler

- Every element earns its place. No lorem ipsum, invented statistics, fake testimonials, dummy
  logos, or sections added to fill space. A board that feels empty is a layout problem: solve it
  with scale and composition, not more content.
- **Placeholders:** a fact you don't have is shown in square brackets and capitals, `[YOUR PRICE]`,
  `[LAUNCH DATE]`, `[CUSTOMER QUOTE]`. An image you don't have is a plain box at the size the real
  one will take, labelled the same way (`[PRODUCT PHOTO]`). List the placeholders left in your reply.
- Ask before adding boards, sections or copy nobody asked for. Options and rationale go in your
  reply, never on a board.

## No AI-design tropes

Leave out what makes a design look generated: gradient washes as backgrounds (above all purple to
blue), emoji as icons or decoration, cards with a colored left border, glows and frosted glass,
every box rounded and shadowed, everything centred, and stock phrases ("Unlock your potential").
Use one set of simple stroke SVG icons (or the design system's), flat toned surfaces, and at most
one soft shadow where something really sits above the page.

## Contrast and touch targets

- Text has 4.5:1 contrast against what is behind it, small grey labels included; 3:1 for text 24 px
  and up, icons, control borders and focus rings. 4.3:1 fails: pick a shade that passes.
- Colors that must be told apart (status, chart series) differ in lightness, not only in hue;
  blue and orange read for more people than red and green.
- On phone and tablet screens, touch targets are at least 44 by 44 px, with room between them.
- For print sizes (96 px per inch), body text is at least 12 pt (16 px), and nothing important sits
  closer than about 24 px to the edge.

## Real controls

- Even in a static mockup, use real elements: `<button>`, `<a href>`, `<input>` with a `<label>`,
  `<select>`. Never a `div` with a click handler. Icon-only buttons get an `aria-label`; decorative
  SVG gets `aria-hidden="true"`.
- When states matter (hover, focus, error, empty, loading), draw them as they look, on boards side
  by side, not as explanatory text.

## Screens and sizes

- Pick the preset for the device (`iphone`, `android`, `desktop`) and design for that exact size:
  no fake browser chrome or status bars, and nothing past the board's edge, which is cut.
- A web page or app screen that people will also use on a phone gets a second board at `iphone`
  with the layout stacked, not shrunk.
- Group related boards with `section` ("Mobile", "Desktop", "Social") in the order people should
  look at them, and give every board a `name` that says what it shows ("Checkout, card declined").
- The same element sits in the same place, in the same style, on every board of a flow.

## Changing a design

- Change only what was asked: every other board, color, size and word stays as it is. Suggest
  broader changes in your reply.
- Keep each board's `id`, so the comments on it stay on it.
