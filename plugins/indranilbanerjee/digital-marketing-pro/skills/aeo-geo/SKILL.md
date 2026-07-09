---
name: aeo-geo
description: "Optimize AI engine visibility. Use when: AEO/GEO strategy, citation optimization, entity consistency across AI platforms."
---

# AEO/GEO Intelligence

## When to Use This Skill

Activate this module when the user's request involves any of the following:

- **AI Visibility**: Questions about how a brand, product, or person appears in AI-generated answers (ChatGPT, Perplexity, **Google AI Mode**, Google AI Overviews, Copilot, Gemini, Claude)
- **Answer Engine Optimization (AEO)**: Optimizing content so it gets selected as a source for AI-generated answers
- **Generative Engine Optimization (GEO)**: Structuring content and entities so generative AI platforms accurately represent a brand
- **Citation Tracking**: Monitoring which sources AI models cite when answering queries related to a brand or industry
- **Entity Consistency**: Ensuring brand information is uniform across all knowledge sources that AI models train on or retrieve from
- **Knowledge Graph Optimization**: Improving how a brand is represented in Google Knowledge Graph, Wikidata, and other structured knowledge bases
- **Structured Data for AI**: Implementing schema markup and structured data specifically to improve AI comprehension and citation likelihood

**Trigger phrases**: "AI visibility," "how does ChatGPT describe my brand," "Perplexity results," "AI Mode optimization," "AI Overview optimization," "answer engine," "generative engine," "LLM optimization," "AI citations," "entity consistency," "Knowledge Graph"

**Google AI Mode (May 2026 — treat as a distinct surface)**: At Google I/O on 19 May 2026 AI Mode became the default search experience for opted-in users, crossed ~1B MAUs, and switched to Gemini 3.5 Flash as the base model. AI Mode is **not** the same as AI Overviews — it is a separate conversational tab with deeper reasoning, multi-turn follow-ups, and a citation pattern that frequently diverges from AI Overviews for the same query. Brands must audit AI Mode independently. Practical implication: an AEO program that only tests AI Overviews + ChatGPT + Perplexity now has a measurable blind spot.

