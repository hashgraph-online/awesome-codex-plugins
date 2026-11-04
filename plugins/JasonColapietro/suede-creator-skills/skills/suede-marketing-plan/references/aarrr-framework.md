# AARRR Framework: Primer for Plan Sequencing

AARRR (Dave McClure's "pirate metrics") is the spine of every plan produced by this skill. This doc is the primer + the decision rules for when each stage gets prioritized.

## The five stages

| Stage | Question | Common metrics |
|---|---|---|
| **A**cquisition | How do strangers become aware of us? | Visits, MQLs, signup-page sessions, app-store visits, CAC by channel |
| **A**ctivation | Once they try us, do they have an experience that converts? | Signup completion rate, time-to-value, % completing first key action, trial → paid rate |
| **R**etention | Do they stay and deepen? | DAU/WAU/MAU, week-1/4/12 retention, churn |
| **R**eferral | Do retained users bring more users? | Viral coefficient, NPS, ambassador attribution |
| **R**evenue | What do they pay, who pays, how does it compound? | ARPU, LTV, expansion revenue, ARR / MRR |

> **Signup boundary rule.** Signup *intent* (a stranger landing on the signup page) is Acquisition. Signup *completion* and everything after (first key action, trial-to-paid) is Activation. Apply this rule consistently across all docs and the plan template.

## Why AARRR for plan sequencing

Three reasons.

**1. Funnel-stage tagging forces prioritization.** Without AARRR, marketing plans become channel-organized ("here's the SEO plan, here's the social plan, here's the paid plan"). Channels can address multiple stages; tagging by stage instead asks the more useful question: *what stage of the funnel is the binding constraint right now?*

**2. Compare constraints before adding volume.** Reconcile qualified exposure,
activation, retention, economics, and capacity before deciding whether the next
test should repair a downstream loss or add acquisition.

**3. The Revenue / Referral conversation is honest.** Most marketing plans bury monetization under "growth" and treat referral as wishful thinking. AARRR forces explicit treatment of both.

## Brand and content: not a stage, cross-cutting

A common mistake: making "Brand" or "Content" the sixth bucket. They're not, they serve every stage.

- **Brand voice** governs every piece of copy across every stage
- **Content** feeds Acquisition (SEO, social), Activation (onboarding copy), Retention (email lifecycle), Referral (ambassador talking points), Revenue (pricing pages, sales material)

In the plan, brand/content shows up as the strategic frame (Section 2) and cross-cutting in Section 11's ops stack, never as its own AARRR section.

## Diagnosing the binding constraint: which AARRR stage is highest leverage?

Treat every proposed binding constraint as a hypothesis. Never select a stage
from company age, business model, traffic volume, or a single benchmark.

For each stage, record:

1. The dated source, cohort, metric definition, and comparison window.
2. The observed loss or opportunity and its plausible alternative explanations.
3. Unit economics, delivery capacity, dependencies, and data-quality limits.
4. The smallest test that can distinguish the leading explanations.
5. The owner, approval state, maximum exposure, review date, and stop condition.

Use these diagnostic questions:

- **Acquisition:** Is qualified exposure the constraint after downstream
  conversion, retention, attribution, and capacity are reconciled?
- **Activation:** Does a defined cohort fail to reach a verified value event,
  and does behavioral or research evidence identify the friction?
- **Retention:** Do comparable activated cohorts leave earlier or deepen less
  than the approved target, with product and measurement changes reconciled?
- **Referral:** Is there observed advocacy or sharing intent that a bounded,
  rights-compliant mechanism could capture?
- **Revenue:** Do realized price, margin, retention, packaging research, and
  willingness-to-pay evidence support a specific pricing hypothesis?

When evidence is insufficient, preserve competing hypotheses and prioritize
instrumentation or research rather than declaring a stage broken.

## Stage-by-stage strategic patterns

### Acquisition

**The diagnostic question:** Where is the gap between TAM-level awareness and current funnel volume? What channels are saturated by competitors vs. open?

**Common Acquisition moves:**
- SEO content strategy (organic compounding)
- Founder-led channels (LinkedIn, X, Substack for B2B; Instagram/TikTok for D2C)
- Paid acquisition only after audience, economics, tracking, creative capacity,
  maximum exposure, approval, review, and stop gates pass
- App Store / Play Store / marketplace listing optimization
- PR and credibility-anchor amplification
- Events (live, webinar, conference speaking)
- Partnerships (newsletter swaps, integration co-marketing, reseller / agency partners)
- Hardware / commerce surface (Shopify SEO + Amazon for hybrid businesses)
- B2B sales support (case studies, partner pages, vertical content)

**Sequencing principle:** Compare organic, paid, partner, product-led, and sales
candidates against current audience evidence, economics, tracking, creative and
owner capacity, time-to-learning, approval, maximum exposure, and stop
conditions. Organic work is not a prerequisite for paid work, and paid work is
not evidence of readiness. Choose the smallest approved test that resolves the
most important uncertainty.

### Activation

**The diagnostic question:** Which current event and research evidence define
first value for this cohort, where is the measured loss, and what competing
explanations remain?

**Common Activation moves:**
- Bedrock fixes (broken gates, broken signup steps, broken paywall)
- Onboarding test or rebuild when behavioral and research evidence isolate it
- App Store listing rewrite (the threshold to the trial)
- Lifecycle Flow ship order (when to ship onboarding emails)
- Paywall structure + trial length
- Free → paid bridge (in-app upsells, soft paywalls)

**Sequencing principle:** Reduce verified friction between entry and the
cohort's defined value event. Preserve steps required for consent, safety,
eligibility, comprehension, trust, or legal compliance.

### Retention

**The diagnostic question:** Why do users churn? What would have made them stay? What's the "second moment of value" after the first one?

**Common Retention moves:**
- Lifecycle email flows: onboarding, lapsed user re-engagement, post-purchase, win-back
- Subscription / preference centers
- Churn reconciliation (often metric definitions don't match across surfaces)
- Hardware → software activation paths (for hybrid businesses)
- Term-length or pricing-structure hypotheses (cross-cuts Revenue)
- Support as marketing (high-touch moments that drive stories)
- Community + practitioner networks

**Sequencing principle:** Rank lifecycle work from dated cohort loss, event
coverage, consent, content dependencies, owner capacity, and expected learning
value. A post-purchase, onboarding, lapsed-user, or win-back flow may come first;
its cadence follows observed behavior and an approved review rule, not a
universal ship order or quarterly calendar.

### Referral

**The diagnostic question:** Is there inbound referral interest that isn't being captured? What's the share-after-value moment that's natural to the product?

**Common Referral moves:**
- Ambassador / affiliate program (start with inbound interest, not cold recruitment)
- Share-after-value moments built into the product (reflection prompts, milestone celebrations)
- Founder amplification (founder as referrer-zero)
- Long-game expert / Guides / certified-host networks (for category-creating businesses)
- Gifting flows (consumer / hardware)
- Two-sided referrals (reward both referrer and referred)

**Sequencing question:** Inbound interest is evidence to investigate, not
authorization to launch. Verify participant fit, rights/disclosures, economics,
owner capacity, tracking, maximum exposure, approval, and stop conditions before
running a bounded pilot.

### Revenue

**The diagnostic question:** Is the company underpricing? Underpackaging? Missing an upsell? What's the "right" price discipline given LTV and brand voice?

**Common Revenue moves:**
- Pricing audit (what's actually charged today vs. listed?)
- Term-length and renewal-presentation tests
- Hardware → software bundling formalization
- Storefront / commerce page optimization
- B2B case studies + sales material
- Long-term value pool flags (data, expansion, enterprise): flagged not executed

**Sequencing principle:** Reconcile listed and realized pricing, discounts,
trials, plan mix, margin, retention, and cohort definitions before approving a
pricing test. If those sources already reconcile, use the current evidence
rather than repeating an audit by default.

## How to assign a move to a stage

Some moves clearly belong to one stage. Others span. The rule:

**Assign to the stage where the move's primary measurable impact lands.**

Examples:
- "Rewrite App Store listing in voice": spans Acquisition (organic discovery) and Activation (threshold to trial). Primary impact = Activation (trial conversion rate). Assign to Activation, mention crossover.
- "Eye mask Shopify page rewrite": spans Acquisition (organic search for sleep mask) and Revenue (sale conversion). Primary impact = Revenue (transaction). Assign to Revenue, mention crossover.
- "Alex's LinkedIn cadence": Acquisition (top of funnel for D2C subscribers).
- "Customer.io Flow 6 (eye mask post-purchase)": Retention (deepens hardware buyer engagement) with crossover to Activation (hardware → app premium activation path).

When in doubt: where would removing this move hurt the most? Assign there.

## When the AARRR breakdown isn't equal

Section volume is not proof of product-market fit, company stage, or a binding
constraint. Treat it as a drafting signal to verify:

- **Acquisition-heavy:** check qualified demand, source mix, downstream
  conversion, and capacity before calling top-of-funnel the constraint.
- **Activation-heavy:** check event definitions, cohorts, traffic quality, and
  user research before calling conversion broken.
- **Retention-heavy:** reconcile churn/retention definitions, cohort windows,
  product changes, and support evidence.
- **Referral-heavy:** verify loyalty, share behavior, attribution, economics,
  rights, and program capacity.
- **Revenue-heavy:** reconcile listed/effective pricing, margin, retention,
  packaging research, and buyer evidence before diagnosing underpricing.

An even or uneven plan can both be valid. Name the binding constraint only when
dated evidence supports it; otherwise list competing hypotheses and the
smallest approved test that distinguishes them.

## A note on the order of presentation

Choose the presentation order that makes the approved decision easiest to
review. Funnel order (Acquisition → Activation → Retention → Referral → Revenue)
is useful when explaining the system end to end. Priority order is useful when
the audience must decide the next commitment. State the ordering rule, keep
stage labels explicit, and distinguish presentation order from execution order.
