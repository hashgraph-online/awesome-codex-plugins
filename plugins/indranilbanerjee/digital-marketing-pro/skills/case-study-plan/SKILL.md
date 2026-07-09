---
name: case-study-plan
description: "Create case studies and success stories. Use when: client results showcase, portfolio piece, testimonial-based proof points."
argument-hint: "[client-name]"
---

# /digital-marketing-pro:case-study-plan

## Purpose

Generate a structured case study creation plan with interview framework, data visualization approach, format variations, and distribution strategy. Produces a complete blueprint for building compelling proof-of-results content that drives sales enablement and builds credibility.

## Input Required

The user must provide (or will be prompted for):

- **Client or project to feature**: The specific client engagement, campaign, or project that will be showcased
- **Challenge or problem addressed**: The business problem, market pressure, or growth obstacle the client was facing before the engagement
- **Solution implemented**: The services, campaigns, strategies, or tools deployed to address the challenge
- **Results achieved**: Quantitative outcomes (revenue lift, traffic growth, conversion improvement, cost reduction) and qualitative outcomes (brand perception, team capability, process improvement)
- **Timeline of engagement**: Duration of the project or campaign — start date, key milestones, and current status
- **Permission status**: Whether the client has approved public use of their name, data, and story — or if anonymization is required
- **Target audience for the case study**: Who will read or watch it — prospects in the same industry, C-suite decision-makers, marketing managers, procurement teams, or general audience
- **Desired formats**: Which output formats are needed — PDF white paper, website page, presentation deck, video testimonial, social media snippets, or sales one-pager
- **Industry vertical**: The client's industry for contextual benchmarking and relevance targeting
- **Competitive context**: What alternatives the client considered and why they chose this approach

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Structure the CSR narrative**: Build the Challenge-Solution-Results framework with sub-sections — situation overview, specific pain points, goals at project start, strategic approach, tactical execution, implementation timeline, quantitative results, qualitative impact, and future outlook. Identify the emotional arc that makes the story compelling, not just informative.
3. **Develop client interview questions**: Create 15-20 interview questions organized by section — background and context (company size, industry pressures, previous attempts), challenge deep-dive (symptoms, root causes, business impact of inaction), solution experience (selection criteria, onboarding, collaboration quality), results and impact (measurable outcomes, unexpected benefits, team reaction), and forward-looking (ongoing plans, what they would tell peers).
4. **Plan internal team interview questions**: Draft 10 questions for internal team members who worked on the engagement — strategic rationale, technical approach, challenges encountered during delivery, key turning points, and lessons learned that could inform future engagements.
5. **Identify data points and visualizations needed**: Map every quantitative result to a visualization type — before/after bar charts, timeline growth curves, funnel improvement diagrams, ROI waterfall charts, and comparison tables. Specify which data needs to be collected, verified, and approved by the client before publication.
6. **Design format variations**: Create specifications for each requested output format — PDF white paper (4-6 pages, designed layout with pull quotes and charts), web page (SEO-optimized with structured data markup), presentation deck (8-12 slides for sales meetings), video testimonial script (2-3 minute interview-based script outline), social media snippets (pull quotes, stat cards, carousel posts), and sales one-pager (front-and-back summary for leave-behinds).
7. **Create distribution strategy**: Plan where and how the case study will be published and promoted — website case study library, sales enablement materials, email nurture sequences, social media campaigns, PR outreach, paid promotion, conference presentations, and partner co-marketing opportunities.
8. **Build approval workflow and permission checklist**: Define the full approval process — internal review (legal, marketing, account team), client review (point of contact, legal, executive sign-off), data accuracy verification, quote approval, logo and brand usage permission, and timeline for each review stage.
9. **Write draft executive summary**: Compose a 150-200 word executive summary that captures the full story arc — who the client is, what they faced, what was done, and what resulted. This summary serves as the foundation for all format variations and distribution copy.
10. **Plan visual assets needed**: Specify all visual elements required — client logo (with usage permissions), data visualization charts, photography (team photos, office shots, product images), branded design templates, infographic elements, pull quote cards, and video b-roll if applicable.

## Output

A structured case study creation plan containing:

- **CSR narrative framework** — Challenge-Solution-Results structure with detailed sub-sections, emotional arc mapping, and story flow outline
- **Client interview question set** — 15-20 questions organized by narrative section (background, challenge, solution, results, forward-looking) with follow-up prompts
- **Internal team interview questions** — 10 questions covering strategic rationale, delivery experience, turning points, and retrospective insights
- **Data visualization plan** — which metrics to highlight, chart types for each data point, before/after comparison designs, and data collection requirements
- **Format variation specifications** — PDF (4-6 pages with layout notes), web page (SEO-optimized with schema markup), slides (8-12 with speaker notes), video (2-3 min script outline), social (pull quotes and stat cards), and one-pager (front-and-back layout)
- **Distribution strategy** — publication channels (website, sales tools, social, email, PR), promotion plan, and audience targeting per channel
- **Permission and approval checklist** — legal review, client sign-off stages, data verification steps, quote approval, logo usage, and review timeline
- **Executive summary draft** — 150-200 word overview capturing the complete story arc for use across all formats
- **Visual asset list** — photography needs, chart specifications, infographic elements, pull quote card designs, and video b-roll requirements
- **SEO metadata** — optimized title tag, meta description, target keywords, and structured data recommendations for the web version
- **Sales enablement notes** — where the case study fits in the sales funnel, which buyer objections it addresses, and how sales teams should use each format
- **Content repurposing plan** — how to extract derivative content pieces (blog posts, social proof snippets, email testimonials, presentation slides) from the core case study

## Agents Used

- **content-creator** — Narrative structure, interview question development, executive summary drafting, format variation planning, visual asset specification, and content repurposing strategy
- **pr-outreach** — Distribution strategy, PR angle identification, media pitch framework, partner co-marketing opportunities, and external publication targeting
