---
name: live-editor
description: "Use this skill whenever a request involves a Godot project's live editor or running game: inspect scene, node, or UI state; change scenes, nodes, properties, or signals; run a scene; or prove gameplay or UI behavior. Prefer the `hera` CLI over guessing from project files or stale editor state."
---

# Hera live Godot workflow

Use Hera only with a running Godot editor that has the Hera Agent Godot addon
enabled (verified on Godot 4.2–4.7; 4.7 recommended). CLI output is the source
of truth for live editor and runtime state.

## Start with the live editor

1. Run `hera status`. If no live editor is found, ask the user to enable the
   addon under **Project Settings → Plugins**; do not infer editor state from
   files.
2. If multiple editors are found, run `hera instances`. Pass
   `hera --instance <pid>` for any mutation.
3. Before UI work, run `hera guidance ui` and follow its returned mode.

## Keep reads small and writes safe

- Default output is compact. Prefer `hera --ids scene tree`, selected
  `node get --prop/--props`, scoped `game ui tree`, and `game qa discover`
  before full dumps.
- Use `node add/set/remove` and `signal connect/disconnect` for normal editor
  changes; Godot records those as undoable steps. Prefer them to `eval`, whose
  expression can have side effects and is not undoable.
- Scene, resource, script, import, and project-setting commands persist to
  disk. `game node set/call`, `game click`, and `game input` affect only the
  running game and disappear when it stops.
- Keep one editor per project. After direct `.tscn` edits, stop the game,
  `hera scene reload`, then save through the editor.

## Prove the result

- After a change, read the changed property or node tree. After a run, check
  `hera output --type error` or `hera diagnostics`.
- For visual/UI work, use `game ui tree`, semantic `game click`, and
  `hera screenshot --runtime --analyze`. For prompt requirements, prefer a
  `game qa --file` scenario with `requirements` and per-step `covers`.
- After editing GDScript, run that project's headless `--check-only` gate when
  available, then re-check diagnostics.

Hera sends any configured `HERA_AGENT_GODOT_TOKEN` automatically. Never print
or place that token in project files. For the complete command reference, see
the Hera repository's `docs/COMMANDS.md`.
