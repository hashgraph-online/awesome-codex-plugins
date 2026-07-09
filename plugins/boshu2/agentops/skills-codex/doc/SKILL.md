---
name: doc
description: "Generate docs from repo truth."
---

# Doc Skill

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Generate and validate documentation for any project.

## Execution Steps

Default mode is deliberately thin — a frontier model runs it correctly with no payload. Given `$doc [command] [target]`:

1. **Detect project type** — `ls package.json pyproject.toml go.mod Cargo.toml` + existing `docs/`; classify CODING / INFORMATIONAL / OPS.
2. **Run the command** — `discover` (grep undocumented funcs), `coverage` (documented vs total), `gen [feature]` (read code → stamp function/class markdown), `all`, or `validate`.
3. **Write the report** to `.agents/doc/YYYY-MM-DD-<target>.md` (coverage %, generated, gaps, validation issues), then report coverage + gaps to the user.

Full step-by-step detail — grep recipes, function/class + code-map templates, the report skeleton, key rules, worked examples, and the troubleshooting table — lives in **[references/default-mode.md](references/default-mode.md)** (moved there in the generic-craft trim). Read it when you need the exact shapes; otherwise just do the three steps.

## Reference Documents

- [references/default-mode.md](references/default-mode.md) — default mode (code/API docs): the full Steps 1-7 detail — grep recipes, function/class + code-map templates, report skeleton, worked examples, troubleshooting
- [references/generation-templates.md](references/generation-templates.md)
- [references/prose-and-report-workmanship.md](references/prose-and-report-workmanship.md)
- [references/project-types.md](references/project-types.md)
- [references/validation-rules.md](references/validation-rules.md)
- [references/de-slopify.md](references/de-slopify.md) — Remove AI writing artifacts from docs
- [references/architecture-report.md](references/architecture-report.md) — Generate technical architecture documents

## Examples

```bash
$doc                    # default: docs for the changed surface (references/default-mode.md)
$doc --mode=readme      # gold-standard README, council-validated
$doc --mode=oss         # full OSS doc pack
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Default mode feels heavyweight | Read references/default-mode.md — or ask the model directly for simple docs |
| README mode verdict fails | Re-run with the council findings addressed (see the readme-mode references above) |

