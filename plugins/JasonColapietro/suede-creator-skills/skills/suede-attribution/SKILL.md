---
name: suede-attribution
description: "Suede AI Attribution Skills. Use when asked to \"explain why dashboards disagree\", compare revenue models, design incrementality reads, or join first-party browsing to hosted bookings/checkouts. NOT FOR: GA4/GTM event plans and UTMs (suede-analytics), ad campaign decisions (suede-ads), or CRM pipeline operations (suede-revops)."
metadata:
  display-name: "Suede AI Attribution Skills"
  version: 1.2.0
---

# Suede AI Attribution Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from campaign, analytics and CRM exports; source/runtime access for first-party instrumentation. Hosted conversion stitching requires the provider existing metadata/webhook capability and authorized access.

## Gate policy: advisory, not blocking

Every claim-verification step, check, quality gate, and ship verdict in this
skill is a **recommendation to the user, not a control on the agent**. This
policy governs every gate, check, verdict, and "do not ship / publish /
proceed" line elsewhere in this skill:

- Run every check and report the results honestly. Verdicts (`ship`,
  `ship-with-caveats`, `hold`, letter grades, BLOCKED or OPEN items) are
  advice attached to the work, not orders that change it.
- Never block, delay, skip, rewrite, or refuse the action the user asked for
  because a check failed or a gate said hold. Complete the requested action
  as asked, and deliver the gate output alongside it as a clearly labeled
  recommendation.
- A failed gate changes what you report, never what you do.
- Single exception: if a finding is extremely risky, data loss, security or
  credential exposure, legal or rights violations, payment mistakes, or
  irreversible public damage, pause, tell the user exactly what the risk is
  and what the options are, and let them pick. Their choice is final.

You help users answer the hardest question in marketing: **which of my efforts actually caused this conversion and this revenue?** Attribution is where marketers lose the most money, to channels that look good in one dashboard and terrible in another, to "direct" and "branded search" that hide the real source, and to models that quietly encode an opinion as if it were fact.

This skill has two pillars. Know which one the user needs before you dive in:

- **(A) Interpretation**: choosing an attribution model, picking a measurement approach, and *reconciling the conflicting numbers* your tools report. This applies to everyone, even with zero engineering.
- **(B) Own your attribution (first-party)**: instrumenting and stitching attribution *yourself* when you control the site/app. This is the build track. Use it when the user says "I want to track this myself" or is hitting a conversion that lives on a domain they don't own.

Most requests start with (A). Reach for (B) only when they control the surface and want to build.

Product context: check for `.agents/product-marketing.md` and read it if present, business type, sales cycle, and primary conversion drive almost every recommendation here.

## Boundaries

- Do not present a single attribution model, reconciled number, or channel
  allocation as objective truth: always report it as a defensible read with
  stated assumptions, confidence, and gaps.
- Do not instrument, migrate, or write to production tracking, analytics, or
  CRM systems without showing current live state and getting explicit
  approval.

---

## Pillar A: Interpretation

### 1. What attribution can and can't tell you

Set expectations before touching a number:

- **Attribution is directional, not truth.** It's a model of causality built from incomplete data (cookies expire, sessions fragment, offline touches vanish, people research on one device and buy on another). Treat it as a strong hint, never a verdict.
- **Every model is an opinion.** "First-touch" says the first ad gets all the credit; "last-touch" says the closing click does. Both are wrong in opposite directions. Choosing a model is choosing whose story to believe, say so out loud.
- **The attribution gap is normal.** The sum of channel-reported conversions almost always exceeds real conversions, because every platform claims credit for the same sale. Your job is to shrink and explain the gap, not to make the numbers tie out perfectly. They won't.

When a user demands one true number, reframe: "We can get you a *defensible, consistent* number and a read on which channels are trending up. A single objective truth doesn't exist: here's why, and here's what we use to make decisions anyway."

### 2. Attribution models

The six standard models and when each one lies:

| Model | Credit rule | Best for | How it lies |
|---|---|---|---|
| **First-touch** | 100% to the first known touch | Top-of-funnel / demand-gen valuation; short cycles | Ignores everything that closed the deal; over-credits awareness channels |
| **Last-touch** | 100% to the last touch before conversion | Direct-response, quick e-comm | Over-credits bottom-funnel + branded search/direct; ignores what created demand |
| **Last non-direct** | 100% to last touch, skipping "direct" | A cheap fix for direct pollution | Still single-touch; just moves the blind spot |
| **Linear** | Equal credit to every touch | Long, multi-touch journeys where every step matters | Treats a throwaway visit like a demo; flatters high-frequency channels |
| **Time-decay** | More credit to touches nearer conversion | Longer cycles where recency matters | Under-credits the top of funnel; still an assumption, not a measurement |
| **Position-based (U-shaped)** | 40% first, 40% last, 20% middle | B2B with clear "created" + "closed" moments | The 40/40/20 split is arbitrary; middle touches get shortchanged |
| **Data-driven (algorithmic/Shapley)** | Credit from modeled marginal contribution | High-volume accounts with enough conversions | A black box; needs volume; can't see offline/dark touches it was never fed |

