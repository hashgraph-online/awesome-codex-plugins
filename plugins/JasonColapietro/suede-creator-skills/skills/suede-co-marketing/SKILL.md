---
name: suede-co-marketing
description: "Suede AI Co-Marketing Skills. Use when asked to \"find co-marketing partners\" or plan a joint campaign: evidence-backed fit, reciprocal value, format, roles, consent, shared KPIs and content. NOT FOR: affiliate/referral programs (suede-referrals), software release packaging (suede-launch-packaging), or partner-facing sales collateral (suede-sales-enablement)."
metadata:
  display-name: "Suede AI Co-Marketing Skills"
  version: 2.1.0
---

# Suede AI Co-Marketing Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from product context and partner evidence; web research or supplied sources for scoring and file tools for campaign plans. Outreach, lead sharing and publication need separate existing authority.

Use this co-marketing playbook to identify credible partners and design measurable joint campaigns with explicit roles and value exchange.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

---

## Partner Identification Framework

### 1. Audience Overlap Analysis

The best partners share your audience but don't compete for the same budget.

**Ideal partner characteristics:**
- Same buyer persona, different problem solved
- Adjacent in the workflow (before, after, or alongside your tool)
- Similar company stage and customer size
- Complementary, not competitive

**Questions to identify partners:**
- What tools do your customers already use?
- What do they use before/after your product?
- Who else is selling to your ICP?
- Which integrations do customers request most?

### 2. Partner Scoring Criteria

Rate each candidate 1-5 on all six criteria, using these anchors. Score from
evidence the user or a public source supplies; a criterion with no evidence is
scored `?` and named as an open question, never guessed.

| Criteria | 1 | 3 | 5 |
|----------|---|---|---|
| **Audience fit** | Different buyer, different problem | Same buyer, partial overlap | Same ICP, adjacent workflow step |
| **Audience size** | Reach materially below yours | Same order of magnitude | At or above your reach on the shared channel |
| **Brand alignment** | You would hedge before associating | Neutral; no known conflict | You would name them in your own marketing unprompted |
| **Engagement quality** | Reach with no observable response | Some engagement, unverified | Documented engagement on the channel the campaign will use |
| **Reciprocity potential** | Nothing of comparable value to offer | One-sided but tolerable | Both sides trade equivalent audience or asset value |
| **Ease of execution** | No partnerships contact, no prior co-marketing | Contact exists, no track record | Partnerships team plus a shipped co-marketing history |

**Pursue/drop rule:** pursue only partners scoring **4+ on both Audience fit and
Reciprocity potential**. Anything below is reported as scored-and-dropped with
the failing criterion named: it is not silently omitted.

**Shortlist cap: 5.** At the cap, rank the five and report; do not expand the
list. Additional candidates go in a named "not pursued this round" line.

### 3. Where to Find Partners

**Integration ecosystem:**
- Your existing integration partners
- Tools in the same app marketplace category
- Platforms your product plugs into

**Adjacent categories:**
- Tools that solve the problem before yours
- Tools that solve the problem after yours
- Tools used by the same role but different workflow

**Community signals:**
- Who sponsors the same podcasts/newsletters?
- Who exhibits at the same conferences?
- Who's active in the same communities?
- Whose content does your audience share?

**Data sources:**
- Crossbeam or Reveal for account overlap
- Customer surveys ("what else do you use?")
- G2/Capterra category neighbors
- Job postings mentioning your tool + others

---

## Co-Marketing Campaign Types

Four families, with per-format effort, lead sharing, and best-fit in
[references/campaign-formats.md](references/campaign-formats.md). Open that file
whenever a campaign format is being chosen: the campaign plan must name its
format from it.

- **Content partnerships**: when both sides can produce and both audiences read.
- **Webinars & events**: when the goal is gated lead generation or education.
- **Product & integration marketing**: when a live integration or shared customer exists.
- **Community & social**: when the goal is exposure or list growth, not pipeline.

---

## Make Joint Content Work in Search and AI Answers

Joint content can earn more than a shared list. Done right, it becomes the
page that ranks and gets cited for the combined use case.

- **Publish one canonical version.** Pick the host domain; the partner links
  to it (or uses a rel="canonical" copy) instead of duplicating it.
- **Target the combined query.** "[Tool A] + [Tool B] integration", "how to
  [job] with [A] and [B]": queries neither brand ranks for alone.
- **Ship original data when possible.** A joint survey or benchmark across both
  customer bases is a link asset neither could produce alone. Publish method,
  sample size, and date.
- **Both brands named consistently** in title, byline, and copy so AI answers
  attribute the claim to both.
- **Integration pages:** list the partner in each side's integration
  directory with a link, a short how-it-works, and the shared customer story.

Technical checks route to `suede-seo-audit`; topic choice to
`suede-content-strategy`.

---

## Brainstorming Partner Campaigns

When brainstorming with a specific partner, consider:

### 1. Shared Audience Moments

- What trigger events matter to both audiences?
- What seasonal moments align with both products?
- What industry trends affect both customer bases?

### 2. Combined Value Propositions

- What can customers achieve with both tools that they can't with one?
- What workflow does the combination enable?
- What pain point does the integration solve?

### 3. Unique Assets Each Brings

Inventory what each side brings across audience, content expertise, product
capabilities, brand credibility, and customer stories, and name which asset the
campaign actually depends on.

---

## Approaching Potential Partners

### Outreach gate (draft-only, hard stop)

Outreach drafts are produced; outreach is never sent. At the handover: stop, name
the four variables in one line each: recipient, channel, visible sending
identity, exact message, state that the outcome is a draft and nothing has been
sent, offer **approve / revise / drop**, and wait for the user's pick. The same
gate covers sharing any customer or overlap data with the partner.

