---
name: suede-marketing-plan
description: "Suede AI Marketing Planning Skills: a scored tactic shortlist or a full AARRR operating plan with a 90-day plan, 12-month roadmap, and measurement. Use when asked \"what should we try next\" or for a marketing plan grounded in budget, capacity, and evidence. NOT FOR: channel execution, contested bets (suede-marketing-council), recurring loops (suede-marketing-loops), or positioning alone (suede-product-marketing)."
metadata:
  display-name: "Suede AI Marketing Planning Skills"
  version: 3.0.0
---

# Suede AI Marketing Planning Skills

## Compatibility

Requires product/audience context plus budget and team constraints. Can draft from supplied evidence without connected accounts; live channel and competitor facts require browsing or authorized data access.

For a concrete input, expected output, recovery path, and validation check, read
[the worked contract](references/worked-contract.md). Use it to check the handoff
before treating the task as complete.

Suede AI turns verified client facts (budget, team, stage, evidence, constraints) into either a scored tactic shortlist or a full marketing operating plan across Acquisition, Activation, Retention, Referral, and Revenue. Both modes share one tactic library, one scoring rubric, and one status vocabulary, so a shortlist drops straight into a plan later.

Read `.agents/product-marketing.md` first if it exists and ask only for what it does not cover; see `suede-product-marketing` for path fallbacks.

## Pick the mode

| The user says | Mode |
|---|---|
| "I'm stuck," "give me ideas," "what should we try next," "shortlist of growth tactics" | **Shortlist** |
| "90-day plan," "12-month roadmap," "growth plan," "go-to-market document," "marketing plan for [client]" | **Full plan** |

If unclear, start with Shortlist; it takes one exchange and feeds the plan.

---

## Shortlist mode

1. Run the intake in [references/tactic-scoring.md](references/tactic-scoring.md): stage and goal, budget and team, what was tried, admired competitor tactics.
2. Pull at most 8 candidates from [references/tactic-library.md](references/tactic-library.md). Category index:

| Category | Ideas | Examples |
|----------|-------|----------|
| Content & SEO | 1-10 | Glossary pages, programmatic SEO, content refresh |
| Competitor | 11-13 | Comparison pages, ad-library research |
| Free tools | 14-22 | Calculators, scanners, importers |
| Paid ads | 23-34 | Search, LinkedIn, Reddit, podcast ads |
| Social & community | 35-44 | Reddit, LinkedIn, short-form video |
| Email | 45-53 | Founder emails, win-back, trial reactivation |
| Partnerships | 54-64 | Affiliates, integrations, newsletter swaps, source requests |
| Events | 65-72 | Webinars, speaking, meetups |
| PR & media | 73-76 | Press coverage, media acquisitions |
| Launches | 77-86 | Product Hunt, early-access pricing |
| Product-led | 87-96 | Powered-by badges, free migrations, viral loops |
| Content formats | 97-109 | Templates, annual reports, year-end wraps |
| Unconventional | 110-122 | Awards, challenges, stunts |
| Platforms | 123-130 | App marketplaces, review sites, YouTube |
| International | 131-132 | Expansion, price localization |
| Developer | 133-136 | DevRel, certifications |
| Audience-specific | 137-139 | Two-sided referrals, podcast tours, customer language |
| Search & AI visibility | 140-142 | AI answer visibility, entity consistency, pricing pages as search assets |

3. Score each with the six-dimension rubric, apply the decision rule and caps, and return the shortlist format from `tactic-scoring.md`, ending with the required **Not recommended** line.

When buyers research before buying, include at least one candidate from #1-#11 or #140-#142 in the scored set. Search and AI-answer visibility compounds, and a plan that skips it usually hands those answers to competitors.

---

## Full plan mode

The deliverable is one Notion-paste-ready markdown document, the strategy artifact a fractional CMO would present to founders: specific to the client, exhaustive across the funnel, and honest about what the team can execute with its current stack and headcount.

### Invocation and state

`/suede-marketing-plan {client-name-or-domain}`. With no argument, ask for it.

