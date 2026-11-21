# Measuring AI Visibility

No single report shows AI visibility. Suede measures it with four sources that
check each other: a prompt panel, analytics referrals, first-party engine
reports, and attribution signals for influence that never clicks.

## 1. Prompt panel

**Build the set.** 30 to 100 prompts, written the way buyers ask, grouped into
clusters:

| Cluster | Example shape |
|---|---|
| Category definition | "What is [category]?" |
| Shortlist | "Best [category] for [segment]" |
| Constraint | "[category] without [pain] under [budget]" |
| Head-to-head | "[Brand] vs [competitor]" |
| Problem | "How do I [job the product does]?" |
| Brand facts | "Who founded [brand]?", "How much does [brand] cost?" |

Source prompts from sales calls, support tickets, Search Console queries, and
community threads, not from the model's imagination. Freeze the set for a
quarter so trends mean something; add new prompts as a separate cluster.

**Run protocol.** For each prompt and engine, log: date, engine and mode
(AI Overviews, AI Mode, ChatGPT search, Perplexity, Copilot, Claude, Gemini),
locale, logged-in state, run number. Run each prompt at least three times per
cycle because answers vary. Use clean sessions without personalization.

**Score each answer.**

| Field | Values |
|---|---|
| Brand cited (URL in sources) | yes / no, which URL |
| Brand mentioned in text | yes / no |
| Recommendation status | recommended / listed / mentioned only / recommended against / absent |
| Competitors cited and recommended | names |
| Third-party sources cited | domains |
| Factual errors about the brand | quote |

**Derived metrics.**

- Share of citations = prompts where the brand's domain is cited / prompts run,
  per engine and cluster.
- Share of recommendations = prompts where the brand is recommended / prompts
  run.
- Competitive share = brand recommendations / all recommendations of tracked
  brands.
- Source gap list = third-party domains cited for competitors but not the brand.
  This list is the off-site work queue.
- Error rate = answers with a wrong brand fact / answers mentioning the brand.
  Fix at the entity layer.

Report ranges across runs, not a single value. A change smaller than run-to-run
variance is noise.

**Read results by buying topic, then fix before you create.** Score the panel
by topic, not prompt by prompt. "Best auth API", "SSO provider for SaaS", and
"SAML authentication tools" are one topic. Per topic, count how often the brand
and each competitor appear across its prompts and runs. A competitor showing up
in 18 of 25 runs while the brand shows up in 4 is where to start. A single
prompt where both appeared once is not.

For each topic the brand is losing:

1. Open the sources the engine cited when competitors won. Log the page, the
   domain, the page type, and the competitor it names. After 20 to 30 prompts
   the same pages and domains repeat.
2. Check whether an existing page should already win. If one exists, find out
   why it is not surfacing (wrong intent, outdated, answer buried, missing the
   proof or comparison the winning page has) and fix it first. Two weak pages
   on one topic do worse than one fixed page.
3. Rule out the technical layer (indexing, crawler access, internal links)
   before rewriting anything.
4. Pick the fix: a new page, a better existing page, corrected facts, or
   third-party sources the brand is absent from (comparison pages, community
   threads).
5. Once the changes are crawled, rerun the identical panel on the same engines
   and compare per topic.

Topic-gap method adapted from Jam's AI search audit (October 2026). Writing one
new post per missing prompt is the failure this method prevents, and at scale it
runs into Google's scaled content abuse policy.

Third-party prompt-tracking tools can automate this at scale. Before relying on
one, confirm which engines, locales, and interfaces it queries (API versus the
consumer product can differ), how often, and whether you can export raw
answers.

## 2. GA4: AI-assistant referrals

Create a custom channel group with an "AI assistants" channel placed above
Referral. Condition: session source matches regex:

```text
^(chatgpt\.com|chat\.openai\.com|perplexity\.ai|www\.perplexity\.ai|copilot\.microsoft\.com|gemini\.google\.com|claude\.ai|chat\.mistral\.ai|meta\.ai|you\.com)$
```

Also include `utm_source` values the assistants append (ChatGPT commonly uses
`chatgpt.com`). Verify the list against your own Traffic acquisition report
first: add domains you see, remove ones you never do.

Report: sessions, engaged sessions, key events, conversion rate, and top landing
pages for the channel, month over month. Landing pages show which of your pages
engines cite most.

Limits: Google AI Overviews and AI Mode clicks arrive as Google organic and
cannot be separated in GA4. Many assistant visits arrive with no referrer and
land in Direct. Treat this channel as a floor.

## 3. First-party engine reports

- **Google Search Console**: Performance, search type Web, includes AI Overview
  and AI Mode clicks and impressions. The Search Generative AI performance
  report (June 2026 onward) adds generative impressions by page, country,
  device, and date where the property clears Google's threshold. No clicks or
  queries there.
- **Bing Webmaster Tools AI Performance**: citations, cited pages, and grounding
  queries for Copilot. Export monthly. Grounding queries are Bing's own
  interpretation of the request, not what the user typed, so they show what the
  engine actually searched for. The report has no click data and does not map a
  query to a specific citation.
- **Server logs**: hits from `OAI-SearchBot`, `Claude-SearchBot`,
  `PerplexityBot`, `Bingbot`, and user-fetch agents on priority pages show
  retrieval even when no click follows.

## 4. Influence that never clicks

Assistant recommendations often show up as branded search or direct visits
days later.

- Branded query impressions in Search Console, trended.
- A "How did you hear about us?" field with an AI assistant option.
- Sales-call notes tagged when the buyer mentions an assistant.

## KPI sheet

| KPI | Cadence | Owner | Baseline | Target (user-approved) |
|---|---|---|---|---|
| Share of citations, per engine | Monthly | | | |
| Share of recommendations | Monthly | | | |
| Brand fact error rate | Monthly | | | |
| AI-assistant sessions and key events | Monthly | | | |
| Copilot citations (Bing) | Monthly | | | |
| Generative AI impressions (GSC) | Monthly | | | |
| Branded search impressions | Monthly | | | |
| Self-reported AI attribution share | Quarterly | | | |

Targets come from the user's baseline and goals. Never fill them from an
industry average.
