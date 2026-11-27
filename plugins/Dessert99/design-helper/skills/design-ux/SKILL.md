---
name: design-ux
description: "Decides how one feature works, the way a UX designer would: the task, its flow, screen layout, interaction patterns, states and wording, one decision at a time. Each candidate is a working prototype on the project's real design, with a step strip recorded by actually performing the task, plus clicks, screen changes and keyboard-only completion. Picks go to the project's design decision record; it writes no code. For one feature or screen, not a whole app's structure. Run only when the user explicitly invokes it (/design-helper:design-ux, or $design-ux in Codex)."
disable-model-invocation: true
---

# design-ux

A flow can't be judged from a still screen or a description: how many clicks a task
takes, where people get lost, whether the list keeps its place, only show when the task
is done. A generator builds one flow and nobody learns what the others would have been.
This skill follows a UX designer's order (the goal, the task, then the flow, the screen,
the interactions, the states and the words) and lets the user try the same task in
several working prototypes side by side, each with a strip of the steps it took and what
was measured on the way. The pick is recorded; building it is ordinary coding that the
record guides.

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
