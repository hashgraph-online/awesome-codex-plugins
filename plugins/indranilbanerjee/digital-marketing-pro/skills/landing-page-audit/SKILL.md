---
name: landing-page-audit
description: "Audit landing pages. Use when: scoring above-fold clarity, trust signals, form friction, message match, or mobile UX."
argument-hint: "[URL]"
---

# /digital-marketing-pro:landing-page-audit

## Purpose

Evaluate a landing page across six key conversion dimensions and deliver a scored assessment with specific, actionable recommendations to improve conversion rate.

## Input Required

The user must provide (or will be prompted for):

- **Landing page URL**: The page to audit
- **Traffic source**: Where visitors come from (paid search, social ads, email, organic)
- **Target action**: Desired conversion (form submit, purchase, signup, download, call)
- **Ad copy or email**: The upstream message driving traffic (for message match analysis)
- **Current conversion rate**: If known, for benchmarking

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Above-fold clarity** (score 1-10): Headline clarity, value proposition, visual hierarchy, CTA visibility within first viewport
3. **Trust signals** (score 1-10): Social proof, testimonials, logos, security badges, guarantees, reviews
4. **Form friction** (score 1-10): Number of fields, field labels, error handling, progressive disclosure, mobile form UX
5. **Message match** (score 1-10): Alignment between traffic source (ad/email) and landing page headline, imagery, offer
6. **Page speed** (score 1-10): Load time, Core Web Vitals, render-blocking resources, image optimization
7. **Mobile experience** (score 1-10): Responsive design, tap targets, scroll depth, mobile-specific CTAs
8. Calculate overall score and benchmark against industry averages
9. Prioritize recommendations by expected conversion impact

## Output

A structured landing page audit containing:

- Overall conversion score (1-10) with industry benchmark comparison
- Dimension-by-dimension scoring with evidence and screenshots/notes
- Top 5 priority fixes ranked by expected impact
- Detailed recommendations per dimension with implementation guidance
- Message match analysis with specific misalignment callouts
- Mobile-specific issues and fixes
- Quick wins vs. major redesign items

## Agents Used

- **analytics-analyst** — Performance scoring, conversion benchmarking, data-driven recommendations
- **brand-guardian** — Brand consistency, trust signal assessment, message alignment
- **cro-specialist** — Conversion scoring, form friction analysis, A/B test sample size calculation, above-fold hierarchy, CTA optimization
