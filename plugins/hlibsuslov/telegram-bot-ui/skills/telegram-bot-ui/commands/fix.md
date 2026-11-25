# fix: one Telegram-facing defect

**When:** "can't parse entities", "message is too long", old buttons stopped working, the bot
feels frozen, updates or button presses don't arrive, a callback has no `message`.

## Read (by symptom)

- Parse errors, escaping: `references/regular-formatting.md`, `references/security-and-escaping.md`,
  `references/errors-and-fallbacks.md` "`can't parse entities` — first response".
- Too long, splitting: `references/limits-and-splitting.md`.
- Presses or updates missing, webhooks vs polling, `allowed_updates`:
  `references/updates-and-delivery.md`.
- A field ignored or rejected by the SDK: `references/sdk-compatibility.md`.
- Frozen waits, Stop, races, late chunks: `references/streaming-and-editing.md`.
- Unknown outcome after a timeout, fallbacks: `references/errors-and-fallbacks.md`.
- Tests: `references/testing-playbook.md`.

## Steps

1. Reproduce first: the exact request, the error text, the SDK and its version. Ideally a failing
   test.
2. Check the request against the catalog: `tgui.py check payload --method <method> <file>` and
   `tgui.py lookup show <Symbol>`.
3. Fix the root cause in the project's style: one escaping function per format, no blind retry
   after an unknown outcome, route by `callback_data` when only `inline_message_id` comes.
4. Add the regression test; run `tgui.py check changed` and the project's checks.

## Without scripts

Search `data/bot-api/catalog.json` for the method and its parameters; compare field by field.

## Done

The failing case passes, no other screen changed, evidence level named.

## Next

If the defect points to a wider problem (many screens escape by hand), suggest `audit`.
