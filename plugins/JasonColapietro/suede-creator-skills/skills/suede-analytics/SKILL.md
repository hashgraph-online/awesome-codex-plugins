---
name: suede-analytics
description: "Suede AI Analytics Skills. Use when asked to \"fix our analytics events\" or set up GA4/GTM, key events, consent, UTMs and search/AI channels with readback proof. NOT FOR: experiment decisions (suede-ab-testing), campaign optimization (suede-ads), attribution reconciliation (suede-attribution), or revenue operations (suede-revops)."
metadata:
  display-name: "Suede AI Analytics Skills"
  version: 2.1.1
---

# Suede AI Analytics Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works with event schemas, source and exports; browser/debugger and existing authorized analytics access for live firing proof. Configuration changes follow the production-change boundary in this skill.

Use this measurement playbook to build tracking that supports auditable marketing and product decisions.

## Initial Assessment

Check for `.agents/product-marketing.md` (or `.claude/product-marketing.md`, or the legacy `product-marketing-context.md`) and read it if present: the key conversions, the decisions the data has to serve, and the tools already in place drive every recommendation here.

Then work the intake list under Task-Specific Questions below; ask only what the context file did not already answer.

---

## Production Changes: Halt Before Mutating

Editing live tags, properties, destinations, or consent settings is the
highest-consequence action in this skill, and Boundaries below forbids doing it
without explicit authorization and a rollback plan. When a task requires one and
you do not have both, halt in four parts:

1. Stop. Do not publish the container, edit the property, or change the consent
   configuration.
