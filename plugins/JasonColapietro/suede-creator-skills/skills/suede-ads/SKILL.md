---
name: suede-ads
description: "Suede AI Ads Skills. Use when planning paid acquisition and asked to \"audit our paid campaigns\" or choose channels, structure campaigns, set budget pacing, retargeting and kill-or-scale rules from verified unit economics and performance. NOT FOR: ad asset production (suede-ad-creative), tracking implementation (suede-analytics), attribution reconciliation (suede-attribution), or landing-page work (suede-site-alchemy)."
metadata:
  display-name: "Suede AI Ads Skills"
  version: 2.3.1
---

# Suede AI Ads Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from campaign exports and business economics; current official platform documentation for changing controls. Live account access is optional for audits and requires existing authorization for changes.

Use this paid-acquisition playbook to create, optimize, and scale campaigns against explicit acquisition economics. Never assume account access.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Campaign Goals
- Which platform(s) are running now, or which do you want to start with?
- What's the primary objective? (Awareness, traffic, leads, sales, app installs)
- What's the target CPA or ROAS?
- What's the monthly/weekly budget?
- Any constraints? (Brand guidelines, compliance, geographic)

### 2. Product & Offer
- What are you promoting? (Product, free trial, lead magnet, demo)
- What's the landing page URL?
- What makes this offer compelling?

### 3. Audience
- Who is the ideal customer?
- What problem does your product solve for them?
- What are they searching for or interested in?
- Do you have existing customer data for lookalikes?

### 4. Current State
- Have you run ads before? What worked/didn't?
- Do you have existing pixel/conversion data?
- What's your current funnel conversion rate?
- Do you have creative assets already, or do they need to be produced?

---

## Reference Routing

This skill's depth lives in references: load by intent. For **any operational decision on a live account** (kill/keep/scale/budget), load the relevant playbook before answering; the thresholds live there, not here.

| User intent | Load | Covers |
|---|---|---|
| B2B strategy, funnel stages, budget splits, kill rules, lead quality, breakeven math | [b2b-paid-playbook.md](references/b2b-paid-playbook.md) | Demand lifecycle, leading/lagging signals, kill rules, offline conversion loop, U/B/F lead scoring, scaling quadrant |
| Meta operations: when to kill/graduate/scale an ad, fatigue, testing structure | [meta-decision-system.md](references/meta-decision-system.md) | TCPL-anchored decision tree, ad-count ceiling, 80/20 CBO structure, fatigue bands, lead forms, Advantage+ transition |
| Meta ad sequencing, ordered ad paths, Target frequency setup | [meta-ad-sequencing.md](references/meta-ad-sequencing.md) | Eligible objectives, flight math, hook-problem-proof-offer path, cost trade-off, retargeting workaround for Sales and Leads |
| LinkedIn operations: bidding, audience sizing, scaling, benchmarks, TLAs, formats | [linkedin-b2b-playbook.md](references/linkedin-b2b-playbook.md) | Bidding progression, penetration scaling, sizing rules, funnel benchmarks, document/conversation ads, audit shortlist |
| Google Search: what to spend on first, structure, match types, negatives, PMax | [google-search-playbook.md](references/google-search-playbook.md) | Intent ladder, account structure, match-type gates (incl. AI Max), negatives, bidding by volume, offline conversions, PMax guardrails |
| Named-account targeting, pipeline acceleration, cross-channel retargeting | [abm-playbook.md](references/abm-playbook.md) | LinkedIn/Meta ABM, list mechanics, acceleration campaigns, UTM cross-channel remarketing, ABM measurement |
| Weekly competitor ad tracker, ad-library monitoring, build vs. buy for ad-spy tools | [competitor-ad-tracker.md](references/competitor-ad-tracker.md) | Scheduled pull from public ad libraries, creative storage, model tagging, weekly diff, gap questions, longevity as a proxy |
| Generating Google RSAs | [rsa-output-spec.md](references/rsa-output-spec.md) | Mandatory output spec: limits, sidecars, template, self-check |
| Audience setup, tracking setup, launch checklists, copy formulas | [audience-targeting.md](references/audience-targeting.md) · [conversion-tracking.md](references/conversion-tracking.md) · [platform-setup-checklists.md](references/platform-setup-checklists.md) · [ad-copy-templates.md](references/ad-copy-templates.md) | Existing foundations |

---

## Platform Selection Guide

| Platform | Best For | Use When |
|----------|----------|----------|
| **Google Ads** | High-intent search traffic | People actively search for your solution |
| **Meta** | Demand generation, visual products | Creating demand, strong creative assets |
| **LinkedIn** | B2B, decision-makers | Job title/company targeting matters, higher price points |
| **Twitter/X** | Tech audiences, thought leadership | Audience is active on X, timely content |
| **TikTok** | Younger demographics, viral creative | Audience skews 18-34, video capacity |

