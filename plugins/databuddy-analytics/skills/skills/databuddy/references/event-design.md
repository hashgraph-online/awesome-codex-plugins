# Databuddy Event Design

Use this file when an external user asks what custom events to add, which properties to send, or how to keep analytics query-friendly.

## Core Principle

Track decisions, milestones, and outcomes. Do not track every UI twitch just because it is easy.

Good events answer product, growth, support, or reliability questions: conversion, activation, feature adoption, workflow failure, channel performance, backend success/failure, or latency.

For instrumentation plans, use this chain before naming events:

```text
Question -> Metric -> Event -> Properties -> Source -> Placement -> Verify
```

If the event does not support a metric or decision, do not recommend it.

## Event Naming

Use stable `snake_case` names. Prefer completed outcomes for facts and started/selected/opened names for intent.

```ts
track("signup_completed");
track("onboarding_completed");
track("feature_used");
```

Avoid names like `button_click`, `clicked_button_123`, `signupCompleted`, `modal`, or framework/component names unless they are truly the product concept.

Prefer one reusable event with properties over many near-duplicates:

```ts
track("report_exported", { format: "csv", source: "dashboard" });
```

## Property Design

Properties should be small, stable, and useful for segmentation. Favor low-cardinality fields:

```ts
track("signup_completed", {
  method: "google",
  source: "landing_page",
});
```

Good property keys include `source`, `feature`, `variant`, `step`, `method`, `status`, `page_type`, `environment`, `provider`, `stage`, and `error_type`.

Avoid high-cardinality or sensitive fields by default: raw URL paths with IDs, emails, names, order IDs, UUIDs, exact search text, stack traces, timestamps, request bodies, API keys, and auth tokens.

Normalize when possible:

```ts
track("page_viewed", {
  page_type: "product",
  section: "features",
});
```

```ts
track("search_performed", {
  results_count: 18,
  category: "templates",
});
```

## What Not To Track

- Generic clicks with no business meaning.
- Hovers, scrolls, and keystrokes by default.
- Events that duplicate page views, errors, or web vitals already captured by the SDK.
- Implementation details that will churn with UI refactors.
- Values nobody will filter, segment, alert on, or debug with later.

## Bad To Better

| Avoid | Better | Why |
| --- | --- | --- |
| `button_clicked` | `signup_started` with `source` and `method` | names the user intent |
| `modal_opened` | `integration_opened` with `provider` and `source` | names the product concept |
| `api_error` with raw message | `webhook_processed` with `status: "failed"` and `error_type` | useful reliability metric without sensitive data |
| `feature_card_clicked_new_dashboard` | `feature_used` with `feature: "dashboard"` and `entrypoint` | stable taxonomy |
| one event per variant name | one outcome event with `flag_key` and `variant` | easier experiment analysis |

## Browser Vs Backend

- Browser events are good for intent and interaction: CTA clicked, onboarding completed, export started, invite sent, integration opened.
- Backend events are better for authoritative outcomes: signup completed, import completed, webhook processed, job failed, API request failed.
- Track sensitive or authoritative events server-side with API keys.
- Place tracking where the fact becomes true: before navigation for intent, after durable success for outcomes, and at terminal job/webhook states for async work.
- When a browser flow completes on the server, pass `getIds()` output (`anonymousId`, `sessionId`) to the backend.

Use declarative `data-track` attributes (`autocapture: { attributes: true }`) only for a few important CTAs or feature entry points. Do not use it as a blanket substitute for event design.

## Minimal Taxonomies

Start small and extend only when a question needs it.

### SaaS

- `signup_started`
- `signup_completed`
- `onboarding_completed`
- `project_created`
- `invite_sent`
- `feature_used`
- `integration_connected`
- `report_exported`

### Content Or Marketing

- `newsletter_signup`
- `demo_requested`
- `cta_clicked`
- `contact_submitted`
- `resource_downloaded`

### API Or Backend Product

- `api_key_created`
- `request_succeeded`
- `request_failed`
- `webhook_processed`
- `integration_connected`

## Backend Examples

```ts
await client.track({
  name: "webhook_processed",
  properties: {
    provider: "github",
    status: "success",
    event_type: "installation.created",
  },
});
```

## Review Checklist

Before recommending an event, check:

- does this answer a real product, support, growth, or reliability question?
- is the event name stable and clear?
- is the event placed where the fact becomes true?
- are the properties low-cardinality enough to segment usefully?
- are we avoiding PII and secrets?
- are attribution IDs included when a server event belongs to a browser session?
- is this duplicating an existing auto-captured event?
- could a smaller taxonomy answer the same question?

## Source Docs

- `apps/docs/content/docs/sdk/tracker.mdx`
- `apps/docs/content/docs/hooks.mdx`
- `apps/docs/content/docs/api/events.mdx`
- `apps/docs/content/docs/getting-started.mdx`
