# Free Public Collection (`collect.mjs`)

`scripts/collect.mjs` pulls free, dated public evidence about a competitor and writes it into the run's raw folder. Node 22 or later, no dependencies, no API keys. It replaces manual collection for site mapping, archived page history, and market signals. It does not capture page text: page capture stays a connector or manual step, and the manual procedures in SKILL.md and `tool-reference.md` remain the fallback whenever a command is blocked or a source is not covered.

## Commands

`<run>` below is `competitor-profiles/raw/<competitor-slug>/<YYYY-MM-DD>`.

```bash
node <skill-dir>/scripts/collect.mjs site <domain> --out <run>/scrapes/urls.csv
node <skill-dir>/scripts/collect.mjs history <domain>/pricing --months 24 --channel pricing --out <run>/signals/pricing-history.csv
node <skill-dir>/scripts/collect.mjs hero <domain> --months 24 --out <run>/signals/hero.csv
node <skill-dir>/scripts/collect.mjs stack <domain> --months 24 --out <run>/signals/stack.csv
node <skill-dir>/scripts/collect.mjs dns <domain> --out <run>/signals/dns.csv
node <skill-dir>/scripts/collect.mjs subdomains <domain> --out <run>/signals/subdomains.csv
node <skill-dir>/scripts/collect.mjs jobs <board-slug> --out <run>/signals/jobs.csv
node <skill-dir>/scripts/collect.mjs reviews <app-id> --country us --out <run>/reviews/app-store-monthly.csv
node <skill-dir>/scripts/collect.mjs adoption --npm <pkg> --github <owner/repo> --out <run>/signals/adoption.csv
node <skill-dir>/scripts/collect.mjs ads "<Competitor>" --domain <domain> --out <run>/signals/ads-links.csv
```

Every command takes `--json` and `--help`. Bad input exits 1 with `collect: <message>`. `adoption` also takes `--pypi <pkg>`; `youtube <channel-id>` and `podcast <rss-url>` exist for content-cadence signals. Optionally add `--moves <run>/signals/moves.csv` to `history`, `hero`, `stack`, `subdomains`, or `dns` to build one dated timeline (`date,channel,kind,move,reach,link,evidence`) for the profile's `## Change Log`; duplicate rows are skipped.

| Command | Source | What it records | Evidence label |
|---|---|---|---|
| `site` | The competitor's robots.txt and sitemaps | Page list with families and lastmod, `url,family,lastmod` | Fact |
| `history` | Wayback CDX digests for one URL | Months the archived page changed | Fact (that it changed) |
| `hero` | Monthly Wayback captures | Title, first H1, and meta description changes | Fact |
| `stack` | Monthly Wayback captures of the homepage | First month each of ~64 tools appears (ad pixels, analytics, testing, referral, lifecycle, ecommerce, payments, call tracking) | Tool presence Fact; an ad pixel is Inference that a paid channel was possible, not proof ads ran |
| `dns` | The system DNS resolver | Email senders, verified tools, marketing subdomain platforms | Fact, dated the pull date |
| `subdomains` | crt.sh certificate logs | Earliest certificate per subdomain | Fact |
| `jobs` | Public Greenhouse, Lever, or Ashby boards | Open roles by function with marketing channels tagged | Fact; the strategy they imply is Inference |
| `reviews` | App Store review feed (app competitors) | Monthly count, average rating, low-star count | Fact |
| `adoption` | npm, PyPI Stats, GitHub (dev tools) | Monthly downloads and stars | Fact (third-party counts) |
| `ads` | None: prints ad-library search links | Links for Meta, Google, LinkedIn, and TikTok libraries | Record the filter and date with each finding |

Cite each collected field with its file and the pull date (the run folder date), per the evidence markers in `templates.md`.

## How it behaves

- **Identifies itself.** User-Agent `suede-collect/1.0 (+https://skills.suedeai.ai)`. It never imitates a browser and reads no environment variables or tokens.
- **Contacts only fixed public hosts:** web.archive.org, crt.sh, boards-api.greenhouse.io, api.lever.co, api.ashbyhq.com, itunes.apple.com, api.npmjs.org, pypistats.org, api.github.com (unauthenticated), and www.youtube.com, plus the competitor domain for `site` (robots.txt and sitemaps only) and the exact host of a podcast feed you pass. Each redirect hop is checked, and an off-list hop stops with a message.
- **Stops at blocks.** A 401, 403, or 429, or a robots.txt Disallow, stops that source with `blocked by <host> (<status>): use an archived copy or a manual export`. One retry on a network error or 5xx, never more. On a block, use the manual method and mark fields `not collected` if that also fails.
- **Paces the archive.** At least 1.5 seconds between archive.org requests and `--max-requests` (default 40) per command. A 24-month `stack` or `hero` run takes about 25 requests and 40 seconds; a capped run says its output is partial.
- **Keeps people out.** Reviewer names are never read, and names, emails, and handles in job posts are never written.
- **Writes only where told.** Files go only to the `--out` and `--moves` paths.

## Known gaps to state in Raw Data Sources

- `stack` cannot see tools loaded through a tag manager or behind a consent banner, and tools present in the first capture are listed "at start" with no date.
- A `history` digest change can be a trivial template edit. Open the two archived captures before calling it a pricing change, and never treat an archived price as current.
- `dns` findings are undated; the row carries the pull date, not the date the tool was adopted.
- The App Store feed holds at most 500 reviews per country. PyPI Stats keeps about 180 days. The YouTube feed holds only the latest ~15 uploads.
- Unauthenticated GitHub allows 60 requests an hour and lists only the first 40,000 stargazers, so stars over time are interpolated from sampled pages.
- Download counts include CI and bots. Use them as a curve shape, not a user count.
- `jobs` sees only boards on Greenhouse, Lever, or Ashby; other careers pages stay manual.
- crt.sh is often slow; a timeout prints a retry message.
