# Marketing Operations Stack: Skills + MCPs per AARRR Stage

This doc maps every marketing-skill and every relevant MCP/API integration to the AARRR stage(s) it primarily serves. It's the source for Section 11 of every plan.

> **Note on scope.** Skills below live in the public Suede skill pack. External
> tools are optional. Discover current callable, authorized capabilities first;
> otherwise use a manual workflow and record the limitation in Section 13.

## The thesis

The public Suede skill pack and verified integrations can make approved workflows more repeatable for a small team. They do not replace channel ownership, human review, or missing expertise, and they do not imply a headcount-equivalence or guaranteed output.

The plan's Section 11 makes this thesis explicit by:
1. Mapping skills to stages so the founder sees which skills execute which work
2. Mapping MCPs/APIs to stages so the founder sees the tooling layer
3. Naming a concrete, evidence-backed operational example that shows how the stack was used
4. Showing capability unlocks by verified evidence, owner capacity,
   authorization, maximum exposure, review date, and stop conditions

## Marketing skills mapped to AARRR

### Acquisition skills

| Skill | What it does | Primary use in Acquisition |
|---|---|---|
| `suede-seo-audit` | Audit technical and on-page SEO, AI-search readiness, and structured data | Quarterly site health and search-readiness checks |
| `suede-programmatic-seo` | Build template-driven SEO pages at scale | Location, comparison, integration page systems |
| `suede-content-strategy` | Plan content topics, pillars, cadence | Setting the editorial calendar |
| `suede-competitors` | Build vs-pages and alternative-to-pages | Capture high-intent SERPs against competitors |
| `suede-ads` | Plan and structure paid campaigns | Apple Search Ads, Meta, Google, LinkedIn |
| `suede-ad-creative` | Generate ad variations and creative | Iterate ad creative across platforms |
| `suede-social` | Plan and write social media content | LinkedIn, Twitter/X, Instagram, TikTok |
| Typefully (external integration) | Schedule/post tweets, threads, LinkedIn content | Cadence operations for founder-led channels |
| `suede-cold-email` | Write B2B cold outreach + sequences | Outbound for B2B SaaS / hybrid businesses |
| `suede-analytics` | Set up tracking, GA4, conversion events | Funnel instrumentation |
| `suede-free-tools` | Plan engineering-as-marketing free tools | Build tools that generate links + leads |
| `suede-site-alchemy` | Design marketing sites with intention | Pillar/landing page design |
| `suede-launch-packaging` | Plan and execute launches (Product Hunt, GA, feature launches) | GTM moments: strategy + tactical execution |

### Activation skills

| Skill | What it does | Primary use in Activation |
|---|---|---|
| `suede-onboarding` | Optimize user onboarding flows | Onboarding rebuild, activation rate tests |
| `suede-onboarding` (Signup lane) | Optimize signup/registration | Reduce friction at top of activation |
| `suede-site-alchemy` | Optimize marketing pages, forms, popups, and landing pages | Conversion testing across activation surfaces |
| `suede-paywalls` | Optimize paywalls and upgrade screens | Trial → paid conversion (also Revenue) |
| `suede-copy` | Write, edit, and iterate marketing copy | Onboarding screens, paywall copy, CTAs, and voice review |
| `suede-ab-testing` | Plan A/B tests | Structure for onboarding variant tests |
| `suede-offers` | Offer design plus evidence-tiered behavioral models | Persuasion principles in activation moments |

### Retention skills

| Skill | What it does | Primary use in Retention |
|---|---|---|
| `suede-emails` | Design email sequences | Customer.io / Mailchimp / Resend flow building |
| `suede-churn-prevention` | Build cancellation flows, save offers, win-back | Reduce churn, recover failed payments |
| `suede-copy` | Email copy production | Lifecycle email content |
| `suede-paywalls` | (cross-cuts): upgrade prompts in retention emails | Upsell within lifecycle |
| `suede-ab-testing` | Test email variants | Subject line, CTA, timing tests |

### Referral skills

| Skill | What it does | Primary use in Referral |
|---|---|---|
| `suede-referrals` | Plan and launch referral / affiliate / ambassador programs | Core skill for Section 7 |
| `suede-social` | Create ambassador-shareable content | Talking points, post templates |
| `suede-copy` | Ambassador / affiliate email copy | Recruitment, onboarding, communication |
| `suede-site-alchemy` | Per-ambassador landing pages | Attribution surface |
| `suede-emails` | Ambassador lifecycle emails | Onboarding, monthly digest, payout notifications |

### Revenue skills

| Skill | What it does | Primary use in Revenue |
|---|---|---|
| `suede-pricing` | Audit and optimize pricing | Plan tier structure, annual defaults, value metrics |
| `suede-paywalls` | Paywall optimization | Trial → paid, free → paid conversion |
| `suede-sales-enablement` | Build sales decks, one-pagers, demos | B2B sales support material |
| `suede-revops` | Revenue operations, lead lifecycle | Marketing → sales handoff |
| `suede-ab-testing` | Pricing experiments | Test annual default, intro pricing, tier consolidation |

### Cross-cutting / brand foundation skills

| Skill | What it does | Primary use |
|---|---|---|
| `suede-product-marketing` | Set up the `.agents/product-marketing.md` context file (positioning, ICP, voice) | Foundational: run first; every section of the plan references this |
| `suede-customer-research` | Conduct customer interviews + surveys | Section 2 + Section 3 (Current state) |
| `suede-offers` | Offer design and behavioral models | Cross-cuts copy, CRO, paywalls |
| `suede-marketing-plan` (tactic library) | The 142-idea library and scoring rubric | Section 12 of plan (Idea bank) |

