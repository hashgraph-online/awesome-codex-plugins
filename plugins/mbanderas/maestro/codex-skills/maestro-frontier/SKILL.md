---
name: maestro-frontier
description: Maestro Frontier local multi-CLI fusion engine - arm, disarm, inspect, roster adapters, save presets, configure CN providers, or debug-run the panel
license: MIT
---

Drive the **Maestro Frontier** engine: a zero-dependency local multi-CLI fusion
engine where a parallel panel of local CLIs feeds a judge model's analysis and a
grounded synthesis.

When the Maestro Codex plugin hook is installed, enabled, and trusted, arming a
non-`off` mode makes normal later Codex prompts auto-run through Frontier until
you turn it off. Users should not need to type `maestro frontier run "<prompt>"`
for normal use.

Map the user's request to one engine CLI call and run it from the repo root.
Do not edit the engine's state file by hand.

## Command launcher

Use `maestro` when it is on `PATH`. If it is not, and this skill is loaded
from the Maestro Codex plugin, locate the plugin root by walking up from this
`SKILL.md` until `.codex-plugin/plugin.json` is present, then run:

```bash
node "<maestro-plugin-root>/bin/maestro.cjs" frontier ...
```

In the examples below, `maestro frontier ...` means either the bare command or
that plugin-root `node .../bin/maestro.cjs frontier ...` form.

## 1. Switch mode

Project/workspace scope is the default recommendation. Use `--scope
codex-project` from the repository root; the CLI expands it to the same
`codex-<8hex>` workspace scope the Codex plugin hook resolves from
`PLUGIN_ROOT` / `PLUGIN_DATA`. Default mode is `off`.

```bash
maestro frontier mode off --scope codex-project
maestro frontier mode single --model <model> --scope codex-project
maestro frontier mode fusion --preset chatgpt-duo --scope codex-project
maestro frontier mode fusion --preset budget-trio --scope codex-project
maestro frontier mode fusion --preset east-west --scope codex-project
maestro frontier mode fusion --preset frontier-trio --judge chatgpt --synth chatgpt --scope codex-project
maestro frontier mode fusion --preset custom --models <a,b,c> --scope codex-project
```

Models: `opus` (Claude Opus 4.8), `fable` (Claude Fable 5), `sonnet-5`
(Claude Sonnet 5) — all need `claude`; `gpt-5.5` (needs `codex`), `gemini`
(needs `gemini`); `glm` (GLM 5.2), `kimi` (Kimi K2.7 Code), and `deepseek`
(DeepSeek V4 Pro) ride `claude` pointed at each vendor's
Anthropic-compatible endpoint. Presets: `opus-duo`, `opus-gpt`, `gpt-duo`,
`frontier-trio`, `fable-duo`, `fable-gpt`, `fable-trio`, `sonnet-duo`,
`sonnet-gpt`, `sonnet-trio`, `frontier-quad`, `frontier-quint`,
`budget-trio`, `east-west`, `custom`, plus saved user presets. Friendly
aliases are accepted: `chatgpt` maps to `gpt-5.5`, and `chatgpt-duo` maps to
`gpt-duo`. The `gpt-duo`, `fable-*`, `sonnet-*`, and `budget-trio` presets
self-judge/synth; `frontier-quad`, `frontier-quint`, and `east-west` keep the
global Opus judge/synth. Fable 5 is subscription-covered only through
2026-07-07, then draws Usage Credits — a non-blocking `[frontier] …` stderr
advisory fires past the cutoff; relay it to the user.

Judge + synth default to Opus except for presets with explicit stage defaults.
Override them for mixed panels with `--judge <model>` and `--synth <model>`;
for example, `--judge chatgpt --synth chatgpt`.

## 2. Inspect readiness and saved presets

```bash
maestro frontier roster
maestro frontier preset save my-duo --models kimi,gpt-5.5 --judge deepseek --scope codex-project
maestro frontier preset list --scope codex-project
maestro frontier preset delete my-duo --scope codex-project
```

`roster` shows each adapter's binary and key availability. It prints env-var
names and set/missing status only, never secret values. CN adapters need:
`ZAI_API_KEY` for `glm`, `MOONSHOT_API_KEY` for `kimi`, and
`DEEPSEEK_API_KEY` for `deepseek`.

For Codex CLI launched from a terminal, exported env vars are enough. Codex
Desktop / IDE sessions may not inherit shell env vars; put required values
and binary overrides such as `MAESTRO_CLAUDE_BIN` in `~/.codex/.env`, then
restart the app and open a new thread:

```bash
export ZAI_API_KEY=
export MOONSHOT_API_KEY=
export DEEPSEEK_API_KEY=
export MAESTRO_CLAUDE_BIN=
```

## 3. Show current mode/preset

```bash
maestro frontier status --scope codex-project
```

If you intentionally want one shared Codex state across unrelated repos, choose
an explicit global name such as `--scope codex-global`. Do not use global scope
unless that cross-repo behavior is what you want.

## 4. Normal use after arming

After mode is non-`off`, type ordinary Codex prompts. The trusted Codex hook
auto-runs Frontier and injects the synthesized answer as context for the live
reply. Turn it off with:

```bash
maestro frontier mode off --scope codex-project
```

## 5. Advanced/debug one-off run

Manual one-off execution remains available for debugging:

```bash
maestro frontier run "<prompt>" --scope codex-project
```

- `off`: prints a notice, spawns nothing.
- `single`: dispatches the one selected CLI, prints its answer.
- `fusion`: runs the panel in parallel, then judge, then synthesizer; prints
  the final answer (a one-line run meta goes to stderr). Report stdout verbatim.

On error the engine prints `ERROR [<reason>]: <detail>` to stderr and exits
non-zero; relay the reason.

## Indicator instruction

<!-- INDICATOR INSTRUCTION - apply every turn while this skill is active -->

Before composing your first reply each turn, run:

```bash
maestro frontier status --scope codex-project
```

Parse the returned JSON `mode` field:

- If `mode` is not `off`, make the **first line** of your reply exactly:
  `Maestro Frontier ON (<label>)`
  where `<label>` is formed as follows:
  - single mode -> `single - <model>` (e.g. `single - opus`)
  - fusion mode -> `fusion - <preset>` (e.g. `fusion - frontier-trio`);
    for a custom preset use `fusion - custom (<model1>, <model2>, ...)`
- If `mode` is `off`, output no indicator line.

<!-- END INDICATOR INSTRUCTION -->

## Notes

- Real `single`/`fusion` runs spawn local CLIs and cost tokens; `off` is free.
- The autorun hook no-ops when `FUSION_DEPTH >= 1`, so child `codex`, `claude`,
  and `gemini` panel processes do not recursively run Frontier.
- Each model's CLI must be on `PATH`, or point at a specific build with
  `MAESTRO_CLAUDE_BIN` / `MAESTRO_CODEX_BIN` / `MAESTRO_GEMINI_BIN`.
- Requires `node` on `PATH`. The bare `maestro` command is optional when the
  skill is loaded from the Maestro Codex plugin; use the plugin-root launcher
  above.
