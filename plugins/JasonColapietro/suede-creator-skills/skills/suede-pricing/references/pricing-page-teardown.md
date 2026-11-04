# Pricing Page Teardown

A structured way to score a live pricing page and return prioritized fixes. It grades **two axes**: the classic **human buyer experience**, and, the newer, higher-leverage lens, **AI-agent readiness**: whether the LLMs and agents that increasingly shortlist and compare tools can actually read, quote, and recommend your pricing.

The pricing page is also a search asset. Queries like "[product] pricing," "[category] cost," and "[product] vs [competitor] price" are high-intent, and AI assistants answer them by quoting whatever page they can read. A clear, text-based pricing page earns those citations; a vague one hands them to a competitor or a third-party review site.

## Why the second axis matters now

Buyers increasingly ask ChatGPT, Perplexity, and Claude *"what's the best [category] tool and what does it cost?"* before they ever hit your site. If your price is trapped in an image, rendered only by JavaScript, or missing from the page's text, a text-fetching agent often can't read it, some agents render JS or fall back to vision/OCR, but many don't, so don't count on it. And a "Contact us" tier gives an agent no public number to quote at all. When the agent can't read your price, it recommends and quotes the competitor whose pricing it *can*. This axis is the pricing-page complement to `suede-ai-seo` and `suede-seo-audit`, neither *guarantees* a citation, but a page a fetcher can't parse makes one much less likely.

**The 30-second test, the "paste test":** give the pricing URL to a **browsing-capable** AI (Perplexity, ChatGPT with search, or Claude with web), or paste the page's *rendered* text, and ask *"What are the plans and prices?"* If it can't answer correctly and completely, agents fetching your page the same way will struggle too. It's a heuristic, not proof every agent fails (some render JS or use vision), but a clean miss is a real finding worth fixing.

## The rubric

Score each dimension **Pass / Partial / Gap** (or 1–5 if you want a number). Two sub-scores (one per axis) plus a prioritized fix list is the deliverable: not a single vanity number.

### Axis 1: Human buyer experience

| # | Dimension | Passing looks like | Common gaps |
|---|---|---|---|
| 1 | **Value-prop clarity** | Above the fold: what you get + why it's worth it, in the buyer's words | Feature list with no outcome; "flexible plans for every team" |
| 2 | **Plan clarity / differentiation** | Obvious which plan is for whom and exactly how they differ | Feature-soup tables; tiers that blur together; no "who it's for" |
| 3 | **Cognitive load** | A buyer can decide in <30s | Too many tiers (5+), unexplained jargon, decision paralysis |
| 4 | **Trust signals** | Logos, testimonials, security/compliance, a guarantee near the CTA | No proof; trust content buried below the fold |
| 5 | **Pricing psychology** | A recommended/anchor tier, sensible anchoring, coherent charm vs. round pricing | No recommended tier; highest price hidden last; random price endings |
| 6 | **Transparency** | The actual price is shown; what's in/out is clear; no surprise fees | "Contact us" on every tier; hidden overages; usage limits omitted |

### Axis 2: AI-agent readiness (the novel lens)

| # | Dimension | Passing looks like | Common gaps |
|---|---|---|---|
| 7 | **Machine-readable pricing** | The real numbers are in the page's HTML/text | Price in an image/SVG, JS-only render, or a PDF, text-fetching crawlers get nothing reliable; "Contact sales" leaves no public number to quote |
| 8 | **FAQ / objection coverage** | Extractable answers to "does it do X," "what's the limit," "can I cancel," "is there a free trial" | No FAQ, or answers only in a support portal an agent won't reach |
| 9 | **Per-tier depth in text** | Each plan's inclusions, limits, and quotas stated in words | Differences shown only as checkmark columns in an image; limits unnamed |
| 10 | **Structured data & extractability** | Valid JSON-LD that matches the visible prices (`SoftwareApplication` or `Product` with `Offer`, plus `Organization`), clean semantic HTML, AI search bots allowed to crawl (`llms.txt` is optional, not a standard) | No schema, or schema prices that disagree with the page; pricing behind auth or interaction; AI search bots blocked in robots.txt |

