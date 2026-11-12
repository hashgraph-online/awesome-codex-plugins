# Landscape Mode

Compare three to five targets side by side before tearing any one of them down. A single teardown shows what one target did. A landscape shows what the whole category does: which plays are table stakes, which are one target's bet, and where nobody is playing. It works the same for companies, apps, and creators in one scene or genre.

## Contents
- When to run it
- Build the matrix
- Read the matrix
- Add the paid and hand-read columns
- Pick who to tear down
- The landscape deliverable

---

## When to Run It

- The user names several competitors or peers, or asks "what is everyone in my category doing?"
- Before a full teardown, to pick the target most worth studying.
- When the user has no clear lead competitor and needs to see the field first.

Use three to five targets of the same type (see `target-types.md`). Fewer than three gives no pattern; more than six becomes noise.

## Build the Matrix

For each target, and for the user, collect the same free signals on the same date, using the procedures in `hidden-signals.md`:

- **Homepage scripts:** ad pixels, analytics, testing, referral, and lifecycle tools in the current page source
- **DNS:** marketing email platforms, ad and social account verifications, platforms behind marketing subdomains
- **Sitemap:** page families with 10 or more pages (templates, integrations, compare, customers, locations, a localized site)
- **Hiring:** marketing channels named on a public ATS board
- **For creators:** platforms active, release cadence, merch store, newsletter, community, touring, sync presence
- **For apps and games:** store page elements, version cadence, in-app events, Discord, demo

Save `teardowns/landscape/matrix.csv`: one row per signal, one column per target plus `you`, each cell `yes`, `no`, or `unchecked` (a source that couldn't be read). Then sort the rows:

| Group | Meaning |
|---|---|
| `everyone` | Every target shows it. Table stakes here |
| `most` | At least half show it |
| `only_one` | One target shows it and the rest don't. A bet worth checking in a full teardown |
| `you_missing` | At least half show it and the user doesn't |
| `you_unchecked` | A source for the user couldn't be read. Unknown, not missing: check by hand |
| `you_only` | The user shows it and no target does |

Count with code, not by eye.

## Read the Matrix

- **Table stakes the user lacks** are the first gaps to close, but only when they fit the user's stage. Every target running a Meta pixel says the channel is normal here, not that the user should start tomorrow.
- **One target's bet** is the most interesting row. Check whether that target is growing faster than the rest (same-source curves). A bet plus faster growth is the teardown to run first.
- **Nobody does it** is an open lane or a dead end. A missing page family might be untapped demand, or it might have been tried and dropped. Check Wayback for a family that once existed and was removed, and check search demand, before calling it an opportunity.
- **Hiring rows lead the rest.** A target hiring for SEO or partnerships today will show those page families or programs in three to six months.
- **Signals are Observed; strategy is Inferred.** "Has a Meta pixel" is Observed. "Runs Meta ads" needs the ad library. "Meta ads drive their growth" needs a full teardown.

## Add the Paid and Hand-Read Columns

Add these by hand or with the user's tools, labeled with source and date:

| Column | Source |
|---|---|
| Curve estimate and 12-month trend | One source for every target (one traffic vendor, or one tracker for one platform) |
| Non-brand share and top page family | The same SEO tool |
| Active ads per network | Public ad libraries |
| AI answer share of voice | The Stage 2 prompt check, same prompts for all |
| Pricing: entry price, free plan, trial | Each pricing page, same date |
| Review count and rating | Store pages and review sites |
| Positioning | Each homepage headline or bio, side by side |

## Pick Who to Tear Down

Rank the targets by growth rate (same source), number of `only_one` bets, and closeness to the user's buyer or audience. Recommend one for a full teardown and say why in one line.

## The Landscape Deliverable

`teardowns/landscape/landscape.md`:

1. **The field:** one line per target with headline, curve trend, and open roles or release cadence
2. **Table stakes:** what everyone does, and which of these the user lacks
3. **Bets:** each target's unique signals, with whether that target is growing faster
4. **Open lanes:** what nobody does, each checked against demand and Wayback
5. **Where each one is weak:** the top complaint theme or gap per target (see `weak-spots.md`)
6. **Recommendation:** the target to tear down first, and the one gap to close this month, with the Suede skill that runs it (see `play-routing.md`)
7. **Method notes:** sources, pull dates, unchecked cells, data cost
