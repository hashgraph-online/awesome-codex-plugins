---
name: design-brand
description: "Decides a product's icon set and logo direction one decision at a time, each candidate drawn on the spots it is really used: the desktop and 360px mobile header, the 16px browser tab (also enlarged pixel by pixel), an app icon, buttons, table actions and empty states. Compares public icon sets (Lucide, Phosphor, Tabler, Heroicons, Material Symbols) on the project's own concepts, and logo forms, typefaces, symbol directions and small versions as SVG, measuring blur and the thinnest strokes at 16px. Never imitates an existing brand. Picks and the chosen SVG and PNG files go to the project's design decision record; it writes no code. Run only when the user explicitly invokes it (/design-helper:design-brand, or $design-brand in Codex)."
disable-model-invocation: true
---

# design-brand

A logo or an icon set handed over on its own says nothing about how it will look where
it is used. A mark that is fine in a wide header smears in a 16px browser tab and collides
with the menu button in a 360px mobile header; an icon set that looks tidy in a grid
reads heavier or fainter inside a 16px button, a table row or an empty state. A generator
returns one finished image on a white background, with no small version, redraws the
whole mark when one attribute is changed, and cannot say whether it resembles someone
else's. This skill follows a brand designer's order (the brief, then broad directions,
then one attribute at a time, then the small sizes) and draws every candidate as SVG on
the spots it will really be used, side by side, with what was measured at 16px. The picks
and the chosen files are recorded; putting them into the code is ordinary coding that
the record guides.

## Paths

Files shared by every skill in this plugin live in `shared/` at the plugin root.

- Claude Code with the plugin installed: the plugin root is `${CLAUDE_PLUGIN_ROOT}`.
- Otherwise (Codex, or a copied or linked skill, where that text stays unreplaced): run
  `cd -P "<this skill's folder>/../.." && pwd` once and use the result. `-P` follows a
  symlinked skill folder to the real clone.

## Run it

Read `<plugin root>/shared/main.md` and follow it. This skill's worker instructions are
`worker.md` in this skill's folder. Its picks end in `기록 지시:` blocks, never in code
changes.
