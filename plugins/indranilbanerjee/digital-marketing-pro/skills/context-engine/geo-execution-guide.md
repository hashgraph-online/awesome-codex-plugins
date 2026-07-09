# GEO Execution Guide — Generative Engine Optimization

Reference knowledge for AI visibility monitoring, optimization execution, entity management, citation building, and narrative control. Use this when assessing or improving brand visibility across AI-powered search and chat interfaces.

---

## 1. AI Engine Query Methodology

### Systematic Visibility Testing

**Step 1 — Query Formulation**: Build a query matrix from target keyword clusters:

| Intent Type | Query Pattern Examples | Purpose |
|---|---|---|
| **Informational** | "What is [topic]?", "How does [product category] work?", "Best practices for [activity]" | Tests whether AI engines reference your content as an authoritative source |
| **Navigational** | "[Brand name]", "[Brand name] reviews", "[Brand name] vs [competitor]" | Tests brand recognition and accuracy of brand information |
| **Transactional** | "Best [product category] for [use case]", "Top [product category] [year]", "[Product category] pricing comparison" | Tests whether AI engines recommend your product in purchase-intent queries |
| **Comparison** | "[Brand] vs [Competitor]", "Alternative to [Competitor]", "[Product category] comparison" | Tests competitive positioning in head-to-head AI responses |
| **Problem-solution** | "How to solve [pain point]", "[Pain point] solutions for [segment]" | Tests whether AI connects your brand to the problems you solve |

**Step 2 — Cross-Platform Testing**: Execute each query across all major AI engines:

| Platform | Access Method | Notes |
|---|---|---|
| **ChatGPT** (OpenAI) | Web UI or API (`/v1/chat/completions`) | Test both GPT-4o and GPT-4o-mini. Web browsing mode vs. training data mode yield different results |
| **Perplexity** | Web UI or API | Always cites sources with links. Pro mode uses multiple search passes. Test both default and Pro |
| **Google AI Overviews** | Google Search (standard query) | Appears above organic results for qualifying queries. Not triggered for all queries. Test from incognito/logged-out |
| **Gemini** (Google) | Web UI or API | Integrates Google Knowledge Graph data. Test with and without Google Search grounding |
| **Microsoft Copilot** | Web UI or Bing Chat | Bing-powered search grounding. Tests Bing index visibility. Cites sources |
| **Claude** (Anthropic) | Web UI or API | Training data based (no web browsing by default). Tests whether brand is in training corpus |
| **Meta AI** | WhatsApp, Instagram, Facebook, web | Llama-based with real-time search integration on some platforms |

**Step 3 — Response Recording**: For each query x platform combination, capture:
- Full AI response text
- Sources cited (URLs, brand names)
- Position of your brand mention (first mention, middle, end, absent)
- Sentiment of mention (positive, neutral, negative, inaccurate)
- Competitors mentioned alongside
- Timestamp (AI responses can change day to day)

---

## 2. Scoring Rubric

### Visibility Score Per Query Per Platform

| Outcome | Score | Definition |
|---|---|---|
| **Cited with link** | 10 | Brand mentioned by name AND a link to your domain is provided as a source |
| **Cited without link** | 8 | Brand mentioned by name with attribution but no clickable link to your domain |
| **Mentioned by brand name** | 7 | Brand explicitly named in the response but not as a cited source |
| **Product/feature referenced** | 5 | Your specific product or unique feature described without brand name attribution |
| **Concept referenced** | 3 | Your content's concepts or data used in the response without any attribution |
| **Absent** | 0 | Brand, product, and content not referenced in any way |
| **Misrepresented** | -5 | Brand mentioned with factually incorrect information, outdated data, or negative framing that mischaracterizes your offering |

### Aggregate Scoring

- **Query score** = Average score across all platforms for a single query
- **Platform score** = Average score across all queries for a single platform
- **Overall GEO score** = Weighted average across all queries and platforms (weight platforms by their traffic share to your site or industry usage data)
- **Competitive GEO score** = Your overall score / (your score + sum of competitor scores) x 100 = GEO share of voice percentage

