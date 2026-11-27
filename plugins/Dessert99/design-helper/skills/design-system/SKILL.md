---
name: design-system
description: "Builds a project's design system one decision at a time from a checklist: each item is drawn on a board of the project's real screens, the user picks by eye, and the pick is written to the project's design decision record (design-decisions/ or a Notion page). Writes no code; syncing the record to code is design-sync. Run only when the user explicitly invokes it (/design-helper:design-system, or $design-system in Codex)."
disable-model-invocation: true
---

# design-system

Someone who isn't a designer doesn't know where a design system starts, and a generator
hands over a finished one: nobody can say why it looks that way, and changing one part
redraws the rest. This skill walks a checklist instead. Each item is one decision,
drawn on a board of the project's real screens with everything settled so far applied,
and the user picks by eye. The pick and its reason go into a decision record that every
later agent follows. Values may come from the current code, from a public design system
or from scratch; all of them are only candidates until the user has seen and picked one.

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
