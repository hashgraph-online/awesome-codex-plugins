# Tucking decisions: editorial method

A reference complementing `progressive-disclosure-defaults-and-tucking` with a more detailed method and worked case studies.

## A repeatable audit method

For an existing surface that needs a progressive-disclosure pass, work through these steps:

### 1. Inventory every visible element

List every control, field, link, and content block on the surface. Don't skip "small" elements — small noisy elements add up.

### 2. Tag each element with usage data

For each, find or estimate:

- **% of users who interact with it per visit.** From analytics if available; from intuition if not.
- **% of users who interact with it ever.** A control used by 30% of users some time but only 2% per visit is different from one used by 30% of users every visit.
- **Role / segment that uses it.** Power users, admins, novices, billing-payers — different roles have different needs.

### 3. Categorize each element by tier

Using the rough thresholds from the parent skill:

- **≥ 50% per-visit usage** → primary tier.
- **20–50% per-visit, or routine for a clear segment** → secondary tier (visible but de-emphasized).
- **5–20% per-visit, or power-user routine** → disclosed (behind one click).
- **< 5% per-visit** → disclosed deeper, or candidate for removal.

### 4. Group disclosed items into coherent sections

The disclosed long tail isn't one bucket; it's several. Group by purpose so the user can predict what's behind which disclosure.

Bad: "More options" → 30 unrelated controls.
Good: "Advanced filters" → 8 filtering controls. "Webhooks" → webhook configuration. "Display preferences" → layout/theme controls.

### 5. Pick affordances per group

Different groups call for different affordances:
- Long settings groups → separate page or accordion.
- Optional fields → inline accordion.
- Filters → inline expand or side panel.
- Help / explanation → tooltip or popover.

### 6. Audit the new layout against tasks

For each major user task, walk through the redesigned surface. Are the controls the user needs accessible without too many clicks? Is anything required hidden? Does the new chrome enable or hinder common workflows?

### 7. Migrate carefully

For existing users, moving controls is disruptive. When possible:

- Announce the change (banner, changelog, in-app notification).
- For at least one release, make the relocated control findable from its old position (a tooltip or short-lived link).
- Make sure search includes the relocated controls so users can find them by name.

## Case study: a settings page redesign

Imagine a Settings page with 38 controls across one long scroll.

**Audit data:**

- 7 controls used by ≥ 50% of users per visit (display name, email, time zone, password, 2FA, notification frequency, default view).
- 14 controls used by 5–20% (workspace name, member list, integrations, etc.).
- 17 controls used by < 5% (webhooks, custom CSS, beta flags, audit log, etc.).

**Redesigned structure:**

```
Settings (entry page; primary tier)
├── Profile (3 controls; primary)
├── Security (2 controls; primary; same page or split for high-stakes)
├── Notifications (1 control + accordion to expand granular controls)
└── Display preferences (1 control + accordion)

Settings → Workspace (separate page)
├── Workspace name, members, billing (primary on this page)
└── Integrations (accordion; secondary)

Settings → Advanced (separate page; secondary tier overall)
├── Webhooks
├── API tokens
├── Custom CSS
└── Feature flags

Settings → Audit log (separate page; rarely used but high-stakes)

Settings → Danger zone (separate panel; visually distinct)
└── Transfer ownership, Delete account
```

The 7 most-used controls are visible on the entry page. The next tier is one click away. The long tail is on its own page, named for what it contains.

## Defaults: open vs. closed

For each accordion or disclosed section, decide its default state:

- **Default open** if more than half the users likely engage with it on most visits.
- **Default closed** if engagement is occasional.
- **Default to user's previous state** if you persist preferences.
- **Default open if it's the only section** — a single closed accordion looks like a bug.

## Anti-patterns specific to tucking

- **The "let's hide the controversial one"** trap. If a control is controversial because it has poor UX, fix the UX. Don't hide it; users still need it.
- **The Marie Kondo trap.** "Does this spark joy?" applied to UI. Some controls don't spark joy — billing, password reset, account deletion — but users need them. Joy isn't the metric; *fitness for purpose* is.
- **The "small team likes it" defense.** A control loved by your design team but used by 0.5% of users is still a tucking candidate. Internal preference doesn't translate to user need.

## Resources

- **Heath, C. & Heath, D.** *Decisive* (2013) — on how to make multi-option decisions deliberately.
- **Tidwell, J.** *Designing Interfaces* — pattern catalog with disclosure patterns.
- **NN/g** — practical articles on settings-page redesign and progressive disclosure analytics.
