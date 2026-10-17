---
name: 80-20-rule
description: 'Use this skill whenever the design has many features, controls, or content elements and decisions about which to prioritize matter — feature roadmaps, redesign scoping, IA decisions, dashboard design, settings page audits, marketing content prioritization, or any design with many candidates competing for attention. Trigger when the user asks "what should we focus on?", "should we add another feature?", "what can we cut?", or when reviewing a UI cluttered with rarely-used controls. The 80/20 rule (Pareto principle) is one of the foundational principles in ''Universal Principles of Design'' (Lidwell, Holden, Butler 2003) and one of the most quoted across design, business, and engineering.'
---

# The 80/20 Rule

The 80/20 rule (also called the Pareto principle, after Italian economist Vilfredo Pareto) is the empirical observation that, in many systems, a small fraction of inputs produces most of the outputs — roughly 80% of effects from 20% of causes. The exact numbers vary (sometimes 70/30, sometimes 90/10) but the shape — a heavily uneven distribution — recurs across economics, management, software usage, and design.

For designers, the principle's central use is *prioritization*: identify the 20% of features or content that produces 80% of the value, design that 20% well, and let the remaining 80% receive proportionally less effort.

## Definition (in our own words)

In most large systems, effects aren't distributed evenly across causes. A small minority of features account for the bulk of usage. A small minority of users generate most of the support tickets. A small minority of bugs cause most of the crashes. A small minority of tasks consume most of the time. The 80/20 rule names the pattern and suggests that designers should put their effort where it produces the most return: the critical 20%, not the trailing 80%.

## Origins and research lineage

- **Vilfredo Pareto** (1848–1923), Italian economist. Originally observed that approximately 20% of Italians owned 80% of the land. The pattern proved remarkably general.
- **Joseph M. Juran** (1951), in *Quality Control Handbook*. Generalized the pattern from economics to industrial quality control: a small fraction of defect causes accounted for most defects. Juran called this "the vital few and the trivial many," a phrasing still used.
- **Lidwell, Holden & Butler** (2003) compactly stated the design implications: focus design and testing effort on the critical 20%, and minimize or remove non-critical functions in the trailing 80%.
- **Software analytics studies** (Microsoft, Salesforce, Atlassian, and many others published in product-design literature) consistently observe 80/20-shaped distributions in feature usage. The Microsoft Office team's data showed that the most-used 20% of features accounted for the bulk of user time; the long tail of features was rarely touched.

## Why the 80/20 rule matters

Design effort is finite. Spreading it evenly across all features means each receives shallow attention. Concentrating it on the critical 20% means those features are world-class; the remaining 80% can be functional-but-unrefined.

The principle's secondary use: it reframes what looks like "we have a lot of features" as "we have a few critical features and a long tail." That reframe shifts decisions about what to surface (the 20%), what to tuck (the 80%), what to cut (the deep tail), and where to invest performance, polish, and onboarding effort.

## When to apply

- **Feature prioritization.** Roadmap planning, MVP scoping, "what should we ship next?" decisions.
- **IA decisions.** What's primary nav vs. tucked behind disclosure; what's surfaced on a dashboard vs. a sub-page.
- **Performance optimization.** Most performance bottlenecks come from a small fraction of code paths. Profile first; optimize what matters.
- **Onboarding design.** Teach the 20% first; let users discover the rest naturally.
- **Settings page design.** Surface frequently-changed settings; tuck the rest.
- **Bug triage.** A small fraction of bug categories cause most user pain. Fix those first.
- **Documentation.** The 20% of content covering the most-asked questions earns the most polish.

## When NOT to apply (or when to be careful)

- **When you don't have data.** The 80/20 rule is empirical; assuming a distribution without evidence can lead you to optimize the wrong 20%. Get usage analytics before declaring the critical fraction.
- **In safety-critical domains.** A rarely-used safety feature (eject seat, emergency stop) is in the trailing 80% by usage but the critical 0.001% by consequence. Don't strip it.
- **Compliance and accessibility features.** May be rarely used but legally or ethically required. Outside the 80/20 framing.
- **Power-user tools that retain power users.** A small group of power users may account for outsize loyalty, retention, or expansion revenue. Their tools matter even if they're a small fraction of total clicks.
- **When the trailing 80% creates competitive moats.** A rarely-used integration may be the reason a small but loyal customer segment chose your product. Surveying might reveal value invisible to click-data.

## How to identify the critical 20%

Three approaches, often combined:

### 1. Usage analytics

Look at click data, page views, feature adoption rates. Sort by frequency; the top items by frequency are usually the critical fraction.

Caveats:
- Frequency isn't always value. A feature used once per quarter (year-end reports) may be more important than one used daily (search).
- Feature usage in a launched product is shaped by what's been *promoted* — features tucked deep in the IA may be unused because they're hard to find, not because no one wants them.

### 2. Task analysis

Identify the user's primary tasks. Map features to tasks. Features that participate in multiple primary tasks are critical; features that participate in none are candidates for removal.

Approach: write down the 5–10 most common user goals. For each, list the features required. Features that show up in many goals are critical; features that show up in no goal are suspect.

### 3. Customer interviews and segmentation

Ask users directly: which features couldn't they live without? Which would they hardly miss?

Caveats:
- Users often overstate the value of features they rarely use ("I might need it someday").
- Power users speak loudly; majority users are quiet. Triangulate.

## Worked examples

### Example 1: dashboard widget prioritization

Imagine a dashboard with 16 widgets. Analytics show:

