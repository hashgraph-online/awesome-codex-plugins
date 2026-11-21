# AEO/GEO/LLMO Strategy Guide

**Purpose**: AI search optimization reference for AEO/GEO phases.
**Last verified**: 2026-11-03 from Google Search Central (AI features, the generative AI optimization guide, documentation updates), OpenAI, Anthropic, and Perplexity crawler docs, the Bing Webmaster blog, arXiv GEO and citation research, the llms.txt proposal and fetch studies, and the Search Console generative AI inclusion and performance documentation.

## Contents

- Evidence Discipline
- Official Caveats
- Terminology
- SEO vs AEO vs GEO
- AEO Strategy
- GEO Strategy
- Platform Policy Matrix
- Search Console AI Inclusion Controls (`official`)
- Generative AI Performance Report (`official`)
- Bot Purpose vs Observed Access (`official` + `field`)
- llms.txt
- Measurement KPIs
- Practical Optimization Order
- Source Ledger

## Evidence Discipline

Label every AEO/GEO recommendation by evidence tier:

| Tier | Meaning | Examples |
|------|---------|----------|
| `official` | Platform/vendor documentation or policy | Google AI features guidance, OpenAI crawler docs |
| `field` | Real user/search data from Search Console, analytics, server logs, or verified AI citations | Search Console performance, AI referral logs |
| `tool` | Deterministic tool output | Rich Results Test, PageSpeed Insights, schema validator |
| `lab` | Controlled but simulated measurement | Lighthouse, local crawler, static render checks |
| `synthetic` | Prompt/citation probes against AI engines | Repeated ChatGPT/Perplexity/Gemini citation prompt set |
| `heuristic` | Best-practice inference or industry observation | 40-80 word answer blocks, table/list extraction patterns |

Do not present heuristic or synthetic findings as guaranteed ranking/citation factors. Record confidence (`high`, `medium`, `low`) separately from severity.

## Official Caveats

- Google says AI Overviews and AI Mode use the same foundational SEO practices as Search; there are no extra technical requirements, special schema.org types or special schema.org markup, or AI text files required for inclusion. Its generative AI optimization guide states that optimizing for generative AI search "is optimizing for the search experience, and thus still SEO", and that tactics such as content "chunking", `llms.txt`, and inauthentic mentions can be ignored.
- A page still needs to be indexed and snippet-eligible to appear as a supporting link in Google AI features, and the property must be included in the Search Console generative AI setting.
- `nosnippet` and `max-snippet` also limit how much page content Google AI Overviews and AI Mode may use as direct input.
- Google's spam policies apply to attempts to manipulate generative AI responses (clarified 2026-05-15).
- OpenAI, Anthropic, and Perplexity each separate a search or citation crawler from a training crawler and a user-triggered fetcher. Blocking the training crawler does not remove a site from that vendor's answers; blocking the search crawler does. Audit each token independently.
- `llms.txt` is an informal proposal and optional machine-readable content map, not a W3C/IETF standard, ranking factor, or guaranteed major-provider fetch contract. Google states that Search ignores it, and a 2026 log study found that 97% of published files received no requests.

## Terminology

| Term | Full Name | Definition |
|------|-----------|------------|
| **AEO** | Answer Engine Optimization | Making visible page content easy to extract as a direct answer |
| **GEO** | Generative Engine Optimization | Improving the chance that AI-generated answers cite, mention, or ground on a source |
| **LLMO** | Large Language Model Optimization | Making content easier for LLMs and retrieval systems to parse, understand, and reuse accurately |
| **AIO** | AI Optimization | Umbrella term; avoid using it when AEO/GEO is more precise |

## SEO vs AEO vs GEO

| Criteria | SEO | AEO | GEO |
|----------|-----|-----|-----|
| **Goal** | Crawlability, indexability, ranking, search appearance, CTR | Direct answer/snippet/voice-style extraction | AI answer citation, brand mention, source selection |
| **Best evidence** | Search Console, crawl/index status, field CWV, structured data validation | Snippet controls, visible Q&A/answer blocks, FAQ/QAPage validity | Query/prompt probes, citation frequency, official crawler access, source diversity |
| **Risk** | No ranking/indexing guarantee | Google FAQ rich results are no longer shown (since 2026-05-07) | Black-box systems vary; results need confidence labels |

## AEO Strategy

### Direct answer blocks (`heuristic`)

- Put a concise answer near the top of sections that target question-like queries.
- Use question-matching H2/H3 headings when natural.
- Favor visible text, short paragraphs, lists, comparison tables, and definition/procedure blocks.
- Treat fixed answer length rules as heuristic. A 40-80 word direct answer is a useful working range, not a platform guarantee.

### FAQ and Q&A (`official` + `heuristic`)