---

## Campaign Structure Best Practices

### Account Organization

```
Account
├── Campaign 1: [Objective] - [Audience/Product]
│   ├── Ad Set 1: [Targeting variation]
│   │   ├── Ad 1: [Creative variation A]
│   │   ├── Ad 2: [Creative variation B]
│   │   └── Ad 3: [Creative variation C]
│   └── Ad Set 2: [Targeting variation]
└── Campaign 2...
```

### Naming Conventions

```
[Platform]_[Objective]_[Audience]_[Offer]_[Date]

Examples:
META_Conv_Lookalike-Customers_FreeTrial_[YYYYQ#]
GOOG_Search_Brand_Demo_Ongoing
LI_LeadGen_CMOs-SaaS_Whitepaper_[MMMYY]
```

### Budget Allocation

**Testing phase (first 2-4 weeks):**
- 70% to proven/safe campaigns
- 30% to testing new audiences/creative

**Scaling phase:**
- Consolidate budget into winning combinations
- Increase budgets ~20% at a time: never 30%+ in one move (resets platform learning)
- Wait 3-5 days between increases for algorithm learning

---

## Ad Copy

Copy formulas, angle libraries, and character limits belong to
`suede-ad-creative`. This skill decides which campaign, audience, and offer the
copy serves. Quick structures for a brief live in
[references/ad-copy-templates.md](references/ad-copy-templates.md).

---

## Audience Understanding & Targeting

Knowing your audience deeply is still the highest-leverage work in paid ads: demographics, job titles, pain points, fears, hopes, the exact language they use, who they follow, what they've tried, why they failed, what they buy. **Gather every identifier you can.**

What has changed is **where you apply that knowledge.** As ad-platform algorithms have gotten dramatically better at finding the right person, jamming all your audience identifiers into the platform's *targeting filters* underperforms feeding those same identifiers into the *creative* (headlines, copy, visuals, hooks, examples).

The discipline now: **audience knowledge → creative first, targeting filters second.** How much that ratio tips toward "creative" varies meaningfully by platform.

### Platform-by-platform: where to apply audience knowledge

| Platform | Audience knowledge → creative | Audience knowledge → targeting filters | Notes |
|----------|------------------------------|-------------------------------------|-------|
| **Meta** | **80%+** | 20% | Broad audiences plus distinct creative usually beat interest stacking. See "Meta in the Andromeda era" below. |
| **Google Search** | 40% | **60%** | Keywords are still the dominant signal: match-types, search-intent layering, and negative keywords still drive performance. Creative (RSA headlines) matters but is downstream of the keyword. |
| **Google Performance Max / Demand Gen** | **70%** | 30% | Audience signals are advisory, not deterministic. Creative + product feed quality dominate. |
| **LinkedIn** | 40% | **60%** | Job-title / company / industry filters still produce real precision because LinkedIn's identity data is high-quality. Creative makes the click; firmographics make the *right person* see it. |
| **TikTok** | **70%** | 30% | Algorithm is closer to Meta's model: broad targeting + native-feeling creative wins. Some audience interests help but creative dominates. |
| **Twitter/X** | 50% | 50% | Interest + follower targeting still meaningful, but creative differentiation is high-leverage given lower competition. |

These ratios are directional, not precise. Test in your actual account.

For how each identifier becomes a headline, hook, or angle, use `suede-ad-creative`: it owns the angle-to-copy mapping.

### Key Concepts (still apply)

- **Lookalikes**: Base on best customers (by LTV), not all customers. Still high-value across platforms.
- **Retargeting**: Segment by funnel stage (visitors vs. cart abandoners). See "Retarget with a different offer" and "The four-ad retargeting layer" below.
- **Exclusions**: Exclude existing customers and recent converters: showing ads to people who already bought wastes spend.

**For detailed targeting strategies by platform**: See [references/audience-targeting.md](references/audience-targeting.md)

---

## Meta in the Andromeda era

**What is verified.** Andromeda is Meta's ad retrieval system. Meta Engineering
described it on December 2, 2024: for each impression it narrows tens of
millions of eligible ads to a few thousand candidates before the ranking models
and the auction run. Meta's advertiser guidance in December 2025 called
creative diversification a foundational practice: vary format, message, and
persona instead of iterating on one concept. Everything else below is operating
practice to test, not platform fact.

**Operating practice that follows:**

- **Creative does most of the targeting.** Start broad (country plus customer
  exclusions) and let distinct creative find distinct buyers. Test it: duplicate
  a winning interest-stacked ad set, remove the interests, run both for 7 days
  on equal budget, and compare CPA on the optimization event.
