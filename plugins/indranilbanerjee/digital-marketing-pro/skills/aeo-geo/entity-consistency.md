# Entity Consistency — Cross-Platform Audit & Optimization

## Overview

Ensuring brand information is consistent across all knowledge sources that AI models reference. Inconsistencies confuse AI platforms and reduce citation confidence.

**Why this matters more for Google AI Mode (mid-2026):** AI Mode — Google's conversational search surface, default for opted-in users since I/O on 19 May 2026 — adds "Personal Intelligence" that reweights answers against each user's own context (Gmail / Calendar / Photos connections). That personalization runs on top of the same entity graph, so gaps or contradictions in your NAP, services, hours, founding date, and leadership degrade AI Mode answers even harder than they degrade AI Overviews. Entity completeness and consistency is the highest-leverage AI Mode investment. AI Mode is a **distinct surface** from AI Overviews — verify entity representation in both.

---

## Entity Audit Checklist

Check the following data points across all platforms:

| Data Point | Google KG | Wikidata | Wikipedia | Crunchbase | LinkedIn | Website | Industry DBs |
|-----------|-----------|----------|-----------|------------|----------|---------|--------------|
| Brand name (exact) | | | | | | | |
| Founding date | | | | | | | |
| Founders/CEO | | | | | | | |
| Headquarters | | | | | | | |
| Industry category | | | | | | | |
| Employee count range | | | | | | | |
| Product descriptions | | | | | | | |
| Revenue range | | | | | | | |
| Key differentiators | | | | | | | |
| Website URL | | | | | | | |
| Social profiles | | | | | | | |

**Mark each cell**: Correct / Incorrect / Missing / Outdated

---

## Common Inconsistency Types

| Type | Example | Impact | Fix Priority |
|------|---------|--------|-------------|
| **Name variation** | "Brand Inc" vs "Brand" vs "Brand Corp" | High — confuses entity resolution | Critical |
| **Date mismatch** | Founded 2019 on Crunchbase, 2020 on LinkedIn | Medium — undermines trust | High |
| **Description conflict** | "AI platform" on one source, "SaaS tool" on another | High — category confusion | High |
| **Leadership outdated** | Former CEO listed as current | Medium — signals stale data | Medium |
| **Address discrepancy** | Different cities across sources | Medium — affects local/geo AI | Medium |
| **Missing entity** | No Wikidata entry at all | High — reduces AI discovery | Critical |

---

## Knowledge Graph Optimization

### Google Knowledge Graph

1. **Claim your Knowledge Panel** via Google Search Console entity verification
2. **Suggest edits** for incorrect information using the "Claim this knowledge panel" flow
3. **Strengthen signals**: Ensure your website, Wikipedia, Wikidata, and authority sources all agree
4. **Use Organization schema** on your homepage with `sameAs` links to all official profiles
5. **Monitor changes**: Set up alerts for Knowledge Panel modifications

### Knowledge Graph Triggers

Google builds Knowledge Graph entries from:
- Wikipedia/Wikidata (highest weight)
- Schema markup on official website
- Crunchbase, LinkedIn, and other authority databases
- News mentions and citations
- Google My Business (for local entities)

---

## Wikidata Editing Guidelines

### Notability Requirements

Wikidata is more permissive than Wikipedia. An entity can have a Wikidata entry if:
- It has been covered in at least one independent reliable source
- It has a unique identifier in at least one external database
- It represents a notable organization, person, product, or concept

### Creating a Wikidata Entry

1. Go to wikidata.org → Create new item
2. Set label (brand name), description (concise identifier), and aliases
3. Add properties:
   - P31 (instance of): Q4830453 (business enterprise) or appropriate type
   - P856 (official website)
   - P571 (inception date)
   - P112 (founded by)
   - P159 (headquarters location)
   - P452 (industry)
   - Add social media identifiers (P2002 Twitter, P4003 Facebook, P4264 LinkedIn)
4. Add references for every claim (link to source)
5. Add `sameAs` equivalent properties linking to other databases

### Editing Rules

- Every claim MUST have a reference (URL to a reliable source)
- Do NOT add promotional content or subjective claims
- Use the talk page for disputed edits
- Disclose conflicts of interest (if editing your own company's entry)
- Focus on verifiable, factual properties only

---

## Brand Name Disambiguation

For brands with common-word names:

1. **Use full official name** in all structured data: "Monday.com" not "Monday"
2. **Add entity type qualifiers**: "Slack (software)" pattern in descriptions
3. **Build co-occurrence signals**: Always mention brand + product category together
4. **Wikidata disambiguation**: Add P1889 (different from) property linking to other entities with similar names
5. **Schema markup**: Use `disambiguatingDescription` property
6. **Content optimization**: Include "[Brand] [category] [description]" in title tags and headers

---

## Entity Monitoring Schedule

| Task | Frequency | Action |
|------|-----------|--------|
| Google Knowledge Panel check | Weekly | Screenshot and compare to previous |
| AI Mode + AI Overviews brand-fact spot check | Weekly | Ask "What is [Brand]?" in both surfaces; confirm NAP/leadership/description match the profile. Reconcile impressions via `/digital-marketing-pro:gsc-ai-performance` |
| Wikidata review | Monthly | Check for unauthorized edits |
| Cross-platform consistency scan | Quarterly | Full audit checklist across all platforms |
| Crunchbase/LinkedIn update | After any change | Update immediately when info changes |
| Wikipedia monitoring | Set alerts | Watch for article edits via watchlist |
| Schema markup validation | Monthly | Test via Google Rich Results Test |