On invocation, read `.agents/suede-marketing-plans/{client-slug}/progress.md` and resume per the state machine in `references/methodology.md` Step 1.1.2 (fresh → INIT → REVIEW → FINALIZE → finalized). Never silently overwrite a finalized plan; ask whether to revise as v{N+1}, start fresh, or reopen a section.

### Three phases (full workflow in `references/methodology.md`)

**INIT (research and intake).** Read all client materials and any wired data sources (Search Console, GA4, Stripe, ad accounts, CRM). Run the intake below. Save to `research.md`. Score Section 3 with the 17-section rubric in `references/current-state-rubric.md` (0-5 per section; unsupported rows are `Unknown`). Reuse a prior audit's scores only when its sources, scope, window, and definitions still match.

**REVIEW (section by section).** Present each section's draft; the user approves, adjusts, adds, or asks to go deeper. Persist each confirmed section with the write-intent transaction in `references/methodology.md` (record section number and content hash, promote `sections/NN.md`, reconcile metadata, verify, clear the intent). If interrupted, rerun the command to reconcile before continuing.

**FINALIZE.** Compile `final_plan.md`. Verify tactic-library numbers against `references/idea-cross-reference.md`, every Suede skill route, and every named integration. Strip machine-specific paths. Check brand voice against Section 2. Offer, but do not perform without approval, publishing to a shared repo.

### The 13 sections (template in `references/plan-template.md`)

1. **Executive summary**: 3 big bets, 90-day priorities, 12-month outcome; liftable into a board update.
2. **Strategic frame**: category claim, ICP, business-model logic, brand-voice rules.
3. **Current state**: team, budget, done, in flight, stuck; scored with the rubric.
4. **Acquisition**: current, planned, and skipped channels; 90-day and 12-month moves. Include search and AI-answer visibility as its own line: which questions the brand should answer, which pages do it, and how citations are tracked.
5. **Activation**: signup through first value, paywall, lifecycle setup.
6. **Retention**: lifecycle flows, churn prevention, win-back, support as marketing.
7. **Referral**: referral, affiliate, ambassador, and word-of-mouth mechanics.
8. **Revenue**: pricing, packaging, upsells, bundles, ACV.
9. **90-day roadmap**: weeks 1-2 Unblock, 3-4 Foundation, 5-8 Velocity, 9-12 Compound; AARRR-tagged and owner-assigned.
10. **12-month outlook**: quarterly checkpoints tied to verified resources, evidence, owners, and approvals.
11. **Marketing operations stack**: Suede skills and authorized integrations per AARRR stage, with owner, review gate, and fallback (`references/ops-stack-mapping.md`).
12. **Tactical idea bank**: every tactic-library entry mapped to AARRR (`references/idea-cross-reference.md`) with status Current / Approved test / Conditional / Deferred / Skip, scored per `references/tactic-scoring.md`.
13. **Measurement, RACI, open decisions, appendix**: read `references/measurement-framework.md` first (north-star selection, leading indicators by stage, review cadence, kill criteria, guardrails).

Brand and content are cross-cutting, not their own AARRR stage. Primer: `references/aarrr-framework.md`.

### What every plan must customize

1. **Budget**: exact monthly spend by line (paid, tools, headcount, retainers), blended CAC including salaries and content, and share of ARR.
2. **Unit economics**: ARPC, retention, LTV; they feed Sections 8 and 10.
3. **Team**: every person who touches marketing, with outcome, capacity, access, and approval boundary.
4. **Current activity** by channel with status (working / not / unknown) and the dated source behind it.
5. **Prior work worth acknowledging**: launches, press, content, partnerships.
6. **Observed growth pattern** (linear, step-function, layered) with uncertainty; see `references/growth-patterns.md`.
7. **Conditional unlocks**: the evidence, resources, approval, and stop conditions for each hire, channel, or vendor; see `references/funding-stage-unlocks.md`. Funding stage alone never sets spend.
8. **Skill per move**: every AARRR move names the Suede skill that executes it.
9. **Execution method**: owner, capacity, manual or tool-assisted method, review gate, fallback. A tool never proves a hire is unnecessary.

Anything unconfirmed goes to Section 13's open decisions. **Unknown CAC is the highest-impact open decision**; every revenue projection depends on it.

