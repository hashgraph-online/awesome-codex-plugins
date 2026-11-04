# Prospecting Data Sources

Tool selection guide for prospecting across all three branches.

Named products are candidates, not assumed integrations or endorsements.
Before use, discover what is currently callable, authenticated, authorized, and
permitted; read current official documentation and account terms. Treat vendor
coverage, accuracy, limits, pricing, and feature claims as unverified until a
dated source or current sample supports them. If no tool is available, use a
manual, source-linked research worksheet or a user-supplied export.

---

## Tool selection by goal

| Goal | Primary tools | Notes |
|------|--------------|-------|
| **Build initial firmographic list (B2B / SaaS)** | Apollo, ZoomInfo, Clay | Apollo for breadth, ZoomInfo for enterprise + intent, Clay for custom workflows |
| **Decision-maker mapping** | LinkedIn Sales Navigator (manual), Apollo, ZoomInfo | Compare current coverage on a representative sample. Never bulk scrape restricted sources. |
| **Tech stack qualification (SaaS)** | BuiltWith, Wappalyzer | BuiltWith has wider coverage + paid plans for bulk; Wappalyzer is lighter + free for small use |
| **Funding signals (SaaS)** | Crunchbase, Pitchbook | Crunchbase free tier sufficient for early signals; Pitchbook for deeper investor data |
| **Email pattern discovery** | Hunter, Snov, Apollo | Pattern guessing: followed by verification |
| **Email deliverability verification** | Any currently authorized validator | Read current result semantics; otherwise label addresses unverified and use a manual handoff |
| **Visitor identification (warm intent)** | RB2B, HubSpot Breeze Intelligence | Anonymous traffic → company identification |
| **Intent data** | ZoomInfo Intent, 6sense, Bombora | Pre-warmed signals; mid-market+ pricing |
| **Trigger event monitoring** | Google Alerts, Feedly, LinkedIn Sales Nav alerts | Free options are sufficient for most |
| **Public posts and announcements** | X search (Grok, for example, searches X directly), LinkedIn posts (manual), news search | Grok via the xAI API; Exa MCP. Read the original post, not a summary |
| **Ad activity (gap plays)** | Meta Ad Library, Google Ads Transparency Center, LinkedIn Ad Library | Meta Ad Library API covers political and EU ads only; check its current scope. Otherwise browser research |
| **Local business discovery** | Google Maps (manual), Yelp, Facebook Pages | Browser-assisted, not bulk-extracted |

---

## Apollo

**Candidate use**: General B2B / SaaS firmographic and contact discovery when a
current sample supports coverage for the target market.

**Strengths**:
- Coverage breadth to verify on the target geography and segment
- Firmographic and signal filters to verify on the current account
- Contact-discovery fields with explicit provenance
- Current export, quota, and pricing terms

**Watch out for**:
- Data freshness varies: re-verify before scoring as "Hot"
- Email accuracy varies by segment and date: validate on a current sample
- Bulk export limits apply

**Verification**: confirm Apollo's current documentation, account access,
freshness, export limits, and terms before use.

---

## Clay

**Use for**: Multi-source enrichment, waterfall lookups, custom scoring logic. When list quality matters more than list size.

**Strengths**:
- Waterfall logic: try Apollo first, then ZoomInfo, then other licensed providers in the Clay catalog
- Current provider set and field-level provenance
- Any automated extraction behavior, source traceability, and review controls
- Custom columns + scoring formulas
- Connector availability varies; discover the current session and verify
  authorization before use

**Watch out for**:
- Per-credit pricing can spike on large lists
- Complexity overhead: easy to over-engineer workflows

**Verification**: confirm Clay's current providers, credit model, field
provenance, account access, and terms before use.

---

## ZoomInfo

**Use for**: Enterprise B2B + intent data. Mid-market+ buyer profiles.

**Strengths**:
- Enterprise-grade firmographic depth
- Intent signals (companies searching topics relevant to your offer)
- Fit for the target segment and deal size must be tested
- Connector availability varies; discover the current session and verify
  authorization before use

**Watch out for**:
- Pricing and contract structure require current written verification
- Overkill for SMB prospecting
- Locked into multi-year contracts typically

