---
title: Defaults & Pre-filling
impact: MEDIUM
tags: defaults, status-quo-bias, autofill, forms, settings
---

**Rule**: Most people keep the default, and every field they don't have to fill is effort saved. Choose defaults that serve the user, and pre-fill what the system already knows.

**Evidence**: Johnson & Goldstein 2003, "Do Defaults Save Lives?" (*Science*) — organ-donor consent rates differed dramatically between opt-in and opt-out countries. Samuelson & Zeckhauser 1988, "Status quo bias in decision making" (*Journal of Risk and Uncertainty*). Baymard Institute checkout research — unnecessary and unfilled fields are a leading cause of form abandonment. WCAG 2.2 SC 1.3.5 (Identify Input Purpose) — personal-data fields declare their purpose so browsers and assistive tech can fill them.

### When Building

- **Settings defaults** — pick what most users would choose if they thought about it, with privacy and safety on by default
- **Pre-fill known data** — account name and email, last-used shipping address, saved payment method, values from the previous step
- **Infer before asking** — country, currency, language, and timezone from locale and device; city from postcode
- **Platform autofill** — `autocomplete` on web, `textContentType` on iOS, autofill hints on Android (platform guides)
- **Smart defaults in creation flows** — today's date, the current project, the most common option preselected where one clearly dominates
- **Make defaults visible and easy to change** — a preselected choice shown, not hidden

### When Auditing

- Asking for data the app already has (email again at checkout, country when the locale is known)
- Missing `autocomplete` / `textContentType` on name, email, address, phone, password, and one-time-code fields
- Settings defaults that favour the business at the user's cost (sharing, marketing, auto-renew upsells)
- Pre-ticked consent or paid add-ons — escalate to `rules/deceptive-patterns.md`

### Incorrect

```html
<input name="email" type="text">
<input name="country" placeholder="Country">
```

### Correct

```html
<input name="email" type="email" autocomplete="email">
<select name="country" autocomplete="country"><!-- preselected from locale --></select>
```

### Why This Matters

Defaults are decisions the user makes by not deciding — so they shape outcomes more than any copy. Pre-filling removes typing, the slowest and most error-prone part of mobile forms.

### Alternatives

Some choices must be active: legal consent, payment authorisation, and anything where a wrong default harms the user. Pre-ticked consent is invalid under EU law (*Planet49*, 2019) — the field must start empty. Where no option fits most people, leave it unselected rather than guessing.
