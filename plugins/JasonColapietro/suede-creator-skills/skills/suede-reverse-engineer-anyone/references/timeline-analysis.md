# Timeline Analysis

Stages 1 and 7 in depth: finding the inflections and finding which moves lined up with them. It needs no new data, only the two spine files, and runs through `scripts/timeline.mjs`. It shows which moves lined up with growth speeding up. It can't show which moves caused it.

## Contents
- Inputs
- Finding the inflections
- Lining up the moves
- Reading the output
- Confounders to name

---

## Inputs

**`curve.csv`**: `month,primary,secondary`, one row per month (`YYYY-MM`), from one source for the whole series (see `data-sources.md`). `primary` is the main curve (visits, monthly listeners, subscribers, downloads). `secondary` is the second demand signal (brand search, a second metric from the same source) or blank. Blank cells and missing months are gaps, never zero. A month listed twice is an error.

**`moves.csv`**: one row per dated move:

| Column | Values |
|---|---|
| `date` | `YYYY-MM-DD` (the 1st of the month if only the month is known) |
| `channel` | search, ai, paid, x, youtube, tiktok, instagram, linkedin, reddit, streaming, playlists, creators, sponsorship, pr, events, touring, sync, product-loop, referral, pricing, lifecycle, sales, store, infrastructure, site, podcast, hiring, launch, release, merch |
| `kind` | launch, raise, release, founder-post, creator-video, ad-start, sponsorship, loop-first-seen, page-family, subdomain, tool-added, tool-verified, page-change, positioning-change, pricing-change, content-format, cadence-change, playlist-add, collaboration, tour, sync-placement, label-signing, review-spike, reported-claim, hire |
| `move` | One line: what happened |
| `reach` | Views, likes, streams, or score, if any |
| `link` | The evidence URL |
| `evidence` | Observed, Inferred, or Reported |

Keep channel names consistent across the file; the leading-channel test counts moves per channel.

## Finding the Inflections

```bash
node <skill-dir>/scripts/timeline.mjs inflections --curve teardowns/<target-slug>/curve.csv
```

An inflection is a month where growth stepped up and held for at least two months. There can be more than one. A single spike that fell back is not an inflection; log it as a move or an event and read it next to the curve.

Report each inflection with the month, the growth before and after (from the script output), and the source of the curve.

## Lining Up the Moves

```bash
node <skill-dir>/scripts/timeline.mjs moves --moves teardowns/<target-slug>/moves.csv --curve teardowns/<target-slug>/curve.csv --out teardowns/<target-slug>/moves-vs-growth.csv
```

What the script computes:

- **Growth:** month-over-month change in `primary` and `secondary`, in percent.
- **Clusters:** a move within 42 days (six weeks) of the previous one joins its cluster. Credit goes to the cluster as a whole, never to one move inside it.
- **Lift per cluster:** mean month-over-month growth for the 3 months from the cluster's start, minus the mean for the 3 months before, in percentage points. Computed for `primary` and `secondary` separately. A cluster too close to either end of the series, or next to a gap, gets no lift rather than a partial one.
- **Leading channel:** Spearman rank correlation between each channel's monthly move count and growth at lag 0, 1, and 2 months. The script declines to call it with under 18 months of data or fewer than 6 moves on that channel.

## Reading the Output

- **Top clusters:** name every move in each. The lift is **Observed**, as numbers. The claim that the moves drove it is **Inferred**. Say this wherever lift is reported.
- **Leading channel:** a channel whose activity correlates with growth one or two months later is a lead worth testing, not a finding. Monthly data and overlapping moves make it weak evidence.
- **Primary vs secondary:**
  - Secondary up, primary flat: the move created demand that arrived another way (direct, AI answers, word of mouth, another platform).
  - Primary up, secondary flat: look at non-brand search pages, paid, or algorithmic placement.
  - Both up: demand and capture moved together, typical after a launch, a release, or a viral moment.
- **High reach, no lift:** posts, releases, or campaigns that spread widely and moved nothing. Good candidates for plays to skip.
- **Before vs after the inflection:** moves that started before it are stronger candidates than moves that started after, which may be a result of growth (more budget, more hires, more press).
- **Reported vs observed:** a cluster backed only by Reported moves is a story to check, not evidence.

## Confounders to Name

Every report of lift lists the ones that apply:

- **Funding:** a round announced in the same months, which funds spend and press at once
- **Press:** a press wave, a big feature, or a TV appearance in the same window
- **Seasonality:** compare the same month a year earlier (holidays, back-to-school, festival season, Q4 streaming, January fitness)
- **Category tide:** the whole category rose; check two peers' curves from the same source
- **Algorithm changes:** a platform ranking or recommendation change, a search core update, a store featuring policy change in the same month
- **A viral moment someone else made:** a creator, meme, news story, show, or film that used the target's product or song without the target's involvement
- **A source change:** a vendor or tracker methodology change (a jump across many targets at once)
- **A site or account change:** a domain move, redesign, migration, channel rename, or account merge
