---
name: email-sequence
description: "Design email sequences. Use when: building subject lines, body copy, timing, segmentation logic, and deliverability plans."
argument-hint: "[sequence-type]"
---

# /digital-marketing-pro:email-sequence

## Purpose

Design a full email sequence ready for implementation in any ESP. Includes subject lines, preview text, body copy, send timing, segmentation rules, and deliverability best practices.

## Input Required

The user must provide (or will be prompted for):

- **Sequence type**: Welcome, nurture, onboarding, re-engagement, cart abandonment, post-purchase, event, promotional
- **Goal**: What the sequence should achieve (activate, convert, retain, upsell, educate)
- **Audience segment**: Who receives this sequence and entry trigger
- **Number of emails**: Desired count or let the system recommend
- **Key messages/offers**: Core value props, promotions, or content to include
- **Existing ESP**: Platform in use (Klaviyo, Mailchimp, HubSpot, etc.) for format guidance

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Map the sequence to the customer journey stage and define the narrative arc
3. Determine optimal email count and send cadence based on sequence type
4. Write each email: subject line (2-3 options), preview text, body copy with clear CTA
5. Define segmentation and branching logic (open/click triggers, conditional paths)
6. Apply deliverability checks: spam trigger words, link density, image-to-text ratio, authentication reminders
7. Add personalization tokens and dynamic content recommendations
8. Review full sequence for brand voice consistency and regulatory compliance (CAN-SPAM, GDPR)

## Output

A complete email sequence containing:

- Sequence overview with goals, audience, and trigger conditions
- Per-email breakdown: subject lines, preview text, body copy, CTA, send timing
- Segmentation and branching logic diagram
- Deliverability checklist per email
- Personalization and dynamic content recommendations
- Compliance checklist (unsubscribe, physical address, consent)
- Performance benchmarks to measure against

## Agents Used

- **content-creator** — Email copy, subject lines, narrative arc, CTA strategy
- **brand-guardian** — Voice consistency, compliance review, regulatory checks
- **email-specialist** — Deliverability optimization, send timing strategy, subject line scoring, spam risk analysis, A/B test design
