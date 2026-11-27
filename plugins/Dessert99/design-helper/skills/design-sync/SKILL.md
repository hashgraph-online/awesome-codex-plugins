---
name: design-sync
description: "Brings the project's code in line with its design decision record (design-decisions/ or a Notion page): shows each changed token's before and after on the project's real screens with its blast radius, applies only the scope the user picks, and adds a short block to AGENTS.md and CLAUDE.md so later agents follow the record. Changes no decisions; that is design-system. Run only when the user explicitly invokes it (/design-helper:design-sync, or $design-sync in Codex)."
disable-model-invocation: true
---

# design-sync

When a design changes, a generator redraws the screens and the user accepts whatever
moved without knowing what it was. This skill moves only what the record has settled:
it lists every token the code would gain or change, shows the project's real screens
before and after side by side with how many places each change reaches, and applies the
scope the user picks. It then leaves a short block in the project's agent files, so
every later agent session uses the settled values instead of guessing.

## Paths

Files shared by every skill in this plugin live in `shared/` at the plugin root.

- Claude Code with the plugin installed: the plugin root is `${CLAUDE_PLUGIN_ROOT}`.
- Otherwise (Codex, or a copied or linked skill, where that text stays unreplaced): run
  `cd -P "<this skill's folder>/../.." && pwd` once and use the result. `-P` follows a
  symlinked skill folder to the real clone.

## Run it

Read `<plugin root>/shared/main.md` and follow it. This skill's worker instructions are
`worker.md` in this skill's folder.
