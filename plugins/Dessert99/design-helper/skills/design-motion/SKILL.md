---
name: design-motion
description: "Decides how one moment moves (a page entering, a list appearing, a panel opening, a scroll section) the way a motion designer would: purpose, choreography, easing or spring, timing, trigger and interruption, and the reduced-motion version, one decision at a time. Candidates play with the project's real library (GSAP or Motion) on its real design, all on one clock with 1x, 0.5x and 0.25x and a scrubber, each with a frame strip and a progress graph measured from the library itself: length, settling time, overshoot and whether layout moves. A scroll-linked moment plays the same scroll path (down, up, down again) in every candidate. Picks go to the project's design decision record as a motion spec; it writes no code. For a single CSS transition value use design-helper instead. Run only when the user explicitly invokes it (/design-helper:design-motion, or $design-motion in Codex)."
disable-model-invocation: true
---

# design-motion

Motion lives in time. A screenshot or `부드럽게 올라온다` can't tell which element leads,
how much the next one overlaps it, or how a section follows the scroll; only playing it
does. A generator writes one animation and nobody sees the others side by side, and a
CSS imitation is no stand-in: GSAP's eases and overlapping timelines, ScrollTrigger and
Motion's springs move differently from CSS. This skill follows a motion designer's order
(purpose, choreography, character, timing, trigger, reduced motion) and plays every
candidate with the project's real library, all on one clock, at full speed, slowed down
or frame by frame, each with a frame strip and a graph measured from the library itself.
The pick is recorded as a motion spec; building it is ordinary coding that the record
guides.

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
