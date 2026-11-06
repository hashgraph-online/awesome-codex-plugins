---
name: suede-directory-submissions
description: "Use when asked \"plan our directory submissions\" or to select and sequence startup, SaaS, AI, MCP, marketplace or review listings. Suede AI adapts truthful positioning, maintains entity consistency and tracks submission evidence and verified backlinks. NOT FOR: release packaging (use suede-launch-packaging), scaled destination pages (use suede-programmatic-seo), or AI visibility audits (use suede-ai-seo)."
metadata:
  display-name: "Suede AI Directory Submissions Skills"
  version: 2.0.1
---

# Suede AI Directory Submissions Skills

Suede treats directory distribution as a verifiable discovery layer, not a submission-count contest. Build the user's backlink and buyer-discovery foundation by selecting the right directories, sequencing them around real launch moments, adapting truthful positioning, and checking that each listing and backlink actually landed.

**Iron Law, approval is per destination:**

```
No external submission, account creation, paid placement, or review request
happens without explicit approval for that exact destination, copy, assets,
timing, and maximum cost. Approval for research or for another destination
never transfers. Any delta is re-approved before it ships.
```

## Compatibility

An agent with web access for directory research and a local tracker. Each actual submission needs separately authorized destination access; a plan requires no new account or paid placement.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

---

## Core Philosophy

Directory submissions can add discovery surfaces, referral paths, and backlinks, but
their value varies by product, directory, listing quality, and current platform
rules. Treat each benefit as a hypothesis to verify with listing status, referral
analytics, search data, and qualified outcomes. A directory plan complements
destination pages and other distribution; it does not guarantee authority,
citation, traffic, ranking, or leads.

The full directory catalog lives in `references/directory-list.md`. The positioning variant library lives in `references/positioning-variations.md`. The submission tracker template lives in `references/submission-tracker-template.csv`.

---

## Three Operating Rules

### Rule 1: Foundation before submission
Before recommending a submission, verify the directory's current official
requirements and record the source URL and check date. The linked page should be
publicly reachable, truthful, useful to the directory's audience, and measurable.
Prepare only the assets the current form requires, using real product screenshots
and approved brand files. Add pricing, legal pages, video, schema, or additional
formats when the product, jurisdiction, or verified directory rules call for them;
do not invent universal prerequisites.

### Rule 2: Destination pages before directories
Choose the most relevant verified destination for each audience: a homepage,
use-case page, integration page, comparison page, template, or documentation page.
It must accurately fulfill the listing promise and have a measurable next step.
Do not impose a fixed page count or block a suitable listing merely because an
unrelated content type does not exist.

### Rule 3: Positioning varies by directory type
Adapt the description to the directory's verified fields, audience, and rules.
Reuse approved facts, but change emphasis when that improves relevance; do not
claim that duplicate descriptions trigger a search or AI penalty without current
evidence. See `references/positioning-variations.md` for templates.

| Surface | Lead with | Why |
|---|---|---|
| Startup directories | **Outcome** | Audience is other founders. They care what it does. |
| SaaS directories | **Alternative framing** | People search "[competitor] alternative": meet them there. |
| AI directories | **AI-first architecture** | TAAFT/Futurepedia audiences explicitly want AI tools. |
| Agent/MCP directories | **Agent/MCP angle** | Use only for a live compatible capability. |
| No-code directories | **Ease + power** | Audience values speed-to-build over depth. |
| Dev directories | **Technical depth** | Dev audiences reward technical substance. |
| B2B review sites | **ROI + use case** | Buyers want outcomes and case studies. |

---

## Workflow

### Step 1: Readiness assessment (Phase 0)

Assess the selected directory against current requirements:

1. Is the product publicly accessible (no password wall)?
2. Is there a pricing page (even "free while in beta")?
3. Are privacy policy + terms live?
4. Are the required approved logo, screenshot, and video assets available?
5. Does the destination page match the proposed listing copy and CTA?
6. Is referral and conversion measurement configured?
7. Does the current directory policy allow this product, claim set, and category?
8. For review sites, are there genuine eligible users and a policy-compliant ask?
9. Who has authority to create the account, accept terms, and submit?

