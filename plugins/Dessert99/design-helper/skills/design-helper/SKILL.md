---
name: design-helper
description: Use when several visual variants need to be compared side by side
  (mockups, layouts, or a range of one value such as spacing, radius, shadow, color,
  motion), or when you are about to ask the user to pick between visual options in prose.
  Renders every candidate in one HTML file, opens it in a browser, lets the user
  choose by eye, then applies the choice to the code. Not a design generator; it
  lays out a range, it does not invent a look. Triggers on "5가지 버전으로 보여줘" ·
  "A 랑 B 중에 뭐가 나아" · "시안 여러 개 비교해줘" · "나란히 놓고 보자". Do not use
  for ordinary UI coding, bug fixes, or implementing a design that is already decided,
  and not for building a whole design system, deciding how a feature flows, choosing an
  icon set or a logo, motion that runs on GSAP or Motion or moves several elements in
  order, or syncing a design record to code (the design-system, design-ux, design-brand,
  design-motion and design-sync skills in this plugin).
---

# design-helper

A value read as a number can't be judged: `12px or 16px?` is not a question until both
are drawn. This skill settles one visual value or layout at a time, by eye, on the real
project: it lays the candidates side by side, the user picks one, and the pick goes into
the code. It measures a range; it does not invent a look.

## Paths

Files shared by every skill in this plugin live in `shared/` at the plugin root.

- Claude Code with the plugin installed: the plugin root is `${CLAUDE_PLUGIN_ROOT}`.
- Otherwise (Codex, or a copied or linked skill, where that text stays unreplaced): run
  `cd -P "<this skill's folder>/../.." && pwd` once and use the result. `-P` follows a
  symlinked skill folder to the real clone.

## Run it

Read `<plugin root>/shared/main.md` and follow it. This skill's worker instructions are
`worker.md` in this skill's folder.
