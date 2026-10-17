---
name: camera-control
description: >
  CRITICAL WHILE ARMED: capture, understand NEW image, USE in reasoning, turn-gate
  record+ready. Blind or theater answers INVALID. Topic irrelevant. Off to disarm.
---

# Agent Vision (Codex)

Recipes: see repo `hosts/grok/skills/agent-vision/references/mood-roast-recipes.md` for shared JSON/roast detail (Codex uses `codex exec -i` for mood/roast).

## HARD GATE — vision in reasoning

ARMED after `/agent-vision` until off. New chat OFF.

**Non-whitelist turns while ARMED:**

1. Do not answer yet.
2. First shell: capture to `$HOME/.codex/agent-vision/frames` via `.../1.5.0/dist/agent-vision-capture-file`.
3. **Ambiguity burst:** one second capture if first unusable.
4. Understand image (`codex exec -i` for mood/roast; path for snapshot).
5. **USE** what you saw in reasoning/delivery (not identical-to-blind).
6. `agent-vision-turn-gate begin` then after capture `record --path "$OUTPUT"` then `ready` (fail-closed, single-use; next turn needs a new record).
7. Then answer.

**FORBIDDEN:** skip for non-visual; capture-without-use; skip turn-gate ready.

**Skip whitelist only:** pure off; pure status/`status`; pure streaming.

## Disposition playbooks (delivery only)

| State | Do | Don’t |
| --- | --- | --- |
| `focused_neutral` | Clear, direct | Over-hedge |
| `frustrated_or_blocked` | Lead with fix | Long preamble |
| `tired_or_overloaded` | Shortest correct path | Option walls |
| `curious_or_exploratory` | Extra context/options | Premature lock-in |
| `skeptical_or_evaluating` | Evidence first | Hand-wavy claims |
| `high_stakes_or_cautious` | Confirm before irreversible | Silent risk |
| `absent`/`uncertain` | Words only | Invent mood |

## Modes

bare/mood arm+loop; snapshot/roast arm+mode; status; off; streaming disabled.

```bash
agent-vision-sticky on|off|status --host codex
agent-vision-purge-frames --ttl-days 7 --codex
```

## Mood prompt (after capture)

`codex exec --ephemeral --skip-git-repo-check -i "$OUTPUT" --` with strict mood JSON keys/gates as in references (presence, interaction_state, confidence, observable_basis, assistant_adjustments). Do not display JSON; use in delivery.
