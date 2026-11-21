---
name: suede-pricing
description: "Suede AI Pricing Skills: value metric selection, tiers, willingness-to-pay research, AI unit economics, migration, and pricing-page clarity. Use when asked \"restructure our pricing tiers\" or to decide prices, raise them, or diagnose buyer confusion. NOT FOR: in-product prompts (suede-paywalls), offer bonuses and guarantees (suede-offers), or executing billing changes."
metadata:
  display-name: "Suede AI Pricing Skills"
  version: 2.1.0
---

# Suede AI Pricing Skills

## Compatibility

Works with supplied product economics, customer evidence, and current pricing. Competitor and regulatory facts require current sources. Produces a decision brief or teardown; billing writes require separate authorization.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI Pricing turns verified product economics, buyer evidence, and commercial
constraints into testable prices, value metrics, tiers, and migration plans.
It produces a decision brief and measurement plan while keeping billing changes
behind explicit approval.

## Before Starting

**Check for product marketing context first:**
If `.agents/product-marketing.md` exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md` filename, in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Gather this context (ask if not provided):

### 1. Business Context
- What type of product? (SaaS, marketplace, e-commerce, service)
- What's your current pricing (if any)?
- What's your target market? (SMB, mid-market, enterprise)
- What's your go-to-market motion? (self-serve, sales-led, hybrid)

### 2. Value & Competition
- What's the primary value you deliver?
- What alternatives do customers consider?
- How do competitors price?

### 3. Current Performance
- What's your current conversion rate?
- What's your ARPU and churn rate?
- Any feedback on pricing from customers/prospects?

### 4. Goals
- Optimizing for growth, revenue, or profitability?
- Moving upmarket or expanding downmarket?

---

## Pricing Fundamentals

Three axes, decided in this order: **packaging** (what's included per tier),
**pricing metric** (what you charge for), **price point** (how much).

Price sits between the next best alternative (the floor) and the customer's
perceived value (the ceiling). Cost to serve is a baseline, never the basis.

---

## Value Metrics

### What is a Value Metric?

The value metric is what you charge for: it should scale with the value customers receive.

**Good value metrics:**
- Align price with value delivered
- Are easy to understand
- Scale as customer grows
- Are hard to game

### Common Value Metrics

| Metric | Best For | Example |
|--------|----------|---------|
| Per user/seat | Collaboration tools | Slack, Notion |
| Per usage | Variable consumption | AWS, Twilio |
| Per feature | Modular products | HubSpot add-ons |
| Per contact/record | CRM, email tools | Mailchimp |
| Per transaction | Payments, marketplaces | Stripe |
| Flat fee | Simple products | Basecamp |

### Choosing Your Value Metric

Ask: "As a customer uses more of [metric], do they get more value?"
- If yes → good value metric
- If no → price doesn't align with value

### Pricing AI features

When a feature's cost to serve scales with model usage, flat per-seat pricing can turn heavy users unprofitable. Common structures:
- **Hybrid:** a seat or platform fee with included usage, plus credits or overage beyond it.
- **Credits:** one currency across AI actions, priced so the most expensive action still clears margin. Publish what a credit buys in plain words.
- **Outcome-based:** charge per resolved ticket, qualified lead, or completed task, when the outcome is countable and attributable.

For each, model margin at the 90th-percentile user, state included limits on the pricing page, and give buyers a usage view before the bill surprises them.

### Defaults to Beat

These are the answers a model reaches for unprompted. Each is allowed, but only
once you state why it beats the alternative for this product: never by default:
**$9/$29/$99** (or any flat 3x ladder); **Starter/Pro/Enterprise** names that
carry no product meaning; **exactly three tiers** when the buyer set is two or
four; **20% off annual** as the reflex discount; **"Contact us"** on the top
tier, which hides price from buyers and from the agents that now shortlist tools
(see Pricing Page Teardown); **per-seat** when usage, records, or transactions
track value better.

---

## Tier Structure Overview

### Good-Better-Best Framework

**Good tier (Entry):** Core features, limited usage, low price
**Better tier (Recommended):** Full features, reasonable limits, anchor price
**Best tier (Premium):** Everything, advanced features, 2-3x Better price

### Tier Differentiation

- **Feature gating**: Basic vs. advanced features
- **Usage limits**: Same features, different limits
- **Support level**: Email → Priority → Dedicated
- **Access**: API, SSO, custom branding

**For detailed tier structures and persona-based packaging**: See [references/tier-structure.md](references/tier-structure.md)

---

## Pricing Research

### Van Westendorp Method

Four questions that identify acceptable price range:
1. Too expensive (wouldn't consider)
2. Too cheap (question quality)
3. Expensive but might consider
4. A bargain

Analyze intersections to find optimal pricing zone.

### MaxDiff Analysis

Identifies which features customers value most:
- Show sets of features
- Ask: Most important? Least important?
- Results inform tier packaging

**For detailed research methods**: See [references/research-methods.md](references/research-methods.md)

---

## When to Raise Prices

### Signs It's Time

**Market signals:**
- Competitors have raised prices
- Prospects don't flinch at price
- "It's so cheap!" feedback

**Business signals:**
- Conversion well above your own trailing baseline with no price objections in sales notes
- Churn low and stable, with price rarely named as a cancel reason
- Strong unit economics (payback and gross margin, from your own data)

**Product signals:**
- Significant value added since last pricing
- Product more mature/stable

### Price Increase Strategies

1. **Grandfather existing**: New price for new customers only
2. **Delayed increase**: Announce 3-6 months out
3. **Tied to value**: Raise price but add features
4. **Plan restructure**: Change plans entirely

**Legal notice floor for existing subscribers:** an increase on an auto-renewing plan needs clear advance notice with cancellation instructions. California's amended Automatic Renewal Law (in force July 1, 2025) requires that notice 7 to 30 days before the new price applies; contracts and other jurisdictions may require more. Current rules live in `suede-paywalls`.

---

## Pricing Page Best Practices

### Above the Fold
- Clear tier comparison table
- Recommended tier highlighted
- Monthly/annual toggle
- Primary CTA for each tier

### Common Elements
- An on-page FAQ that answers cost, limits, trials, and cancellation in plain text (buyers and AI assistants both read it)
- The annual saving stated in dollars and percent, whatever discount you chose
- A guarantee or trial terms near the CTA
- Renewal terms beside any auto-renewing plan: price, billing interval, and how to cancel

### Price transparency rules
- Show the total mandatory price. In the UK, the DMCC Act has banned drip pricing of mandatory fees since April 6, 2025 ([CMA207 guidance](https://www.gov.uk/government/publications/unfair-commercial-practices-cma207)).
- Auto-renewing plans need clear disclosure and consent before billing under US ROSCA and state auto-renewal laws; `suede-paywalls` holds the current US, UK, and EU subscription rules.

### Pricing Psychology
Treat each as a test, using the evidence tiers in the `suede-offers` behavioral-models catalog:
- **Anchoring (Robust):** show the higher-priced option or the cost of the alternative first, honestly.
- **Good-better-best relativity (Context-dependent):** design the middle tier as the target and check real tier-selection data.
- **Decoy tier (Contested):** a third tier can clarify the comparison; do not count on it to move choice.
- **Charm vs. round endings (Context-dependent):** weak for B2B subscriptions; test rather than assume.

---

## Pricing Page Teardown

When someone wants to audit an existing pricing *page* for **clarity, transparency, and AI-readability** (not the pricing strategy itself, and not conversion-rate optimization, that's `suede-site-alchemy`), run a **teardown** that scores it across two axes and returns prioritized fixes:

- **Human buyer experience**: value-prop clarity, plan differentiation, cognitive load, trust signals, pricing psychology, and price transparency.
- **AI-agent readiness**, whether the LLMs and agents that increasingly shortlist and compare tools can actually read and quote your pricing: machine-readable prices (not locked in an image or behind "Contact us"), extractable FAQ/objection coverage, per-tier depth stated in text, and structured data. Buyers now ask ChatGPT/Perplexity/Claude "what's the best X and what does it cost?" *before* visiting, a pricing page an agent can't parse loses deals you never see.

**Fast check, the "paste test":** give the pricing URL to a browsing-capable AI (Perplexity, ChatGPT with search, Claude with web), or paste the rendered page text, and ask "what are the plans and prices?" A clean miss means agents fetching your page will struggle too (a heuristic, not proof every agent fails).

The AI-readiness fixes are usually high-impact, low-effort (put prices in text, add JSON-LD that matches them). Hand implementation to **suede-seo-audit** (structured data and supported-schema checks), **suede-ai-seo** (extractability and AI-bot access), and **suede-competitors** for "vs" and alternatives pages that cite the same prices.

**For the full 10-dimension rubric, scoring, structured-data facts, and report template:** See [references/pricing-page-teardown.md](references/pricing-page-teardown.md).

---

## Output: Pricing Decision Brief

Every pricing or packaging engagement that is not a teardown returns this exact
structure. Use these headings verbatim; leave a heading in with "not decided,
[what's missing]" rather than dropping it.

```markdown
# Pricing Decision Brief: [product]

