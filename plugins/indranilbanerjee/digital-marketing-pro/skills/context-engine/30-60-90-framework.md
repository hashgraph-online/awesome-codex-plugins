# The 30 / 60 / 90-Day Framework

No marketing strategy should be planned as a single 12-month block. Breaking the first quarter into 30 / 60 / 90-day phases creates milestones that allow early-stage course correction and prevent slow-rolling failure.

This framework is the default phasing for the Implementation Timeline in the Growth Plan (Section 8) and for the start of every new engagement.

## The Three Phases

### Days 1–30 — Foundation

**Goal:** establish the operational base. Get tracking right. Launch on proven channels. Build the assets the strategy depends on.

**Standard activities:**

1. **Tracking infrastructure setup** — GA4 properly configured (events, conversions, audiences mirroring the channel strategy), Google Tag Manager firing correctly, ad platform pixels deployed, server-side tracking (CAPI) where applicable, conversion events validated end-to-end
2. **Initial campaigns on proven channels** — typically Google Search (brand + non-brand high-intent keywords) + retargeting (anyone who visits the site gets retargeted). These are the highest-ROI channels for most businesses; start here while building toward more sophisticated activity.
3. **Establish baseline metrics** — first 2–3 weeks of data become the baseline against which all future periods are compared. Document carefully.
4. **Finalise creative assets** — landing pages live, ad creative produced, content calendar planned, brand voice references documented
5. **Initial keyword research and competitor monitoring setup** — Ahrefs / Semrush projects created, weekly competitor watching automated

**What success looks like by Day 30:**

- Tracking is verified working end-to-end
- Initial campaigns running with first performance data
- Baseline metrics documented
- Creative production rhythm established
- Team operating cadence (daily / weekly cadences) established

**Common Day 30 anti-patterns:**

- Tracking not validated → measurement breaks the moment scaling starts
- Launching too many channels at once → impossible to attribute what is working
- Not documenting baseline → no reference point for evaluating future performance
- Skipping competitor monitoring setup → blind to market context

### Days 31–60 — Validation

**Goal:** confirm the initial channels are working. Begin first optimisations. Expand cautiously to secondary channels. Establish reporting rhythm.

**Standard activities:**

1. **Analyse initial campaign performance vs KPI targets** — first real comparison of plan vs reality
2. **Run first A/B tests** — typically on ad copy variants, landing page headlines, CTA wording. Tests run for at least 2 weeks for statistical significance.
3. **Expand to secondary channels** if primary channels are performing — typically Meta or LinkedIn (depending on B2C vs B2B), email lifecycle flows, organic social posting cadence
4. **Begin content marketing and SEO activities** — content takes months to rank, so start producing in earnest now even though impact is later
5. **First monthly performance report** — full structured report (see [monthly-report-template.md](monthly-report-template.md))

**What success looks like by Day 60:**

- Primary channels validated as on-track or course-corrected if not
- First A/B test results in hand (some winners, some learnings)
- Secondary channels launched with initial data
- Content engine producing per the plan
- First monthly report delivered to client; client knows where things stand

**Common Day 60 anti-patterns:**

- Not running A/B tests because "we are still optimising" — without tests there is no systematic optimisation
- Adding too many channels in this phase — Days 31–60 should add 1–2 secondary channels max
- Reactive ad-hoc reporting instead of structured monthly report

### Days 61–90 — Optimisation & Scale

**Goal:** double down on winners. Pause losers. Begin scaling. Launch awareness layer. Establish the optimisation rhythm that will continue indefinitely.

**Standard activities:**

1. **Double down on winning campaigns** — Variable budget deployed toward proven below-target CPA campaigns (see [fixed-vs-variable-budget.md](fixed-vs-variable-budget.md))
2. **Pause or restructure losers** — campaigns consistently above target CPA for 3+ weeks get restructured or paused
3. **Introduce variable budget recommendations** — first formal Variable budget conversation with client
4. **Launch awareness-layer campaigns (TOFU)** — now that conversion tracking is proven, brand-building investment can be measured for indirect impact
5. **Begin email / WhatsApp nurture flows** for leads captured in Days 1–60
6. **Quarterly strategy review** — what is working, what is not, what to change for Q2

**What success looks like by Day 90:**

- Performance data shows clear winners and losers
- Variable budget mechanism in active use
- TOFU campaigns running for awareness building
- Lifecycle nurture flows active
- Quarterly review completed; Q2 plan refined

**Common Day 90 anti-patterns:**

- Scaling too aggressively (jumping from INR 1L/day to INR 5L/day overnight) — the platform learning algorithms reset and performance temporarily collapses
- Pausing campaigns too quickly (before 3-week trend is clear) — kills campaigns that need more time
- Skipping the quarterly review — locks in problems that should have been corrected for Q2

## Why this phasing

The 30 / 60 / 90 sequencing reflects how digital marketing campaigns mature:

- **Foundation work matters disproportionately** — tracking errors caught in Day 1 cost INR X to fix; tracking errors caught in Day 90 cost INR 100X (because all data since is suspect)
- **Channels need 14–30 days of data before optimisation decisions are reliable** — earlier "winners" and "losers" are usually noise
- **A/B tests need 14+ days to reach significance** for typical conversion volumes
- **Content marketing has a 90+ day lead time** — start producing in Days 1–60 so content has time to compound by Days 91–180
- **Brand awareness investment compounds over months** — start TOFU in Day 61–90 so it has time to lift conversion in Q2

Trying to compress the sequence (e.g., scaling at Day 30) consistently underperforms the disciplined sequence.

## Beyond Day 90

The 30 / 60 / 90 framework is the **first quarter** structure. After Day 90, the engagement transitions to a quarterly cadence:

- **Monthly:** performance review + Variable budget recommendation + tactical adjustments
- **Quarterly:** strategy refresh — channel mix re-evaluation, budget re-allocation, KPI target reset
- **Annually:** full Growth Plan refresh + new Yearly Planner

The discipline established in Days 1–90 (tracking accuracy, A/B testing rigor, structured reporting, Variable budget mechanism) carries through every subsequent quarter.

## When to deviate from the standard 30 / 60 / 90

- **Major product launch in Days 1–30:** front-load creative and campaign setup; defer secondary channel expansion until post-launch
- **Active competitive crisis:** front-load competitive response; defer infrastructure work to Days 31–60
- **Highly seasonal business with critical season in Days 1–60:** front-load all critical-season activity; treat Days 61–90 as the "Days 1–30 equivalent" for the off-season
- **Tracking infrastructure already in place:** skip much of Days 1–30 setup; start at Days 31–60 equivalent

The framework is a default, not a constraint. Adapt to engagement specifics, but always document why standard phasing is not being used.

## Where the 30 / 60 / 90 lives in the engagement

- **Growth Plan Section 8 (Implementation Timeline):** the 30 / 60 / 90 milestones for the engagement
- **Yearly Planner:** the first three months expand the 30 / 60 / 90 phases
- **Living Project Instruction File:** current phase + day count visible
- **Monthly reports:** explicitly reference which phase the engagement is in

## Related references

- [growth-plan-template.md](growth-plan-template.md) — Section 8 implementation timeline
- [monthly-report-template.md](monthly-report-template.md) — monthly cadence after Day 30
- [fixed-vs-variable-budget.md](fixed-vs-variable-budget.md) — Variable budget introduced in Days 61–90
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — engagement structure context