- 4 widgets are interacted with by >70% of users on most visits.
- 6 widgets are interacted with by 20–60% of users sometimes.
- 6 widgets are interacted with by <10% of users.

The 80/20 redesign:

- The 4 frequent widgets become primary (top of page, prominent sizing).
- The 6 medium-use widgets become secondary (collapsed by default or placed below the fold).
- The 6 rarely-used widgets move to a "Reports" sub-page (still accessible; not on the main dashboard).

Most users see a focused dashboard; the long tail remains for users who need it.

### Example 2: form field prioritization in a sign-up flow

A sign-up flow asks for 12 fields. Analytics show drop-off jumps after field 6.

The 80/20 redesign:
- Identify the 4 fields the system *requires* to function (email, password, plan, agreement).
- Identify 2 fields highly correlated with retention (use-case selection, team size).
- Defer the remaining 6 fields to "later" — collected progressively as the user uses the product.

Sign-up completion rises; data quality improves over time.

### Example 3: support documentation focus

A docs site has 200 pages. Analytics show:
- 20 pages account for 80% of total page views.
- 50 pages account for 95%.
- 150 pages have <100 views per year.

The 80/20 docs investment:
- The top 20 pages get rewriting, screenshots, video walkthroughs.
- The middle 30 pages get review and freshening.
- The trailing 150 pages get a "needs review" tag and are revisited annually.

Resources flow to where readers are; the long tail receives custodial attention only.

### Example 4: settings page audit

A Settings page exposes 38 controls in one long scroll. Usage analytics:
- 7 controls used by >50% of users per visit.
- 14 used by 5–20%.
- 17 used by <5%.

The 80/20 redesign (combining with `progressive-disclosure`):
- The 7 frequent controls are primary, visible on the entry settings page.
- The 14 medium controls are grouped behind expanded sections or sub-pages.
- The 17 rare controls move to "Advanced," with a search affordance for finding them.

The page reads as 7 controls, not 38; the 17 rare are still reachable.

## Cross-domain examples

### Business: revenue distribution

In most companies, ~20% of customers generate ~80% of revenue. Sales teams adapt: spend account-management effort on the critical fraction; lighter touch on the rest.

The same observation in software: a small fraction of users (sometimes called "power users" or "whales" depending on context) account for outsize usage, support burden, or revenue. Product decisions weigh their needs disproportionately — sometimes appropriately, sometimes to the detriment of the broader user base.

### Engineering: performance optimization

Profiling consistently shows that a small fraction of code paths consume most CPU time. The optimization rule: don't optimize speculatively; profile first; concentrate effort on the hot paths revealed.

### Logistics: warehouse layout

Retail and logistics warehouses often arrange storage so the 20% of SKUs that account for 80% of orders are nearest the shipping dock. Walking distance is the cost being optimized.

### Medicine: treatment focus

A small fraction of patients consume most of healthcare resources. Population-health programs target this critical fraction with intensive case management, leaving the broader population on lighter-touch protocols.

### Linguistics: word frequency

A few hundred words account for most of typical conversation. Language-learning apps prioritize those — the 20% of vocabulary that produces 80% of comprehension — before tackling rarer words.

## Anti-patterns

- **Optimizing the wrong 20%.** Choosing the critical fraction by intuition rather than data. The team's pet features get priority; user-favorite features languish.
- **Removing the trailing 80% without checking dependencies.** A rarely-used feature might be critical to a small but loyal segment whose departure costs more than the feature's maintenance.
- **Assuming the distribution is symmetric.** Not all distributions are 80/20. Some are 90/10, some are 50/50. Measure your actual distribution; don't assume.
- **80/20 as an excuse for under-investing in accessibility / safety / compliance.** These features are 80/20 outliers — rarely-used but high-consequence.
- **Static 80/20 thinking.** The critical fraction shifts over time. Re-measure periodically; what was 20% three years ago may not be today.

## Heuristics

1. **Run a usage histogram.** Plot feature usage frequency. Look at the shape. Confirm it's heavily uneven before designing around an 80/20 assumption.
2. **The "if we removed this, who would scream?" test.** For each feature in the trailing 80%, ask. Sometimes the answer is "no one"; sometimes it's "our biggest customer." Different responses, different actions.
3. **The "what does the typical user need?" check.** For each surface, ask: what does the typical user need on this surface? Surface that. Tuck the rest.
4. **The 80/20 squared check.** Within the critical 20%, the 80/20 may apply again — a few features dominate even within the dominant set. Drill in.

## Related principles

- **`progressive-disclosure`** — the structural mechanism for surfacing the 20% and tucking the 80%.
- **`hicks-law`** — fewer visible options means faster decisions; 80/20 informs which options to make visible.
- **`signal-to-noise-ratio`** (perception) — the 80/20 is the design layer where SNR decisions are made.
- **`flexibility-usability-tradeoff`** (interaction) — every feature added affects usability; 80/20 helps you decide which trade-offs are worth it.
- **`form-follows-function`** (aesthetics) — the function should derive from the 20% of needs that drive most of the use.
- **`ockhams-razor`** — among solutions that work, prefer the simplest; 80/20 is a discipline of subtraction.

## Sub-aspect skills

- **`80-20-feature-prioritization`** — applying the rule to roadmap and scoping decisions.
- **`80-20-redesign-targeting`** — applying the rule to redesign-pass focus and effort allocation.

## Closing

The 80/20 rule is more a discipline than a principle. The discipline is: don't believe your features are equally important; measure; concentrate effort. Designers who internalize this consistently produce sharper products than those who try to give every feature equal love.
