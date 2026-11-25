# audit: find what is wrong, rank it, save it

**When:** "review this bot", "why is it confusing", "check my diff", "is this safe to merge".
Read-only for the user's code; it writes only `bot-ui/context/` (and not even that under
mandate A0, see `references/redesign-orchestration.md` §0).

## Read

- Whole bot: `references/auditing-existing-bots.md` Pass 0-4 (scope, text inventory, diagnose,
  rank, report). A pasted snippet: its "Auditing a pasted snippet" section only.
- Screen map: `references/navigation-and-flows.md` (states, back, dead ends).
- Text that should be a table, list or collapsible block: `references/content-shape-detection.md`.
- A diff: `references/consistency-and-review.md` "Final review checklist", and
  `references/testing-playbook.md` for the tests the change needs.
- A worked example of a real audit: `references/case-study-btc-tracker.md`.
- The command menu: `references/bot-commands.md` "The lifecycle" (`tgui.py commands audit`).

## Steps

1. `tgui.py context` already ran. If findings are fresh (no `CONTEXT_STALE`), don't re-audit:
   report the open ones and stop. With `CONTEXT_STALE`, audit only the changed files it lists.
2. Detect the SDK and its Bot API ceiling (`tgui.py profile probe --json <project>`,
   `references/sdk-compatibility.md`).
3. Build the screen/state map (every message, keyboard, `callback_data`, command, deep link,
   transition) and classify each screen: entry, menu, form step, confirmation, result, error,
   empty, notification.
4. List only real defects, each with file:line and the rule it breaks: ambiguous labels,
   overloaded keyboards, dead ends, destructive actions one tap away, frozen waits, personal data
   in public, unlocalized strings, unreadable bodies. Rank P0-P3 by reader gain.
5. Save each one: `tgui.py findings add --severity P1 --screen <id> --rule <rule> --where
   <file:line> --summary "<what the user sees>" --fix <improve|fix|emoji|...>`, then
   `tgui.py context --refresh`. The first time, tell the user to commit `bot-ui/context/`.
6. A diff: run `tgui.py check changed`, read every changed handler against `references/floor.md`,
   report with file:line; do not edit.

## Without scripts

Same passes by reading; give the findings as a table in the answer instead of files.

## Done

Map, ranked defects with evidence, each naming the command that fixes it. Nothing in the
user's code changed.

## Next

"Next: fix the P0/P1 items on <screens>. Say 'go' or name a screen." (`improve` or `fix`)
