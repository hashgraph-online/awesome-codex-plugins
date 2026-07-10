---
name: maestro-frontier
description: Maestro Frontier local multi-CLI fusion engine - compose or choose a read-only model panel, inspect the catalog, arm, disarm, or run it
license: MIT
---

Drive the **Maestro Frontier** engine: a local multi-CLI fusion engine where a
parallel panel feeds a judge and grounded synthesis. When a user asks to
compose or choose a model panel, route the request to `frontier compose` after
consulting `frontier catalog`; never guess a model or preset ID.

When the trusted Maestro Codex plugin hook is installed, arming a non-`off`
mode makes normal later Codex prompts auto-run through Frontier. `run` remains
an advanced, manual one-off. Do not edit Frontier state files by hand.

## Command launcher

Use `maestro` when it is on `PATH`. If it is not, and this skill is loaded from
the Maestro Codex plugin, locate the plugin root by walking up from this
`SKILL.md` until `.codex-plugin/plugin.json` is present, then run:

```bash
node "<maestro-plugin-root>/bin/maestro.cjs" frontier ...
```

In the examples below, `maestro frontier ...` means either the bare command or
that plugin-root launcher.

## Catalog and compose a panel

Use project scope from the repository root for state-changing commands:

```bash
maestro frontier catalog
maestro frontier catalog --json
maestro frontier compose --models <model>,<model> --dry-run --scope codex-project
maestro frontier compose --models <model>,<model> --judge <model> --synth <model> --scope codex-project
maestro frontier compose --models <model>,<model> --save <name> --scope codex-project
```

`frontier catalog` is the source of truth for models, presets, aliases,
readiness, and required configuration. `compose` accepts one to eight
comma-separated models. Judge and synth default to the first panel model.
`--dry-run` changes nothing; a non-dry run saves and arms the resolved custom
fusion panel.

## Modes, inspection, and saved presets

```bash
maestro frontier mode off --scope codex-project
maestro frontier mode single --model <model> --scope codex-project
maestro frontier mode fusion --preset <preset> --scope codex-project
maestro frontier mode fusion --preset custom --models <model>,<model> --scope codex-project
maestro frontier status --scope codex-project
maestro frontier roster
maestro frontier preset save <name> --models <model>,<model> --judge <model> --synth <model> --scope codex-project
maestro frontier preset list --scope codex-project
maestro frontier preset delete <name> --scope codex-project
```

Use `catalog` before selecting any model or preset. `roster` reports only
readiness and configuration names, never secret or configured model values.

## Configuration and release gate

Configure optional Codex aliases only through
`MAESTRO_FRONTIER_MODEL_TERRA`, `MAESTRO_FRONTIER_MODEL_LUNA`, and
`MAESTRO_FRONTIER_MODEL_SOL`. Codex Desktop / IDE sessions read those settings
from `~/.codex/.env`; restart the app and open a new thread after changing it.

Before releasing configured optional Codex aliases, run:

```bash
node frontier/smoke.cjs
```

This explicit release gate invokes only configured optional aliases through the
normal read-only dispatch path.

## Normal and debug use

After mode is non-`off`, use ordinary Codex prompts; the trusted hook supplies
the Frontier result. Turn it off or run one manual prompt with:

```bash
maestro frontier mode off --scope codex-project
maestro frontier run "<prompt>" --scope codex-project
```

All panel, judge, and synthesizer subprocesses are one-shot and read-only:
they return text only and never edit the workspace, commit, or run autonomous
loops. On `ERROR [<reason>]: <detail>`, relay the reason.

## Indicator instruction

<!-- INDICATOR INSTRUCTION - apply every turn while this skill is active -->

Before composing your first reply each turn, run:

```bash
maestro frontier status --scope codex-project
```

Parse the returned JSON `mode` field:

- If `mode` is not `off`, make the **first line** of your reply exactly:
  `Maestro Frontier ON (<label>)`
  where `<label>` is `single - <model>` or `fusion - <preset>`; for a custom
  preset use `fusion - custom (<model1>, <model2>, ...)`.
- If `mode` is `off`, output no indicator line.

<!-- END INDICATOR INSTRUCTION -->