- **Distinct concepts beat near-duplicates.** Ten color swaps of one ad teach
  the system one thing. Ten different angles, formats, and personas teach it ten.
  Track concept count, not ad count.
- **Make statics part of the mix.** Statics are cheap and fast, so they make
  concept volume affordable. Test them against video on cost per qualified
  result; do not assume either format wins.
- **Identity-keyword variants.** Duplicate a winner and insert the buyer's
  identity into the headline or first line ("leads per week" becomes "dental
  leads per week", "law firm leads per week"). The word works on the reader and
  gives the system a clearer signal. Use only identities the offer truly serves.
- **AI-assisted segment rewrites.** Give a model the winning ad and ask it to
  rewrite for one named segment while keeping voice, structure, and claims
  identical. Review every variant for invented claims, then route the batch
  through `suede-ad-creative` for the pre-delivery self-check.
- **Rescue test for unspent variants.** Budget optimization often gives most
  variants little or no spend. Move the few you have strong evidence for into a
  separate ad set and give them a fair read before discarding them.
- **Look native.** Study what performs organically in the niche on Instagram,
  TikTok, and YouTube and match that look. A proven organic post run as a
  partnership or boosted ad is often the cheapest test available.
- **Attribution windows changed.** Since January 12, 2026 the Ads Insights API
  no longer returns 7-day view and 28-day view windows. Available windows are
  1-day click, 7-day click, 28-day click, 1-day engaged-view, and 1-day view.
  Update dashboards and any report that compared view-through windows.

### Ad sequencing

Meta ranks the second ad someone sees against the first, so plan two or three
ads as a path (hook, problem, proof, offer) rather than testing each alone.
Setup limits, flight math, costs, and the retargeting workaround for Sales and
Leads objectives live in [meta-ad-sequencing.md](references/meta-ad-sequencing.md).

The full kill, graduate, and scale rules live in
[meta-decision-system.md](references/meta-decision-system.md).

## Creative Best Practices

### Image Ads
- Clear product screenshots showing UI
- Before/after comparisons
- Stats and numbers as focal point
- Human faces (real, not stock)
- Short, legible text overlay. Meta retired its 20% text rule in 2020, but
  text-heavy images can still deliver worse; test a lighter version

### Video Ads Structure (15-30 sec)
1. Hook (0-3 sec): Pattern interrupt, question, or bold statement
2. Problem (3-8 sec): Relatable pain point
3. Solution (8-20 sec): Show product/benefit
4. CTA (20-30 sec): Clear next step

**Production tips:**
- Captions by default: much feed video plays muted, and captions help
  comprehension either way
- Vertical for Stories/Reels, square for feed
- Native feel outperforms polished
- First 3 seconds determine if they watch

### Creative Testing Hierarchy
1. Concept/angle (biggest impact)
2. Hook/headline
3. Visual style
4. Body copy
5. CTA

---

## Campaign Optimization

Read [optimization and retargeting](references/optimization-and-retargeting.md) before proposing budget, bid, audience or retargeting changes. It contains the existing metric, bid progression and funnel-window rules.

## Landing Page Alignment (the headline-mirror trick)

The ad platform tests headlines against far more people than ever reach the landing page, so it resolves a winning headline much faster than on-page testing does. Use it that way:

1. Run **20-40 different headlines** as ad variations
2. Pick the winner by CTR **and** downstream conversion, not CTR alone
3. **Mirror the winning headline verbatim** in the landing page H1, sub-headline, and lead-in copy
4. Measure the landing-page conversion rate before and after with `suede-ab-testing`; message match usually helps, but the size of the lift is the account's to prove

Keep at least 3 split tests running somewhere in the funnel (creative, page, offer, or post-conversion flow) at any given time.

Post-click page work itself belongs to `suede-site-alchemy`.

---

## Reporting & Analysis

### Weekly Review
- Spend vs. budget pacing
- CPA/ROAS vs. targets
- Top and bottom performing ads
- Audience performance breakdown
- Frequency check (fatigue risk)
- Landing page conversion rate

### Attribution Considerations
- Every platform counts the same sale; never sum platform-reported conversions
- Use UTM parameters consistently and reconcile against the CRM or backend
- Record each platform's attribution window with the number (Meta's API now
  offers only 1-day view and click windows up to 28 days)
- Judge on blended CAC and pipeline, not platform CPA alone; route model and
  reconciliation work to `suede-attribution`

### Scaling discipline (net cash > ROAS percentage)

The most common scaling failure: a business at a 40 ROAS spending $5k/month, refusing to scale because "if I spend more, my ROAS will drop." This is the wrong frame.

**Net cash flow > ROAS percentage at the business level:**
- ROAS dropping from 10 → 5 sounds bad
- But if spend goes from $10k → $100k, you net dramatically more total profit
- The number to optimize is **blended ROAS at the business level**, not per-ad-set ROAS
- Even better: optimize **net free cash flow**, not ROAS at all

