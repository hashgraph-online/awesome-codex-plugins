# Mode 1. Thread monitoring — output spec

Canonical sample outputs for the daily thread-monitoring report. See `SKILL.md` for the workflow steps.

## Daily report

| Posted | Author | Post | Comment | Reply? | Stage | Action |
|---|---|---|---|---|---|---|
| 18h ago | Author A | SaaS Co. | "moat moved to taste" | author replied 14h ago | Warm (6-24h window) | Reply now |
| 22h ago | Author B | Enterprise SaaS | "integration depth moat" | No | Cold | Skip |
| 3h ago | Author C | AI vendor | "twin economies" | No | Watch | Check in 3h |

## For each warm thread

- Thread preview (last 3 turns)
- Suggested response (drafted via `linkedin-reply-handler`)
- Reaction target (the specific reply URN, not the post)
- Priority (high / medium / low)

## Weekly roll-up

- Total comments posted
- Author-reply rate (target 15%+)
- Conversion to DM (when thread closes warm)

## Example run

> Input: monitor sbulaev profile, last 24h

> Output:
> - 1 warm thread: the author replied 14h ago on their post. Current stage: Warm (8-24h). Suggested response ready. Action: post within 2 hours.
> - 8 cold threads (no author engagement). Skip.
> - 3 watching threads (<6h old, author may still reply). Check again in 3-6h.