- Use visible FAQ content when the page genuinely answers common questions.
- Google FAQ rich results are no longer shown in Google Search as of 2026-05-07. FAQ content may still help users and answer extraction, but do not promise Google FAQ rich results.
- Use `QAPage` instead of `FAQPage` when users can submit multiple answers to one question.
- Structured data must match visible content and must not mark up hidden, irrelevant, or misleading information.

## GEO Strategy

GEO is experimental. The 2023 GEO paper reports gains only within its benchmark and setup; do not generalize its “up to 40%” result to live engines or a client site. Later evidence points the other way for most page-level tactics: a 2025 benchmark found most conversational SEO methods ineffective or harmful while traditional SEO stayed effective, and a 2026 study of 468,037 ChatGPT citations found that whether the engine's own search retrieved the site explained about 32% of citation variation against 2.8% for page properties, with FAQ blocks and structured data showing no robust within-site effect. Prefer field evidence or repeatable citation probes and label the rest heuristic.

### GEO CORE Framework (`heuristic`)
This is a local audit mnemonic, not an official platform framework or validated ranking model.

| Dimension | What to inspect | Evidence examples |
|-----------|-----------------|-------------------|
| Context | Complete background, definitions, related concepts | Topic coverage map, query fan-out gaps |
| Organization | Extractable hierarchy, tables/lists, short sections | H2/H3 scan, answer block detector |
| Reliability | Sources, dates, author/site trust, factual verifiability | Citations, author bio, organization schema, external references |
| Exclusivity | Original research, proprietary data, unique examples | First-party benchmarks, case studies, original screenshots/data |

### Citation-ready content (`synthetic`/`heuristic` unless probed)

- Write short, self-contained statements that can be cited without surrounding context.
- Add dates, source names, and links for factual claims.
- Prefer original data, comparisons, benchmark tables, and clearly scoped definitions.
- Avoid creating pages only to manipulate AI answers; keep people-first usefulness as the primary goal.

### Query fan-out simulator

When a coverage experiment is useful, generate a proportionate subquery set across the following categories. `10–30` is an optional working range for broad topics, not a required platform behavior:

- definitions and beginner questions
- comparisons and alternatives
- pricing, risk, limitations, and implementation questions
- entity/brand/product questions
- local, industry, or YMYL-specific variants when relevant

Record uncovered subtopics in `results.json.query_fanout` and turn them into prioritized content recommendations.

### AI citation probe

If the runtime and user permissions allow it, run a stable prompt set across AI search engines and record:

- engine, date, region/language, prompt text, and sample size
- cited URLs, brand mentions, sentiment, and competitor share of voice
- repeated-run volatility and confidence: citations churn daily (a 2026 study saw 50-83% disappear the next day and about 75% return within 20 days), so report citation frequency over a fixed window (for example share of days cited over 7-30 days), never one observation

If probing is unavailable, save the prompt pack as `not-run` rather than pretending the signal exists. Do not infer ChatGPT citations from Google rankings; the overlap is partial and engine retrieval differs.

## Platform Policy Matrix

| Platform / bot | Primary purpose | Optimization implication |
|----------------|-----------------|--------------------------|
| Googlebot | Google crawling/indexing/search snippets | Must allow important indexable pages and resources unless intentionally excluded |
| Google-Extended | Google AI product/training controls outside normal Search crawling | Separate from Search visibility decisions |
| OAI-SearchBot | ChatGPT Search inclusion | Allow when ChatGPT Search visibility is desired |
| GPTBot | OpenAI model training | Can be allowed or blocked independently from OAI-SearchBot |
| ChatGPT-User | User-triggered fetches | Not a normal automatic search crawler; robots.txt may not apply; document separately |
| Claude-SearchBot / ClaudeBot / Claude-User | Anthropic search indexing / model training / user-triggered fetches | Allow Claude-SearchBot for Claude search visibility; ClaudeBot is a separate training decision |
| PerplexityBot / Perplexity-User | Perplexity search results (not model training) / user-triggered fetches | Allow PerplexityBot for Perplexity visibility; Perplexity-User generally ignores robots.txt |
| Applebot-Extended / Meta-ExternalAgent / CCBot | Training-use controls (Applebot-Extended is a usage token that does not crawl) | Training decisions; Meta-WebIndexer is the separate Meta AI citation crawler |
| CDN or WAF bot rules | Edge-level allow, block, or charge decisions | A CDN default that blocks AI crawlers can override robots.txt intent; check the edge separately |

## Search Console AI Inclusion Controls (`official`)

Google surfaces generative AI inclusion as a per-property setting, not a ranking signal.

