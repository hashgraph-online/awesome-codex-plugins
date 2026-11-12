# Free Account Signals (`collect.mjs`)

`scripts/collect.mjs` pulls free, dated public evidence about a target account: its technographics, hiring, new properties, developer adoption, and ad-library links. Node 22 or later, no dependencies, no API keys. Use it before paying for a tech-lookup or enrichment credit, and keep the paid or manual routes in `data-sources.md` as the fallback whenever a command is blocked or a signal is not covered.

It studies companies only. It never collects people: reviewer names are never read, and names, emails, and handles in job posts are never written. Contacts still come from the Phase 3 contact rules in SKILL.md and `compliance.md`, never from this script.

## Commands for prospecting

Run these per account after the ICP is set (Phase 1) and the candidate list exists (Phase 2). They qualify known accounts; they do not discover new ones.

```bash
node <skill-dir>/scripts/collect.mjs dns <domain> --out prospects/<run>/<domain>/dns.csv --moves prospects/<run>/<domain>/signals.csv
node <skill-dir>/scripts/collect.mjs stack <domain> --months 12 --out prospects/<run>/<domain>/stack.csv --moves prospects/<run>/<domain>/signals.csv
node <skill-dir>/scripts/collect.mjs jobs <board-slug> --out prospects/<run>/<domain>/jobs.csv
node <skill-dir>/scripts/collect.mjs subdomains <domain> --out prospects/<run>/<domain>/subdomains.csv --moves prospects/<run>/<domain>/signals.csv
node <skill-dir>/scripts/collect.mjs adoption --npm <pkg> --github <owner/repo> --months 12 --out prospects/<run>/<domain>/adoption.csv
node <skill-dir>/scripts/collect.mjs ads "<Company>" --domain <domain> --out prospects/<run>/<domain>/ads.csv
```

Every command takes `--json` and `--help`. `--moves` appends dated rows (`date,channel,kind,move,reach,link,evidence`) to a per-account `signals.csv`, creating it with a header when absent and skipping rows already present by date, channel, kind, and move, so a rerun does not duplicate signals. Bad input exits 1 with `collect: <message>`.

| Command | Source | Prospecting signal | Evidence label |
|---|---|---|---|
| `dns` | The system DNS resolver | Email senders (MX, SPF), verified tools (TXT verification records), and marketing subdomain platforms (CNAME). A free technographic read: which CRM, email, or support vendor the domain is set up for | Observed, dated the pull day; what a record implies about use is Inferred |
| `stack` | Monthly Wayback captures of the homepage | First and last month each of ~64 tools appears (ad pixels, analytics, testing, referral, lifecycle, ecommerce, payments, call tracking). A recent `first_seen` is a stack change; a `last_seen` well before the latest capture can mean a tool was removed, a possible vendor switch | Ad pixels Inferred (`ad-start`), other tools Observed (`tool-added`) |
| `jobs` | Public Greenhouse, Lever, or Ashby boards | Open roles by function, posted date, and marketing channels named in each post (seo, paid, lifecycle, content, partnerships, and others). Roles in your buyer's function or channel are a buying trigger | Observed; the strategy they imply is Inferred |
| `subdomains` | crt.sh certificate logs | Earliest certificate per subdomain: a new `docs.`, `app.`, `shop.`, or country subdomain points to a launch or expansion | Observed; what a subdomain is for stays Inferred until a page confirms it |
| `adoption` | npm, PyPI Stats, GitHub (unauthenticated) | Monthly downloads and star counts for a developer-tool account's own package or repo: a rising curve is a growth signal | Observed (third-party counts) |
| `ads` | None: prints ad-library search links | Links for Meta, Google, LinkedIn, and TikTok libraries to check whether the account is spending on paid | Record the library, filter, and date with each finding |

The board slug for `jobs` is not always the domain. Find it in the careers page's link to `boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, or `jobs.ashbyhq.com/<slug>`. When `jobs` reports no board, the company may use another applicant system: check the careers page before recording "no open roles."

## Batch use across a candidate list

Run the cheap commands across the whole list and the slow ones only on the shortlist:

1. **Every candidate:** `dns` (local resolver, seconds per domain) and `jobs` (three board lookups per slug).
2. **Shortlist only:** `stack` and `subdomains`. `stack` spaces archive.org requests at least 1.5 seconds apart and caps each run at `--max-requests` (default 40). A 24-month run takes about 25 requests and 40 seconds; `--months 12` needs fewer and usually covers a buying-signal window. crt.sh is often slow.
3. **Developer-tool accounts only:** `adoption`, when the account publishes a package or public repo.
4. **Accounts where paid spend matters to the offer:** `ads`, then open each link by hand.

