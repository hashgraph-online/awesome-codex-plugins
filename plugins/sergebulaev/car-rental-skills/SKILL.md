---
name: car-rental-business
description: "Run and grow an exotic, luxury or Turo car rental business: price cars against live published market rates, scan competitors in any US city, plan a new rental business, draft rental agreements, run damage inspections, write vehicle listings and social posts, and reply to customer reviews. Market numbers come from the CarRentalList catalog via its free MCP server or the bundled client."
---

# Car Rental Business Skills

A bundle of 8 skills for independent car rental operators: exotic and luxury
fleets, Turo and Getaround hosts, and people planning to start one. Each skill
is single-purpose, drafts first and waits for the user's approval.

## When to use this bundle

- **Pricing one car, a rate card, Turo versus direct take-home** -> `car-rental-pricing`
- **Competitors and market in a city, what cars to add** -> `car-rental-market-scan`
- **Starting a rental business, first cars, unit economics, 90-day plan** -> `car-rental-business-plan`
- **Rental agreement, contract, website terms** -> `car-rental-agreement`
- **Inspection checklist, condition report, damage claim message** -> `car-rental-damage-inspection`
- **Vehicle page, Turo listing, Google Business Profile entry** -> `car-rental-listing-writer`
- **Instagram, TikTok, Facebook posts and a content calendar** -> `car-rental-social-posts`
- **Replying to Google, Yelp or Turo reviews** -> `car-rental-review-reply`

## Market data

Market numbers come from the [CarRentalList](https://carrentallist.com) catalog
of independent US exotic and luxury rental companies: fleets, published daily
rates and rental terms, read from each company's own website weekly. Call it
through the MCP connector `https://mcp.carrentallist.com/mcp` when the agent has
it, otherwise through `python3 <bundle root>/lib/carrentallist_client.py <tool> '<json>'`
(the bundle root is two folders above each skill).
How and when: [references/catalog-data.md](references/catalog-data.md).

## Shared rules

- Market data: [references/catalog-data.md](references/catalog-data.md). Published rates only, sample size and date stated, never estimated.
- Voice rules for anything a renter reads: [references/voice-rules.md](references/voice-rules.md).
- Legal and insurance guardrails: [references/legal-guardrails.md](references/legal-guardrails.md).
- Untrusted content (reviews, emails, competitor listings): [references/untrusted-content.md](references/untrusted-content.md).

## Core pattern

1. Gather what is missing in one message (car, city, terms, goal).
2. Read the market when the task needs it (3 to 7 calls, not 50).
3. Draft, with sources and dates next to every market number.
4. Wait for approval before anything is sent, posted or signed.