**Additional I/O 2026 announcements that change AEO scope** ([source: blog.google/products-and-platforms/products/search/search-io-2026](https://blog.google/products-and-platforms/products/search/search-io-2026/)):

- **AI Overview → AI Mode follow-up flow** is live worldwide (desktop + mobile) — users can ask a follow-up directly from an AI Overview and flow into a conversational AI Mode session. AEO implication: the *first* impression in an AI Overview is now also a gateway to multi-turn citation. Optimize for being the foundational citation, not just the brief snippet.
- **Personal Intelligence in AI Mode** is expanding to ~200 countries and 98 languages, no subscription required, with Gmail / Photos / Calendar connections. AEO implication: AI answers are increasingly personalized — generic brand-search results will be reweighted against the user's own context. Brand schema completeness and entity consistency (NAP, services, hours) matter even more.
- **AI Information Agents** (user-created, monitoring blogs/news/social 24/7) launch for AI Pro & Ultra subscribers in summer 2026. AEO implication: brands that publish structured, dated updates on owned channels will be more legible to user-configured agents than those relying on third-party PR pickup.

**Official Google guidance on AI search optimization** (updated 15 May 2026 — [Google AI Optimization Guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)):

- **No `llms.txt` file is needed.** Google's official position: "You don't need to create new machine readable files, AI text files, markup, or Markdown to appear in generative AI search." Do not waste time generating `llms.txt` for Google AI Features. (Other AI search engines may or may not consume it; current Anthropic / OpenAI / Perplexity public positions are also that they do not require it. Document any client pressure to ship `llms.txt` as a low-priority deliverable with no measurable upside.)
- **No special AI-specific schema is needed.** "Structured data isn't required for generative AI search, and there's no special schema.org markup you need to add." Schema continues to matter for classic SEO and rich results.
- **Eligibility is standard Search.** "To be eligible to be shown in generative AI features on Google Search, a page must be indexed and eligible to be shown in Google Search with a snippet, fulfilling the Search technical requirements."

**Opt-out and AI training controls** ([Google AI Features doc](https://developers.google.com/search/docs/appearance/ai-features)):

- For AI Overviews and AI Mode (inside Google Search): use existing snippet directives — `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`. Robots.txt for Googlebot is the canonical control. **There is no AI-specific robots/meta directive.**
- For Google's *other* AI systems (Gemini app training, Vertex AI grounding outside Search): use the **Google-Extended** user agent in robots.txt. This is a distinct control from Googlebot.
- **NEW (3 June 2026):** Search Console now ships an **opt-out toggle** at the property level — flip it to exclude the site from grounding AI Overviews / AI Mode responses without editing robots.txt. See `/digital-marketing-pro:gsc-ai-performance` for the decision framework on when to use it.

**EU AI Act Article 50 (applicable 2 August 2026)** — for AI-generated marketing content surfaced in EU markets, see `skills/context-engine/eu-code-of-practice.md` for the voluntary Code of Practice (WG1 providers / WG2 deployers) and the C2PA `c2pa.ai-disclosure` assertion path. Compliance is plugin-level and applies to `c2pa-metadata` outputs.

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing AEO/GEO work, gather:

1. **Brand Identity**: Official brand name, key products/services, unique value propositions, and brand positioning
2. **Current AI Footprint**: Ask the user if they have tested how AI platforms currently describe their brand (or offer to audit)
3. **Target Queries**: The questions and topics the brand wants to be cited for in AI-generated answers
4. **Existing Content Assets**: Website URL, blog, knowledge base, Wikipedia presence, schema markup status
5. **Competitive Landscape**: Key competitors who may already have strong AI visibility
6. **Industry Vertical**: Needed to assess YMYL (Your Money Your Life) sensitivity and trust signal requirements

If the user cannot provide all context, proceed with what is available and flag gaps as recommendations.

**Minimum viable context**: Brand name and website URL. Everything else can be inferred or discovered during the audit process.

## Capabilities

- **AI Visibility Audit**: Systematic testing of how a brand appears across the 6 canonical surfaces — Google AI Mode, Google AI Overviews, ChatGPT, Perplexity, Gemini, and Copilot — for target queries (scored with the standard defined in `/digital-marketing-pro:aeo-audit`)
- **Citation Optimization**: Restructuring content to maximize the probability of being cited as a source in AI-generated responses
- **Entity Consistency Audit**: Cross-referencing brand information across Google Knowledge Graph, Wikidata, Wikipedia, Crunchbase, LinkedIn, and industry databases to identify inconsistencies
- **LLM Content Strategy**: Creating content specifically designed to be ingested and accurately represented by language models
- **AI Answer Monitoring Framework**: Setting up systematic tracking of AI mentions and citations over time
- **Structured Data for AI Citation**: Implementing Organization, Product, FAQ, HowTo, and other schema types that improve AI comprehension
- **Knowledge Graph Optimization**: Improving entity representation in structured knowledge bases
- **Topical Authority Mapping**: Identifying content gaps that prevent a brand from being recognized as an authority by AI models
- **AI-First Content Formatting**: Restructuring existing content with clear definitions, factual statements, and citation-worthy snippets
- **Competitive AI Visibility Benchmarking**: Comparing brand AI presence against competitors across platforms

## Process

**Primary Workflow: AI Visibility Audit & Optimization**

1. **Discovery & Baseline**
   - Collect brand details, target queries (10-25 queries), and competitor list
   - Document current schema markup, Knowledge Graph presence, and Wikipedia/Wikidata status
   - Identify the business model to determine which AI platforms matter most
   - Catalog existing authoritative content assets (whitepapers, research, data, expert bios)
   - Assess YMYL classification — brands in health, finance, or legal face higher authority thresholds

2. **AI Platform Testing**
   - For each target query, document how the brand appears (or fails to appear) on:
     - **Google AI Mode** (default conversational surface, Gemini 3.5 Flash backbone — May 2026)
     - Google AI Overviews (classic SERP summary block)
     - ChatGPT (latest model, web-search mode on)
     - Perplexity
     - Gemini (gemini.google.com)
     - Microsoft Copilot
   - Score each result: Cited (direct mention with link), Referenced (mentioned without link), Absent, Misrepresented
   - Capture exact AI-generated text for each query as a baseline

3. **Entity Consistency Check**
   - Audit brand name, founding date, leadership, product descriptions, and key claims across all knowledge sources
   - Flag inconsistencies between sources (e.g., different founding years on Crunchbase vs. Wikipedia)
   - Prioritize fixes by source authority weight

4. **Gap Analysis & Strategy**
   - Identify patterns: Which query types yield citations? Which don't?
   - Map content gaps: What authoritative content is missing that AI models need?
   - Assess structured data gaps: What schema markup is missing or incorrect?
   - Benchmark against competitors who ARE getting cited

5. **Optimization Execution Plan**
   - Prioritized list of content to create or restructure
   - Schema markup implementation plan
   - Knowledge Graph correction/enhancement steps
   - Entity consistency fix checklist
   - Content formatting guidelines for AI-first optimization

6. **Monitoring & Iteration**
   - Define monitoring cadence (weekly for priority queries, monthly for full audit)
   - Set up tracking framework to detect citation changes
   - Establish KPIs: citation rate, accuracy score, query coverage percentage
   - Track competitor citation changes as part of ongoing monitoring
   - Re-test after major content updates or schema implementations to measure impact
   - Log all AI platform model updates that may affect visibility (new model releases, retrieval changes)

**Secondary Workflow: Citation-Optimized Content Creation**

1. Identify a target query cluster where the brand should be cited but currently is not
2. Analyze what sources ARE being cited for those queries — study their content structure, authority signals, and formatting
3. Create or restructure content that surpasses cited sources in:
   - Factual accuracy and specificity (include precise data, dates, numbers)
   - Clear definitional statements (AI models favor content with unambiguous definitions)
   - Structured formatting (clear headings, bullet points, tables that AI can parse)
   - Source credibility signals (author credentials, citations to primary research, organizational authority)
4. Implement supporting schema markup (FAQ, HowTo, Article, Organization as appropriate)
5. Build inbound authority signals (internal links from high-authority pages, external citations)
6. Re-test AI platform responses 2-4 weeks after publication to measure citation pickup

## Reference Files

- `ai-visibility-audit.md` — Step-by-step audit methodology, scoring rubric, and platform-specific testing protocols
- `citation-optimization.md` — Content restructuring techniques, citation-worthy formatting patterns, and source authority building
- `entity-consistency.md` — Cross-platform entity audit checklist, Knowledge Graph optimization, Wikidata editing guidelines
- `llm-content-strategy.md` — AI-first content creation framework, topical authority mapping, and structured data implementation guide

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| AI Visibility Scorecard | Table/Spreadsheet | Query-by-query visibility scores across all AI platforms |
| Entity Consistency Report | Document | All inconsistencies found with correction instructions |
| AEO Content Brief | Document | Content creation/restructuring briefs optimized for AI citation |
| Schema Markup Spec | Code snippets (JSON-LD) | Ready-to-implement structured data markup |
| Monitoring Dashboard Spec | Document | KPIs, tracking methodology, and reporting cadence |
| Competitive AI Visibility Matrix | Table | Side-by-side comparison of brand vs. competitor AI visibility |
| LLM Content Strategy | Document | 90-day content plan focused on building AI authority |

## Edge Cases

### Brand with Negative AI Perception
- **Situation**: AI platforms are generating inaccurate or negative information about the brand
- **Approach**: Prioritize entity consistency fixes and authoritative source correction before any content optimization. Create factual correction content on high-authority owned properties. Do NOT attempt to manipulate AI outputs directly — focus on fixing the underlying source material. Flag potential reputation management needs to the user.

### New Brand with Zero AI Visibility
- **Situation**: Brand does not appear in any AI-generated answers
- **Approach**: Start with foundation-building — create a Wikipedia-worthy web presence (not necessarily Wikipedia itself), establish Wikidata entry, implement comprehensive schema markup, and build topical authority content. Set realistic timelines: AI model knowledge has lag times (weeks to months depending on platform).

### Common-Word Brand Names
- **Situation**: Brand name is a common word (e.g., "Apple," "Slack," "Monday")
- **Approach**: Entity disambiguation is critical. Emphasize co-occurring terms, use full official names in structured data, ensure Knowledge Graph correctly disambiguates, and optimize content with entity-clarifying context. Always include industry/product qualifiers in target queries.

### Multi-Brand Companies
- **Situation**: Parent company with multiple sub-brands needing separate AI identities
- **Approach**: Audit each brand entity separately. Ensure clear parent-child relationships in structured data. Avoid cannibalization where sub-brands compete with each other in AI answers. Create distinct topical authority for each brand.

### Regional AI Engines (Baidu, Yandex)
- **Situation**: User needs visibility on non-Western AI platforms
- **Approach**: Acknowledge that optimization strategies differ significantly for Baidu (China) and Yandex (Russia). These require localized content, platform-specific structured data standards, and different knowledge bases. Recommend specialized regional expertise if the request goes deep. Provide general framework but flag limitations in specific platform knowledge.

### YMYL Brands (Health, Finance, Legal)
- **Situation**: Brands in Your Money Your Life categories face elevated trust requirements from AI platforms
- **Approach**: AI platforms apply stricter source quality thresholds for YMYL topics. Prioritize: (1) Expert authorship with verifiable credentials on all content. (2) Citations to primary research, government sources, and peer-reviewed studies. (3) Medical/legal/financial review disclosures. (4) Comprehensive E-E-A-T signals (link to Digital PR module for authority building). (5) Schema markup that explicitly declares author qualifications and organizational credentials. Test AI outputs carefully for accuracy — misrepresentation in YMYL categories carries higher reputational risk.

### Rapidly Evolving AI Landscape
- **Situation**: AI platforms frequently update their models, retrieval methods, and citation behavior
- **Approach**: Treat all AEO/GEO strategies as living processes, not one-time optimizations. Build monitoring into every engagement. When a major platform update occurs (new model release, retrieval system change, AI Overview format change), re-run the visibility audit for priority queries. Document observed behavior changes and update the workflow accordingly. Maintain a changelog of platform updates and their observed impact on brand visibility.

## Tips & caveats

- **Google's official position (15 May 2026):** no `llms.txt`, no AI-specific schema, no separate AI eligibility gate. Don't manufacture work around fictional ranking factors — schema + entity consistency + citation-worthy formatting are what works.
- **AI Mode citation patterns frequently differ from AI Overviews** on the same query (internal observation, 05/2026 — the "40-60%" figure is a rough estimate, re-verify against your own probe set). Audit and optimise for both, treating them as distinct surfaces.
- **Entity consistency across Knowledge Graph, Wikidata, Wikipedia, LinkedIn, Crunchbase is the single highest-leverage AEO investment** — more impactful than schema tweaks.
- **AI citations are stickier than blue-link rankings** but slower to win. Expect 3-6 months of consistent work before measurable shift.
- **Don't try to "trick" AI into citing you** with stuffed content or fake authority signals. AI platforms detect and demote this faster than traditional search.
- **`Google-Extended` (robots.txt) opts out of Google's *other* AI systems** (Gemini training, Vertex grounding) — distinct from the in-Search-Console toggle for AI Overviews/AI Mode (rolled out 3 Jun 2026 via `/digital-marketing-pro:gsc-ai-performance`).
- **EU markets** require Article 50 disclosure on AI-generated content (applicable 2 Aug 2026) — see `skills/context-engine/eu-code-of-practice.md`.

## Related Skills

- **Content Engine** — For creating and optimizing the actual content that drives AI citations
- **Analytics & Insights** — For measuring AI visibility performance and tracking citation changes over time
- **Digital PR & Authority** — For building the E-E-A-T signals and earned media that strengthen AI trust in a brand
- **Audience Intelligence** — For understanding which queries your target audience is asking AI platforms