**Verification**: confirm ZoomInfo licensing, export rights, signal freshness,
account access, and terms before use.

---

## HubSpot Breeze Intelligence (formerly Clearbit)

**Status (checked October 2026)**: HubSpot acquired Clearbit in 2023 and folded it into Breeze Intelligence inside HubSpot. The standalone Clearbit products and free tools were retired; existing API access depends on the user's contract.

**Use for**: Company and contact enrichment and company-level visitor intent, for teams already on HubSpot.

**Strengths**:
- Company enrichment (industry, size, funding, tech stack) written straight to HubSpot records
- Company-level identification of website visitors

**Watch out for**:
- Credits and tier access are part of HubSpot packaging and change; verify in current HubSpot documentation
- Outside HubSpot, use Apollo, Clay, or ZoomInfo instead

**Verification**: confirm the user's HubSpot tier, credit balance, coverage, and terms before use.

---

## Hunter / Snov

**Use for**: Email pattern discovery + lightweight verification on small lists.

**Hunter strengths**:
- Domain-based email discovery
- Built-in deliverability verification
- Current free or paid quota may support occasional use; verify first

**Snov strengths**:
- Email finder + drip campaigns (overlap with outreach tooling)
- Bulk verification
- Compare current total cost at the intended volume

**Watch out for**:
- Both are pattern-guessing tools: accuracy depends on the target company's email pattern being inferable
- Use a currently callable, authorized validator when available and read its
  result semantics. Otherwise label results `unverified` and keep them out of
  send-ready exports.

**Verification**: confirm Hunter or Snov access, current result semantics,
verification quality, quotas, and terms before use.

---

## Truelist

**Use for**: Email deliverability validation before adding contacts to outreach lists. Critical safety step.

**Strengths**:
- Single-email sync verification (`/api/v1/verify_inline`) + bulk async (`/api/v1/verify`)
- Returns `email_state` (ok / email_invalid / risky / unknown / accept_all) + `email_sub_state` (email_ok / is_disposable / is_role / unknown_error / failed_smtp_check) + did-you-mean typo suggestions
- Catches catch-all domains, role accounts, spam traps, disposable providers
- API or connector availability must be confirmed from current vendor
  documentation and the current session
- SDKs, integrations, and pricing must be verified from current documentation

**Why this matters**: Unverified addresses can damage sender reputation and
create compliance risk. Define an approved bounce threshold with the sending
provider, validate current samples, and quarantine unknown or risky results.
Do not assume one verifier catches every invalid address.

**Verification**: confirm Truelist's current result semantics, account access,
API limits, and vendor documentation before use.

---

## LinkedIn Sales Navigator

**Candidate use**: Manual decision-maker discovery when current account access,
terms, and a representative sample support it.

**Strengths**:
- Decision-maker coverage and freshness to test on the target segment
- Job-change, post, and signal fields to verify before use
- Lead lists, alerts, saved searches
- Inmail credits (separate channel from cold email)

**Hard rules**:
- **Never bulk scrape**. LinkedIn aggressively bans scrapers. Account ban risk is real and permanent.
- Use Sales Nav as a research interface: open profiles, read, take notes, capture key data manually.
- Apollo and other tools claim LinkedIn data via partnerships / public mirroring: verify the source legitimacy before assuming compliance.

**Access rule**: default to manual research unless a currently callable,
authorized connector is discovered and its terms permit this use.

---

## BuiltWith / Wappalyzer

**Use for**: Tech stack qualification (SaaS branch).

**BuiltWith**:
- ~50K+ technologies tracked
- API + bulk lookups (paid)
- Historical data (when stack changed)

**Wappalyzer**:
- Free browser extension; paid API
- Lighter coverage than BuiltWith
- Faster for one-off lookups

Cross-reference both for high-confidence tech stack signals.

---

## Crunchbase

**Use for**: Funding signals (SaaS branch).

**Strengths**:
- Free tier shows recent funding events
- Paid (Pro / Enterprise) unlocks alerts and deep history
- API access for paid users

**Watch out for**:
- Coverage is best for VC-backed companies; bootstrapped + small businesses underrepresented
- Self-reported data: verify funding amounts independently

---

## GitHub (stargazers / forks / watchers)