2. Name the blocker in one line ("publishing this GTM container version changes
   what fires for all live traffic; I have no rollback version identified").
3. Offer 2-4 options (stage it in Preview and hand over the trace; write the
   change as a diff for the owner to publish; publish after the user names the
   rollback version; scope the change to a test environment).
4. Wait for the answer. Do not pick one and continue.

The same halt applies to anything the Privacy and Compliance section below sends
to legal or privacy review: an unresolved lawful-basis question blocks
implementation, it does not get an assumption.

---

## Tracking Plan Framework

### Structure

```
Event Name | Category | Properties | Trigger | Notes
---------- | -------- | ---------- | ------- | -----
```

### Event Types

| Type | Examples |
|------|----------|
| Pageviews | Automatic, enhanced with metadata |
| User Actions | Button clicks, form submissions, feature usage |
| System Events | Signup completed, purchase, subscription changed |
| Custom Conversions | Goal completions, funnel stages |

**For comprehensive event lists**: See [references/event-library.md](references/event-library.md)

---

## Event Naming Conventions

### Recommended Format: Object-Action

```
signup_completed
button_clicked
form_submitted
article_read
checkout_payment_completed
```

### Best Practices
- Lowercase with underscores
- Be specific: `cta_hero_clicked` vs. `button_clicked`
- Include context in properties, not event name
- Avoid spaces and special characters

---

## Essential Events

### Marketing Site

| Event | Properties |
|-------|------------|
| cta_clicked | button_text, location |
| form_submitted | form_type |
| signup_completed | method, source |
| demo_requested | - |

### Product/App

| Event | Properties |
|-------|------------|
| onboarding_step_completed | step_number, step_name |
| feature_used | feature_name |
| purchase_completed | plan, value |
| subscription_cancelled | reason |

**For full event library by business type**: See [references/event-library.md](references/event-library.md)

---

## Event Properties

### Standard Properties

| Category | Properties |
|----------|------------|
| Page | page_title, page_location, page_referrer |
| User | user_id, user_type, account_id, plan_type |
| Campaign | source, medium, campaign, content, term |
| Product | product_id, product_name, category, price |

### Best Practices
- Avoid PII in properties
- Reuse the Standard Properties names above rather than inventing per-event variants

---

## GA4 Implementation

### Quick Setup

1. Create GA4 property and data stream
2. Install the Google tag (gtag.js) or GTM, with consent mode v2 defaults set
   before any tag fires
3. Enable enhanced measurement
4. Configure custom events
5. Mark key events in Admin (GA4 renamed "conversions" to key events in March
   2024), then create Google Ads conversions from the key events that bidding
   should use

### Event Example

```javascript
// GA4's recommended sign_up event, not a custom name, so it feeds built-in reports.
// The tracking plan can still call it signup_completed; map the name explicitly.
gtag('event', 'sign_up', {
  'method': 'email',
  'plan': 'free'
});
```

**For detailed GA4 implementation**: See [references/ga4-implementation.md](references/ga4-implementation.md)

---

## Google Tag Manager

### Container Structure

| Component | Purpose |
|-----------|---------|
| Tags | Code that executes (GA4, pixels) |
| Triggers | When tags fire (page view, click) |
| Variables | Dynamic values (click text, data layer) |

### Data Layer Pattern

```javascript
dataLayer.push({
  'event': 'form_submitted',
  'form_name': 'contact',
  'form_location': 'footer'
});
```

**For detailed GTM implementation**: See [references/gtm-implementation.md](references/gtm-implementation.md)

---

## UTM Parameter Strategy

### Standard Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| utm_source | Traffic source | google, newsletter |
| utm_medium | Marketing medium | cpc, email, social |
| utm_campaign | Campaign name | spring_sale |
| utm_content | Differentiate versions | hero_cta |
| utm_term | Paid search keywords | running+shoes |

### Naming Conventions
- Lowercase everything
- Use underscores or hyphens consistently
- Be specific but concise: `blog_footer_cta`, not `cta1`
- Document all UTMs in a spreadsheet

---

## Search and AI Assistant Traffic

Organic search and AI answer engines now send traffic that default channel
groups misfile. Add a custom channel group in GA4 (Admin > Data display >
Channel groups) with an **AI assistants** channel placed above Referral:

```text
Session source matches regex:
chatgpt\.com|chat\.openai\.com|perplexity\.ai|gemini\.google\.com|copilot\.microsoft\.com|claude\.ai|you\.com
```

Many AI-assisted visits arrive with no referrer and land in Direct, so pair the
channel with a "How did you hear about us?" field (see `suede-attribution`) and
with Search Console data for organic queries. Review the regex quarterly as
assistants change domains. For the visibility work itself, route to
`suede-ai-seo` and `suede-seo-audit`.

---

## Debugging and Validation

### Testing Tools

| Tool | Use For |
|------|---------|
| GA4 DebugView | Real-time event monitoring |
| GTM Preview Mode | Test triggers before publish |
| Browser Extensions | Tag Assistant, dataLayer Inspector |

### Validation Checklist

Each box closes on an artifact from the tools above, matched to the tool
category's "Required current proof" in Tool Integrations below. An unchecked box
does not mean "probably fine": it means the tracking is reported as
**unverified**, never as done. Inspecting the tag config is not proof; a readback is.

- [ ] **Events firing on correct triggers**: a DebugView/live-events capture showing each event on the intended action
- [ ] **Property values populating correctly**: a property readback per event, values matched against the tracking plan
- [ ] **No duplicate events**: the same capture inspected for repeat fires (multiple containers, trigger firing twice)
- [ ] **Works across browsers and mobile**: the readback repeated on at least one non-primary browser and one mobile session
- [ ] **Conversions recorded correctly**: a source receipt plus a destination receipt for the conversion, not the source alone
- [ ] **No PII leaking**: the payload of a real captured event read field by field, plus masking/sampling settings for session replay

Report what was proven and what was not. "Instrumented" and "verified" are
different claims; only the second one may cite this checklist.

### Common Issues

| Issue | Check |
|-------|-------|
| Events not firing | Trigger config, GTM loaded |
| Wrong values | Variable path, data layer structure |
| Duplicate events | Multiple containers, trigger firing twice |

---

## Privacy and Compliance

Privacy, consent, retention, deletion, and identifier rules vary by
jurisdiction, audience, data type, contract, and platform configuration. Do not
treat this skill as legal advice or declare a universal consent rule.

Before implementation:

1. Identify the actual markets, audience age, data categories, vendors,
   purposes, and data flows in scope.
2. Review current official regulator and platform requirements for those
   jurisdictions and configurations; obtain qualified privacy or legal review
   when the requirement is unclear or material.
3. Document the approved lawful basis or consent state, retention and deletion
   behavior, access controls, and prohibited properties.
4. Collect only approved data, avoid direct personal identifiers unless the
   reviewed design expressly allows them, and test both allowed and denied
   consent paths.
5. For Google tags, set all four consent mode v2 signals (`ad_storage`,
   `analytics_storage`, `ad_user_data`, `ad_personalization`) before any tag
   fires. Google requires them for advertising features used with EEA traffic.
   Pattern and basic-versus-advanced trade-off:
   [references/gtm-implementation.md](references/gtm-implementation.md).

---

## Output Format

### Tracking Plan Document

```markdown
# [Site/Product] Tracking Plan

## Overview
- Tools: GA4, GTM
- Last updated: [Date]

## Events

| Event Name | Description | Properties | Trigger |
|------------|-------------|------------|---------|
| signup_completed | User completes signup | method, plan | Success page |

## Custom Dimensions

| Name | Scope | Parameter |
|------|-------|-----------|
| user_type | User | user_type |

## Conversions

| Key event | Event | Counting | Google Ads conversion |
|-----------|-------|----------|-----------------------|
| Signup | signup_completed | Once per session | Primary / secondary / none |
```

---

## Task-Specific Questions

1. What tools are you using (GA4, Mixpanel, etc.)?
2. What key actions do you want to track?
3. What decisions will this data inform?
4. Who implements - dev team or marketing?
5. Are there privacy/consent requirements?
6. What's already tracked?

---

## Tool Integrations

This pack does not ship analytics connectors. Use the user's authorized
property UI, debugger, export, API, or installed connector and verify current
official documentation before constructing a call.

| Tool category | Typical use | Required current proof |
|---------------|-------------|------------------------|
| Web analytics | Sessions, acquisition, web conversions | Debug event plus property readback |
| Product analytics | Event funnels, cohorts, retention | Schema check plus sampled event readback |
| Tag manager | Controlled client-side deployment | Preview trace plus published-version ID |
| Customer data router | Send approved events to destinations | Source receipt plus destination receipt |
| Session replay | Diagnose interaction friction | Consent, masking, sampling, and replay verification |

---

## Boundaries

- Do not claim an event, conversion, consent state, or attribution path works until a current debug or readback proves it.
- Do not mutate production tags, properties, destinations, or consent settings without explicit authorization and a rollback plan.
- Do not collect secrets, direct personal identifiers, or sensitive traits merely because a tool permits them.
- Do not decide business success from a single dashboard number; state the metric definition, window, denominator, and exclusions.

## Routing

- Need experiment design or result interpretation -> use `suede-ab-testing`.
- Need paid-campaign decisions -> use `suede-ads`.
- Need attribution modeling, model comparison, or cross-tool reconciliation -> use `suede-attribution`.
- Need pipeline and CRM attribution -> use `suede-revops`.
- Need organic visibility diagnosis -> use `suede-seo-audit`.
- From those skills, route instrumentation plans and firing verification back to `suede-analytics`.