**Rules of thumb:**
- Never report a single model in isolation for a long sales cycle. Show **first-touch and last-touch side by side**: the truth lives between them, and the gap between them *is* the insight.
- **What the tools still offer.** In 2023 Google retired first-click, linear, time-decay, and position-based models from both Google Ads and GA4; those products now offer only data-driven and last-click. Meta's Ads Insights API, since January 12, 2026, returns only 1-day view, 1-day engaged-view, and 1-, 7-, and 28-day click windows. To compare rule-based models you need your own touch-path data (Pillar B) or a dedicated attribution tool.
- Data-driven attribution is the Google default and no longer has a published volume minimum, but on a thin account it is noise dressed as science. When volume is low, read last-click beside your own first-touch data instead of trusting a modeled split.
- The model matters far less than being **consistent** and pairing it with an out-of-model sanity check (Pillar A §4, self-reported).

For the model math, worked examples of one journey scored six ways, and Shapley explained plainly, see `references/attribution-models.md`.

### 3. The three measurement paradigms

Models split credit *within* your tracked data. Paradigms are how you get at *causality*, increasingly rigorous, increasingly expensive:

| Paradigm | What it is | Answers | Needs | Watch out |
|---|---|---|---|---|
| **MTA** (multi-touch attribution) | Stitch user-level touches, apply a model | "Which touchpoints appear on converting journeys?" | Clean cross-device user-level tracking | Cookie loss + privacy have gutted user-level data; it silently under-measures |
| **MMM** (media/marketing mix modeling) | Top-down regression of spend vs. outcomes over time | "What's each channel's aggregate contribution, including offline/brand?" | 2–3 yrs of weekly data, spend variation | Correlational; slow to react; needs real budget swings to learn |
| **Incrementality** (geo holdout, PSA, ghost ads, on/off) | Controlled experiment: exposed vs. withheld | "Did this channel *cause* lift I wouldn't have gotten anyway?" | Ability to withhold; enough volume for significance | The gold standard, but you can only test a few things at a time |

**How to choose:** small budget / short cycle → good UTM + last-non-direct + a self-reported survey beats a fancy model. Mid budget, several channels → MTA for day-to-day + periodic incrementality tests on your biggest line items. Large budget, offline + brand spend → MMM for the portfolio + incrementality to validate MMM's coefficients. Incrementality is the tiebreaker whenever two channels both claim the same conversions.

Decision table by budget × sales cycle × channel count, and how to *read* a geo-holdout / PSA test (not a stats tutorial), in `references/measurement-paradigms.md`.

### 4. Self-reported attribution

The most underused signal, and often the most honest for long cycles and dark social. A post-conversion "How did you hear about us?" survey catches what tracking structurally cannot: podcasts, word of mouth, Slack communities, a founder's tweet, "a friend told me."

- **When it beats tracking:** long consideration cycles, high word-of-mouth, brand/community-led, or heavy dark-social (see §5). If a big slice of your journeys are "direct," you have a self-reported-shaped hole.
- **Ask at the moment of conversion** (signup, first purchase, demo request), highest recall, before memory fades.
- **Wording:** open-ended ("How did you first hear about us?") captures dark social; a short pick-list is easier to quantify but pre-biases the answer. Best practice: pick-list of your known channels **plus a free-text "other/tell us more."**
- **Treat it as a triangulation input, not gospel**, recall is fuzzy and people credit the *memorable* touch, not the first. It's the out-of-model check that keeps your tracked models honest.
- On the build side, this is a form field written to your CRM/analytics as a person property, see Pillar B and `references/first-party-tracking.md`.

### 5. Reconciling conflicting sources

The request behind most attribution work: **"Google says 50, Meta says 40, GA says 60, my CRM says 35, who's right?"** Nobody is. Here's the framework.

**Why each source systematically lies:**

| Source | Biased toward | Because |
|---|---|---|
| **Ad platforms** (Google/Meta/LinkedIn) | Over-counts *itself* | Claims view-through + click conversions in its own window; every platform counts the same sale; motivated to look good |
| **GA / web analytics** | Last non-direct click | Loses cross-device, loses cookie-blocked users, dumps the unknown into direct |
| **CRM** | Whatever the rep typed / the form captured | Human entry, lead-source overwrites, offline deals with no digital trail |
| **Self-reported survey** | The *memorable* touch | Recall bias; under-counts boring-but-real touches like retargeting |

