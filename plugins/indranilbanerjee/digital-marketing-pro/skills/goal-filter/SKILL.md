---
name: goal-filter
description: "Lock ONE primary marketing goal per brand, then judge any idea, draft, campaign, or plan against it — ON GOAL, PARTIAL, or OFF — always returning the fix or a sharper version that pulls harder toward the metric, and naming drift patterns across the verdict history. Triggers on \"/digital-marketing-pro:goal-filter\", \"is this on goal\", \"lock the goal for this quarter\", \"does this serve the objective\", \"keep me focused\", \"what's our priority\". Stores the lock in the brand workspace (goal-lock.json) so every session reads the same goal; inside a 12-Part engagement it offers to lock Part 1's primary objective rather than inventing a parallel one."
argument-hint: "[brand-name] [--set \"goal, metric, deadline\"] [--check <idea/draft/plan>] [--status]"
user-invocable: true
---

# /digital-marketing-pro:goal-filter

The strategic filter. One goal is locked per brand; everything gets measured
against it before time or budget is committed. Marketing fails quietly by doing
good work toward nothing in particular — every piece defensible, the quarter's
number missed anyway.

## State

The locked goal lives in the brand workspace, so every session reads the same
one:

```
~/.claude-marketing/brands/{brand-slug}/goal-lock.json
```

```json
{
  "goal": "40 qualified demo bookings per month from organic + email",
  "metric": "demo bookings attributed to owned channels",
  "target": 40,
  "deadline": "2026-12-31",
  "locked_at": "2026-08-12",
  "history": [
    {"checked": "2026-08-14", "item": "podcast idea", "verdict": "OFF"}
  ]
}
```

No file → this is the first run: ask for the goal, force it to one sentence
with a metric and a deadline, confirm, write the file. If the user names three
goals, make them rank — the filter is useless with more than one.

## Judging an item

Read the locked goal, read what the user brought, and rule honestly:

```
# Goal check — {the locked goal}

## What you brought
[One line]

## Verdict: ON GOAL / PARTIAL / OFF GOAL

## Why (2-3 sentences)
[Does this move the goal's metric? How directly? What is the opportunity cost —
what on-goal work does this displace?]

## The fix (if PARTIAL or OFF)
[The specific change that would make it serve the goal — or "park it", with
what to do instead]

## The sharper version (always)
[The same idea, rewritten to pull harder toward the metric]
```

Append the verdict to `history` in the state file.

## Critical rules

- **ONE goal at a time.** Multiple goals are a priority argument the user has
  not had yet. Force the ranking before locking anything.
- **Rule honestly.** OFF GOAL is a legitimate verdict, and the filter is
  worthless if it rubber-stamps. An agency that never says "this doesn't serve
  your objective" is a vendor, not a partner.
- **Never just judge — always hand back an action.** The fix or the sharper
  version, every time. The user leaves with something to do, not just a grade.
- **Name patterns across checks.** The history is there to be read: three OFF
  verdicts in a week is not three isolated ideas, it is a drift — say so, and
  ask what is pulling attention off the goal. This is the filter's second job:
  the single verdicts protect the quarter, the pattern protects the strategy.
- **Goals are marketing outcomes** — revenue, qualified leads, audience
  quality, authority in a niche, retention. "More followers" is accepted only
  with a because-clause that survives one round of "and what does that get
  you?".
- **Changing the goal is allowed, silently drifting is not.** `--set` on an
  existing lock archives the old goal into history with its end date, so the
  quarter's record shows one deliberate change rather than a smear.
- **Engagement integration:** inside a 12-Part engagement, the engagement's
  objectives are the goal source — offer to lock Part 1's primary objective
  rather than inventing a parallel one.
