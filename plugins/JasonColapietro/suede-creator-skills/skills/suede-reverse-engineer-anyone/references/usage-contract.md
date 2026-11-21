# Worked contract: Suede AI Reverse Engineer Anyone Skills

This is an illustrative application, not a claim of measured customer results.

## Input

An independent artist asks how a peer in the same genre went from about 40K to about 400K monthly listeners in 18 months, and what to copy for their own next single. The peer's artist profile, official site, and three public interviews are supplied. The user's own streaming dashboard export is connected; paid trackers are unavailable, so the data budget stays at $0 of the $5 cap. The user approves joining the peer's newsletter and public Discord as themselves, and declines any merch purchase.

## Expected output

Build `curve.csv` from monthly Wayback captures of the one streaming profile, with gaps left blank, and log releases, features, a playlist add, a tour support slot, and a sound that spread on short-form video in `moves.csv`. Run `inflections` and `moves`; report cluster lift in percentage points with confounders named (a viral video another creator made, the platform's year-end lists). Label interview claims Reported. Split the peer's TikTok posts into thirds only if 24 or more settled posts exist. Compare against the user's own export only for depth, never against the archived counts. End with ranked plays routed to `$suede-campaign-in-a-box`, `$suede-social`, and `$suede-release-linter`, each with a paste-ready prompt, plus the one play to start this week.

## Failure and validation

A month with no capture is a gap, not zero, and the curve never mixes in a second tracker. The leading-channel call is declined because the window holds fewer than 6 moves per channel. Discord rules and announcements may be read; member names and messages are never recorded, and nobody is contacted. Every Observed claim resolves to a saved capture or URL with its pull date.
