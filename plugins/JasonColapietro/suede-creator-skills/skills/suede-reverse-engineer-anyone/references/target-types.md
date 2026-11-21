# Target Types

Pick the target type before Stage 1. It decides what the curve measures, which stages run in full, what "going inside" means, and where the privacy line sits. A target can span two types (a founder whose personal brand drives their company): build one curve per type and keep them in separate files (`curve.csv`, `curve-founder.csv`), never merged.

## Contents
- Choosing the type
- Company
- Creator, artist, or band
- Founder or personal brand
- App or game (including developer tools)
- Single launch or campaign
- Privacy rules for every type

---

## Choosing the Type

| The user says | Type | Curve unit |
|---|---|---|
| "How did [company or product] grow" | Company | Monthly web visits plus brand search |
| "How did [artist, band, YouTuber, streamer] blow up" | Creator, artist, or band | One platform's audience metric |
| "How did [founder or expert] build an audience" | Founder or personal brand | One platform's followers or a public subscriber count |
| "How did [app, game, package] take off" | App or game | Downloads, store rank, wishlists, or package downloads |
| "How did [launch, drop, tour, campaign] work" | Single launch or campaign | The parent target's curve, plus a daily launch log |

Confirm the type with the user in one line, then load the matching section of `industry-signals.md` as well (two sections when the target spans two industries).

## Company

**Curve sources:** monthly visits from one traffic vendor for the whole window (`primary`), and brand search volume from the same vendor or Google Trends interest for the brand name (`secondary`). For a company that sells mostly through retail or stores, a store-count or doors series read from archived locator pages can be the `primary` instead.

**Stages:** all nine. Stage 3 runs only with per-action approval.

**Stage 3 equivalents:** sign up for the free plan or trial, log the email sequence, push to the upgrade wall without paying, walk the cancel flow, book a demo only under the user's own name, and ask the chat bot how the target compares with the user. Funnel Hack mode adds an approved purchase. See `go-inside.md` and `funnel-hack.md`.

**Privacy limits:** study the company. Leaders' public talks, posts, and interviews in a work capacity are in scope. Staff lists, customer lists, and follower lists are out.

**Typical moves to log:** page families appearing in the sitemap, ad pixels first seen, ads starting in a library, pricing and packaging changes, homepage headline changes, new subdomains, integration listings, funding, launches, press waves, hiring pushes by channel, review spikes.

## Creator, Artist, or Band

**Curve sources:** one metric from one platform source for the whole window. Options:
- Music: monthly listeners or followers on one streaming platform, read from a public tracker or archived profile captures; or monthly YouTube views on the official channel.
- Video creators: YouTube subscribers or monthly views, or TikTok followers, from one public tracker or archived profile pages.
- Newsletter or podcast: the subscriber or download count the creator publishes (label it Reported) or a chart position series.

Put that metric in `primary`. Use `secondary` for a second metric from the same source (followers next to monthly listeners) or for search interest in the name from Google Trends. Never add platforms together into one curve, and never switch trackers mid-window.

**Stages:**
- Stage 1, 6, 7, 8, 9: run in full. Stage 6 is often the core of a creator teardown.
- Stage 2: read the funnel as an audience funnel. Discovery (playlists, algorithmic placement, short-form sounds, features and collaborations, press, sync), conversion (follow, pre-save, newsletter or Discord join), revenue (merch, tickets, memberships, direct sales, sponsorships, licensing), referral (shares, duets, stitches, videos using their sound), and retention (release cadence, community rituals).
- Stage 3: only the equivalents below.
- Stage 4: the artist's or creator's own interviews, plus public interviews by their manager, label, producer, or collaborators about the project.
- Stage 5: link-in-bio and official site history on Wayback, the merch store's platform from public DNS and page source, release credits, distributor or label changes, tour listings, public playlist add dates, and sync placement listings.
- Hiring: usually skip. Log a label signing, management change, or publicly announced team hire as a move instead.

**Stage 3 equivalents (each with the user's approval, under the user's real identity):**
- Follow the official accounts, pre-save a release, and subscribe to the newsletter with a dedicated inbox. Log every message by day.
- Join the public Discord, Patreon free tier, or fan community as the user. Read announcements and onboarding; don't post, recruit, or message members.
- Walk the merch store or ticket checkout to the final step and stop. Buy merch only with explicit approval and a set amount. Buy tickets only if the user will attend.
- Never stream on loops, use bots, or create extra accounts to test anything. Artificial streams break every platform's terms.

**Privacy limits:** public professional capacity only: releases, public stats, public posts about the work, public interviews. Out of scope: family, relationships, health, home location, private accounts, and anything about fans. Never build a list of followers, commenters, fans, or community members, and never contact the creator, their team, or their audience.

