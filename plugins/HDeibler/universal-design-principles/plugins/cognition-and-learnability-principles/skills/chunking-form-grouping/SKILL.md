---
name: chunking-form-grouping
description: 'Use this skill when designing or fixing long forms that ask the user for many fields — sign-up flows, profile setup, settings panels, checkout, intake forms, applications. Trigger when forms exceed ~6 fields, when users complain forms are "too long," when seeing high mid-form drop-off, or when picking how to break a form into sections. Sub-aspect of `chunking`; read that first.'
---

# Chunking applied to forms

A form with 25 fields in one continuous scroll is a wall. The same 25 fields organized into 4–5 named sections of 5–6 fields each is a list of small tasks. The total content is identical; the perceived complexity drops dramatically.

## When to chunk a form

- The form has more than ~7 fields.
- Drop-off analytics show users abandoning mid-form.
- Users describe the form as "long," "complicated," or "I don't know where I am."
- The fields fall into natural categories (account info, profile info, preferences).

If the form is short (3–5 fields) or all fields belong to a single concept, chunking adds noise without benefit.

## Section structure

Three patterns for chunked forms:

### Single-page with named sections

All sections visible on one page; user scrolls through and fills in.

```html
<form class="long-form">
  <section>
    <h2>Account</h2>
    <p class="hint">How you'll sign in.</p>
    <!-- 4-5 fields -->
  </section>

  <section>
    <h2>Profile</h2>
    <p class="hint">How others see you.</p>
    <!-- 4-5 fields -->
  </section>

  <section>
    <h2>Workspace</h2>
    <p class="hint">Set up your team space.</p>
    <!-- 4-5 fields -->
  </section>

  <button>Create account</button>
</form>
```

Pros: user sees total scope; can fill in any order; one save action.

Cons: the scroll can still feel long; mid-form abandonment possible.

### Accordion sections (one open at a time)

Sections collapse to headers; user opens one at a time.

Pros: less visual mass; user focuses on current chunk.

Cons: total scope is hidden; users may not realize how many sections remain.

### Multi-step wizard

Each section is its own page; "Continue" advances; "Back" returns.

Pros: focused attention on one chunk; easier mobile experience.

Cons: more clicks; loss of context between steps; back-button management complexity.

The right pattern depends on form length, mobile context, and whether the user benefits from seeing total scope (probably yes for sign-up; maybe not for long government forms).

## Naming sections

Section names should:

- **Match the user's mental model** — "Profile" not "User Information Subsystem."
- **Suggest what's inside** without requiring the user to open it.
- **Be parallel** in grammar — all noun phrases, or all verb phrases, not mixed.

Bad section names:

- "Section 1 of 5" — generic; provides no structure.
- "Required Information" — vague; everything is information.
- "Etc." — gives up.

Good section names:

- "Account credentials"
- "Notification preferences"
- "Billing address"

## Section progress signals

For long single-page forms, a sticky table-of-contents or progress indicator helps:

```html
<aside class="form-toc">
  <ol>
    <li><a href="#account" class="done">Account</a></li>
    <li><a href="#profile" class="active">Profile</a></li>
    <li><a href="#workspace">Workspace</a></li>
  </ol>
</aside>
```

For multi-step wizards, a stepper:

```html
<nav class="stepper" aria-label="Progress">
  <ol>
    <li class="done">1. Account</li>
    <li class="active">2. Profile</li>
    <li>3. Workspace</li>
  </ol>
</nav>
```

Both let the user see where they are and how much remains.

## Field count per section

Aim for 4–7 fields per section. More than that and the section itself becomes a wall; less and the section overhead exceeds its benefit.

If you find yourself with 12 fields in one logical section, ask:

- Are all 12 actually required? (Often not; cut.)
- Can the section split into two? (E.g., "Personal" and "Contact.")
- Can some fields move to "later" via progressive disclosure?

## Single-page vs. multi-step decision

A useful matrix:

| Length | Mobile-primary | Recommended |
|---|---|---|
| ≤ 5 fields | Either | Single page, no sections |
| 6–15 fields | Desktop | Single page with named sections |
| 6–15 fields | Mobile | Multi-step or accordion |
| 16–30 fields | Either | Multi-step wizard |
| 30+ fields | Either | Multi-step + reconsider scope |

The question after 30+: do you really need all this data up front? Most products can defer 60% of fields until the user has experienced value.

## Anti-patterns

- **Sections without names.** Visual breaks (a horizontal rule) without headings provide visual chunking but no semantic chunking. The user doesn't know what's in each.
- **Inconsistent section size.** Five fields, two fields, fourteen fields. The user can't predict what's coming.
- **Required + optional mixed within sections.** A user finishing what looked like a required field discovers more required fields hidden among optional ones. Worse: discovers there are required fields in a section they thought was optional.
- **Auto-advance on field change.** A field that automatically moves focus or advances steps when value changes surprises the user.
- **Save state per section unclear.** Multi-step wizards that don't save state per step can lose user data on navigation.

## Heuristics

1. **The "name each section in 2–3 words" test.** If you can't, the chunking isn't meaningful.
2. **The completion-rate audit.** If sign-up completion drops below ~70% (varies by industry), the form is too long; cut, defer, or chunk better.
3. **The mobile walkthrough.** Walk the form on a 375px screen. Single-page sections that feel manageable on desktop often feel oppressive on mobile.

## Related sub-skills

- **`chunking`** (parent).
- **`chunking-numeric-and-otp`** — chunking within field values.
- **`progressive-disclosure`** — defer optional fields rather than showing them all.
- **`proximity-form-fields`** (perception) — visual proximity within and between sections.
- **`hicks-law`** — fewer fields = faster decisions.