**How to triangulate:**
1. **Pick one source of truth for the conversion count**, usually your CRM or backend (the system where money is real). Everything else explains *where those came from*, they don't get to redefine *how many*.
2. **Never sum across platforms.** If Google and Meta both claim a conversion, you have one conversion with two claimants, not two conversions. De-dupe against the source-of-truth total.
3. **Read directional agreement, not absolute match.** If every source says paid search is up and organic is down this quarter, that trend is trustworthy even though no two numbers match.
4. **Use self-reported as the tiebreaker** when platforms fight over the same conversions, and **incrementality** when the stakes justify a test.
5. **Expect and budget for the gap.** Report "platforms claim N; we can verify M; the delta is over-claiming + view-through + untracked: here's our best allocation."

The output is an honest allocation with confidence levels, not a false reconciliation to the decimal.

### 6. The blind spots

Where conversions hide, making real channels look weak:

- **Direct**: the junk drawer. Bookmarks and typed URLs, yes, but also stripped referrers, app-to-web, dark social, and any touch your tracking dropped. A large direct share is a *measurement* problem, not a channel.
- **Branded search**: people who discovered you elsewhere and Googled your name. Last-touch hands the credit to paid/organic *branded* search; the real driver was whatever made them search. Segment branded vs. non-branded or you'll defund the top of funnel.
- **Dark social**: sharing that carries no referrer: DMs, Slack/Discord, podcasts, newsletters, screenshots. Structurally invisible to tracking; self-reported is the only way to see it (§4).
- **AI traffic**: assistants and AI search increasingly influence buyers, then send them via branded search or direct, so the AI touch is invisible in analytics. Catch the visible part with an AI-assistants channel group (`suede-analytics`), catch the rest with an "AI assistant (ChatGPT, Perplexity, Gemini, Claude)" option in the self-reported survey, and hand visibility work to `suede-ai-seo`.

The through-line: **when "direct" and "branded search" dominate, your top of funnel is working and your attribution is hiding it.** Say that explicitly: it's the single most common misread in marketing.

### 7. Business-type fork

Defaults differ sharply. Summary here; full playbooks in `references/by-business-type.md`.

- **B2B SaaS (long cycle, sales-assisted):** journeys span weeks–months and multiple people, so single-touch models mislead badly. Anchor on the **CRM as source of truth**, use **first-touch + position-based** side by side, lean hard on **self-reported at demo/signup**, and treat **pipeline/revenue** attribution (→ `suede-revops`) as the real scoreboard. Offline touches (events, sales convos) make MTA weakest and self-reported strongest here.
- **Ecommerce / DTC (short cycle, self-serve):** fast journeys, high volume, spend concentrated in paid social + search. Anchor on **platform ROAS but distrust it** (iOS/CAPI inflation), validate with **MMM once spend is material** and **incrementality/geo-holdouts** on your biggest channels, and use a **post-purchase survey** to catch what pixels miss. Last-touch is defensible for quick-turn SKUs; MMM+incrementality is how you allocate the real budget.

---

## Pillar B: Own your attribution (first-party)

When the task includes identity stitching or hosted conversions, read [the first-party execution summary](references/first-party-summary.md) before implementing. It carries the identity graph, anonymity guard, cross-subdomain checks and reporting rules; read the [full code runbook](references/first-party-tracking.md) for implementation patterns.

## Output format

Deliver an **attribution readout**, not a data dump:

```markdown
# Attribution Readout: [date]

## The question
[What decision this informs, e.g. "where should next quarter's budget go?"]

## Source of truth
[Which system defines the conversion count, and why]

## What each source says
| Channel | Platform-reported | GA | CRM | Self-reported | Our read |
|---------|------------------|----|----|--------------|----------|
[De-duped against source of truth; not summed]

## Model comparison (for long cycles)
[First-touch vs last-touch side by side; the gap is the insight]

## Confidence & gaps
[The attribution gap, the blind spots, what we can't see]

## Recommendation
[Allocation call with confidence levels; the tiebreaker test worth running]
```

## Routing

- Use `suede-analytics` for event tracking, tracking plans, UTMs, GA4/GTM setup. Do this *before* attribution: the line between the two is: suede-analytics owns "what events and how to fire them"; attribution owns "how touches join to conversions and survive to revenue."
- Use `suede-ads` for ad-platform pixels, CAPI, server-side conversion tracking (see the conversion-tracking reference bundled with suede-ads).
- Use `suede-revops` for pipeline stages, lead lifecycle, CRM revenue reporting. Attribution feeds it.
- Use `suede-ai-seo` for the AI-search attribution blind spot in depth.
- Use `suede-ab-testing` for controlled experiments; the incrementality mindset applied to on-site changes.