## MCPs and APIs mapped to AARRR

### Acquisition tooling

| Optional tool | What it can provide | Availability and authority check |
|---|---|---|
| **Ahrefs API** | SEO data: keyword research, backlinks, competitor analysis | Confirm an already authorized connection; never request or expose a secret |
| **DataForSEO API** | SERP data, keyword volume, competitor SERP analysis | Confirm authorized account, cost ceiling, and data terms |
| **GA4 MCP** | Traffic by channel, conversion events, retention curves | Confirm callable property, identity, scope, and read-only boundary |
| **GitHub MCP** | Repo work: marketing site, content authoring | Confirm exact repo, branch, permissions, and mutation approval |
| **Typefully MCP** | Social drafting or posting where supported | Confirm account identity; posting requires explicit publication approval |
| **Google Ads MCP** | Campaign analysis or approved account changes | Confirm account identity and read-only/change scope; spend changes need explicit approval |
| **Browser automation** | Form checks, screenshots, and authorized workflows | Use only if already available and permitted; installation and submission are separate approvals |
| **Page extraction** | Clean text extraction from permitted web pages | Use an available reader; do not install software or bypass access controls |
| **Notion** | Authorized internal knowledge access | Confirm workspace, page scope, and read/write boundary |
| **Stripe MCP** | LTV inputs and paid-CAC reconciliation | Confirm account identity, restricted scope, and read-only boundary |

### Activation tooling

| Tool | What it provides |
|---|---|
| **App Store Connect** | Conversion rate by listing variant, install funnel | Confirm authorized property and available read method; do not assume browser tooling |
| **GitHub MCP** | Mobile app repo for onboarding code edits |
| **Figma / Pencil MCP** | Onboarding screen design + iteration |
| **Customer.io MCP** | In-app messaging + lifecycle email coordination |
| **Stripe MCP** | Subscription state for paywall logic |
| **GA4 MCP** | Activation events instrumentation |

### Retention tooling

| Tool | What it provides |
|---|---|
| **Customer.io MCP** | The retention infrastructure: flow building, segmentation, sending |
| **Shopify** | Hardware buyer events as lifecycle triggers |
| **Stripe MCP** | Subscription state, churn cohorts, plan changes |
| **GA4 MCP** | Session events, retention curves |
| **Resend / Mailchimp / SendGrid** | Alternatives to Customer.io for different stacks |

### Referral tooling

| Tool | What it provides |
|---|---|
| **Dub.co** | Ambassador attribution, short links, per-ambassador tracking |
| **Stripe MCP** | Commission accounting + payouts via Connect |
| **GitHub MCP** | Per-ambassador landing pages |
| **Customer.io MCP** | Ambassador lifecycle (recruitment → onboarding → monthly digest → payout notifications) |
| **Rewardful / Tolt / Mention Me** | Alternatives to Dub for affiliate management |

### Revenue tooling

| Tool | What it provides |
|---|---|
| **Stripe MCP** | Pricing tests, subscription analytics, churn cohort analysis, blended CAC math |
| **Shopify** | Hardware transactions |
| **GA4 MCP** | Revenue events |
| **Customer.io MCP** | Paywall / pricing-related lifecycle |
| **Notion** | Commercial knowledge directory |

### Cross-cutting tooling

| Tool | What it provides |
|---|---|
| **Notion** | Shared knowledge base |
| **GitHub MCP** | Shared context repo (`{client-org}/{client-context}`) |
| **defuddle** | Research extraction |
| **obsidian-cli** | Working notes for fCMO |
| **Pencil MCP** | Design files |
| **Figma MCP** | Design files (if Figma) |

## Capability unlocks by verified resource state

Section 11 must include this table (or equivalent). Funding stage may be context,
but it does not supply the answer.

| Capability | Current evidence and owner | Constraint | Unlock condition | Approval / maximum exposure | Review |
|---|---|---|---|---|---|
| Acquisition test | | | | | |
| Lifecycle | | | | | |
| Content / creative | | | | | |
| Analytics | | | | | |
| Community / PR | | | | | |

Mark each capability `current`, `approved test`, `conditional unlock`, or
`deferred` using `funding-stage-unlocks.md`. Never infer headcount, tool spend,
or channel scale from a round label.

## The concrete-example test

Section 11 of the plan must include at least one concrete operational example that grounds the stack thesis in evidence. The example should be:
- A specific event (not abstract claim)
- From this client's actual history when a source artifact is available
- Tied to a named owner, workflow, review step, and observable result
- Careful not to attribute an outcome to a skill or integration unless the evidence supports that causal claim

Use this evidence format:
- *"On [date], [owner] used [verified skill/tool] to complete [specific workflow]. [Reviewer] approved [artifact or deployment]. The recorded result was [measured observation], according to [source]."*
- If the result is only an illustrative planning scenario, label every number as an assumption and state that it is not an expected outcome.

If the client has no verified example yet, frame it as the *first test*, "Here is the workflow the team will run in week one, the artifact it will produce, and the metric it will observe." Do not present the test as proof or forecast its result.

## When the stack doesn't apply (yet)

For clients without callable authorized connections, frame Section 11
differently:
- List the manual workflows and public Suede skills that apply now.
- Name the specific evidence or efficiency question an optional connection
  could address, plus owner, data boundary, cost, fallback, and review.
- Keep setup or installation as an unapproved option until the user explicitly
  authorizes the exact tool, account, scope, cost, and mutation boundary. Do not
  assign it to Q1 by default.

A plan can't claim the agentic-stack thesis if the stack isn't wired. Be honest about state.
