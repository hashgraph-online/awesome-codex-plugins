---
name: context-engine
description: "Load and manage the shared marketing context other skills build on — the active brand profile (voice, audiences, competitors, goals), industry benchmark profiles, geographic and industry compliance rules, platform specs, and scoring rubrics — plus brand switching and campaign-data persistence under ~/.claude-marketing/. Triggers on \"/digital-marketing-pro:context-engine\", \"switch to brand X\", \"what are the benchmarks for my industry\", \"which compliance rules apply to us\", \"load my brand context\". Pairs with /digital-marketing-pro:brand-setup to create profiles and /digital-marketing-pro:switch-brand to change them; its reference files are read by nearly every sibling skill."
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

### Core context & specs

- **industry-profiles.md** — 20+ industry profiles with benchmarks, channels, compliance, content types
- **platform-specs.md** — Social media, email, and ad platform specifications
- **platform-publishing-specs.md** — API-level publishing requirements and content formats per platform (payloads, field mapping, validation)
- **google-seo-reference.md** — Concise Google SEO quick reference (crawling/indexing/serving, surfaces, schema status, algorithm dates)
- **schema-templates.json** — Ready-to-use JSON-LD schema templates with Google support/deprecation status
- **india-market-context.md** — India regional market context: regulation (DPDP), platforms, and market dynamics

### Methodology frameworks

- **engagement-flow-methodology.md** — The 12-Part sequential engagement methodology every command, skill, and agent reads back to
- **four-core-documents-spec.md** — Full spec of the four Part 3 Core Documents (61 steps) that form the strategic spine
- **decision-matrix-rerun.md** — Which Part 3/4 documents to re-run as v2 after Part 5 client validation
- **two-views-model.md** — Keeping v1 (unbiased research) and v2 (client-validated) views authoritative for different questions
- **update-back-rule.md** — Corrections land in the source document, not just the deliverable that caught the error
- **stone-vs-opinion.md** — Confidence tagging of intake facts: verifiable Stone vs client Opinion
- **living-instruction-file-spec.md** — Spec for the per-engagement Living Project Instruction File (single source of truth)
- **30-60-90-framework.md** — Default first-quarter phasing: Foundation / Optimization / Scale milestones
- **actionable-persona-format.md** — Six-question persona format that replaces biographical narratives
- **b2b-decision-making-unit.md** — B2B buying-committee roles overlay for every B2B persona
- **five-digital-markets.md** — Strategic taxonomy of the five digital market types; market type determines channel
- **channel-families.md** — Operational grouping of the 17 Part 9 channels into seven families
- **in-market-out-market.md** — Budget split logic between in-market (3–5%) and out-market (95–97%) audiences
- **fixed-vs-variable-budget.md** — Separating committed monthly spend from data-backed variable spend
- **unit-economics-framework.md** — CAC/LTV foundation every channel and budget decision checks back to
- **three-scenario-forecasting.md** — Every projection presented as conservative/expected/optimistic scenarios
- **decision-framework.md** — Multi-dimensional decision framework: name, weight, and score every dimension
- **competitor-3-question-output.md** — The three questions every competitor analysis must answer per competitor

### Execution guides

- **execution-workflows.md** — Standard operating procedures for publishing, sending, and launching marketing actions
- **seo-execution-guide.md** — SEO execution via CMS APIs, search console ops, schema deployment, rank monitoring
- **geo-execution-guide.md** — Generative Engine Optimization: AI visibility monitoring, entities, citations
- **multilingual-execution-guide.md** — End-to-end multilingual campaign pipeline: translation services, RTL/Indic/CJK, SEO
- **transcreation-framework.md** — Transcreation vs translation vs localization, with process and QA scoring
- **crm-integration-guide.md** — CRM connection patterns, object mapping, and data sync (Salesforce, HubSpot, etc.)
- **custom-mcp-guide.md** — Adding or building MCP servers beyond the opt-in connector catalog
- **self-healing-ops-guide.md** — Automated campaign monitoring and correction within safety guardrails
- **approval-framework.md** — Risk classification determining auto-execute vs explicit-approval flows
- **agency-operations-guide.md** — Multi-client SOPs: onboarding, portfolio health, credential isolation, white-labeling
- **team-roles-framework.md** — Team roles, permissions, approval chains, and capacity planning
- **guidelines-framework.md** — How brand guidelines, restrictions, and style rules are structured and enforced

### Compliance & EU

- **compliance-rules.md** — Geographic privacy laws (16 jurisdictions) + industry regulations (10+ sectors)
- **eu-code-of-practice.md** — EU Code of Practice on AI-generated content + AI Act Article 50 obligations for marketers

### Templates & rubrics

- **scoring-rubrics.md** — Content quality, ad creative, email, and landing page scoring criteria
- **eval-rubrics.md** — Detailed scoring rubrics for the six eval dimensions used by eval-runner.py
- **eval-framework-guide.md** — Architecture and usage of the automated six-dimension content QA pipeline
- **growth-plan-template.md** — Flagship Part 8 client-facing Growth Plan deliverable template
- **yearly-planner-template.md** — Part 8 twelve-month operating calendar template
- **monthly-report-template.md** — Decision-driving monthly client report structure
- **reporting-cadence.md** — Matching metric review frequency (daily→quarterly) to decision velocity
- **advanced-reporting-guide.md** — PDF report generation, dashboards, attribution, cohort and variance reporting

### Intelligence & memory

- **intelligence-layer.md** — How the adaptive intelligence system works (scoring, learning, persistence)
- **memory-architecture.md** — The 5-layer persistent brand knowledge system
- **compound-intelligence-guide.md** — Intelligence graph that makes each decision better than the last
- **creative-intelligence-guide.md** — Creative fatigue prediction, content decay, and refresh prioritization
- **market-intelligence-guide.md** — Macro signal detection: economic indicators, market timing, regulatory tracking
- **competitive-monitoring-guide.md** — Ongoing competitor change detection, social listening, share of voice
- **narrative-warfare-guide.md** — Narrative territory mapping, counter-narratives, and category creation
- **journey-growth-guide.md** — Journey state machines, growth loops, dark funnel analysis, journey simulation
- **marketing-science-guide.md** — Causal inference, Bayesian MMM, incrementality, and experimentation rigor
- **synthetic-audience-guide.md** — AI-simulated audience research, focus groups, and message testing with calibration