| Aspect | What to record | Why it matters |
|--------|----------------|----------------|
| Location | Settings > Search generative AI in the property | This is where inclusion is controlled, not in robots.txt |
| States | Included, excluded, or inherited from a parent property | Record the observed state and whether it was set locally or inherited |
| Targets | AI Overviews, AI Mode, Discover | One property can be included in one surface and excluded from another |
| Default | A property is included or inherits unless someone excluded it | Absence of an explicit choice is not evidence of exclusion |
| Separation | Distinct from `Google-Extended`, which governs AI product and training use | Blocking training is not an inclusion decision, and inclusion is not a training allowance |
| Ranking | Not a ranking or inclusion signal for ordinary Search | Do not present it as an SEO lever |

Audit the policy and the live setting as two separate items. Per-property access conditions can leave the setting unreadable, so a missing value is `unknown`, not a finding that inclusion is disabled.

## Generative AI Performance Report (`official`)

The Search Console generative AI performance report reports exposure counts, not citations.

| Aspect | What to record | Why it matters |
|--------|----------------|----------------|
| Dimensions | Page, country, date, device | Exposure is only interpretable with the dimension it was sliced by |
| Date handling | Dates are reported in Pacific Time | Compare against the same calendar basis before drawing a trend |
| Availability | Global rollout reached all users by 2026-08-31 | Absence before that date is a rollout artifact, not a performance signal |
| Aggregation | Do not merge these numbers with ordinary web search data | They are a separate surface with separate semantics |
| Collection | No dedicated API was documented as of 2026-09-21 | Automated collection is `unknown`; do not script an undocumented endpoint |
| Export caveat | Exported `~` and `-` values are converted to `0` | A zero in an export is not a measured zero |
| Meaning | Exposure visibility only; it does not measure citations | Do not report exposure as citation evidence |

## Bot Purpose vs Observed Access (`official` + `field`)

Keep four channels separate, because each one answers a different question.

| Channel | Evidence tier | Question it answers |
|---------|---------------|---------------------|
| Published policy | `official` | What the vendor says the bot is for |
| Crawl configuration | `tool` | What the site currently allows in robots.txt, meta, or headers |
| Observed requests | `field` | What actually reached the origin |
| Observed citations | `synthetic` | Whether answers cited the source |

- A robots allowance is not evidence of crawling, and crawling is not evidence of citation.
- `OAI-SearchBot`, `GPTBot`, and `ChatGPT-User` have different purposes. `ChatGPT-User` is not an automatic crawler, so absent requests from it are not a defect.
- Exclude `OAI-AdsBot` from search-visibility findings.
- Inspect these bots only when the target actually depends on the related service; otherwise record `unknown`.

## llms.txt

Use `llms.txt` as an optional, low-risk content map:

```text
# llms.txt
> Site: example.com
> Description: One-line site description

## Core pages
- /about: Company overview
- /docs: Technical documentation
- /blog/key-topic: Best overview of the topic
```

Rules:

- Do not mark missing `llms.txt` as critical by default, and never score its presence as a ranking or citation factor.
- Consider it for documentation sites, developer tools, API references, or content-heavy products only when a maintained content map has clear user or retrieval value for coding agents.
- Keep it aligned with canonical URLs and sitemap priorities.
- Check server logs before claiming any effect; most published files are never fetched.

## Measurement KPIs

| KPI | Description | Preferred evidence |
|-----|-------------|--------------------|
| AI Citation Frequency | How often target URLs are cited in AI answers | Synthetic probes or AI visibility tools |
| Brand Mention Rate | How often the brand/entity is named | Synthetic probes, AI referrals, third-party tools |
| Share of Voice | Citation/mention share vs competitors | Repeated prompt set with competitors |
| AI Overview Inclusion | Whether Google AI features include links to the site | Search Console generative AI performance report plus manual SERP evidence |
| Bing AI Citations | Citations, cited pages, and grounding queries in Copilot and Bing AI answers | Bing Webmaster Tools AI Performance and Citation Share (preview) |
| Citation Sentiment | Positive/neutral/negative framing | Manual or tool-assisted review |
| AI-referred Conversion | Conversions from AI/search referrers | Analytics custom channel for AI assistants and server logs; AI app traffic often arrives as direct |

## Practical Optimization Order

1. Ensure indexability, crawlability, canonical correctness, and snippet eligibility.
2. Verify visible content quality, trust signals, and structured data parity.
3. Add answer blocks and Q&A content where useful to humans.
4. Build citation-ready sections with sources, original data, and clear entities.
5. Audit platform crawler policies with search and training tokens kept apart (OAI-SearchBot vs GPTBot, Claude-SearchBot vs ClaudeBot), and check the CDN or WAF layer.
6. Optionally add `llms.txt` for content maps.
7. Run query fan-out and citation probes when access allows, then iterate using `score_history` and `best_run`.