### Cold Outreach Template

```
Subject: [Your Company] + [Their Company] co-marketing idea

Hey [Name],

I'm [Role] at [Your Company]. We [one-line description].

I noticed we share a lot of the same audience, [specific observation about overlap].

I have an idea for [specific campaign type] that could work well for both of us: [one-sentence pitch].

Would you be open to a quick call to explore?

[Your name]
```

### What to Prepare for the Call

1. **Account overlap data** (if available via Crossbeam/Reveal)
2. **2-3 specific campaign ideas** (not just "let's do something")
3. **Your audience metrics** (list size, traffic, engagement)
4. **Examples of past partnerships** (shows you can execute)
5. **Clear ask** (what you want from them, what you'll provide)

---

## Structuring the Partnership

### Key Questions to Align On

- **Lead ownership**: gated/split (one shared form, agreed split, written data
  and consent terms) or each-keeps-own (no shared list: the default until data
  terms are agreed). The format chosen from `references/campaign-formats.md`
  names which arrangement it assumes.
- **Promotion commitments**: What will each party do to promote?
- **Asset creation**: Who creates what? Who approves?
- **Timeline**: When does each phase happen?
- **Success metrics**: How will you measure success?
- **Follow-up**: Will you do more together if it works?

### Simple Co-Marketing Agreement Outline

1. **Campaign description**: What you're doing together
2. **Responsibilities**: Who does what
3. **Timeline**: Key dates and deadlines
4. **Lead handling**: How leads are captured, shared, followed up
5. **Promotion**: Minimum commitments from each side
6. **Branding**: Logo usage, approval process
7. **Costs**: Who pays for what (if any)
8. **Metrics sharing**: What data you'll share post-campaign

---

## Measuring Co-Marketing Success

- Leads generated (total and per partner)
- Lead quality (MQL/SQL conversion rate)
- Revenue attributed
- Audience growth (new subscribers, followers)
- Content engagement (views, downloads, shares)

Baselines and targets come from the user's current analytics, not from a generic
benchmark. Report only metrics both sides agreed to share.

---

## Co-Marketing Checklist

### Partner Identification
- [ ] List tools your customers already use
- [ ] Check Crossbeam/Reveal for account overlap
- [ ] Score candidates on all six criteria and apply the pursue/drop rule (cap 5)
- [ ] Research their past co-marketing activities

### Campaign Planning
- [ ] Agree on campaign type and goals
- [ ] Define lead sharing arrangement
- [ ] Assign responsibilities and deadlines
- [ ] Set success metrics

### Execution
- [ ] Create shared assets (landing page, content, etc.)
- [ ] Coordinate promotion schedules
- [ ] Brief both teams on talking points

### Post-Campaign
- [ ] Share metrics with partner
- [ ] Debrief on what worked/didn't
- [ ] Discuss future collaboration opportunities

---

## Output Format

This skill returns one of two deliverables. Copy the matching skeleton verbatim
from [references/output-templates.md](references/output-templates.md), open that
file before writing either one.

**Scored partner shortlist** must contain:

1. The ranked shortlist (max 5) with all six criterion scores per partner
2. A scored-and-dropped list naming the failing criterion for each
3. Open questions for any criterion scored `?`
4. Candidates not pursued this round
5. A recommended first move with a format named from `references/campaign-formats.md`

**Joint campaign plan** must contain:

1. Campaign format (named from the formats reference), goal, and its one proving metric
2. Value exchange on both sides
3. Responsibilities and timeline with an owner and approver per phase
4. Lead handling: gated/split or each-keeps-own, with the capture path
5. Promotion commitments, branding approvals, and maximum approved cost
6. Measurement plan with agreed shared metrics and a debrief date
7. An approval-status line stating nothing has been sent, published, or committed

---

## Task-Specific Questions

1. Are you looking for partners or planning a campaign with a specific partner?
2. What type of co-marketing are you most interested in? (content, events, integrations, community)
3. What's your audience size? (email list, social following, traffic)
4. Do you have existing integration partners?
5. Have you done co-marketing before? What worked/didn't?
6. What's your timeline and budget for co-marketing?

---

## Tool Integrations

This pack does not ship partner-platform connectors. Use an authorized product
UI, current export, API, or installed connector and verify the provider's
current official documentation before reading or changing partner data.

Select capabilities against the campaign:

- Privacy-safe aggregate account overlap, with minimum cohort thresholds
- Partner records, owners, approvals, commitments, and deal registration
- Shared asset review, version history, deadlines, and publication approval
- Source-specific links or codes and agreed lead/revenue attribution
- Export, deletion, access control, and audit-history requirements

---

## Boundaries

- Do not claim a partnership, audience overlap, endorsement, reach, or committed deliverable without evidence from both sides.
- Do not contact partners, share customer lists, sign terms, spend budget, or publish joint work without explicit authorization.
- Do not decide ownership, licensing, attribution, lead-sharing, or revenue-sharing terms for the parties.
- Do not expose private customer or partner data to prove overlap; use approved aggregate or privacy-safe methods.

## Routing

- Need referral or affiliate mechanics -> use `suede-referrals`.
- Need launch sequencing and release assets -> use `suede-launch-packaging`.
- Need co-created editorial planning -> use `suede-content-strategy`.
- Need partner-facing collateral -> use `suede-sales-enablement`.
- Need earned media for a joint launch announcement -> use `suede-public-relations`.
- From those skills, route partner selection and joint-campaign design back to `suede-co-marketing`.
