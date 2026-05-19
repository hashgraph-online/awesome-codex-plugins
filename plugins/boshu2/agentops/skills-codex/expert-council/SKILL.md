---
name: expert-council
description: 'Alias for $council --mode=debate (adversarial named-persona debate).'
---
# $expert-council — alias for $council --mode=debate

`expert-council` has been **absorbed into the `council` skill** as its `debate`
mode. The adversarial named-persona duel — independent verdicts → 0–1000
cross-scoring → mandatory reveal → ranked decision with dissent — is now
`$council --mode=debate`.

This thin alias is kept for one release. **Invoke `$council --mode=debate`
directly.**

## Routing

When invoked, route immediately to `$council --mode=debate` with the same
arguments. Do not run a separate workflow.

| You typed | Runs |
|-----------|------|
| `$expert-council <question>` | `$council --mode=debate <question>` |
| `dueling-idea-wizards` | `$council --mode=debate --focus=ideas` |

## Where the behavior lives now

The full debate-mode contract — persona slate, the duel, the mandatory reveal,
and the score matrix — lives in the `council` skill. Read `skills-codex/council/SKILL.md`
(its `## Modes` section) and follow its reference documents from there.