A missing current platform requirement, truthful destination, or submission
authority is a hard block for that directory. At the block: stop work on that
directory, name the blocker in one line ("<directory>: missing <requirement>"),
list the resolution options (obtain the requirement, substitute a truthful
destination, get explicit submission authority, or drop the directory from the
tier), and wait for the user's pick before submitting there. Other gaps are
prioritization inputs, not universal launch blockers.

### Step 2: Choose the tiers

Full catalog in `references/directory-list.md`. Summary:

| Tier | When | Illustrative candidates to verify |
|---|---|---|
| **Flagship launch** | Around a relevant launch | Product Hunt, BetaList, HN Show HN, Fazier, DevHunt |
| **Startup/SaaS** | Launch and rolling | AlternativeTo, SaaSHub, G2, Capterra, F6S |
| **AI directories** | If the product has a substantiated AI capability | TAAFT, Futurepedia, Toolify, Future Tools |
| **Agent/MCP registries** | If a live compatible integration exists | Glama, APITracker, LF MCP Registry |
| **No-code directories** | If the product genuinely serves that audience | NoCodeFinder, No Code MBA |
| **Integration marketplaces** | When the integration ships | The integration owner's official marketplace |
| **Profiles and vertical directories** | When audience and category fit | Relevant company profiles or industry-specific catalogs |

**Triage rule:** Only submit where the product is a genuine fit under the
platform's current eligibility and category rules.

### Step 3: Prepare asset variations

For each tier, prep distinct variants from
`references/positioning-variations.md` only after inspecting the destination's
current form:
- **Tagline** sized to the verified field limit
- **Short description** sized to the verified field limit
- **Long description** sized to the verified field limit
- **Category tags** limited to the verified taxonomy and product fit
- **Logo** assets
- **Screenshots** + demo video URL
- **Founder story** (2–3 sentences)

Keep facts consistent and approved. Adapt length and emphasis to each verified
form without inventing features, customers, outcomes, or platform support.

### Step 4: Batch submit

Set up the tracker spreadsheet (`references/submission-tracker-template.csv`).
Work in evidence-backed approval batches of **3–5 directories**. At the cap,
submit, verify, and report that batch's results before opening the next one.
Every submission is gated by the Iron Law: show the exact public copy, assets,
account, destination, timing, and maximum cost first.

Per submission:
1. Verify the current form, rules, price, and account identity.
2. Prepare the exact field values and assets as a reviewable draft.
3. Obtain explicit approval for that destination (Iron Law).
4. Fill and upload only the approved values.
5. Pause before any changed price, upsell, or materially different rendered
   preview; re-approve the delta.
6. Submit once, then capture confirmation.
7. Log: date, URL, status, moderator notes.
8. Once live, fetch the canonical listing URL, locate the anchor pointing at the
   destination in the rendered HTML, and record its `rel` value, redirect
   behavior, resolved destination, and the check date in the tracker. Absence of
   `rel` in response headers does not prove link attributes: inspect the
   rendered page, and log the method used.

**Reporting rule:** a listing is reported **live** only when the tracker's Live
URL, Rendered Link Attributes, and Destination Verified cells are all filled
with a check date. Anything else is reported as **submitted, unverified**.

---

## Flagship Launch Listing

For any time-sensitive launch surface, research the platform before building the
plan. Use its current official help, submission form, and community rules; record
the URLs and check date. Do not present remembered algorithm behavior, ideal
launch times, asset dimensions, hunter effects, or engagement thresholds as facts.

### Preparation milestones

- Confirm eligibility, account standing, moderation rules, scheduling options,
  required assets, and prohibited promotion.
- Draft truthful positioning, an approved maker story, real product visuals, and
  a working destination CTA in the exact current form limits.
- Preview the listing and test the product, signup, analytics, and support path.
- Build a communication plan from channels the user owns or is authorized to use.
- Assign a responder for genuine questions and feedback.

