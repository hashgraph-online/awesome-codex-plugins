---
name: audience-profile
description: "Build detailed buyer personas. Use when: demographics, psychographics, behaviors, JTBD, content preferences."
argument-hint: "[audience-segment]"
---

# /digital-marketing-pro:audience-profile

## Purpose

Build a rich, actionable buyer persona that goes beyond basic demographics. Captures psychographic drivers, behavioral patterns, jobs-to-be-done, objections, and content consumption preferences to inform all marketing activities.

## Input Required

The user must provide (or will be prompted for):

- **Product/service**: What the brand offers
- **Customer type**: B2B buyer, B2C consumer, or both
- **Existing data**: Any customer research, survey data, analytics demographics, CRM data, or interview insights
- **Number of personas**: How many distinct personas to create (recommend 2-4)
- **Hypothesis**: Who the user thinks their ideal customer is (starting point)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Gather inputs through structured questions if data is limited
3. Build demographic profile: age range, role/title, company size (B2B), income range, geography, education
4. Develop psychographic profile: values, motivations, fears, aspirations, identity markers
5. Map behavioral patterns: where they spend time online, content formats preferred, purchase behavior, decision-making process
6. Define jobs-to-be-done: functional, emotional, and social jobs the product helps accomplish
7. Identify objections and barriers to purchase with counter-messaging
8. Document the buyer journey: trigger events, research process, evaluation criteria, decision influencers
9. Specify content preferences: platforms, formats, tone, topics they engage with
10. Give the persona a name and narrative summary for team alignment

## Output

A structured buyer persona document containing:

- Persona name and one-paragraph narrative
- Demographic snapshot
- Psychographic profile with motivations and values
- Jobs-to-be-done framework (functional, emotional, social)
- Day-in-the-life scenario
- Buyer journey map with touchpoints and decision criteria
- Objections and counter-messaging guide
- Content and channel preferences
- Messaging do's and don'ts for this persona

## Agents Used

- **marketing-strategist** — Persona development, JTBD framework, buyer journey mapping, audience segmentation