## Source Ledger

| Source | Accessed | Supports | Caveat |
|---|---|---|---|
| https://developers.google.com/search/docs/appearance/ai-features | 2026-07-28 | Ordinary SEO requirements for AI features, snippet eligibility, query fan-out, controls | No inclusion, traffic, or citation guarantee |
| https://developers.openai.com/api/docs/bots | 2026-07-28 | OAI-SearchBot/GPTBot/ChatGPT-User purpose separation | Bot strings and policies can change |
| https://llmstxt.org/ | 2026-07-28 | Format and stated intent of the llms.txt proposal | Proposal, not a standards-body or ranking contract |
| https://arxiv.org/abs/2311.09735 | 2026-07-28 | Origin and benchmark scope of GEO research | 2023 benchmark result is not a live-engine guarantee |
| https://support.google.com/webmasters/answer/16908024 | 2026-09-21 | Search Console generative AI inclusion controls and their per-property states | A setting audit is not a ranking or traffic guarantee; unreadable settings stay `unknown` |
| https://support.google.com/webmasters/answer/16984139 | 2026-09-21 | Generative AI performance report dimensions, Pacific Time dates, and export caveats | Exposure counts are not citation measurements; exported `0` may be an unset value |
| https://developers.google.com/search/docs/fundamentals/ai-optimization-guide | 2026-11-03 | Generative AI optimization is still SEO; chunking and llms.txt can be ignored; inclusion setting is required | Google surfaces only |
| https://developers.google.com/search/updates | 2026-11-03 | Spam policies apply to generative AI responses (2026-05-15) | Changelog wording is brief |
| https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler | 2026-11-03 | ClaudeBot, Claude-SearchBot, and Claude-User purposes | Bot strings and policies can change |
| https://docs.perplexity.ai/guides/bots | 2026-11-03 | PerplexityBot is not used for model training; Perplexity-User generally ignores robots.txt | Vendor statement |
| https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/ | 2026-11-03 | Bing AI Performance citation reporting | Public preview |
| https://arxiv.org/abs/2506.11097 | 2026-11-03 | Most conversational SEO methods are ineffective; traditional SEO stays effective | Benchmark setting |
| https://arxiv.org/abs/2610.15033 | 2026-11-03 | Retrieval explains about 32% of ChatGPT citation variation against 2.8% for page properties | Preprint, two markets |
| https://ahrefs.com/blog/how-stable-are-ai-citations/ | 2026-11-03 | 50-83% of citations disappear the next day; about 75% return within 20 days | Vendor study |
| https://ahrefs.com/blog/llmstxt-study/ | 2026-11-03 | 97% of published llms.txt files received no requests in May 2026 | Vendor study |

## Sources

> Content checked 2026-11-03; each source below was last read on the date recorded in the ledger above.

| Claim | Source |
|---|---|
| AI-feature requirements, snippet eligibility, query fan-out, and crawl controls | <https://developers.google.com/search/docs/appearance/ai-features>, accessed 2026-07-28 |
| OpenAI crawler purpose separation (OAI-SearchBot, GPTBot, ChatGPT-User) | <https://developers.openai.com/api/docs/bots>, accessed 2026-07-28 |
| Format and stated intent of the llms.txt proposal | <https://llmstxt.org/>, accessed 2026-07-28 |
| Origin and benchmark scope of the GEO research the GEO CORE framework summarizes | <https://arxiv.org/abs/2311.09735>, accessed 2026-07-28 |
| Search Console generative AI inclusion controls and their per-property states | <https://support.google.com/webmasters/answer/16908024>, accessed 2026-09-21 |
| Generative AI performance report dimensions, Pacific Time dates, and export caveats | <https://support.google.com/webmasters/answer/16984139>, accessed 2026-09-21 |
| Generative AI optimization stance, ignorable tactics, and the inclusion precondition | <https://developers.google.com/search/docs/fundamentals/ai-optimization-guide>, accessed 2026-11-03 |
| Spam policies covering generative AI responses | <https://developers.google.com/search/updates>, accessed 2026-11-03 |
| Anthropic and Perplexity crawler purpose separation | <https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler>, <https://docs.perplexity.ai/guides/bots>, accessed 2026-11-03 |
| Bing AI citation reporting | <https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/>, accessed 2026-11-03 |
| GEO and citation evidence after the 2023 paper | <https://arxiv.org/abs/2506.11097>, <https://arxiv.org/abs/2610.15033>, accessed 2026-11-03 |
| Citation volatility and llms.txt fetch rates | <https://ahrefs.com/blog/how-stable-are-ai-citations/>, <https://ahrefs.com/blog/llmstxt-study/>, accessed 2026-11-03 |
