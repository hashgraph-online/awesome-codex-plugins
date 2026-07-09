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
6. Apply deliverability checks: spam trigger words, link density, image-to-text ratio, authentication reminders, and the **bulk-sender checklist** below
7. Add personalization tokens and dynamic content recommendations
8. Review full sequence for brand voice consistency and regulatory compliance (CAN-SPAM, GDPR)

### Bulk-sender deliverability checklist (Gmail / Yahoo / Outlook)

Any brand sending at bulk volume (~5,000+ messages/day to a mailbox provider) must meet the mailbox-provider sender requirements or mail is throttled or rejected. Bake these into the sequence's implementation notes (ported from `/digital-marketing-pro:send-email-campaign`, with Outlook 2025 added):

- **Authenticate the sending domain**: SPF **and** DKIM **and** a published DMARC policy (at least `p=none`, aligned) — required by **Gmail & Yahoo (Feb 2024)** and **Microsoft Outlook / Outlook.com (rolling out through 2025 for senders ≥5,000/day)**.
- **One-click unsubscribe**: include the `List-Unsubscribe` header with one-click support (RFC 8058), and honour opt-outs within 2 days. A visible unsubscribe link in the body is still required in addition.
- **Keep the spam-complaint rate under 0.3%** (measured in Google Postmaster Tools / Yahoo / Microsoft SNDS) — ideally under 0.1%.
- **Send from a consistent, PTR/reverse-DNS-valid IP over TLS**, with a warmed-up sending domain and consistent from-address.
- **Physical mailing address + accurate From/Reply-To identity** in every message (CAN-SPAM), and documented opt-in consent per jurisdiction (GDPR / CASL).
- **List hygiene**: suppress hard bounces and inactive addresses; never send to purchased lists.

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