### Launch and follow-through

- Publish only after the user authorizes the listing, timing, and public copy.
- Follow current solicitation and outreach policies. Do not manipulate voting,
  fabricate engagement, or message people without a legitimate relationship and
  authorization.
- Respond helpfully, log referrals and qualified outcomes, and capture lessons.
- Share a recap only where current community rules permit it.

---

## Reviews Playbook

Review directories can help buyers evaluate products, but eligibility, incentive,
moderation, badge, report, and paid-plan rules change. Before recommending a
campaign:

1. Read the current official review and incentive policy for the chosen platform.
2. Record the source URL, check date, eligibility rules, deadlines, and maximum
   verified cost.
3. Identify real users with firsthand product experience; never manufacture,
   gate, pre-score, or script reviews.
4. Get explicit authorization for the recipient list, wording, channel, cadence,
   and any incentive before outreach.
5. Track requests, completed reviews, moderation status, referral outcomes, and
   complaints. Set targets from the actual eligible pool and user goals.

Do not claim a badge threshold, report cutoff, ownership relationship, incentive
permission, plan price, or expected response rate unless it was verified from a
current authoritative source. A small customer base is a planning constraint, not
automatic proof that a listing is worthless.

---

## Destination Pages Strategy (What the Backlinks Point At)

Match each listing to the most useful truthful page available. A homepage can be
appropriate when it satisfies the audience and promise; a specialized page may be
better when evidence supports it.

| Page type | Build it when |
|---|---|
| Alternatives page (`/alternatives/[competitor]`) | Current customer or search evidence shows comparison intent |
| Use-case / ICP page (`/for/[audience]`, `/use-cases/[use-case]`) | Demand and product evidence justify a dedicated page |
| Template or asset gallery (`/templates/[slug]`) | Templates carry standalone value and activation is measurable |
| Self-authored category roundup | The team can research the category and disclose its methodology |
| Integration page | The integration is live and the page explains setup, capabilities, and limits |

On any comparison or roundup page: verify material competitor claims, state
clearly when each option fits, date the comparison, and correct it when the facts
change. Set output volume from quality capacity and measured demand, not a
borrowed traffic or revenue story, and do not promise ranking or AI citation.

Page production at scale belongs to `suede-programmatic-seo`; comparison-page
strategy belongs to `suede-competitors`.

---

## Directories as AEO/GEO inputs

Answer engines recommend brands that the wider web corroborates, and they
often cite review sites, marketplaces, and category directories when they
build a shortlist. A directory plan is part of the off-site consensus layer
in `suede-ai-seo`. Two rules stay this skill's own:

1. **Entity consistency.** Every listing uses the canonical entity sheet from
   `suede-ai-seo` (`references/entity-graph.md`): exact brand name, one-line
   description, founder names, logo, category, and URL. A listing that
   disagrees with the site is a finding, and fixing old listings often matters
   more than adding new ones. Add each verified listing URL to the brand's
   `sameAs` set only when the profile is controlled by the brand.
2. **Genuine discussion only.** Earn reviews and community mentions; never
   seed, script, or fabricate them.

Which directories engines cite for your category is observable: when
`suede-ai-seo` runs its prompt panel, the source gap list (domains cited for
competitors but not for you) is a prioritized directory and review-site queue.
Use it to rank tiers instead of guessing.

### Measurement

Record engine, account context, prompt, locale, date, result, and whether the
result reproduced. Verify any tracking product and its cost before
recommending it.

---

## Community & Ongoing Distribution

Most directory submissions are episodic; community participation is ongoing.
Measure each as a separate source before combining funnel conclusions.

Cross-posts and community links are still backlinks: publish only where the
community's current rules permit it, use a canonical URL where the platform
supports one, and verify the rendered link with the same Step 4.8 check applied
to directory listings.

Channel selection, cadence, and post formats belong to
`suede-community-marketing`, `suede-social`, and `suede-content-strategy`.

---

## KPIs & Tracking

