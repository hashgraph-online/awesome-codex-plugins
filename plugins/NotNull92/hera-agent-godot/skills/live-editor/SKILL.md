---
name: live-editor
description: "Use this skill whenever a request involves a Godot project's live editor or running game: inspect scene, node, or UI state; change scenes, nodes, properties, or signals; run a scene; or prove gameplay or UI behavior. Prefer the `hera-godot` CLI over guessing from project files or stale editor state."
---

# Hera live Godot workflow

Use Hera only with a running Godot editor that has the Hera Agent Godot addon
enabled (verified on Godot 4.2–4.7; 4.7 recommended). CLI output is the source
of truth for live editor and runtime state.

## Start with the live editor

1. Run `hera-godot status`. If no live editor is found, ask the user to enable the
   addon under **Project Settings → Plugins**; do not infer editor state from
   files.
2. Reads select the first live editor. Mutations reject multiple editors with
   their PID list; use `instances` only to choose a PID, then pass `--instance <pid>`.
3. Before UI work, read `game_feel_ui_mode` from `status`; use `guidance ui`
   when the checklist text is needed.

Editor and game PIDs are separate. Use global `--instance <editor-pid>` for the
editor, then `game --pid <game-pid> ...` to select a fresh entry from
`game instances`, including externally launched games. Keep the game PID on QA
commands and scenarios. Never fall back to a different runtime when it expires.
`--instance`/`--pid` do not isolate `user://`; if `shared_user_data` is set,
split user data directories before parallel QA. Runtime screenshot sizes are
the live viewport; do not assume the project resolution or upscale. If `hera-godot
instances` shows `stale`, the editor process may still be running with an
expired heartbeat — that is not the same as no editor.

The 2.1 CLI shape omits redundant counts/names, false `truncated`, and status
session/path fields. Missing log `source` means file. Pretty/batch share these rules;
explicit `--fields` stay. See `docs/MIGRATING_TO_V2_1.md`.

Value flags accept `--flag=value`; `--flag=` equals `--flag ""`, subject to
the same validation.

## Keep reads small and writes safe

- Default output is compact. Prefer `hera-godot --ids scene tree`, selected
  `node get --prop/--props/--changed`, `scene tree [path] --depth N --type Class
  --props a,b`, `signal list <path> --connected`, scoped `game ui tree`, and `game qa discover`
  before full dumps.
- Use `node add/set/remove` and `signal connect/disconnect` for normal editor
  changes; Godot records those as undoable steps. Prefer them to `eval`, whose
  expression can have side effects and is not undoable.
- Scene, resource, script, import, and project-setting commands persist to
  disk. `game node set/call`, `game click`, and `game input` affect only the
  running game and disappear when it stops.
- Keep one editor per project. After direct `.tscn` edits, stop the game,
  `hera-godot scene reload`, then save through the editor.
- The Hera runtime autoload is excluded from exports and restored afterward;
  do not persist a separate production autoload for the inspector.

## Choose the script language

Use `.gd` for GDScript or `.cs` for C#; optional `--lang gdscript|csharp` on
`script create` must match the extension. Do not infer a default from the
project. Before C# create/open/attach, check `status.csharp_supported`; it reports
Godot .NET capability, not SDK installation. C# templates use a filename-matching
partial class. Build and reload the assembly before attachment; Hera does not
build or generate solution files. C# inspect/current reads loaded-assembly
metadata, which can be unavailable or stale. `script current` cannot observe
external IDE focus. `eval` defaults to C# through the helper host; use
`--lang gdscript` for a GDScript expression.

Runtime QA discovery accepts `qa_*` and `Qa` followed by an uppercase letter,
such as `QaReady`; preserve exact case when calling C# methods. See the Hera
repository's `docs/CSHARP_SUPPORT.md` for setup and limitations.

## Prove the result

- After `node set`, check the response's re-read `value`; use `node get` for
  other properties. Use repeatable `--set prop=value` on `node add` or
  `node instance`; check returned `values`. Creation and properties share one
  undo action. Without `--set`, confirm with `hera-godot --ids scene tree`.
  After a run, check `diagnostics` first; use `output --type error` for raw lines.
- For eventual runtime state, use `game assert ... --within-ms N` (1–30,000).
  QA assertion steps accept `within_ms`. Read `waited_ms`; timeouts return
  `timed_out: true`, the last available `actual`, and exit 1.
- For visual/UI work, use `game ui tree`, semantic `game click`, and
  `hera-godot screenshot --runtime --analyze`. For prompt requirements, prefer a
  `game qa --file` scenario with `requirements` and per-step `covers`.
- After editing GDScript, run `script validate res://file.gd`; fall back to
  the project's headless `--check-only` gate, then re-check diagnostics.
  After C# changes, build the .NET project,
  reload the assembly, and verify runtime behavior; GDScript `--check-only` does
  not compile C#.

Hera sends any configured `HERA_AGENT_GODOT_TOKEN` automatically. Never print
or place that token in project files. For the complete command reference, see
the Hera repository's `docs/COMMANDS.md`.
