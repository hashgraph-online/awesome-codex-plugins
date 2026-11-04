# SaaS Prospecting Reference

For when the user sells SaaS or digital services to other SaaS companies / digital businesses.

---

## ICP Signals That Matter (SaaS branch)

Beyond standard firmographics (industry, size, geography), SaaS prospects are qualified by:

### Technographic signals

- **Tech stack**: do they use complementary tools (your integration target) or competing tools (a switch opportunity)?
- **Recent stack changes**: adding/removing tools signals active vendor evaluation
- **Custom-built vs off-the-shelf**: DIY tooling often means a buyer who'd benefit from your product
- **Free/freemium plan signals**: using a free competitor means they may be ready to upgrade

### Growth signals

- **Funding round**: Series A / B / C in last 6 months = budget + new hires + tool needs
- **Headcount growth**: a material, recently verified change can indicate
  scaling pressure; compare it with the company's baseline
- **Hiring signals**: specific role openings (e.g., "Head of RevOps" → ICP for revops tooling)
- **Product velocity**: frequent shipping, new features, blog posts = healthy growth motion
- **Open positions for your buyer's role**: if you sell to Marketing Ops and they're hiring one, that's a signal

### Decay signals (downgrade scoring)

- Layoffs in target department
- Funding round >2 years ago with no follow-up
- Product hasn't shipped in 6+ months
- Team page shows founders only (very early: may not have budget)

---

## Discovery Sources (SaaS branch)

Combine 2+ sources for cross-verification.

### Tier 1: primary discovery

- **Apollo**: firmographic + technographic + contact data. Good for building large initial lists.
- **Clay**: candidate for waterfall enrichment, custom scoring, and
  multi-source merges; test quality and cost on the intended list
- **ZoomInfo**: enterprise-grade firmographic + intent signals. Expensive; mid-market+.
- **LinkedIn Sales Navigator**: decision-maker mapping. Use manually, never bulk scrape.

### Tier 2: technographic / growth signals

- **BuiltWith**: tech stack lookups, find sites using specific tools
- **Wappalyzer**: free browser extension + API; lighter tech stack signal
- **Crunchbase**: funding rounds, headcount, founders
- **Pitchbook**: deeper investor data (enterprise/paid)
- **ProductHunt**: recent launches, builder audience
- **Hacker News / Show HN**: technical builders launching products

### Tier 3: buying signals

- **Job boards** (LinkedIn Jobs, Indeed, AngelList): role openings as signals
- **RB2B or HubSpot Breeze Intelligence**: visitor identification (warm anonymous traffic)
- **GitHub stars/forks of competitor or adjacent repos**: a possible
  developer-level intent signal when the current GitHub API and account access
  lawfully expose it. Confirm rate limits, source date, company mapping, and
  terms; a star alone indicates attention, not purchase intent.
- **Recent blog posts / changelog**: product direction signals
- **G2 reviews mentioning competitor switches**: explicit dissatisfaction signal

#### GitHub prospecting pattern (when audience is developers)

For dev-tool SaaS, GitHub can supply an attention signal when current API or
manual access is authorized:

1. Identify 3–5 anchor repositories: direct competitors, category leaders, and
   complementary tools.
2. Discover whether an authenticated GitHub API, approved export, or manual
   repository view is currently available; confirm rate limits and terms.
3. Review only the public fields needed for the stated business purpose.
4. Map company affiliation only when a current public source supports it.
5. Treat a star or fork as attention, not purchase intent; require another
   recent work-context signal before qualification.
6. Validate any approved contact channel with a currently available validator,
   or provide a manual validation checklist.

If no authorized API or browser is available, ask for repository URLs or an
export and use a manual review worksheet.

---

## Gap Plays: a signal plus a gap you can verify

The strongest plays for services and tooling sellers pair two things: a signal
that the company is spending or growing, and a gap you can verify from outside
that your offer fixes. The signal says they have budget and a reason to act. The
gap gives you a specific, checkable opener instead of a guess. This applies to
the B2B branch as well.

