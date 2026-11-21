# Hidden Signals

Stage 5 in full: evidence most teardowns never check. Infrastructure, archives, and third-party footprints show moves the target never announced, often with exact dates. Almost all of it is free. Each procedure says what to look up, where, what to record, and which evidence label applies.

## Contents
- Infrastructure
- Archives
- Paid promotion sweep
- Growth counters off the website
- Creator and app signals
- How they see the market
- Launch radar

---

## Infrastructure

### DNS records

- **Look up:** TXT and MX records for the target's domain, plus CNAME records for common marketing subdomains (`go.`, `email.`, `mail.`, `help.`, `docs.`, `community.`, `shop.`, `store.`, `merch.`, `creators.`, `partners.`).
- **Where:** any public DNS resolver, for example `dns.google/resolve?name=target.com&type=TXT`, or a DNS lookup tool the session exposes.
- **Record:** email senders named in SPF and MX (marketing and lifecycle email platforms), domain verification strings for connected tools (ad accounts, social business accounts, payment and AI vendors), and the platform behind each subdomain (a help desk, a store platform, a community platform).
- **Label:** the record itself is **Observed**. What it implies (they send lifecycle email through X, they run a store on Y) is **Inferred**. DNS has no dates; date a finding only when Wayback or another source shows when it appeared.

### Certificate-log subdomains

- **Look up:** every certificate issued for `*.target.com`.
- **Where:** `crt.sh/?q=%25.target.com&output=json`, or another certificate transparency search the session exposes.
- **Record:** each distinct subdomain and the earliest `not_before` date. Drop obvious preview, staging, and machine-generated names. A new certificate usually lands days before launch: free tools, showcases, creator programs, campaigns, enterprise pages, new products, merch stores, tour sites.
- **Label:** the name and date are **Observed**. What the subdomain is for is **Inferred** until a live or archived page confirms it; then the move is **Observed**.
- **Move:** `kind: subdomain`, `channel: infrastructure`, dated to the first certificate.

### Page scripts and pixel first-seen

- **Look up:** ad pixels, analytics, testing, affiliate, and lifecycle scripts in the homepage source, month by month.
- **Where:** Wayback captures of the homepage, one per month across the window (`web.archive.org/web/YYYYMM*/target.com`). Open the page source and search for each tool's script domain.
- **Record:** the first month each script appears, and whether it was already present at the window's start.
- **Label:** a pixel's presence is **Observed**; that ads ran is **Inferred**, because a pixel shows the channel was possible, not used. Check the ad library for **Observed** ads.
- **Limits:** scripts loaded through a tag manager or after a consent banner won't show in the source, so a missing pixel isn't proof the channel wasn't used. Say so in the method notes.
- **Move:** `kind: tool-added` (or `ad-start` with evidence Inferred for ad pixels).

### UTM parameters

Links in their posts, ads, emails, and partner pages carry campaign names (`utm_source=newsletter_sponsor`, `utm_campaign=q3_creator`). Record them: they show how the target organizes channels and which partners it tracks. **Observed**.

### robots.txt and llms.txt

Read `target.com/robots.txt` and `/llms.txt`. Record which AI crawlers they allow and whether they publish an AI-readable summary. **Observed**. See `$suede-ai-seo` for what this means for the user.

## Archives

All from Wayback captures, one per month unless noted.

| Signal | Procedure | Record | Label |
|---|---|---|---|
| **Headline history** | Open the homepage capture for each month; read the H1, title tag, and meta description | Each month the wording changed, with both versions and the capture link | Change **Observed**; the strategy behind it **Inferred** |
| **Pricing history** | Open the pricing page capture for each month | Plans, prices, free-plan limits, trial terms, and the month each changed. Pages that render prices with JavaScript may need the capture opened in a browser | **Observed** |
| **Sitemap growth** | List archived URLs with the CDX API (`web.archive.org/cdx/search/cdx?url=target.com/*&output=json&fl=timestamp,original&collapse=urlkey`), group by path family (`/templates/`, `/integrations/`, `/vs/`, `/city/`), and count first captures per month | When each page family first appeared and how fast it grew | **Observed** (first capture is an upper bound on launch date) |
| **Customer logo wall** | Homepage and `/customers` captures | Who they landed and when; a shift from startup to enterprise logos dates a move upmarket | **Observed** |
| **Old landing pages** | CDX for `target.com/lp/*`, `/go/*`, `/try/*`, `/offer/*` | Retired campaign pages and their offers | **Observed** |
| **Link-in-bio history** | Captures of the bio link page or official site | Order of links over time: what they pushed first each month | **Observed** |