### Score Interpretation

| Score Range | Assessment | Action Required |
|---|---|---|
| 8.0-10.0 | Strong AI visibility — consistently cited as authoritative source | Maintain. Monitor for degradation. Expand query coverage |
| 5.0-7.9 | Moderate visibility — recognized but not consistently cited | Strengthen entity signals, increase citation-worthy content |
| 2.0-4.9 | Weak visibility — concepts used but brand not attributed | Major entity optimization needed. Focus on structured data and authoritative backlinks |
| 0.0-1.9 | Minimal visibility — largely absent from AI responses | Foundational work required. Build domain authority, create definitive content, establish entity presence |
| Below 0 | Negative visibility — misrepresented in AI responses | Crisis-level. Prioritize correction of inaccurate information at source |

---

## 3. Per-Platform Optimization Strategies

### ChatGPT Optimization

- **Training data bias**: Favors Wikipedia, Reddit, Stack Overflow, high-authority domains (DA 70+), academic sources, government sites
- **Web browsing mode**: When enabled, functions like a search engine. Optimize for standard SEO best practices — top-ranking content gets cited
- **Optimization priorities**:
  1. Ensure accurate Wikipedia presence (brand page or mention in category pages)
  2. Maintain active, helpful Reddit presence in relevant subreddits (authentic participation, not self-promotion)
  3. Strengthen E-E-A-T signals: author bios with credentials, expert quotes, original research citations
  4. Structure content with clear definitions, step-by-step instructions, and data tables that AI can extract

### Perplexity Optimization

- **Source selection**: Explicitly lists and links sources. Heavily favors content that ranks in top 10 search results
- **Citation triggers**: Clear, extractable answers in content. Structured data (tables, lists, definitions). FAQ format. Statistics with source attribution
- **Optimization priorities**:
  1. Rank in top 10 for target queries (traditional SEO is the foundation)
  2. Format content for extractability: concise answer paragraphs, definition-style openings, data tables
  3. Include unique data, statistics, and research that Perplexity cannot find elsewhere
  4. Maintain accurate, up-to-date content (Perplexity uses live search; outdated content loses citations)

### Google AI Overviews Optimization

- **Source selection**: Draws primarily from top-ranking organic content. Cross-references multiple sources for synthesis
- **Optimization priorities**:
  1. Traditional SEO alignment — AI Overviews pull from pages that rank organically
  2. Structured data (FAQ, HowTo, Product schema) increases chance of inclusion
  3. Content that directly answers the query in the first 1-2 paragraphs
  4. Authoritative backlink profile signals trustworthiness for inclusion
  5. Content freshness matters — regularly updated pages preferred for topics with temporal relevance

### Gemini Optimization

- **Data sources**: Google Knowledge Graph, Google Search, Google Business Profile, structured data across the web
- **Optimization priorities**:
  1. Google Knowledge Panel: Claim and optimize. Ensure all facts are correct
  2. Google Business Profile: Complete all fields. Regular posts. High review rating
  3. Structured data: Organization, Product, FAQ schema — feeds directly into Knowledge Graph
  4. YouTube presence: Gemini can reference YouTube content. Optimize video titles, descriptions, and transcripts

### Microsoft Copilot / Bing Chat Optimization

- **Powered by**: Bing search index. Content must be indexed in Bing (not just Google)
- **Optimization priorities**:
  1. Submit site to Bing Webmaster Tools. Verify indexing
  2. Schema markup (Bing is aggressive about using structured data)
  3. Authoritative backlinks from domains Bing trusts (Microsoft properties, LinkedIn, educational institutions)
  4. Social signals: Bing reportedly factors social engagement into rankings more than Google

---

## 4. Entity Optimization Workflow

### Google Knowledge Panel

1. **Claim panel**: Search for brand name. If panel appears, click "Claim this knowledge panel." Verify via Google Search Console, YouTube, or other official profiles
2. **Edit panel**: Once claimed, suggest edits to: title, subtitle, description, social profiles, logo, website, founding date. Edits are reviewed by Google (24-72h)
3. **If no panel exists**: Build entity signals — consistent NAP across directories, structured Organization schema on website, Wikidata entry, active Google Business Profile, Wikipedia mention

