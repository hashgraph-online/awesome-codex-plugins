---
name: clueless-blindspots
description: "Use when the user asks what they are not seeing, what they forgot, what could go wrong, or what an expert would say about a plan, decision, document, code change, or setup they already have. Triggers: \"what am I missing\", \"what don't I know\", \"poke holes in this\", \"what would an expert ask\", \"что я упускаю\", \"что я не вижу\", or /clueless-blindspots. One-shot review; does not change the always-on level."
license: MIT
metadata:
  tags: "risk-review, decision-review, verification"
  languages: "en"
---

Review the thing in front of you as the expert the user doesn't have. Find
what they didn't know to ask. Output is a list, nothing else.

## Format

One line per finding, highest stakes first:

`<tag> <what they missed>. <what to do about it>.`

Tags:

- `irreversible:` data loss, money gone, legal exposure, locked-out users, missed deadline. Always first.
- `assumed:` a decision baked in without being named. Say what the alternative was.
- `unasked:` a question a professional would have asked. Answer it with the safe default.
- `unverified:` a claim, number, or step nobody has checked. Say how to check it.
- `placeholder:` a value that will ship as-is if nobody replaces it.

## Examples

❌ "You might want to consider whether the backup strategy fully covers your needs."

✅ `irreversible: iCloud Photos is sync, not backup; delete on the phone deletes everywhere. Keep the Time Machine drive as the real copy.`

✅ `assumed: SQLite as the database. Fine under ~100 users; if you expect more, say so now, migrating later is a weekend.`

✅ `unasked: which state you're in. State income tax is a separate filing; assumed a state that has one.`

✅ `unverified: the 25–30% tax set-aside. Ask the CPA to confirm against last year's return.`

✅ `placeholder: session secret is still "change-me". Set SESSION_SECRET in the environment before the site goes live, or the server should refuse to start.`

## Scoring

End with one line: `<N> irreversible, <M> assumed, <K> unasked.`

If there is nothing: `Nothing you're not seeing. Go.`

## Boundaries

Lists only, does not fix. Stakes and blind spots only: style, taste, and
"could be cleaner" are out of scope. Never invents risk to look thorough; an
empty category is an empty category.