**Use for**: Developer-intent prospecting. Especially powerful for dev-tool SaaS: stargazers of competitor or category-defining repos are in-market signal.

**Strengths**:
- Public API may be available; confirm current authentication, rate limits,
  fields, privacy constraints, and terms
- High signal quality (a starred repo = explicit interest)
- Forks are an even stronger signal (intent to modify, not just bookmark)
- No GitHub extraction CLI ships with this skill. Use a currently callable,
  authorized connector/API or a user-supplied export; otherwise provide a
  manual collection worksheet.

**Watch out for**:
- Public contact coverage varies by cohort and must be measured rather than
  assumed; never infer or fabricate private addresses
- Define repository relevance from product fit and a sampled signal-quality
  review, not a universal star-count band
- Most prospects are individuals, not company contacts directly: need to figure out their company from `company` field or LinkedIn

**Verification**: confirm GitHub's current API documentation, authentication,
rate limits, and applicable terms before use.

---

## Firecrawl / Browserbase (single-target site research)

**Use for**: Programmatically extracting content from a **prospect's own website** that you already found via discovery on platforms like Google Maps, Yelp, or LinkedIn. Not for scraping those platforms themselves.

### Firecrawl

- **Best for**: "Just give me the page as markdown": Local SMB website status checks, B2B company about/team page extraction, structured field extraction
- **Strengths to verify**: source extraction and structured output for
  individual public sites
- **Access**: discover whether an authorized API, connector, or manual browser
  is currently available

### Browserbase

- **Best for**: When you need real Chromium: JS-heavy pages, cookie consent dialogs, form submission to reach a contact page, session state
- **Strengths**: Full browser control via Playwright/Puppeteer; Stagehand provides AI-friendly natural-language extraction; session recordings for debugging
- **Access**: discover whether an authorized browser, API, or connector is
  currently available

### Critical compliance line

Both tools can technically point at any URL. The hard rule:

- ✓ **OK**: extracting content from a single business's own website (`joescoffeeshop.com`) that you found through manual discovery
- ✗ **NOT OK**: pointing them at `google.com/maps`, LinkedIn search results, Yelp listings, or any platform whose ToS prohibits bulk extraction

Discovery happens on platforms (manual browser-assisted research). Extraction happens on individual public business sites.

**Verification**: confirm current Firecrawl or Browserbase documentation,
session access, pricing, and target-site terms before use.

---

## RB2B and company-level visitor identification

**Use for**: Identifying anonymous site visitors as warm intent signals.

**Strengths**:
- Pixel-based visitor → company identification
- High-intent: they came to your site, they're already in research mode
- Slack / email alerts on key visits

**Watch out for**:
- Privacy/GDPR considerations: verify your privacy policy disclosures
- Person-level identification raises higher concerns than company-level

**Verification**: confirm RB2B's current identification grain, account access,
privacy requirements, and terms before use.

---

## Free / browser-only fallbacks

When the user has no callable or paid tools, give them a manual checklist using:

- **Google Search**: exact business name + city + role searches
- **LinkedIn** (manual, no scraping): company pages, employee lookups
- **Crunchbase or another current source**: funding events, when access and
  terms are verified
- **Wappalyzer browser extension**: tech stack at a glance
- **Authorized contact-data source**: verify current allowance, terms, and
  permitted use before each run
- **Google Maps**: for Local SMB discovery
- **Business websites + About pages**: primary source for any claim
- **News sites + press releases**: trigger event monitoring via Google Alerts

Slower than tooled-up workflows, but produces high-quality smaller lists if the user is willing to do the work.

---

## Sequencing recommendations

A typical full-stack prospecting workflow:

1. **Define ICP** from product-marketing context (no tools needed)
2. **Initial list** from Apollo or ZoomInfo (firmographic filter)
3. **Enrich** with Clay (waterfall: tech stack, funding, trigger events)
4. **Decision-maker mapping** in LinkedIn Sales Nav (manual)
5. **Email pattern discovery** with Hunter or Apollo's built-in
6. **Email status** from an authorized validator, or an explicit `unverified`
   label plus a user-operated validation handoff
7. **Hand off** to `suede-cold-email` for outreach copy

Adapt this sequence based on which tools the user actually has.