| Signal | Gap to verify | How to check it from outside | Fits an offer like |
|--------|---------------|------------------------------|--------------------|
| Recent funding or a new marketing leader | The site hasn't changed in a long time, or doesn't match the new story | Wayback Machine snapshots, the copyright year, positioning that doesn't match the funding announcement | Website, CRO, positioning |
| Hiring several SDRs or BDRs | The outbound stack doesn't match the plan | Tools named in the job post, sending-domain DNS (SPF, DKIM, DMARC), the tech stack | Email infrastructure, enrichment, deliverability |
| Hiring for repetitive work (data entry, reporting, lead research, CRM admin) | The job post describes tasks that can be automated | The responsibilities list in the post itself | Automation, RevOps, AI agents |
| Running paid ads | No visible ad or analytics tags | Page source, the browser network tab, or a tag-checker extension (Meta Pixel Helper, Google Tag Assistant) | Tracking and attribution setup |
| Running paid ads | Paid traffic lands on the homepage | The destination link on each ad in the Meta Ad Library or LinkedIn Ad Library | Landing pages, CRO |
| Running the same ads for months | Creative fatigue | Start dates in the Meta Ad Library; the Google Ads Transparency Center for search and YouTube | Ad creative |
| Many locations | Missing or thin location pages | Store-locator count vs. pages found with `site:domain.com/locations`; Google Business Profiles per location | Local SEO |
| Many integrations or use cases | Few pages about them | The integrations directory vs. a `site:` search for integration or use-case pages | Programmatic SEO, content |
| A lead magnet (ebook, calculator, webinar) | No follow-up after opt-in | Opt in with an address you control, log every email for 14 days, then unsubscribe | Email nurture, lifecycle |
| Expanding into a new country | The site isn't localized for it | Language switcher, `hreflang` tags, local currency and payment methods on pricing | Localization, international SEO |

**Rules for gap plays:**

1. **Verify the gap; never assume it.** Record what you checked, the date, and a
   screenshot or URL, the same as any other row. An agent asked to find gaps will
   invent them unless every gap needs evidence. "No gap found" is a valid result.
2. **Know what can't be seen from outside.** Server-side tracking (Meta's
   Conversions API, server-side Google Tag Manager) doesn't show in page source,
   so a missing browser tag isn't proof of missing tracking. Ask, don't accuse. A
   homepage is a normal destination for brand-name search ads, and an ad running
   for months may be the winner rather than tired. Ad longevity is a proxy, not
   proof.
3. **Re-check before sending.** Gaps get fixed. Re-verify within 7 days of the
   first touch, or drop the gap from the message.
4. **The gap must map to your offer.** Spotting a problem you can't fix is
   research, not a play.
5. **Lead with the observation and a question, not a verdict.** "Your Meta ads
   for the spring launch point to the homepage. Is that on purpose?" gets
   replies. "Your landing pages are wasting your ad spend" gets deleted. Offer the
   evidence, and any teardown, only after they say yes. The opener itself belongs
   to `suede-cold-email`.

Searching for these by hand is slow, which is why the plays used to be rare.
Agents with web, ad-library, and X search access can build the candidate list. A
human still reviews the evidence for every Hot row and a sample of Warm rows.
Once a play gets replies, `suede-marketing-loops` can run it as a scheduled
signal check.

---

## Qualification Checklist (SaaS branch)

For each candidate, verify:

- [ ] Industry vertical matches ICP
- [ ] Company size (headcount) within range
- [ ] Tech stack includes (or notably excludes) a target technology
- [ ] Funding stage matches buyer maturity
- [ ] At least one growth signal in last 90 days (funding, hiring, product velocity)
- [ ] Decision-maker role exists at the company (named or inferable from job listings)
- [ ] Email contact verifiable
- [ ] No disqualifiers (closed, acquired-and-paused, layoffs, ICP miss)

---

## Output Columns (SaaS branch)

Recommended CSV columns:

```csv
score,company,domain,industry,size_band,country,funding_stage,last_round_date,tech_stack_match,signal,signal_date,contact_name,contact_title,contact_email,email_status,linkedin_url,source_urls,why_prospect,confidence,verified_date,notes
```

For chat table, condense to: Score | Company | Industry | Size | Signal | Contact | Email status | Confidence.

---

## Top Outreach Targets Selection (SaaS)

Prioritize a bounded review set when the evidence supports it:

1. **Signal recency**: compare current and older signals without assuming a
   universal expiry window
2. **Tech stack match strength**: prefer cited current compatibility over
   inferred fit
3. **Decision-maker evidence**: distinguish confirmed professional contacts
   from role-pattern guesses
4. **Source confidence**: prefer independent current corroboration over a
   single vendor record

Each top target gets a one-sentence outreach rationale that names the specific signal: "Raised Series B 30 days ago; hiring Head of RevOps; verified VP of Ops email."

---

## Common Mistakes (SaaS)

1. **Buying lists from Apollo wholesale** without re-verifying email and re-checking firmographics. Stale data is the norm.
2. **Treating tech stack data as 100% accurate**. BuiltWith and Wappalyzer miss things; Clay's waterfalls miss things. Cross-check.
3. **Targeting Series C+ for early-stage SaaS sellers**. The buyer profile is wrong: too many procurement hoops, too much red tape.
4. **Targeting Series Pre-Seed seed** for products requiring meaningful budget. They have neither budget nor evaluator bandwidth.
5. **Treating intent data as proof**: verify freshness, provenance, grain, and
   predictive value on the target segment before changing priority.
