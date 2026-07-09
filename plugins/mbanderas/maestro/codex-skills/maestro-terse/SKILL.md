---
name: maestro-terse
description: Toggle Maestro terse output level (lite, full, ultra, off) via the settings CLI
license: MIT
---

Toggle the **Maestro terse** output level for this environment. Terse mode
condenses agent replies; levels range from `off` (default verbosity) through
`lite`, `full`, and `ultra` (most compressed).

When the user invokes this skill, run the settings CLI to read or change the
terse level. Do not edit settings files by hand.

## Command launcher

Use `node settings/cli.cjs` when Maestro is installed in the project root. If
that file is not present and this skill is loaded from the Maestro Codex
plugin, locate the plugin root by walking up from this `SKILL.md` until
`.codex-plugin/plugin.json` is present, then run:

```bash
node "<maestro-plugin-root>/settings/cli.cjs" ...
```

## Check current terse level

```bash
node settings/cli.cjs --help
```

Consult the help output for the exact read subcommand, then run it. If
`settings/cli.cjs` is not present, use the plugin-root launcher above.

## Set terse level

```bash
node settings/cli.cjs set terse <level>
```

Valid levels: `off` | `lite` | `full` | `ultra`

Examples:

```bash
node settings/cli.cjs set terse off
node settings/cli.cjs set terse lite
node settings/cli.cjs set terse full
node settings/cli.cjs set terse ultra
```

If the CLI rejects an argument or the subcommand name differs, run
`node settings/cli.cjs --help` first and follow the printed usage.

## Notes

- The change persists in Maestro's settings store; it applies to subsequent
  agent turns in this project.
- Requires `node` on `PATH`. A project-local Maestro install is optional when
  the skill is loaded from the Maestro Codex plugin.
