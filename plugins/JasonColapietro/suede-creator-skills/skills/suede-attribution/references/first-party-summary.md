# Pillar B: Own your attribution (first-party)


Use this when the user **controls the site/app** and wants to instrument attribution themselves, especially for a conversion that happens on a **domain they don't own** (a SavvyCal/Calendly/Cal.com booking, a Stripe Checkout page). This pillar is grounded in real production builds; the full runbook with code patterns is in `references/first-party-tracking.md`. The essentials:

### The identity graph

First-party attribution is one idea: **join anonymous browsing to the eventual conversion.**

1. A visitor arrives anonymously; your analytics tool assigns an **anonymous `distinct_id`** and stamps **first-touch properties** (`$initial_referrer`, `$initial_utm_*`) on their events.
2. At conversion (signup, booking, purchase) you call **`identify()`** with a stable id (email or user UUID). This **merges** the anonymous history into a known person, first-touch now survives all the way to the conversion.
3. Every conversion event can now be broken down by first-touch channel. That's the whole game.

### Closing the `identify()` gap

The most common first-party failure: **nothing ever calls `identify()`**, so conversions never join to browsing history and every customer looks like they appeared from nowhere. The fix is to call identify at each real conversion. **Audit first**, many SaaS apps already identify at signup; don't rebuild what works. Find the *specific* un-instrumented conversions and close only those.

### Stitching conversions on a third-party domain

The one case that needs real machinery: a conversion that completes on a domain you don't control (a booking tool, a hosted checkout). You can't run your analytics there, so:

1. **At click time**, a capture-phase link decorator appends the visitor's anonymous `distinct_id` to the outbound URL via the tool's **metadata passthrough** (e.g. `?metadata[ph_distinct_id]=<id>`). One document-level listener covers every CTA: no per-link edits.
2. The third-party tool stores that metadata and returns it in its **webhook**.
3. Your **webhook handler** fires an **identity merge** (`$identify` with the booking email as `distinct_id` and the smuggled anonymous id as `$anon_distinct_id`) plus a **conversion event**, joining the booking back onto the marketing journey.

### Guardrails (do not skip)

- **Anonymity guard: fail closed.** Only ever smuggle the *anonymous* id. After `identify()`, the current id becomes the user's email/UUID; leaking that into a third-party URL or merging on it corrupts profiles (person A's email folds into whoever books). Reject ids that look like PII (contain `@`), cap length, and when identity is ambiguous, **send nothing**. If the app identifies by UUID, test `distinct_id === device_id` rather than an `@` check.
- **First-touch data quality.** Redirects overwrite the true first touch. Exclude OAuth/checkout referrers (`accounts.google.com`, `checkout.stripe.com`, `login.*`), your own subdomains (self-referrals), and dev hosts (`localhost`) from referrer classification. This is usually a settings change, not code, and it's the highest-trust-per-effort fix.
- **Cross-subdomain stitching.** Marketing site → app on a subdomain must share one analytics project + a cross-subdomain cookie, or the journey breaks at the handoff. Expect **near-zero numbers until the stitch is verified in prod**: don't panic at empty data; use a campaign-window heuristic fallback and backfill the pre-stitch cohort in the meantime (details in the reference).

### Reporting and the last mile

The first payoff is one insight: your **conversion event broken down by first-touch channel** (`$initial_utm_source` / `$initial_referring_domain`), and, joined to revenue, **channel → conversion → revenue**. Confirm first-touch vs. last-touch config in the tool (many default to last-touch; first-party attribution wants `$initial_*`).

But first-touch alone can't run the multi-touch models from §2. **Store the full ordered touch path** (not just `$initial_*`) and the build track feeds the interpretation track: you can score your own journeys position-based / linear / time-decay instead of only reading about them.

**The last mile, get it into the CRM**. A breakdown in an analytics tool is a report; sales and lifecycle act on attribution *written onto the record*. Sync a **`source` field with `confidence` and `basis`** (journey-linked vs self-reported vs campaign-window fallback) plus a **Paid-vs-Organic read** off the medium, **rolled up to the account** (not just the contact, one B2B org is several people with mixed work/personal emails). How pipeline/lifecycle then *use* it is `suede-revops`'s job.

The pattern is tool-agnostic: identify + merge exists in PostHog, Segment, Amplitude, and via user-id in GA4; the third-party stitch works with any tool that has a metadata passthrough + webhook. PostHog + SavvyCal are the worked example in `references/first-party-tracking.md`.

---
