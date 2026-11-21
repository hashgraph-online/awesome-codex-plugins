# Free Public Collection (`collect.mjs`)

`scripts/collect.mjs` pulls free, dated public evidence for listing work: App Store review trends, archived listing and marketing-site changes, and ad-library links for competitors. Node 22 or later, no dependencies, no API keys. It never logs into App Store Connect or Google Play Console, so console readbacks and exports still come from the user. Live listing fields still come from the Phase 1 fetch and screenshot in SKILL.md; the collector adds the history and review volume a single page fetch cannot show.

## Where outputs go

Write collector files under `aso/evidence/`, next to `aso/keywords.md` and `aso/aso-doc.md`, one file per app and country so competitor pulls do not overwrite each other:

```
aso/evidence/reviews-<app-id>-<cc>.csv
aso/evidence/listing-history-<app-id>.csv
aso/evidence/site-hero-<domain>.csv
aso/evidence/ads-<app-name>.csv
```

Cite the file and the pull date (printed on the first line of every run) wherever a finding uses it in the report.

## Commands that matter for ASO

```bash
node <skill-dir>/scripts/collect.mjs reviews <app-id> --country us --out aso/evidence/reviews-<app-id>-us.csv
node <skill-dir>/scripts/collect.mjs history "apps.apple.com/us/app/<name>/id<digits>" --months 24 --channel listing --out aso/evidence/listing-history-<app-id>.csv
node <skill-dir>/scripts/collect.mjs hero <marketing-domain> --months 24 --out aso/evidence/site-hero-<domain>.csv
node <skill-dir>/scripts/collect.mjs ads "<App or developer name>" --domain <marketing-domain> --out aso/evidence/ads-<app-name>.csv
```

Every command takes `--json` and `--help`. Bad input exits 1 with `collect: <message>`. The other commands (`site`, `stack`, `subdomains`, `dns`, `jobs`, `youtube`, `podcast`) serve growth teardowns and are rarely needed here; `adoption` matters only when the app ships a public SDK or package on npm, PyPI, or GitHub whose usage curve explains install demand.

| Command | Source | What it records | ASO use | Evidence label |
|---|---|---|---|---|
| `reviews` | App Store customer review feed for one country | Monthly review count, average rating, and 1 to 2 star count (`month,count,avg_rating,low_count`), plus the top complaint terms from 1 to 2 star reviews (printed and in `--json`, not in the CSV) | Ratings & Reviews dimension: recency, volume trend, rating drift after a release, and complaint themes to answer in What's New, developer responses, or screenshots. Run it for the user's app and each App Store competitor in Phase 3. | Observed |
| `history` | Wayback CDX digests for one listing URL | Months the archived listing page changed, with a capture link per month | Dating title, subtitle, screenshot, or description changes on the user's or a competitor's listing | Observed that the page changed; what changed stays unconfirmed until both captures are opened |
| `hero` | Monthly Wayback captures of a domain's homepage | Title, first H1, and meta description changes | Positioning shifts on the app's marketing site that the listing copy should match (entity match check) | Observed |
| `ads` | None: prints ad-library search links | Links for Meta, Google, LinkedIn, and TikTok ad libraries | Whether a competitor runs user-acquisition ads, which can explain rank or review spikes | Record the library, filter, and date with each finding |
| `adoption` | npm, PyPI Stats, GitHub | Monthly downloads and stars | Only for apps tied to a public developer package | Observed (third-party counts) |

### App id and country

`reviews` takes the numeric App Store id (the digits after `id` in the listing URL; a leading `id` is accepted). `--country` is the two-letter storefront code (`us`, `gb`, `de`); run one pull per market the audit covers, because each storefront has its own reviews. `--pages` defaults to and caps at 10 pages (the feed maximum).

### Google Play

The collector has no Google Play review source: there is no free public review API it can call. For Play, keep this skill's existing method: read the reviews visible on the listing page, ask the user for a Play Console reviews export or ratings readback, or use an authorized connector within its terms. Never scrape Play review pages in bulk. `history` works on a `play.google.com/store/apps/details?id=<package>` URL, but Play pages render client-side, so captures can be sparse or carry little listing text.

## How it behaves

- **Identifies itself.** User-Agent `suede-collect/1.0 (+https://skills.suedeai.ai)`. It never imitates a browser and reads no environment variables or tokens.
- **Contacts only fixed public hosts.** For the ASO commands that is itunes.apple.com (`reviews`) and web.archive.org (`history`, `hero`); `ads` fetches nothing. Each redirect hop is checked, and an off-list hop stops with a message.
- **Stops at blocks.** A 401, 403, or 429 stops that source with `blocked by <host> (<status>): use an archived copy or a manual export`. One retry on a network error or 5xx, never more. When this prints, fall back to the manual method: the visible listing, a user-supplied screenshot, or a console export, and say which one the finding rests on.
- **Paces the archive.** At least 1.5 seconds between archive.org requests and `--max-requests` (default 40) per command. A 24-month `hero` run takes about 25 requests and 40 seconds; a capped run says its output is partial.
- **Keeps people out.** Reviewer names are never read, and personal details are scrubbed from review text before complaint terms are counted.
- **Writes only where told.** Files go only to the `--out` and `--moves` paths.

## Using the output under this skill's rules

- Review counts and averages from the feed are a sample of the newest written reviews, not the store's lifetime rating. Score the rating average and count from the listing itself; use the feed for recency, monthly trend, and complaint themes.
- Complaint terms are single words counted across 1 to 2 star reviews. Read a few matching reviews before naming a theme, and label the theme Inferred.
- A `history` change month is a candidate listing change. Open the capture for that month and the one before it, and confirm which field moved (title, subtitle, screenshots, description, rating count) before calling it a listing experiment or metadata change.
- A month with no captures is unknown, not unchanged.
- Competitor data from the collector is public evidence about the competitor's page, never about their conversion or rank. Keep the Boundaries rule in SKILL.md: no invented performance.

## Known gaps to state in the method notes

- The App Store feed holds at most the 500 newest reviews with text per country, so the oldest month in the CSV may be partial and high-volume apps may cover only a few weeks. Star-only ratings without text are not in the feed.
- No Google Play reviews, no keyword rank, no search volume, and no conversion data: those need the store consoles or a paid tool, as the report rules already say.
- A `history` digest change can be a trivial template edit or a rating count update. Product page optimization tests and custom product pages do not show in archived default pages at all.
- Wayback coverage of store listing pages is uneven; small apps may have few or no captures.
- `hero` reads only a homepage. Pass the app's marketing domain, not a store URL.
- `ads` links omit Apple Search Ads, which has no public ad library.
