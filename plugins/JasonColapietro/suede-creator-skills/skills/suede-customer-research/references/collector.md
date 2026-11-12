# Free Public Collection (`collect.mjs`)

`scripts/collect.mjs` pulls a few free, dated public sources that help voice-of-customer research pick where to read. Node 22 or later, no dependencies, no API keys. It counts and lists; it never quotes customers. Quotes, themes, and personas still come from reading the sources through the method in `SKILL.md` and the playbooks in `source-guides.md`, which stay the fallback whenever a command is blocked or a source is not covered.

## Where outputs go

Write every output into the run's raw-evidence folder, `customer-research/raw/<YYYY-MM-DD>/`, next to the per-source capture files, and add one row per output to `captures.csv` with the command, source, and pull date. Never overwrite a prior date's folder.

## Commands that matter for customer research

```bash
node <skill-dir>/scripts/collect.mjs reviews <app-id> --country us --out customer-research/raw/<date>/app-store-<app>-us.csv --json > customer-research/raw/<date>/app-store-<app>-us.json
node <skill-dir>/scripts/collect.mjs youtube <channel-id> --out customer-research/raw/<date>/youtube-<channel>.csv
node <skill-dir>/scripts/collect.mjs podcast <rss-url> --out customer-research/raw/<date>/podcast-<show>.csv
node <skill-dir>/scripts/collect.mjs jobs <board-slug> --out customer-research/raw/<date>/jobs-<company>.csv
```

Every command takes `--json` and `--help`. Bad input exits 1 with `collect: <message>`. The other commands in the script (`site`, `stack`, `history`, `hero`, `subdomains`, `dns`, `adoption`, `ads`) serve growth teardowns and are not part of this workflow.

| Command | Source | What it records | How to use it here |
|---|---|---|---|
| `reviews` | App Store review feed for one country | Per month: review count, average rating, and 1 to 2 star count (CSV); plus the top terms in 1 to 2 star reviews, each with the number of low-star reviews containing it (`complaint_terms` in `--json`, and printed to the terminal) | Find the months where low-star reviews spiked and the words they share, then read those reviews in the store and quote them through the capture table. Pass the numeric id from the app's store URL (`id284882215` or `284882215`). Run once per country that matters to the segment. |
| `youtube` | The channel's public feed | Recent uploads: date, link, views, title | Pick the videos where the segment talks (reviews, tutorials, "after 6 months" videos), then mine their comments and transcripts by the existing method. The id starts with `UC` and has 24 characters. |
| `podcast` | The show's RSS feed | Episodes: date, title, link, audio file, duration | Pick episodes where people from the segment are guests or callers, then mine the published transcript or show notes as a Mode 1 transcript. |
| `jobs` (optional) | Public Greenhouse, Lever, or Ashby boards | Open roles: title, department, location, posted date, link, function | Context on what the segment's companies prioritize and staff for. Treat it as an inference about priorities, never as a customer quote. |

## Rules that still apply

- **Terms point; quotes prove.** A complaint term like `sync` or `crash` is a lead to read the matching reviews, not a theme, not a quote, and not a frequency count. "Appeared in X of Y sources" and confidence labels come only from capture records, per the provenance gate.
- **Reviewers stay anonymous.** The collector never reads reviewer names. When you quote review text in a quote bank, cite platform, app, country, star rating, and date, never the reviewer's display name, and drop any identifying detail inside the text.
- **Public content only.** The collector reads public feeds. Transcripts come from what the creator or show published (captions, transcript pages, show notes). Do not record, download, or transcribe audio or video beyond what the platform terms allow, and do not contact commenters, guests, or reviewers without explicit authorization and consent.
- **Label the sample.** A review feed or a creator's channel is a convenience sample. State the source, country, date range, and counts in the deliverable, and apply the sample bias checks before generalizing.

## How it behaves

- **Identifies itself.** User-Agent `suede-collect/1.0 (+https://skills.suedeai.ai)`. It never imitates a browser and reads no environment variables or tokens.
- **Contacts only fixed public hosts.** For these commands: itunes.apple.com (`reviews`), www.youtube.com (`youtube`), boards-api.greenhouse.io, api.lever.co, and api.ashbyhq.com (`jobs`), and the exact host of a podcast feed you pass. Each redirect hop is checked, and an off-list hop stops with a message.
- **Stops at blocks.** A 401, 403, or 429 stops that source with `blocked by <host> (<status>): use an archived copy or a manual export`. When you see it, switch to the manual method in `source-guides.md` (read the store page, the channel, or the show's site directly) and note the block in the method notes. One retry on a network error or 5xx, never more.
- **Keeps people out.** Reviewer names are never read, personal details are scrubbed before complaint terms are counted, and names, emails, and handles in job posts are never written.
- **Writes only where told.** Files go only to the `--out` path; `--json` prints to standard output.

## Known gaps to state in the method notes

- The App Store feed holds at most the 500 newest reviews with text per country, so the oldest month may be partial and older history is out of reach.
- `reviews` covers the iOS App Store only. Google Play, G2, Capterra, Trustpilot, and Amazon reviews still come from the manual playbooks.
- Complaint terms are single words from 1 to 2 star reviews, top 12, each in at least 2 reviews. They miss phrases, sarcasm, and non-English reviews, and say nothing about 3 star reviews.
- The YouTube feed holds only the latest ~15 uploads and carries no comments or transcripts. Older videos are found by search.
- A podcast feed lists episodes, not what was said. Some feeds trim old episodes.
- Job boards show open roles only, not past hiring, and only for companies on Greenhouse, Lever, or Ashby. A missing board is not evidence of no hiring.
- Reddit, forums, communities, and review sites other than the App Store have no collector. Gather them by hand.