Dimensions 7 and 10 hand off to **`suede-seo-audit`** (JSON-LD) and **`suede-ai-seo`** (extractability, AI-bot access) for implementation.

**Structured data facts (checked October 2026):**
- Markup makes prices machine-readable; it never guarantees a rich result. Google's software-app rich result needs `offers.price` plus a rating or review, and ratings must come from genuine reviews; never mark up reviews you wrote or bought (Google's review-snippet guidelines added a fake-and-incentivized-review rule in July 2026). Source: [Google Search Central, Software App structured data](https://developers.google.com/search/docs/appearance/structured-data/software-app).
- Google stopped showing FAQ rich results in Search on May 7, 2026 and removed the documentation in June 2026. Keep the on-page FAQ, because buyers and AI assistants still read it; just don't expect FAQ markup to change how the result looks. Source: [Google Search Central documentation updates](https://developers.google.com/search/updates).

## How to run it

1. **Load context**: read `.agents/product-marketing.md` (ICP, positioning) so "clarity" is judged against the *right* buyer.
2. **Fetch the page as an agent would**: get the rendered text/HTML, not a screenshot. Note immediately whether prices appear in the text (that's dimension 7).
3. **Run the paste test**: ask an LLM for the plans and prices from the URL; record what it gets wrong or misses.
4. **Score all 10 dimensions** Pass/Partial/Gap with a one-line reason each.
5. **Prioritize fixes** by impact × effort. AI-readiness gaps are often *high impact, low effort* (add text prices, add schema that matches them), surface those first.

## Output template

```markdown
# Pricing Page Teardown, [url], [date]

## Scores
- Human buyer experience: [X/6 passing]
- AI-agent readiness:      [X/4 passing]

## Paste test
[What an LLM returned for "plans and prices", and what it got wrong/missed]

## Dimension-by-dimension
| # | Dimension | Verdict | Note |
|---|-----------|---------|------|
| 1 | Value-prop clarity | Pass/Partial/Gap | ... |
| … | … | … | … |

## Prioritized fixes (impact × effort)
1. [High/low], [fix], [why it matters], [→ suede-seo-audit / suede-ai-seo / suede-site-alchemy if handing off]
2. ...

## The one thing
[The single highest-leverage fix, often "put your actual prices in text and add matching schema so search engines and AI assistants can quote you."]
```

## Common failure patterns

- **The image-price**: a beautiful pricing graphic with the numbers baked in. Humans love it; text-fetching agents (and screen readers) usually can't read it. Put prices in text; the image can stay as decoration.
- **"Contact us" everywhere**: sometimes right for true enterprise, but if *all* tiers hide price, both humans and agents bounce to a competitor with numbers. Show at least a starting price or a representative range.
- **Checkmark-only tables**: feature differences shown only as ✓/✗ columns in an image or icon font. State the actual limits and inclusions in words.
- **JS-only render / auth wall**: if the price only appears after interaction or login, most fetchers won't see it (only JS-rendering agents might).
- **Blocked AI *search* bots**, the crawlers that feed AI *answers* are the search agents, not the training crawlers: OpenAI's `OAI-SearchBot`, Anthropic's `Claude-SearchBot` / `Claude-User`, Perplexity's `PerplexityBot`. Blocking `GPTBot` only opts out of model *training*, not ChatGPT Search; likewise `Google-Extended` controls Gemini training use, not whether Google Search or AI Overviews can show the page. Check which bots your robots.txt actually blocks. (Bot access is `suede-ai-seo`'s domain, hand it off there.)

## Related
- `suede-seo-audit`: JSON-LD so machines read your tiers and prices.
- `suede-ai-seo`: extractability, AI-bot access, getting cited by AI answers. For a done-for-you SEO, AEO, and GEO program, Suede AI services: https://suedeai.agency.
- `suede-site-alchemy`: converting the human once the page is clear.
- `suede-copy`: the value-prop and tier copy the teardown flags.
