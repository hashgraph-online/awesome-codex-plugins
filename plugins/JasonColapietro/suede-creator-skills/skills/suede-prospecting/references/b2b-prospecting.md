# B2B Prospecting Reference

For when the user sells to non-SaaS B2B: services, agencies, manufacturers, mid-market and enterprise companies, professional services firms.

---

## ICP Signals That Matter (B2B branch)

### Firmographic signals

- **Industry / vertical**: NAICS or SIC codes if precision matters
- **Company size**: headcount band, revenue band, location count
- **Geography**: relevant for time zones, regulations, on-site requirements
- **Business model**: service vs product vs distribution; B2B vs B2B2C
- **Ownership**: independent, PE-backed, public, family-owned: affects buying motion

### Buying signals

- **Trigger events**: new C-level hire, recent acquisition or divestiture, IPO/funding, opening a new location, recent rebrand, expansion announcement
- **Vendor signals**: posting RFPs publicly, switching costs in last quarterly report, contract renewal windows
- **Operational signals**: recent layoffs (cost pressure) or rapid hiring (capacity pressure)
- **News mentions**: launching new initiative, entering new market, regulatory change forcing action
- **PR / press**: anything that signals "this company is changing right now"

### Decay signals

- Multiple bankruptcies or PE-stripped operations
- Negative growth + cost-cutting headlines
- Ownership stagnation (small family-owned, no growth incentive)
- Buyer turnover (3+ Marketing Directors in 2 years)

---

## Discovery Sources (B2B branch)

### Tier 1: primary discovery

- **Apollo**: candidate for general B2B firmographic and contact discovery;
  verify current coverage on the target segment
- **ZoomInfo**: enterprise B2B + intent signals (mid-market+)
- **LinkedIn Sales Navigator**: candidate for manual industry, role, and signal
  research; verify current coverage and terms
- **Clay**: when you need custom waterfall lookups (e.g., enrich Apollo records with Hunter and another licensed provider)

### Tier 2: industry-specific directories

- **Crunchbase / Pitchbook**: funded businesses
- **D&B Hoovers**: large traditional B2B firmographics
- **State / national business registries**: for verified incorporation data
- **Industry association membership rosters**: trade groups often publish member lists
- **Trade show exhibitor lists**: signals active participation in a vertical
- **Procurement databases** (Procore for construction, e.g.): vertical-specific signals

### Tier 3: trigger event monitoring

- **Google Alerts / Feedly**: trigger keywords ("acquired," "hires," "expansion," "raises," "announces")
- **PR Newswire / Business Wire**: company-controlled announcements
- **SEC filings** (public companies): material change disclosures
- **State filings**: new entity formation, dissolution

For gap plays (a signal plus a gap you can verify from outside, such as ads
running with no visible tracking or many locations with thin location pages), see
[saas-prospecting.md](saas-prospecting.md#gap-plays-a-signal-plus-a-gap-you-can-verify).
The table and rules apply to B2B accounts too.

---

## Qualification Checklist (B2B branch)

- [ ] Industry / vertical matches ICP (use a recognized classification if possible)
- [ ] Company size within range (employees or revenue)
- [ ] Geography fits
- [ ] At least one trigger event in last 90–180 days
- [ ] Decision-maker role exists (CEO, COO, VP Operations, Director of X: match buyer profile)
- [ ] Email contact verifiable (named role > info@ catchall)
- [ ] Source URLs captured for firmographic claims
- [ ] No disqualifiers (closed, acquired-paused, multi-bankrupt, off-ICP)

---

## Output Columns (B2B branch)

Recommended CSV columns:

```csv
score,company,domain,industry,naics_code,size_band,revenue_band,country,city,trigger_event,trigger_date,contact_name,contact_title,contact_email,email_status,linkedin_url,source_urls,why_prospect,confidence,verified_date,notes
```

For chat table, condense to: Score | Company | Industry | Size | Trigger | Contact | Email status | Confidence.

---

## Top Outreach Targets Selection (B2B)

Prioritize a bounded review set when the evidence supports it:

1. **Trigger event recency**: compare current and older events without imposing
   a universal expiry window
2. **Trigger specificity**: prefer a cited event tied to the buyer's problem
   over general company news
3. **Decision-maker evidence**: distinguish a confirmed professional contact
   from a role-only inference
4. **Vertical fit precision**: use the taxonomy the current ICP and source data
   can support

Each top target rationale names the trigger and decision-maker: "Hired new VP of Marketing 14 days ago; verified email; mid-market manufacturer matching ICP."

---

## Common Mistakes (B2B)

1. **Treating B2B like SaaS**: funding rounds matter less; PE ownership and acquisition activity matter more.
2. **Trying to verify private company revenue precisely**: most public databases approximate. Use size bands, not point estimates.
3. **Ignoring procurement complexity** at enterprise scale: your prospect contact list may not include the actual approver.
4. **Cold-emailing executive assistants**: they're not the buyer and they will flag your outreach as spam.
5. **Source URL hygiene**: without source lineage, you can't defend a contact under GDPR DSAR or CAN-SPAM challenge.
6. **Stopping at one source**: provider accuracy varies by segment and date.
   Cross-verify important claims with a current first-party or independent
   source.
