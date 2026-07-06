---
name: maestro
description: Direct Maestro command hub for Codex slash menu: frontier, settings, terse, and update
license: MIT
---

Use this skill when the user invokes `/maestro`, asks for Maestro slash
commands in Codex, or gives a Maestro command-shaped request such as
`frontier off`, `terse ultra`, `settings status`, or `update`.

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
/maestro frontier single <model>
/maestro frontier fusion <preset>
/maestro frontier fusion custom --models <a,b,c> [--judge <model>] [--synth <model>]
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
node bin/maestro.cjs frontier mode single --model <model> --scope codex-project
node bin/maestro.cjs frontier mode fusion --preset <preset> --scope codex-project
node bin/maestro.cjs frontier mode fusion --preset custom --models <a,b,c> --scope codex-project
node bin/maestro.cjs frontier preset save <name> --models <a,b,c> --scope codex-project
node bin/maestro.cjs frontier preset list --scope codex-project
node bin/maestro.cjs frontier preset delete <name> --scope codex-project
node bin/maestro.cjs frontier run "<prompt>" --scope codex-project
```

Presets include `opus-duo`, `opus-gpt`, `gpt-duo`, `chatgpt-duo`,
`frontier-trio`, `fable-duo`, `fable-gpt`, `fable-trio`, `sonnet-duo`,
`sonnet-gpt`, `sonnet-trio`, `frontier-quad`, `frontier-quint`,
`budget-trio`, `east-west`, `custom`, and saved user presets.

Models include `opus`, `fable`, `sonnet-5`, `gpt-5.5`, `gemini`, `glm`,
`kimi`, and `deepseek`. CN providers use `claude` pointed at each vendor's
Anthropic-compatible endpoint and read `ZAI_API_KEY`, `MOONSHOT_API_KEY`, and
`DEEPSEEK_API_KEY` from the environment at spawn time.

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