Set baselines and goals from the user's current analytics, eligible audience,
capacity, and launch objective. Do not use generic day-based forecasts.

| Metric | Baseline | User-approved goal | Source and check date |
|---|---:|---:|---|
| Listings submitted and live | | | |
| Verified referring links | | | |
| Directory referral sessions | | | |
| Qualified conversions by listing | | | |
| Review requests and published reviews | | | |
| Listings matching the canonical entity sheet | | | |
| Directory domains cited in AI answers (prompt panel) | | | |
| Referring domains (Search Console Links, Bing Webmaster Tools) | | | |
| Cost and team time | | | |

---

## What NOT to Do

1. **Don't buy a mass-submission package without diligence and explicit approval.** Verify exact destinations, editorial standards, data handling, rights, maximum cost, and refund terms.
2. **Don't submit to low-quality or deceptive directories.** Evaluate audience fit, moderation, live traffic evidence, existing listings, outbound-link behavior, and reputation rather than relying on one authority score.
3. **Don't treat directories as your entire GTM.** Compare them with content, community, reviews, partnerships, and other measured channels.
4. **Don't churn listings without evidence.** Set a review cadence from product
   changes, platform notices, and observed listing issues.
5. **Don't over-index on launch-day spike.** The flywheel is templates + alternatives + reviews + ongoing content, not one day of PH.

---

## Task-Specific Questions

1. **What are you launching?** (Category changes tier mix. AI vs traditional SaaS vs no-code vs dev tool.)
2. **When is launch day?** (Work backward from verified platform requirements.)
3. **Do you have destination pages built?** (Alternatives, use cases, templates: if not, build first.)
4. **Which flagship surface is being considered, and what do its current rules require?**
5. **How many eligible users could receive a policy-compliant review request?**
6. **Do you have a live tested MCP or agent capability?** (If yes, verify compatible registries.)
7. **Existing integrations?** (If yes, verify each owner's marketplace eligibility.)
8. **Which owned audiences can be contacted, and has the user authorized outreach?**
9. **Current DR and referring domain count?** (Baseline for measuring the compounding effect.)

---

## Output Format

When the user asks for a directory plan, return:

1. **Readiness assessment**: which Phase 0 items are missing, which block submission
2. **Tier selection**: which tiers apply, which to skip, why
3. **Submission order**: evidence-backed batches mapped to current requirements
4. **Destination page list**: what to build first if missing
5. **Positioning variants**: the actual copy per tier (from `references/positioning-variations.md`)
6. **Flagship listing timeline**: mapped from current rules to calendar dates
7. **Policy-compliant review plan**: eligible audience, authorization, copy, cadence
8. **Weekly measurement plan**: baselines and user-approved goals
9. **Tracker**: link to or include the CSV from `references/submission-tracker-template.csv`

Keep the plan actionable. Every item should be something the user can do today.

---

## Boundaries

- Do not claim a directory is dofollow, indexed, high-authority, or producing leads without a current check.
- Do not submit listings, create accounts, publish copy, buy placements, or request reviews without explicit authorization.
- Do not fabricate traffic, ranking, review, or citation outcomes; label estimates and record the evidence date.
- Do not decide positioning or public product claims when the required product context is missing.

## Routing

- Use `suede-launch-packaging` for the broader launch sequence.
- Use `suede-programmatic-seo` for destination pages, `suede-seo-audit` for technical checks on those pages, and `suede-ai-seo` for entity facts, the prompt-panel source gap list, and AI citation measurement.
- Use `suede-competitors` for comparison-page strategy and `suede-content-strategy` for editorial support.
- Use `suede-free-tools` for interactive destination assets, and `suede-community-marketing`, `suede-social`, or `suede-content-strategy` for community and social distribution.
- Use `suede-public-relations` when a flagship launch also warrants earned media.
- From those skills, route directory selection, listing positioning, and backlink verification back to `suede-directory-submissions`.

## Worked contract

[Worked contract](references/usage-contract.md) gives a bounded input, expected output and failure check for this workflow.