### Wikidata Entry

- **Create or edit**: `https://www.wikidata.org/`
- **Key properties to set**:
  - `P31` (instance of): company, software, product — appropriate entity type
  - `P856` (official website): primary domain URL
  - `P553`/`P554` (social media): handles for each platform
  - `P571` (inception): founding date
  - `P452` (industry): relevant industry classification
  - `P159` (headquarters location): city, country
  - `P169` (CEO): link to person entity
  - `P1056` (product/service): what the entity offers
- **Impact**: Wikidata feeds into Google Knowledge Graph, Alexa, Siri, and multiple AI training datasets. High-leverage action for entity recognition

### Wikipedia Presence

- **Notability assessment**: Does the brand meet Wikipedia's notability guidelines for organizations? Requires significant coverage in reliable, independent sources (not press releases or self-published content)
- **If notable**: Do NOT create or edit the page yourself (conflict of interest). Instead:
  1. Gather 5+ independent reliable sources (major publications, industry reports, academic citations)
  2. Use Wikipedia's "Request an article" process or hire a Wikipedia-compliant editor
  3. Ensure the article is neutral, well-sourced, and factual
- **If not yet notable**: Focus on earning coverage in reliable independent sources first. Every major media mention, industry award, or research citation builds toward notability
- **Monitoring**: Watch the Wikipedia page for vandalism or inaccurate edits. Set up Wikipedia watchlist alerts

### Directory Consistency Audit

- **Audit scope**: Check brand information across the top 50 directories, data aggregators, and industry-specific listings
- **Data points to verify**: Business name (exact match), address, phone, website URL, description, category, logo, social links
- **Common issues**: Outdated addresses, old phone numbers, inconsistent brand name formatting (Inc. vs LLC vs no suffix), HTTP vs HTTPS URLs
- **Resolution**: Update each listing manually or via data aggregator services (Data Axle, Neustar Localeze, Foursquare). Priority: Google Business Profile > Apple Maps > Bing Places > Yelp > industry-specific directories

---

## 5. Narrative Control Strategies

### Authoritative Content Creation

- **Original research**: Conduct surveys, analyze proprietary data, publish findings with methodology. AI engines heavily favor unique data they cannot find elsewhere
- **Expert roundups**: Aggregate expert opinions on industry topics. Multiple expert names + credentials boost E-E-A-T signals
- **Definitive guides**: Comprehensive, 3,000+ word guides that become the reference resource for a topic. Update quarterly to maintain freshness
- **Data studies**: Analyze publicly available data with unique methodology. Present findings with charts, tables, and downloadable datasets
- **Statistical content**: "X% of [professionals] report [finding]" — AI engines love citing specific statistics with source attribution

### Citation-Worthy Content Formatting

| Format | Why AI Cites It | Example |
|---|---|---|
| **Definition paragraph** | AI engines extract definitions for "what is" queries | "Content marketing is a strategic approach focused on creating valuable, relevant content to attract a clearly defined audience." |
| **Numbered lists** | Extractable for "how to" and "steps to" queries | "Step 1: Audit existing content. Step 2: Identify gaps..." |
| **Data tables** | Structured data is easy for AI to parse and cite | Comparison tables, pricing tables, benchmark data tables |
| **Statistics with attribution** | AI needs sourced data for factual claims | "According to [Brand]'s 2026 State of Marketing report, 73% of marketers..." |
| **FAQ pairs** | Direct question-answer format maps to user queries | "Q: How long does SEO take? A: Most SEO campaigns show measurable results within 3-6 months..." |

### Building Citation Signals

- **Be referenced by authoritative sites**: Guest contributions, expert commentary in industry publications, data licensing, speaking engagements cited in event recaps
- **Maintain accurate entity data**: Wikidata, Knowledge Panel, directory listings — inconsistency reduces AI confidence in citing your brand
- **Interlink content strategically**: Strong internal linking between topically related content pages helps AI understand your topical authority
- **Publish on platforms AI engines favor**: Medium (high domain authority), LinkedIn articles (professional authority), industry publications (vertical authority)