A shell loop over a `domains.txt` file works for the first step, writing each account's files under `prospects/<run>/<domain>/`. Run accounts one after another, not in parallel, so the pacing holds.

## Where the output goes in this workflow

- **Phase 1 (ICP):** use `dns` and `stack` columns to write technographic pass or fail criteria the collector can check, such as "uses a complementary CRM" or "runs a Meta pixel."
- **Phase 3 (qualify):** each collector value is one cited source. Put the capture or record link from the output in the row's `source_urls` and the pull date in `verified_date`. `dns` and `stack` read different sources (live DNS records versus archived page code), so agreement between them on the same tool can count as two independent sources for High confidence. A collector value alone, with no corroboration, is Medium at most.
- **Phase 4 (score):** a dated `jobs` role in your buyer's function, a recent `stack` change, or a new `subdomains` launch can serve as the buying signal. Older than the ICP's signal window, it supports Warm, not Hot.
- **Phase 5 (lead sheet):** stamp every collector value in the `signal` or `why_prospect` column with its command, source, and pull date, for example `Hiring 2 lifecycle marketers (jobs: greenhouse, pulled 2026-11-12)`. Keep the per-account `signals.csv` as the lineage file for the sheet.

## Evidence rules

- **Dated public observation.** Collector output is what a public source showed on the pull date. It is not licensed data, not a verified fact about the company's intent, and not a contact record. No license check is needed to run it, but the fixed hosts' own terms still apply and the output is for the user's own prospecting, never for resale.
- **Blocks mean "not collected."** When a command prints `blocked by <host> (<status>): use an archived copy or a manual export`, record that signal as `not collected (blocked by <host>, <date>)` and fall back to a manual or licensed source. Never retry around a block or read it as a negative result.
- **Absence is not disqualification.** No pixel in `stack`, no board in `jobs`, or no ads found is not evidence on its own. Disqualify only on a positive finding (for example, `dns` shows a direct competitor's verification record and `stack` shows its script) or on a manual check that confirms the absence, and cite both in the Skip row.
- **Partial runs say so.** A run that hits `--max-requests` prints that its output is partial. Carry that note into the open questions.

## How it behaves

- **Identifies itself.** User-Agent `suede-collect/1.0 (+https://skills.suedeai.ai)`. It never imitates a browser and reads no environment variables or tokens.
- **Contacts only fixed public hosts:** web.archive.org, crt.sh, boards-api.greenhouse.io, api.lever.co, api.ashbyhq.com, itunes.apple.com, api.npmjs.org, pypistats.org, api.github.com (unauthenticated), and www.youtube.com, plus the target domain for `site` (robots.txt and sitemaps only) and the exact host of a podcast feed you pass. Each redirect hop is checked, and an off-list hop stops with a message.
- **Stops at blocks.** A 401, 403, or 429, or a robots.txt Disallow, stops that source with `blocked by <host> (<status>): use an archived copy or a manual export`. One retry on a network error or 5xx, never more.
- **Paces the archive.** At least 1.5 seconds between archive.org requests and `--max-requests` (default 40) per command; a capped run says its output is partial.
- **Keeps people out.** Reviewer names are never read, and names, emails, and handles in job posts are never written. Star history reads only star dates, never who starred.
- **Writes only where told.** Files go only to the `--out` and `--moves` paths.

The script also has `site`, `history`, `hero`, `reviews`, `youtube`, and `podcast` commands built for growth teardowns. They are rarely needed for qualification; run `--help` for their usage.

## Known gaps to state in the open questions

- `stack` reads only the homepage and cannot see tools loaded through a tag manager or behind a consent banner. Tools present in the first capture are listed "at start" with no move, and `first_seen` is the first monthly capture containing the script, so the tool may predate it.
- `dns` findings are undated; the row carries the pull date, not the date the tool was adopted. A verification record can outlive the tool.
- `jobs` covers only public Greenhouse, Lever, and Ashby boards. Greenhouse posted dates fall back to the last update.
- `ads` fetches nothing. Open each link, and write "no ads found in <library, filter, date>" when empty.
- PyPI Stats keeps about 180 days. Unauthenticated GitHub allows 60 requests an hour and lists only the first 40,000 stargazers, so stars over time are interpolated from sampled pages.
- Download counts include CI and bots. Use them as a curve shape, not a user count.
- crt.sh is often slow; a timeout prints a retry message.
