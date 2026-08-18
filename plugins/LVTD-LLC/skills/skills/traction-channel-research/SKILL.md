---
name: traction-channel-research
description: Research and shortlist startup traction channels before running Bullseye tests. Use when comparing acquisition channels, studying how similar companies grew, finding underused distribution strategies, or preparing the outer ring for a Traction-style growth process.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Traction Channel Research
  category: Marketing
  tags: traction,growth,research,marketing,startups
---

# Traction Channel Research

Use this skill before `traction-bullseye` when the agent needs evidence about
which channels might work. The job is to replace founder guesses with grounded
channel ideas.

## Source Traceability

Primary source: Traction, chapters 1, 3, and 5. Authoring notes: converted
lines 238-393, 555-674, and 787-902. The canonical channel list also appears
in `../traction-bullseye/references/source-map.md`.

## Research Workflow

1. Define the product, target customer, business model, ACV or price point, and
   current growth stage.
2. List all 19 channels, even if some look unlikely:
   targeting blogs, publicity, unconventional PR, search engine marketing,
   social and display ads, offline ads, search engine optimization, content
   marketing, email marketing, viral marketing, engineering as marketing,
   business development, sales, affiliate programs, existing platforms, trade
   shows, offline events, speaking engagements, and community building.
3. For each channel, research comparable companies, adjacent markets, failed
   examples, and underused tactics.
4. Separate channel from strategy. "SEO" is a channel; "comparison pages for
   high-intent alternatives" is a strategy.
5. Estimate reach, cost, speed, confidence, and customer fit.
6. Shortlist the top three to five strategies for Bullseye middle-ring tests.

## Evidence To Look For

- Founder interviews, teardown posts, podcasts, and launch retrospectives.
- Competitor traffic sources, ad libraries, backlink patterns, and content
  footprints.
- Marketplaces, communities, events, newsletters, podcasts, and niche platforms
  where the customer already gathers.
- Signs of saturation: crowded ad auctions, copied content, high affiliate
  competition, or low response rates.
- Signs of underuse: unfashionable offline channels, narrow communities,
  ignored partners, or new platforms.

## Output Format

```markdown
# Traction Channel Research

## Context
- Product:
- Customer:
- Stage:
- Traction goal:

## Channel Scan
| Channel | Strategy Idea | Evidence | Reach | Cost | Speed | Fit | Confidence |
|---------|---------------|----------|-------|------|-------|-----|------------|

## Shortlist
1. [Channel + strategy] - [why test this]
2. [Channel + strategy] - [why test this]
3. [Channel + strategy] - [why test this]
4. [Optional channel + strategy] - [why test this]
5. [Optional channel + strategy] - [why test this]

## Bias Check
- Channels the team may be overvaluing:
- Channels the team may be ignoring:

## Recommended Next Tests
[Hand off to traction-test-planner.]
```

## Quality Bar

- Prefer specific strategies over broad channel labels.
- Include at least one uncomfortable or underused channel.
- Distinguish evidence from guesses.
- Flag channels that cannot plausibly move the user's current traction goal.