Each change becomes a dated move: `positioning-change`, `pricing-change`, `page-family`.

## Paid Promotion Sweep

Who the target pays to talk about it. These moves rarely show in an ad library.

| Signal | How to find it |
|---|---|
| **Newsletter sponsorships** | Search `"sponsored by [target]"`, `"presented by [target]"`, `"[target]" sponsor` together with newsletter platform domains, plus the archives of the category's big newsletters |
| **Podcast ads** | Search transcripts and show notes for `"brought to you by [target]"` and `[target].com/[show]` vanity URLs |
| **Video sponsorships** | Video descriptions with the target's link and #ad, sponsored, or partner wording |
| **Affiliates** | Links to the target's domain with `?via=`, `?ref=`, `?aff=`, `?fpr=`, or `/go/`; affiliate pages on review and comparison sites |
| **Coupon and deal sites** | `"[target] coupon"`, `"[target] promo code"`, lifetime-deal listings. Heavy presence means discount-led acquisition |
| **Events** | Sponsor pages of the category's main events; the target's own events page |
| **Creator programs** | `creators.`, `ambassadors.`, or `/partners` pages, plus disclosed creator videos found in Stage 2 |
| **Playlist and promotion services (music)** | Disclosed paid playlist pitching, pre-roll ads on the artist's videos, and promoted posts visible in ad libraries |

For each: date, placement, offer or code, and landing page. Label **Observed** when the placement is visible; label paid status **Observed** only when disclosed, otherwise **Inferred**. Vanity URLs and codes that recur show which placements they kept buying.

## Growth Counters off the Website

Public numbers that move with growth and carry dates:

| Counter | Where | Record |
|---|---|---|
| **Review count and velocity** | App store pages, review sites, retailer pages, store pages for games; Wayback for older counts | Reviews per month and rating per month. A sudden spike usually means a review campaign: log it as `kind: review-spike` |
| **App store rank and ratings** | Store pages and their captures | Rank by month, rating count |
| **Developer adoption** | Package registry download stats, repository stars and contributors | Monthly downloads and stars |
| **Browser extensions** | Extension store user counts (Wayback has old counts) | Users by month |
| **Community size** | Public invite pages (Discord, Slack), subreddit subscriber counts, forum member counts | Count by date. Never member names |
| **Marketplace listings** | Integration marketplaces, app marketplaces, merch and print platforms | The date each listing appeared, installs where shown |
| **Open metrics** | Public revenue or traffic dashboards the target publishes | **Observed** numbers, not estimates |
| **AI visibility** | The prompt check from Stage 2, repeated monthly | Share of voice by month |

A counter goes on the timeline when it has dates. The complaints inside reviews feed `weak-spots.md`.

## Creator and App Signals

| Signal | Where | Record |
|---|---|---|
| Playlist adds | Public playlist trackers or the playlist pages and their captures | Playlist, follower count, date added, date removed |
| Sound usage | The sound's page on the short-form platform, read by hand | Video count using the sound, by capture date |
| Sync placements | Public placement databases and episode credits | Show, episode, air date |
| Tour and show history | The tour page on Wayback, public concert listings | Dates, venues by size, support slots |
| Release credits | Streaming credits and liner notes | Producers, features, label, distributor changes |
| Store page history (apps, games) | Captures of the store page | Icon, screenshots, subtitle, and description changes by month |
| Deep link and ad files (apps) | `/.well-known/apple-app-site-association`, `/.well-known/assetlinks.json`, `/app-ads.txt` | Linked paths, ad monetization partners |

## How They See the Market

- **Which competitors they target:** companies named on their `/vs`, `/compare`, and `/alternatives` pages and in their paid search ads.
- **Which segments they pay for:** landing pages behind their ads, by audience or industry.
- **What their chat bot and sales team say** about competitors (from Stage 3).
- **Who they co-market with:** integration pages, joint webinars, partner directories, collaborations and features.

If they target the user directly, the plays should include the user's own comparison pages (`$suede-competitors`).

## Launch Radar

Flag a likely launch when **two or more** of these land within a few weeks of each other:

- A new subdomain in the certificate logs
- A new trademark filing in a public trademark database
- New job titles clustered in one area
- A jump in sitemap size or a new page family
- A new domain verification in DNS
- A new teaser, waitlist, or pre-save page
- A store page "coming soon" listing

Say what the cluster points to, label it **Inferred**, and list the observations behind it. In Watch mode, "no new moves" is the usual result; write it plainly when that's the case.
