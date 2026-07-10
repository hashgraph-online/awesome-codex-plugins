---
name: maestro
description: Direct Maestro command hub for Codex slash menu: compose or choose a Frontier model panel, settings, terse, and update
license: MIT
---

Use this skill when the user invokes `/maestro`, asks for Maestro slash
commands in Codex, asks to compose or choose a Frontier model panel, or gives a
Maestro command-shaped request such as `frontier off`, `terse ultra`,
`settings status`, or `update`.

This is the direct Codex command hub. Enabled Codex skills appear in the slash
command list, so `/maestro ...` should route here instead of requiring
`/prompts:*`.

## Launcher

Prefer project-local launchers from the repo root:

```bash
node bin/maestro.cjs frontier ...
node settings/cli.cjs ...
```

If those files are not present and this skill is loaded from the Maestro Codex
plugin, locate the plugin root by walking up from this `SKILL.md` until
`.codex-plugin/plugin.json` is present, then run:

```bash
node "<maestro-plugin-root>/bin/maestro.cjs" frontier ...
node "<maestro-plugin-root>/settings/cli.cjs" ...
```

Do not edit Maestro state files by hand.

## Command Forms

Map the text after `/maestro` to exactly one operation. For Frontier state,
use `--scope codex-project` unless the user explicitly names another scope.

### Frontier

```bash
/maestro frontier off
/maestro frontier status
/maestro frontier roster
/maestro frontier catalog
/maestro frontier single <model>
/maestro frontier fusion <preset>
/maestro frontier fusion custom --models <a,b,c> [--judge <model>] [--synth <model>]
/maestro frontier compose --models <model>,<model> [--judge <model>] [--synth <model>] [--save <name>] [--dry-run]
/maestro frontier preset save <name> --models <a,b,c> [--judge <model>] [--synth <model>]
/maestro frontier preset list
/maestro frontier preset delete <name>
/maestro frontier run "<prompt>"
```

Run:

```bash
node bin/maestro.cjs frontier mode off --scope codex-project
node bin/maestro.cjs frontier status --scope codex-project
node bin/maestro.cjs frontier roster
node bin/maestro.cjs frontier catalog
node bin/maestro.cjs frontier mode single --model <model> --scope codex-project
node bin/maestro.cjs frontier mode fusion --preset <preset> --scope codex-project
node bin/maestro.cjs frontier mode fusion --preset custom --models <a,b,c> --scope codex-project
node bin/maestro.cjs frontier compose --models <model>,<model> --judge <model> --synth <model> --save <name> --scope codex-project
node bin/maestro.cjs frontier preset save <name> --models <a,b,c> --scope codex-project
node bin/maestro.cjs frontier preset list --scope codex-project
node bin/maestro.cjs frontier preset delete <name> --scope codex-project
node bin/maestro.cjs frontier run "<prompt>" --scope codex-project
```

Start composition with `frontier catalog`: it is the source of truth for
selectable models, presets, aliases, readiness, and required configuration.
Do not invent IDs. `compose` validates one to eight comma-separated models;
without `--dry-run`, it saves and arms the resolved custom fusion panel.

Configure optional Codex aliases only with
`MAESTRO_FRONTIER_MODEL_TERRA`, `MAESTRO_FRONTIER_MODEL_LUNA`, and
`MAESTRO_FRONTIER_MODEL_SOL`. Codex Desktop reads them from `~/.codex/.env`;
restart and open a new thread after changing that file. All panel, judge, and
synthesizer subprocesses are one-shot and read-only.

Before releasing configured optional Codex aliases, run:

```bash
node frontier/smoke.cjs
```

### Settings

```bash
/maestro settings
/maestro settings status
/maestro settings list
/maestro settings help
/maestro settings set <key> <value>
```

Run:

```bash
node settings/cli.cjs status --scope codex-project
node settings/cli.cjs list
node settings/cli.cjs help
node settings/cli.cjs set <key> <value> --scope codex-project
```

Settings keys: `terse`, `frontier`, `context-bar`, `discipline`, `verify`.

### Terse

```bash
/maestro terse off
/maestro terse lite
/maestro terse full
/maestro terse ultra
```

Run:

```bash
node settings/cli.cjs set terse <off|lite|full|ultra>
```

### Update

```bash
/maestro update
```

Run:

```bash
codex plugin marketplace upgrade maestro
codex plugin add maestro@maestro
```

If the marketplace is not configured, run:

```bash
codex plugin marketplace add mbanderas/maestro
codex plugin add maestro@maestro
```

After updating the plugin, tell the user to restart Codex or open a new thread
so the slash-list skill entries, hooks, and refreshed skill files reload.

## Reporting

- After changing Frontier state, verify with
  `node bin/maestro.cjs frontier status --scope codex-project`.
- After changing settings, verify with
  `node settings/cli.cjs status --scope codex-project`.
- Relay command output clearly and include any restart/new-thread requirement.