**Find your break-even ROAS:**
1. Calculate the absolute maximum you can pay to acquire a customer and still be profitable (factoring LTV)
2. That's your break-even ROAS / CPA ceiling
3. **Scale until you approach that ceiling**, not until your ad-account ROAS drops below an arbitrary preference

**The monthly owner review:**
- Block about 3 hours a month for the budget owner to read the raw numbers
  directly, not a summary from the analyst or media buyer
- First-hand familiarity with the data is what makes fast scale decisions safe

**Outbound-call your leads who didn't convert:**
- Every lead that downloaded a lead magnet or hit your funnel but didn't buy gets a call
- Ask why they didn't book, what was confusing, what the actual blocker was
- These verbatim answers become objection-handling ads (see Retargeting section)
- Massive insight-to-creative loop that most advertisers skip

---

## Platform Setup

Before launching campaigns, ensure proper tracking and account setup.

**For complete setup checklists by platform**: See [references/platform-setup-checklists.md](references/platform-setup-checklists.md)

**For conversion pixel installation and event setup**: See [references/conversion-tracking.md](references/conversion-tracking.md)

### Universal Pre-Launch Checklist

Each box names the artifact that proves it. A box is checked when the artifact exists, not when it sounds true.

- [ ] Conversion tracking fired: the test conversion is visible in the platform's event manager with a timestamp
- [ ] Landing page loads in <3 sec: cite the PageSpeed / Lighthouse number and the test date
- [ ] Landing page mobile-friendly: a mobile render of the page, not a desktop assumption
- [ ] UTM parameters working: paste the resolved destination URL with parameters intact
- [ ] Budget set correctly: the daily/lifetime figure, against the cap the user stated
- [ ] Targeting matches intended audience: the saved audience definition, read back

Any unchecked box means do not recommend launch. Name the box and what is missing.

---

## Google RSA Output Spec (mandatory when generating RSAs)

When the user requests Google Ads RSAs, load [references/rsa-output-spec.md](references/rsa-output-spec.md) and follow it exactly: hard character limits, required sidecar artifacts (ad groups, negatives, sitelinks, callouts), output order, template shape, CFM medical compliance, and the pre-send self-check. Do not output any RSA that violates it.

---

## Common Mistakes to Avoid

- **Too many campaigns**: fragmenting budget across campaigns none of which exit learning
- **Optimizing for the wrong metric**: clicks or CTR when the objective is conversions
- **Only one ad per ad set**: the algorithm has nothing to allocate between
- **Overlapping audiences competing**: the same account bidding against itself

---

## Tool Integrations

This pack does not include ad-network integrations. Work through an authorized
platform UI, current export, API, or installed connector; verify current
official documentation and the selected account before any mutation.

| Platform family | Typical use | Verify before execution |
|-----------------|-------------|-------------------------|
| Search ads | Capture declared intent | Query scope, match behavior, negatives, location, conversion action |
| Social feed ads | Create or harvest demand | Audience controls, placement, creative specs, attribution window |
| Professional-network ads | Reach role or account segments | Targeting availability, minimum audience, lead form and CRM mapping |
| Short-video ads | Visual discovery and creator-style demand | Placement specs, audio rights, age and regional policy |

For the measurement contract, use
[references/conversion-tracking.md](references/conversion-tracking.md) and
route implementation and firing checks to `suede-analytics`.

---

## Boundaries

- Do not create, launch, pause, delete, or change campaigns, bids, audiences, or budgets without explicit authorization.
- Do not claim ROAS, attribution, or incrementality when conversion tracking and revenue inputs have not been verified.
- Do not recommend spend above the stated cap; if no cap exists, provide a bounded test budget and wait for approval.
- Do not target sensitive traits, evade platform policy, or present inferred audience attributes as verified facts.

**When authorization is missing.** If an authorized account or connector is present and the user asks for a mutation you have no approval for, stop before the call. Name the exact mutation and the account, campaign, or ad set it would hit. Offer: a draft-only change list they can apply themselves, a request for written approval on that specific change, or continuing read-only with an audit instead. Then wait, do not execute on assumed consent. (For the spend-cap case, the standing rule in the third boundary above already applies; don't restate it.)

## Routing

- Need ad copy or visual variants -> use `suede-ad-creative`.
- Need conversion tracking implementation -> use `suede-analytics`; attribution
  models and cross-platform reconciliation -> use `suede-attribution`.
- Need post-click conversion work -> use `suede-site-alchemy`.
- Need CRM handoff or offline conversion design -> use `suede-revops`.
- From those skills, route paid channel, budget, bid, and campaign decisions back to `suede-ads`.
