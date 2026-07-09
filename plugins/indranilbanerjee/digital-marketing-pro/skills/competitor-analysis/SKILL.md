---
name: competitor-analysis
description: "Run competitive analysis. Use when: content, SEO, paid ads, social, AI visibility, pricing, positioning comparison."
argument-hint: "[competitor names]"
---

# /digital-marketing-pro:competitor-analysis

## Purpose

Deliver a comprehensive competitive intelligence report across all major marketing dimensions. Identify competitor strengths, weaknesses, strategies, and gaps the brand can exploit.

## Input Required

The user must provide (or will be prompted for):

- **Competitors**: 2-5 competitor names and/or URLs
- **Analysis scope**: Full analysis or specific dimensions (SEO, content, ads, social, pricing)
- **Key battleground keywords**: Terms where the brand competes head-to-head
- **Industry/category**: For contextual benchmarking

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Content analysis**: Content types, publishing frequency, top-performing content, content gaps, topic authority
3. **SEO analysis**: Domain authority, keyword overlap, ranking gaps, backlink comparison, technical health
4. **Paid advertising**: Ad copy themes, landing page strategies, estimated spend, platform focus
5. **Social media**: Platform presence, follower growth, engagement rates, content mix, posting cadence
6. **AI visibility**: How competitors appear in AI answer engines versus the brand
7. **Pricing and positioning**: Pricing models, value proposition, messaging frameworks, market positioning
8. Synthesize findings into strategic opportunities and threats
9. Generate actionable recommendations for competitive advantage

## Output

A structured competitive analysis containing:

- Competitor overview matrix with key metrics per competitor
- Content strategy comparison with gap analysis
- SEO competitive landscape with keyword and link opportunities
- Paid media intelligence with creative and targeting insights
- Social media benchmarking with engagement analysis
- AI visibility comparison across platforms
- Pricing and positioning map
- SWOT summary per competitor
- Strategic recommendations prioritized by opportunity size

## Agents Used

- **competitive-intel** — All competitive dimensions, benchmarking, gap analysis, and strategic recommendations
