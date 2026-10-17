# Teaching Skills for Codex

Codex-native packaging of the **Teaching Skills** suite — the full university
teaching lifecycle (design → build → assess → deliver → reflect → improve)
for OpenAI Codex CLI. This is the sibling Codex distribution of
[Teaching Skills for Claude Code](https://github.com/YujxZJCN/teaching-skills).

This repository vendors the suite as a **single Codex skill** that routes to
15 workflows by intent:

```text
skills/teaching-suite/
  SKILL.md            # router: intent -> workflow, plus ts-* alias emulation
  manifest.json       # adapter metadata + upstream commit pin
  VERSION
  agents/openai.yaml
  ts/                 # vendored content (each upstream SKILL.md -> WORKFLOW.md)
    <15 skills>/WORKFLOW.md + agents/ references/ templates/
    shared/ scripts/ commands/ MODE_REGISTRY.md
```

> Generated, not hand-edited. The canonical source is the Claude Code repo; this
> package is reproduced by `scripts/build_codex.py` there, with no drift. Do not
> edit files here directly — change the upstream suite and regenerate.

## Which repo do I want?

- **Claude Code** (CLI / VS Code / JetBrains): use
  [`YujxZJCN/teaching-skills`](https://github.com/YujxZJCN/teaching-skills) —
  native skills, `/plugin` install, `/ts-*` slash commands.
- **Codex CLI**: use this repo — the single-suite Codex skill with `ts-*` aliases.

## Install or update

Install the skill from this repo with the Codex skill installer:

```bash
python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo YujxZJCN/teaching-skills-codex \
  --ref main \
  --path skills/teaching-suite \
  --method git
```

To update, remove the installed copy and reinstall:

```bash
rm -rf "$HOME/.codex/skills/teaching-suite"
python3 "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo YujxZJCN/teaching-skills-codex \
  --ref main \
  --path skills/teaching-suite \
  --method git
```

On macOS / most Linux, Python 3 is `python3`. If your only `python` is Python 3,
substitute it.

## Use

Ask in natural language ("design a course on machine learning for 90 students"),
or use a Claude-style alias as a mode shortcut: `ts-course`, `ts-exam`,
`ts-rubric`, `ts-feedback`, `ts-cohort`, `ts-dashboard`, and more. The router
(`skills/teaching-suite/SKILL.md`) dispatches to the right workflow and enforces
the suite's non-negotiables (professor checkpoints, no invented context,
evidence-bound person-affecting output, integrity-by-design, no student data in
the passport).

**How this works in Codex.** Codex does not register Claude Code slash commands.
The `ts-*` names are *emulated aliases*: the vendored `ts/commands/*.md` files are
prompt recipes the router reads to pick a workflow and mode — they are not
installed commands. Type `ts-exam ...` (with or without a leading slash) and the
router treats it as a mode shortcut. If anything looks wrong after an upstream
change, recover by reinstalling (the update step above) — the skill is a
regenerated build product, so a clean reinstall always restores a consistent state.

The deterministic validators travel too:

```bash
python3 skills/teaching-suite/ts/scripts/check_passport.py course_passport.yaml
python3 skills/teaching-suite/ts/scripts/build_dashboard.py course_passport.yaml
```

## Versioning

Codex package `0.2.1`. Vendored from
`YujxZJCN/teaching-skills@87cc1aa13784` on 2026-10-03. The package version tracks
the adapter independently of the upstream suite version; see `manifest.json`.

## License

MIT — same as the upstream suite. Architecture inspired by
[academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
and its Codex sibling.
