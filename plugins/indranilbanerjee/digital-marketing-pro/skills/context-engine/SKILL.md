---
name: context-engine
description: "Load brand context for marketing tasks. Use when: setting up brands, switching context, or needing industry benchmarks."
argument-hint: "[brand-slug]"
---

# Context Engine — Shared Marketing Intelligence

## When to Use This Skill

- User is setting up a new brand or project for marketing
- User switches between brands/clients (agency use case)
- Any other marketing skill needs brand context, industry data, compliance rules, or platform specs
- User asks about industry benchmarks, platform requirements, or regulatory compliance

## Required Context

This skill loads and manages:
1. **Brand Profile** — identity, voice, audiences, competitors, goals (from `~/.claude-marketing/brands/`)
2. **Industry Profiles** — benchmarks, KPIs, channel effectiveness per industry (see `industry-profiles.md`)
3. **Compliance Rules** — geographic privacy laws + industry regulations (see `compliance-rules.md`)
4. **Platform Specs** — character limits, image sizes, algorithm signals per platform (see `platform-specs.md`)
5. **Scoring Rubrics** — standardized evaluation criteria for all content types (see `scoring-rubrics.md`)

## Brand Profile Management

### Loading a Brand

1. Check `~/.claude-marketing/brands/_active-brand.json` for the currently active brand
2. If active brand exists, load `~/.claude-marketing/brands/{slug}/profile.json`
3. If no active brand, prompt: "No active brand configured. Run /digital-marketing-pro:brand-setup to create one, or tell me about your brand and I'll help set it up."

### Brand Profile Schema

```json
{
  "brand_name": "",
  "brand_slug": "",
  "created_at": "",
  "updated_at": "",
  "schema_version": "1.0.0",
  "identity": {
    "tagline": "",
    "mission": "",
    "vision": "",
    "values": [],
    "unique_selling_proposition": "",
    "positioning_statement": "",
    "elevator_pitch": ""
  },
  "business_model": {
    "type": "",
    "revenue_model": "",
    "price_range": "",
    "sales_cycle_length": "",
    "average_deal_size": "",
    "customer_lifetime_value": ""
  },
  "industry": {
    "primary": "",
    "secondary": [],
    "regulated": false,
    "regulation_codes": [],
    "compliance_notes": ""
  },
  "target_markets": [],
  "brand_voice": {
    "formality": 5,
    "energy": 5,
    "humor": 3,
    "authority": 5,
    "personality_traits": [],
    "tone_keywords": [],
    "avoid_words": [],
    "prefer_words": [],
    "this_not_that": [],
    "sample_content": []
  },
  "channels": {
    "active": [],
    "primary": "",
    "handles": {}
  },
  "competitors": [],
  "goals": {
    "primary_objective": "",
    "kpis": [],
    "budget_range": "",
    "team_size": ""
  }
}
```

### Switching Brands

When user says "switch to [brand name]":
1. Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" --switch-brand SLUG`
2. The script handles fuzzy matching, validation, and updates `_active-brand.json`
3. Confirm: "Switched to [brand_name]. All marketing outputs will now use this brand's voice, compliance rules, and context."

Or use: `/digital-marketing-pro:switch-brand`

## How Other Modules Use This Skill

Every module should:
1. Check if an active brand exists before producing marketing outputs
2. Load relevant industry profile for benchmarks and channel recommendations
3. Auto-apply compliance rules based on brand's `target_markets` and `industry.regulation_codes`
4. Reference platform specs when creating platform-specific content
5. Use scoring rubrics when evaluating or grading content quality
6. Use **adaptive scoring** — run `adaptive-scorer.py` to get brand-specific weights before content scoring
7. **Save campaign data** — use `campaign-tracker.py` to persist plans, performance, and insights
8. **Check past campaigns** — before making recommendations, check if similar campaigns exist in brand history

## Business Model Types

The following types trigger different funnel models, KPI frameworks, and channel strategies:

- `B2B_SaaS` — MRR/ARR focused, product-led or sales-led growth
- `B2C_eCommerce` — ROAS focused, product catalog marketing
- `B2C_DTC` — Direct-to-consumer brand building + performance
- `B2B_Services` — Thought leadership, long sales cycles
- `Local_Business` — Google Business Profile, local SEO, reviews
- `Agency` — Multi-client management, white-label outputs
- `Creator` — Personal brand, audience building, monetization
- `Enterprise` — ABM, buying committees, complex sales
- `Non_Profit` — Donor acquisition, awareness, advocacy
- `Marketplace` — Two-sided acquisition, liquidity, trust

## Brand Voice Scoring

The brand voice scorer (`brand-voice-scorer.py`) automatically normalizes profile data:
- Reads `brand_voice.formality` (1-10 int scale) → converts to 0.0-1.0 float internally
- Maps `brand_voice.prefer_words` → `preferred_words`, `brand_voice.avoid_words` → `avoided_words`
- Supports both the full profile schema (from brand-setup) and legacy direct schemas

## Data Persistence

Campaign data, performance snapshots, and marketing insights persist across sessions:
```
~/.claude-marketing/brands/{slug}/
├── campaigns/              # Campaign plans and post-mortems
│   ├── _index.json         # Campaign index for quick lookup
│   └── {id}.json           # Individual campaign data
├── performance/            # Performance snapshots over time
│   └── {campaign}-{date}.json
├── insights.json           # Marketing learnings (last 200)
├── content-library/        # Saved content pieces
└── voice-samples/          # Brand voice reference content
```

Use `campaign-tracker.py` for all persistence operations.

## MCP Integrations

When MCP servers are configured (in `.mcp.json`), modules can pull real data:
- **Google Analytics** → actual traffic/conversion data for performance reports
- **Google Search Console** → real ranking data for SEO audits
- **Google Ads / Meta** → live campaign performance for paid advertising
- **HubSpot** → CRM data for funnel analysis
- **Mailchimp** → email campaign metrics
- **Google Sheets** → export reports and calendars

All MCP servers connect to the USER'S OWN accounts via their API keys.

## Reference Files

- **industry-profiles.md** — 20+ industry profiles with benchmarks, channels, compliance, content types
- **compliance-rules.md** — Geographic privacy laws (16 jurisdictions) + industry regulations (10+ sectors)
- **platform-specs.md** — Social media, email, and ad platform specifications
- **scoring-rubrics.md** — Content quality, ad creative, email, and landing page scoring criteria
- **intelligence-layer.md** — How the adaptive intelligence system works (scoring, learning, persistence)