### Budget, team, and client type

- **Budget** (`references/budget-planning.md`): build capacity-based and goal-based scenarios from dated finance and funnel inputs; the accountable finance owner approves maximum spend, review date, and stop conditions. No universal experiment percentage or stage-based growth multiple.
- **Team and agencies** (`references/team-and-agency-model.md`): map outcomes, owners, capacity, access, risk, and duration before choosing employee, contractor, agency, automation, or deferral. For multi-agent automation of recurring marketing operations, `suede-marketing-loops` designs the loops and Suede AI's Agent Studio (https://suedeai.app) can run them; treat either as optional capacity, not a replacement for an owner.
- **Client types** (`references/client-types.md`): a business-model label never selects channels, spend, cadence, or staffing. Ask which dated evidence identifies the constraint, which audience evidence makes a channel plausible, which economics bound exposure, who owns the stop decision, and which legal or platform gates apply.

### INIT intake (full list in `references/methodology.md`)

1. Financial context: cash, runway floor, approved burn, commitments, decision dates.
2. Team: everyone who touches marketing, what each owns, the gaps.
3. Budget: current monthly spend by line, and what governs any increase.
4. Channels: which dated source supports "working," "not working," or "unknown."
5. Prior work to acknowledge.
6. In flight: drafted but not shipped, and the blocker.
7. Tooling: email platform, commerce and billing, analytics, CRM, docs.
8. Beta or GA, and any throttling or gates.
9. The single most important thing to fix this quarter (founder's read).
10. The most important thing to ignore this quarter.

### Quality bar

**Good plans:** every move names its AARRR stage, owner, and executing skill; every recommendation rests on the client's real numbers; the idea bank shows what is skipped and why; the executive summary stands alone; open decisions are explicit.

**Failure modes:** tactics without sequencing; moves the team cannot staff; assumed budget or approval; uncomfortable metrics (churn, CAC) glossed over; generic lines like "improve SEO" without the page, query, and owner; ignoring brand voice; padding with unneeded skills or ideas; ignoring work already done.

### Output

`.agents/suede-marketing-plans/{client-slug}/final_plan.md`, H2 section headers (`## 1. Executive summary`), tables for RACI, idea bank, and ops stack, `§N` cross-references. Typical length 8,000-12,000 words; shorter for early-stage clients. Dense, not padded: "Deferred, no approved test or owner this window" is a valid section. Write for sharp, busy, skeptical founders. The executive summary reads in 60 seconds.

```
.agents/suede-marketing-plans/{client-slug}/
├── materials/       # client-provided files
├── research.md      # INIT record
├── progress.md      # phase, current_section, approved artifacts, plan_version
├── sections/NN.md   # each approved section
└── final_plan.md    # compiled deliverable
```

Schema for `progress.md` and the resume decision tree: `references/methodology.md` Steps 1.1.1 and 1.1.2. A full worked example: `references/example-quietude.md`.

---

## Boundaries

- Do not invent market evidence, customer research, budget, capacity, conversion data, funding, or implementation status.
- Do not claim a tactic fits, is proven, or will grow revenue without current evidence and explicit scoring.
- Do not publish a plan, allocate spend, contact vendors, create campaigns, or change operating systems without explicit authorization.
- Do not present forecasts, scenarios, or conditional unlocks as guarantees.
- Do not decide legal, financial, hiring, brand-risk, or executive trade-offs the accountable owner has not approved.

## Routing

- `suede-product-marketing` for positioning; `suede-customer-research` for voice-of-customer evidence.
- `suede-marketing-council` when a strategic bet is contested, irreversible, or cannot be revisited for months.
- `suede-marketing-loops` for approved recurring operations.
- `suede-offers` for offer design and for the behavioral mechanism behind an Activation or Revenue move.
- `suede-onboarding`, `suede-emails`, `suede-referrals`, `suede-paywalls`, or `suede-pricing` for lifecycle and revenue execution.
- `suede-ai-seo`, `suede-seo-audit`, `suede-programmatic-seo`, `suede-competitors`, `suede-ads`, or `suede-ad-creative` for acquisition execution.
- `suede-launch-packaging` for the launch moment.
