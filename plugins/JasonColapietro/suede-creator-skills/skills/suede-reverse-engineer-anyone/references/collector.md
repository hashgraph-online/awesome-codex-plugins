# Free Public Collection (`collect.mjs`)

`scripts/collect.mjs` pulls the free, dated public evidence a teardown needs and writes it straight into the teardown's data files. Node 22 or later, no dependencies, no API keys. It sits next to `timeline.mjs` and shares its CSV format. The manual procedures in `hidden-signals.md`, `funnel-read.md`, and `data-sources.md` remain the fallback whenever a command is blocked or a source is not covered.

## Commands

```bash
node <skill-dir>/scripts/collect.mjs site <domain> --out teardowns/<target>/urls.csv
node <skill-dir>/scripts/collect.mjs stack <domain> --months 24 --moves teardowns/<target>/moves.csv
node <skill-dir>/scripts/collect.mjs history <domain>/pricing --months 24 --moves teardowns/<target>/moves.csv
node <skill-dir>/scripts/collect.mjs hero <domain> --months 24 --moves teardowns/<target>/moves.csv
node <skill-dir>/scripts/collect.mjs subdomains <domain> --moves teardowns/<target>/moves.csv
node <skill-dir>/scripts/collect.mjs dns <domain> --out teardowns/<target>/dns.csv
node <skill-dir>/scripts/collect.mjs jobs <board-slug> --out teardowns/<target>/jobs.csv
node <skill-dir>/scripts/collect.mjs reviews <app-id> --country us --out teardowns/<target>/reviews-monthly.csv
node <skill-dir>/scripts/collect.mjs adoption --npm <pkg> --github <owner/repo> --out teardowns/<target>/curve.csv
node <skill-dir>/scripts/collect.mjs youtube <channel-id> --out teardowns/<target>/posts-youtube.csv
node <skill-dir>/scripts/collect.mjs podcast <rss-url> --out teardowns/<target>/episodes.csv
node <skill-dir>/scripts/collect.mjs ads "<Target>" --domain <domain>
```

Every command takes `--json` and `--help`. `--moves` appends rows to `moves.csv` (creating it with a header when absent) and skips rows already present by date, channel, kind, and move. Bad input exits 1 with `collect: <message>`.

| Command | Source | What it records | Evidence label |
|---|---|---|---|
| `site` | The target's robots.txt and sitemaps | Page list with families and lastmod, `url,family,lastmod` | Observed |
| `stack` | Monthly Wayback captures of the homepage | First month each of ~64 tools appears (ad pixels, analytics, testing, referral, lifecycle, ecommerce, payments, call tracking) | Ad pixels Inferred (`ad-start`), other tools Observed (`tool-added`) |
| `history` | Wayback CDX digests for one URL | Months the archived page changed (`page-change`) | Observed |
| `hero` | Monthly Wayback captures | Title, first H1, and meta description changes (`positioning-change`) | Observed |
| `subdomains` | crt.sh certificate logs | Earliest certificate per subdomain (`subdomain`) | Observed |
| `dns` | The system DNS resolver | Email senders, verified tools, marketing subdomain platforms (`tool-verified`) | Observed, dated today |
| `jobs` | Public Greenhouse, Lever, or Ashby boards | Roles by function with marketing channels tagged | Observed; the strategy they imply is Inferred |
| `reviews` | App Store review feed | Monthly count, average rating, and low-star count | Observed |
| `adoption` | npm, PyPI Stats, GitHub | Monthly downloads and stars as a timeline-ready `curve.csv` | Observed (third-party counts) |
| `youtube` | Public channel feed | Recent uploads with date, link, and views | Observed |
| `podcast` | The show's RSS feed | Episodes and monthly cadence (`release`) | Observed |
| `ads` | None: prints ad-library search links | Links for Meta, Google, LinkedIn, and TikTok libraries | Record the filter and date with each finding |

## How it behaves

- **Identifies itself.** User-Agent `suede-collect/1.0 (+https://skills.suedeai.ai)`. It never imitates a browser and reads no environment variables or tokens.
- **Contacts only fixed public hosts:** web.archive.org, crt.sh, boards-api.greenhouse.io, api.lever.co, api.ashbyhq.com, itunes.apple.com, api.npmjs.org, pypistats.org, api.github.com (unauthenticated), and www.youtube.com, plus the target domain for `site` (robots.txt and sitemaps only) and the exact host of a podcast feed you pass. Each redirect hop is checked, and an off-list hop stops with a message.
- **Stops at blocks.** A 401, 403, or 429, or a robots.txt Disallow, stops that source with `blocked by <host> (<status>): use an archived copy or a manual export`. One retry on a network error or 5xx, never more.
- **Paces the archive.** At least 1.5 seconds between archive.org requests and `--max-requests` (default 40) per command. A 24-month `stack` or `hero` run takes about 25 requests and 40 seconds; a capped run says its output is partial.
- **Keeps people out.** Reviewer names are never read, and names, emails, and handles in job posts are never written.
- **Writes only where told.** Files go only to the `--out` and `--moves` paths.

## Known gaps to state in the method notes

- `stack` cannot see tools loaded through a tag manager or behind a consent banner, and tools present in the first capture are listed "at start" with no move.
- A `history` digest change can be a trivial template edit. Open the two captures before calling it a pricing move.
- `dns` findings are undated; the row carries the pull date, not the date the tool was adopted.
- The YouTube feed holds only the latest ~15 uploads. The App Store feed holds at most 500 reviews per country. PyPI Stats keeps about 180 days.
- Unauthenticated GitHub allows 60 requests an hour and lists only the first 40,000 stargazers, so stars over time are interpolated from sampled pages.
- Download counts include CI and bots. Use them as a curve shape, not a user count.
- crt.sh is often slow; a timeout prints a retry message.
