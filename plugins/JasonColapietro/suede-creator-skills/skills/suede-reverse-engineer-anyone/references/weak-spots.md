# Where They're Weak

Stage 8's second half. Copying what worked is half of a teardown. The other half is finding where the target is losing: what its customers or fans complain about, what it stopped doing, and which audiences it ignores. Those gaps are where the user can win without outspending it.

## Contents
- Sources of weakness
- Mining complaints
- Reading the pattern
- Turning weak spots into plays
- Rules for using weak spots

---

## Sources of Weakness

| Weakness | Where to find it | Procedure |
|---|---|---|
| **What customers hate** | 1-2 star reviews on app stores, review sites, retailer pages, game store pages | Read or export to `reviews.csv` (`date,rating,source,title,text,link`), newest first |
| | Reddit, Hacker News, forums, and comment threads | `site:reddit.com "<target>" (slow OR expensive OR switched OR alternative OR cancel)` |
| | Regulated industries | Public complaint databases and regulator actions named in `industry-signals.md` |
| **Why people leave** | "Switched from X" and "X alternative" posts, migration guides, competitors' import tools | Search `"switched from <target>"`, `"<target> alternative"`, `"migrate from <target>"` |
| **Where support breaks** | Stage 3: response time, chat bot dead ends, cancel flow length | `go-inside.md`, with approval |
| **Price pain** | Price rises in the pricing history, price complaints in reviews, removed plans | Pricing captures from `hidden-signals.md` |
| **Search they gave up** | Page families that shrank or vanished, keywords where rank fell | Sitemap growth on Wayback; the SEO tool's lost keywords |
| **Markets they left or ignore** | Locales dropped from the sitemap, countries with no pages or jobs, segments with no landing page | Sitemap and job board history |
| **Slowing output** | Changelog, release, or posting cadence that dropped; a shrinking engineering hiring share | Changelog or release dates by month; job posts by function |
| **Weak AI answers** | Prompts where they're missing, named after the user, or described wrongly | The Stage 2 AI answer check |
| **Unhappy partners** | Low-rated integration listings, partners who removed them | Marketplace listings and their captures |
| **Fan friction (creators)** | Recurring complaints about ticket fees, merch quality, shipping, release delays, a sound change, paywalled content | Public comments and threads, read by theme. No names |

## Mining Complaints

1. Pull reviews or complaints from at least two sources, newest first, and note the date range each covers.
2. Count with code: low-star share by month, and terms that appear in a larger share of 1-2 star reviews than 4-5 star ones.
3. Read recent low reviews in full. Group them into themes in your own words: price, missing feature, bugs after an update, support, billing, onboarding, performance, shipping, fees.
4. For each theme, record the count, the share of low reviews, the first month it appears, and two short quotes with links (no names or handles).
5. Check whether a rise lines up with a dated move (a price change, a redesign, a big release). Add the spike to `moves.csv` as `kind: review-spike`.

**A theme needs 5 or more low reviews across more than one month to count.** One loud thread is an anecdote.

## Reading the Pattern

- **Complaints about a recent change** (a redesign, a price rise, a removed free plan) are the most usable: the unhappy customers are still deciding whether to leave.
- **Complaints that never change** (slow support for three years) are structural. The target has decided not to fix them, which makes them a lasting angle.
- **Complaints that come with growth** (outages, support wait times, sold-out shows) can mean the target is winning. Read them next to the curve before calling it weakness.
- **Praise inside low-star reviews** ("love the product, but the price doubled") shows what not to attack.
- **Who complains** matters more than how many: complaints from the segment the user serves outweigh the rest.

## Turning Weak Spots into Plays

| Weak spot | Play | Suede skill |
|---|---|---|
| A complaint theme the user solves | "Alternative to X for [the complaining segment]" page with the specific difference | `$suede-competitors` |
| Price pain after a price rise | A switching offer or migration help for their plan tier | `$suede-offers`, `$suede-pricing` |
| Customers leaving over a missing feature | Positioning that leads with that feature | `$suede-product-marketing`, `$suede-copy` |
| Searches on "[their brand] alternative" and "[their brand] [problem]" | Search ads and comparison pages on those queries, within trademark rules | `$suede-ads`, `$suede-competitors` |
| Support or onboarding complaints | Onboarding and support promises in the funnel, then proof | `$suede-onboarding`, `$suede-site-alchemy` |
| Search families they abandoned | Build the family they dropped, if demand is still there | `$suede-programmatic-seo`, `$suede-content-strategy` |
| Markets they left | Localized pages or a market launch | `$suede-site-alchemy`, `$suede-campaign-in-a-box` |
| Weak or wrong AI answers about them | Content that answers those prompts with the user's evidence | `$suede-ai-seo` |
| Sales objections the target can't answer | A battle card for the user's sales team | `$suede-sales-enablement` |
| Voice of customer in their reviews | Interview and survey prompts in the complainers' own words | `$suede-customer-research` |
| Fan friction on fees, merch, or release delays (creators) | A clearer direct offer: fair-fee presale, merch bundle, reliable release cadence | `$suede-offers`, `$suede-campaign-in-a-box` |

## Rules for Using Weak Spots

- **Attack the gap, not the target.** Write about what the user does better, with evidence. Don't publish their customers' complaints as if they were the user's findings.
- **Every comparative claim must be true, current, and provable.** Comparative advertising is lawful in the US and the EU only when accurate and not misleading. Date each claim and keep the source. Check with counsel before naming a competitor in paid ads.
- **Trademarks:** bidding on a competitor's name is allowed in many markets, but using it in ad text often isn't. Check each platform's trademark policy.
- **No personal data:** quote reviews without the reviewer's name or handle, and never contact reviewers, fans, or customers on the strength of a complaint.
- **Recheck before publishing.** A weakness from last year may be fixed. Re-read reviews and pricing before any page or ad goes live.
