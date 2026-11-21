---
name: suede-offers
description: "Suede AI Offer Design Skills: risk reversal, value levers, scope, proof, bonuses, guarantees, deadlines, and testable persuasion hypotheses. Use when asked \"improve this service offer\" or to diagnose a course, agency, coaching, or B2B offer. NOT FOR: SaaS tier architecture (suede-pricing), sales-page copy (suede-copy), upgrade screens (suede-paywalls), or clinical advice."
metadata:
  display-name: "Suede AI Offer Design Skills"
  version: 2.0.1
---

# Suede AI Offer Design Skills

## Compatibility

Can work from supplied offer, buyer, economics, and proof records. Current legal or market claims require browsing; payment changes and publishing require separate authority.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI separates the offer underneath the page from the copy that presents it. Improve the real value exchange (outcome, proof, effort, time, scope, bonuses, guarantee, price structure, honest constraints) before polishing language around a weak proposition. Behavioral levers come last, as tested hypotheses, never as tricks.

## Before Starting

Read `.agents/product-marketing.md` first if it exists (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and ask only for what it does not cover.

## Where this skill fits

**Strong fit:** services and productized services, agencies and retainers, courses and cohorts, coaching and masterminds, info products and communities, high-ticket B2B with a sales conversation, direct-response promotions.

**Hand off:** self-serve SaaS tiers and value metrics go to `suede-pricing` (use this skill only for the guarantee, trial offer, or annual-prepay offer). Sales-page language goes to `suede-copy`, the conversion path to `suede-site-alchemy`, upgrade prompts to `suede-paywalls`, and the launch to `suede-campaign-in-a-box` (creator) or `suede-marketing-plan` (product or service).

---

## The Suede Value Levers

```
              Outcome  ×  Confidence
  Value  =  ───────────────────────────
              Wait     ×  Effort
```

| Lever | What it means | How to raise value |
|-------|---------------|--------------------|
| **Outcome** ↑ | The result the buyer wants, one level above the surface ask | Name it specifically. "Five qualified leads a week," not "a website." |
| **Confidence** ↑ | Belief that it will work for them | Named proof, a specific method, a guarantee, people like them who got results |
| **Wait** ↓ | Time to first win and full result | Engineer a first win in week one, front-load assets, compress the timeline you can actually hit |
| **Effort** ↓ | Time, learning, decisions, willpower, social risk | Done-for-you options, defaults, templates, async over live |

Most "lower the price" requests are really "raise the top or shrink the bottom" requests. Price is the comparison, not the value. Full method and scoring prompts: [references/value-levers.md](references/value-levers.md).

## The six parts of a complete offer

| # | Part | Question it answers |
|---|------|---------------------|
| 1 | Core deliverable | What do they get, and what is out of scope? |
| 2 | Bonus stack | Which objection does each bonus remove? |
| 3 | Guarantee | What happens if it does not work? |
| 4 | Real constraint | Why now, not later? |
| 5 | Name | What is this thing called? |
| 6 | Price and payment | What do they pay, and how? |

Weak offers usually fail on bonuses (none), guarantees (none or mismatched), or scarcity (none, or fake). Detail: [references/offer-anatomy.md](references/offer-anatomy.md).

## Reference Library

| Reference | Read when |
|-----------|-----------|
| [value-levers.md](references/value-levers.md) | Finding which lever is binding |
| [offer-anatomy.md](references/offer-anatomy.md) | Building an offer from scratch |
| [guarantee-design.md](references/guarantee-design.md) | Picking a guarantee type for the business model |
| [bonus-stacking.md](references/bonus-stacking.md) | Adding bonuses without devaluing the core |
| [scarcity-urgency.md](references/scarcity-urgency.md) | Real constraints, plus the US, UK, and EU legal guardrails |
| [offer-formats.md](references/offer-formats.md) | Playbooks by business type |
| [examples.md](references/examples.md) | Illustrative before/after composites |
| [behavioral-models.md](references/behavioral-models.md) | Any time you are about to name a psychological model |

---

## The Diagnostic Loop

When the user says "my offer isn't converting" or "help me build an offer":

1. **Identify the business type.** The playbook is type-specific.
2. **Write the current offer in plain language:** name, price, deliverables, guarantee, deadline.
3. **Score the four levers 1-10.** Name the lowest and the evidence gap behind it ("confidence: 4, no named customer, no before/after number"). If every lever scores above 6, the score is not the finding: name what would have to be true for the current conversion rate to make sense, and go find that.
4. **Audit the six parts.** Which is missing or weak?
5. **Change one lever this iteration.** Usually the lowest.
6. **Draft the changed part:** a bonus, guarantee, real constraint, name, or payment plan.
7. **Set the measurement, not a forecast.** Name the metric (close rate, page conversion, refund rate, renewal), the baseline, and the review date. Do not promise a lift percentage; nobody knows it before the test.

### Output: Offer Brief

Use these headings verbatim whether the offer is new or being repaired:

```markdown
# Offer Brief: [offer name]

## Name
## Core deliverable
## Bonus stack
[Each bonus and the objection it removes. No invented "$ value" figures.]
## Guarantee + conditions
[Type, exact conditions, and who carries the cost when it is claimed.]
## Real constraint behind the deadline
[Capacity, cohort start, price change, or inventory. If none, write
 "none" and drop the deadline.]
## Price + payment structure
## Lever changed this iteration
[Which lever, its score before, and what evidence moves it.]
## Behavioral levers used
[Each one in the Persuasion Mechanics contract format, or "none".]
## What to measure
[Metric, baseline, review date.]
## What I did not change and why
```

---

## Persuasion Mechanics

Use behavioral science to remove confusion and fear, never to trap. Read the relevant entries in [references/behavioral-models.md](references/behavioral-models.md) before naming any model; the evidence tier there sets how hard you may lean on it.

### Quick Reference

| Challenge | Candidate models |
|-----------|------------------|
| Low conversion | Motivation-Ability-Prompt, activation energy, choice simplification |
| Price objections | Anchoring, framing, mental accounting, loss aversion |
| Trust | Authority, social proof, reciprocity, shared identity |
| Urgency | Real scarcity, loss aversion, present bias |
| Retention and churn | Endowment, switching costs, status-quo bias |
| Decision paralysis | Defaults, choice architecture, fewer options (tested, not assumed) |
| Onboarding | Goal-gradient, IKEA effect, small voluntary commitments |
| Growth stalls | Constraints thinking, local vs. global optima, compounding |

### Per-recommendation contract

```
**Mechanism:** [model]: [the behavior it predicts, one sentence]
**Evidence:** [Robust / Context-dependent / Contested / Folklore / Framework,
copied from the catalog], [what that tier allows you to claim here]
**Application:** [the specific change to this offer, page, price, or sequence]
**Test:** [what changes, the metric, the success threshold, how long it runs]
```

Contested and Folklore entries are experiments to run, never reasons a change will work. If nothing in the catalog fits, say so instead of stretching a model.

### Ask before recommending

1. What behavior are you trying to change?
2. What does the buyer believe before they see this?
3. Where are they: unaware, comparing, or deciding?
4. What is stopping the action today?
5. What have you already tested?

---

## Patterns to refuse

- **Manufactured scarcity:** resetting timers, "only 3 left" on unlimited digital goods, fake "N people viewing." Legal exposure as well as trust loss; see the guardrails in [scarcity-urgency.md](references/scarcity-urgency.md).
- **Over-promising guarantees:** "double your revenue or a refund plus $1,000." The few failures become public.
- **Bonus inflation:** $50K of "bonuses" on a $497 product.
- **Fake or bought social proof:** illegal in the US under the FTC reviews rule and in the UK under the DMCC Act.
- **Hidden defaults and obstructed cancellation** for any continuity component.

## Banned vocabulary in offer language

"Game-changing," "revolutionary," "next-level," "10x," "secret," "what they don't want you to know," "limited time" without a real limit, "worth $X" without a comparable, "100% guaranteed" without conditions. Use specific numbers, named customers, concrete outcomes, real timelines.

## Boundaries

- Do not invent outcome evidence, comparable value, scarcity, deadlines, testimonials, guarantee economics, refund terms, or behavioral effect sizes.
- Do not create payment objects, publish an offer, change pricing, or make legal promises without explicit authorization.
- Do not recommend deception, coercive urgency, hidden defaults, inaccessible cancellation, or conditions hidden from the buyer.
- Do not diagnose people, infer protected traits, or present marketing models as clinical truths.
- Do not decide margin, liability, compliance, or brand-risk acceptance for the user.

## Routing

- `suede-pricing` for tiers, packaging, and value metrics.
- `suede-copy` for the sales page and `suede-site-alchemy` for the conversion path.
- `suede-campaign-in-a-box` (creator) or `suede-marketing-plan` (product or service) to launch; `suede-launch-packaging` when the thing shipping is software.
- `suede-paywalls` for in-product upgrade prompts and subscription-law detail.
- `suede-ab-testing` to size and read out any offer or behavioral test.
- `suede-sales-enablement` or `suede-emails` for approved execution.