---

## 6. Monitoring Cadence and Competitive Benchmarking

### Weekly Priority Monitoring

- **Queries**: Brand name queries, top 5 product/service queries, top 3 comparison queries
- **Platforms**: ChatGPT, Perplexity, Google AI Overviews (highest traffic AI surfaces)
- **Action**: Record scores. Compare to previous week. Flag any score drops >2 points or new misrepresentations

### Monthly Full Audit

- **Queries**: All target queries from query matrix (50-200 queries depending on brand scope)
- **Platforms**: All 6+ AI engines
- **Deliverable**: Monthly GEO scorecard with per-platform scores, trend arrows, competitive comparison, and recommended actions
- **Time investment**: 4-8 hours per audit (automate query execution where possible; manual review of responses)

### Quarterly Competitive Benchmark

- **Scope**: Run full query matrix for your brand AND top 3-5 competitors across all platforms
- **Deliverable**: Competitive GEO report with share of voice, platform-by-platform comparison, trend analysis, and strategic recommendations
- **Key questions answered**: Who is gaining AI visibility? Which platforms favor which competitors? Where are you losing citations to competitors?

---

## 7. Narrative Drift Detection and Correction

### Detection Process

1. **Capture AI responses** about your brand for navigational queries ("What is [Brand]?", "[Brand] reviews", "Tell me about [Brand]")
2. **Compare to desired positioning**: Does the AI response match your brand's positioning statement, key value propositions, and target audience?
3. **Flag discrepancies**:
   - **Outdated information**: Old pricing, discontinued products, former leadership, previous company name
   - **Inaccurate claims**: Wrong feature descriptions, incorrect market position, fabricated statistics
   - **Negative framing**: Disproportionate emphasis on negative reviews, old controversies, competitor advantages
   - **Missing key information**: Core value propositions absent, key products not mentioned, target market misidentified

### Correction Strategies

| Issue Type | Correction Approach | Timeline |
|---|---|---|
| **Outdated info** | Update source content (website, Wikipedia, directories). Ensure structured data reflects current information | 1-2 weeks for AI engines to re-index |
| **Inaccurate claims** | Identify source of inaccuracy. Update or request correction. Create authoritative counter-content with correct information | 2-4 weeks for propagation |
| **Negative framing** | Publish positive authoritative content at scale. Earn positive coverage from independent sources. Do not attempt to suppress — overwhelm with positive signal | 1-3 months for sentiment shift |
| **Missing information** | Create dedicated pages for missing topics. Add structured data. Build topical authority through content clusters | 2-4 weeks for initial pickup |

---

## 8. Dark Funnel and AI Attribution

### AI Visibility as Hidden Buyer Journey Stage

- **Reality**: Buyers increasingly query AI chatbots during research. These queries are invisible in traditional analytics — no referral traffic, no UTM parameters, no click-through tracking
- **Impact**: AI-influenced decisions show up as "direct" traffic, branded search, or "no referral" in analytics. True AI influence is underreported
- **Proxy measurement signals**:
  - Branded search volume increase after GEO improvements (correlation, not causation — but directionally useful)
  - Survey data: "How did you first hear about us?" with AI chatbot as an option
  - New visitor branded search patterns: users who arrive via branded search but have no prior cookie history (possible AI-to-search pathway)
  - Correlation analysis: map GEO score improvements to branded search volume and direct traffic changes with 2-4 week lag

### Attribution Framework for AI Visibility

Since direct attribution is not possible, use a contribution model:

1. **Track GEO scores over time** (independent variable)
2. **Track branded search volume, direct traffic, and demo/trial requests** (dependent variables)
3. **Control for other marketing activity** (ad spend, PR, events, content publishing)
4. **Calculate correlation** between GEO score changes and downstream metrics with appropriate lag (2-4 weeks)
5. **Report as "AI visibility contribution"** — directional, not precise, but establishes value of GEO investment
