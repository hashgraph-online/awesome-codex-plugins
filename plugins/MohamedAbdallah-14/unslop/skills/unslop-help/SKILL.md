---
name: unslop-help
description: >
  Quick-reference card for unslop modes, sub-skills, and slash commands.
  One-shot display, not a persistent mode. Trigger: /unslop-help,
  "unslop help", "what unslop commands", "how do I use unslop".
---

# Unslop Help

## Purpose

Show a single reference card for unslop modes, related sub-skills, exit phrases, and config. One-shot. Does not toggle modes. Does not write flag files.

## Output

Render the card below in normal prose (not unslop style — this is documentation).

### Modes

| Mode | Trigger | What it does |
|------|---------|--------------|
| `subtle` | `/unslop subtle` | Light touch. Trim AI tells, keep length and structure. |
| `balanced` | `/unslop` (default) | Cut slop, vary rhythm, restore voice. |
| `full` | `/unslop full` | Strong rewrite. Restructure. Allow opinions. |
| `voice-match` | `/unslop voice-match` | Follow a provided voice/style sample. |
| `anti-detector` | `/unslop anti-detector` | Adversarial paraphrase for detector resistance. Use only when explicitly requested. |

Modes persist until changed or the session ends.

### Sub-skills

| Skill | Trigger | What it does |
|-------|---------|--------------|
| `unslop-commit` | `/unslop-commit`, `/commit`, "write a commit" | Conventional Commits in human voice. |
| `unslop-review` | `/unslop-review`, `/review`, "review this PR" | Direct, kind PR review comments. |
| `unslop-file` | `/unslop-file <filepath>`, "unslop this file", "humanize memory file" | Rewrite a markdown file removing AI-isms while preserving code/URLs/structure. |
| `unslop-reasoning` | `/unslop-reasoning`, "fix this chain of thought", "clean up my reasoning" | Strip AI-slop reasoning patterns (over-hedging, over-decomposing, infinite-loop rationalization) from chain-of-thought traces. |
| `unslop-help` | `/unslop-help`, "unslop help" | This card. |

### Deactivate

- `"stop unslop"` or `"normal mode"` — revert immediately
- Resume with `/unslop` (or any mode flag)

### Configuration

- Default mode: `balanced`
- Override: `UNSLOP_DEFAULT_MODE=full` (env), or `~/.config/unslop/config.json`:
  ```json
  { "defaultMode": "full" }
  ```
- `"off"` disables auto-activation entirely
- Resolution order: env var > config file > `balanced`

### More

Full docs and source: <https://github.com/MohamedAbdallah-14/unslop>

## Boundaries

- One-shot. Do not toggle a mode, write a flag file, or persist any state.
- Do not output in unslop style — this card is reference material.