## Value metric
[What you charge for, and the one sentence proving usage of it tracks value.]

## Tier map
| Tier | Who it's for | Included | Limits | Price |
|------|--------------|----------|--------|-------|

## Price points + rationale
[Each number, and what it is anchored to: alternative, perceived value, or research.]

## Assumptions
[Every number taken on faith, flagged as assumption not measurement.]

## Validation plan
[What test or research confirms each assumption, and the metric that reads out.]

## Migration + grandfathering
[Existing customers: who moves, when, on what notice, and who is held.]

## What I did NOT decide
[Anything left to the user: committed price, published copy, billing changes.]
```

---

## Boundaries

- Do not create or change billing products, prices, subscriptions, or customer
  migrations without verified live state, a maximum-cost check, and explicit
  approval.
- Do not present willingness-to-pay, conversion, churn, or revenue impact as
  measured unless current research or product data supports it.
- Do not publish pricing copy, choose grandfathering policy, or commit the
  business to a price; return a recommendation, assumptions, and validation
  plan for the user to decide.

## Routing

- Use `suede-paywalls` for in-product upgrade and paywall experiences.
- Use `suede-offers` for bonuses, guarantees, and offer framing.
- Use `suede-ab-testing` to validate pricing-page or packaging hypotheses.
- Use `suede-revops` for approved deal-desk and pipeline implementation.
