# CUAR terminology

These are CUAR-defined terms describing observed Codex usage behavior. They are
not official OpenAI terminology.

## Scheduled Reset

The reset OpenAI currently reports in advance for the active seven-day usage
window. When it occurs, remaining usage returns to 100% and a new Scheduled
Reset is set exactly seven days later. Unlike an Unscheduled Reset, its expected
time is reported beforehand and is viewable in ChatGPT/Codex settings.

*OpenAI may change this observed behavior without notice.*

## Unscheduled Reset

An OpenAI-initiated reset that occurs before the current Scheduled Reset without
redeeming a Banked Reset. Like a Scheduled Reset, it returns remaining usage to
100% and sets a new Scheduled Reset exactly seven days later. Unlike a Scheduled
Reset, its timing is not reported in advance. CUAR can detect evidence
consistent with one, but cannot prove its cause or exact time.

*OpenAI may change this observed behavior without notice.*

## Banked Reset

An expiring replacement reset made available separately from the current weekly
usage allotment. Redeeming it restores usage to 100% remaining, begins a new
seven-day usage window, and sets the Scheduled Reset to exactly seven days after
redemption. It does not add percentage to the existing allotment.

*OpenAI may change this observed behavior without notice.*

## Banked Reset Expiration

The deadline by which a Banked Reset must be redeemed before it disappears.
Expiration does not itself restore usage or change the Scheduled Reset.

*OpenAI may change this observed behavior without notice.*

## Linear Pace

On pace to exhaust weekly Codex usage exactly at the Scheduled Reset.

*OpenAI may change this observed behavior without notice.*

## Projected Exhaustion

CUAR's estimate of when the user's remaining weekly Codex usage will run out. It
is merely a forecast based on current pace, not an OpenAI-set deadline.

*OpenAI may change this observed behavior without notice.*