**Typical moves to log:** single, EP, or album release; music video; a sound taking off on short-form video; a playlist add; a feature or collaboration; a tour or support slot announcement; a press feature or live session; a sync placement; a merch drop; a label or distributor change; a new content format or series; a cadence change; a paid promotion or ad start.

## Founder or Personal Brand

**Curve sources:** followers on one platform from one public tracker or archived profile captures (`primary`), and search interest for the person's name or a newsletter subscriber count they publish (`secondary`, labeled Reported when self-published). LinkedIn is read by hand; record each reading with its date.

**Stages:**
- Stage 2: the audience funnel. Posts and guest appearances, then the profile, then the lead magnet or newsletter, then the offer (course, community, consulting, the product they run).
- Stage 3: subscribe to the newsletter, download a lead magnet, join a free community, each as the user with approval. A paid course or cohort only with explicit approval and a set amount.
- Stage 4: central. Their own podcasts, talks, and threads about how they grew, each claim labeled Reported.
- Stage 5: newsletter platform and sending tools from public DNS on their domain, link-in-bio history, the about page's audience claims on Wayback, guest appearance dates.
- Hiring: skip unless the personal brand fronts a company; then run the company type too.

**Privacy limits:** the work only. Never study their personal life, family, or private accounts, and never compile who they follow, who replies, or who buys from them.

**Typical moves to log:** a new post format, a posting cadence change, a viral post, a guest run on podcasts, a newsletter launch, a lead magnet, a course or cohort launch, a book, a speaking circuit, a collaboration, a platform switch.

## App or Game (Including Developer Tools)

**Curve sources:**
- Mobile apps: monthly download estimates from one app intelligence vendor, or category rank history from one source. Ratings count from the store page as `secondary`.
- PC and console games: store followers or wishlists from one public data site, or review count by month as a proxy; concurrent players where public.
- Developer tools: monthly downloads from one package registry (npm, PyPI, crates.io, Docker Hub) as `primary`, GitHub stars by month as `secondary`.

**Stages:** all nine. Stage 2 adds the store page as the landing page. Stage 5 adds store page history, version history, soft launch countries, deep link files, and `app-ads.txt`.

**Stage 3 equivalents:** install on a device the user controls, screenshot onboarding, permission prompts, and the paywall. No paid trial or in-app purchase without approval; if one is approved, set a cancel reminder. For games: wishlist and follow under the user's account, play the demo, join the Discord as the user. Never request creator or press keys unless the user really is one.

**Privacy limits:** the product and the studio's public statements. No player lists, reviewer names, or Discord member data.

**Typical moves to log:** store page icon, screenshot, or subtitle change; version release; editorial feature; soft launch; worldwide launch; festival or event participation; demo or playtest; UA creative start; creator campaign; price or paywall change; update or DLC.

## Single Launch or Campaign

**Curve sources:** the parent target's monthly curve from one source, as above. Alongside it, keep `launch-log.csv` with daily counters the launch made public (waitlist claims, pre-save counts, crowdfunding backers and totals, launch-platform rank, view counts), each with its source and pull time. The monthly curve feeds `timeline.mjs`; the daily log is read by hand.

**Window:** 90 days before the first public signal to 90 days after launch, unless the user names one.

**Stages:**
- Stage 1: date the first public signal (a teaser, a new subdomain, a trademark filing, a waitlist page).
- Stage 2 and 6: the announcement sequence, the assets per channel, and which pieces carried reach.
- Stage 3: join the waitlist or pre-save as the user, with approval.
- Stage 4: the team's launch retrospectives.
- Stage 5: certificate logs for launch subdomains, Wayback captures of the teaser page, the paid promotion sweep.
- Stage 7: the launch is one cluster. Lift compares the three months from launch with the three before. The leading-channel call will be declined for windows under 18 months; that's expected.
- Hiring: skip.

**Privacy limits:** as for the parent target's type.

**Typical moves to log:** teaser, waitlist open, trailer, announcement, partner or creator seeding, press embargo lift, launch day, launch-platform post, first update, price change, follow-up drop.

## Privacy Rules for Every Type

- Study people only in their public, professional capacity: published work, public stats, public interviews, public posts about the work.
- Never build lists of a target's followers, fans, customers, staff, community members, or reviewers. Quote reviews and comments without names or handles.
- Never contact the target, its team, or its audience on the strength of the teardown.
- Never record private details (home location, family, health, private accounts), even if public somewhere.
- Blur or crop personal details out of screenshots before sharing the playbook.
