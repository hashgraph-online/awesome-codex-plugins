---
name: progressive-disclosure-defaults-and-tucking
description: 'Use this skill when deciding *what to surface* and *what to tuck* — the editorial choices behind progressive disclosure. Trigger when laying out a settings page, picking which form fields to show by default, deciding whether a section starts collapsed or open, or arguing about whether a feature deserves primary chrome or belongs in "Advanced." Sub-aspect of `progressive-disclosure`; read that first.'
---

# Progressive disclosure: defaults and tucking decisions

Progressive disclosure is mostly an *editorial* discipline. The technical patterns (accordions, tabs, "More" buttons) are easy; the hard work is deciding which content earns primary placement and which gets tucked. This skill is about that decision.

## The framework: who, when, how often

For each candidate piece of content or control, ask three questions:

### 1. Who is it for?

- **Everyone (every user, every visit)** → primary layer, always visible.
- **Most users (the typical case)** → primary layer, visible by default.
- **Some users (specific roles or contexts)** → secondary layer, disclosed by user action.
- **Few users (power users, edge cases)** → secondary or tertiary layer, disclosed and possibly behind labels like "Advanced."

### 2. When is it needed?

- **Always** → primary.
- **Per visit, but only sometimes per session** → secondary, easy to reach.
- **Once during setup, never again** → primary during setup, then move to settings.
- **Only on error / exception** → don't show by default; surface on the relevant condition.

### 3. How often is it used?

This is the most concrete question — answerable from analytics.

- **Used by ≥ 50% of users on most visits** → primary.
- **Used by 20–50% of users, or by everyone occasionally** → primary, possibly with tighter visual treatment.
- **Used by 5–20% of users, or by power users routinely** → secondary, behind one explicit affordance.
- **Used by < 5% of users** → secondary or tertiary, possibly worth removing entirely.

These thresholds are rules of thumb; tune to your product. The bigger point: usage data is the strongest signal for tucking decisions, and most teams don't look at it before laying out chrome.

## Defaulting disclosure state

When a section *can* start open or closed, choose deliberately:

### Default open

- The section the user is most likely to read or modify.
- The section required to complete the task (if disclosure is in a form).
- The first section in a sequence (so the user has somewhere to land).
- A single-section accordion (if there's only one, it's not really collapsed by purpose).

### Default closed

- Sections that supplement the primary task.
- "Advanced" or "Optional" sections.
- Sections so long they'd dwarf the rest of the page if open.
- Sections used by < 20% of users on a given visit.

### Remember user state

For settings pages and frequent surfaces, remember which sections each user opened previously and restore on next visit:

```js
// On open, persist
sectionToggle.addEventListener('toggle', () => {
  localStorage.setItem(`section-${sectionId}`, sectionToggle.open ? '1' : '0');
});

// On load, restore
const saved = localStorage.getItem(`section-${sectionId}`);
if (saved !== null) sectionToggle.open = saved === '1';
```

Power users who always reopen the same section will appreciate it; novices who never expand it pay no cost.

## What earns primary placement

The primary layer is finite real estate. Be ruthless. A useful triage:

### Always primary

- The page's purpose-defining content. (A user lands on a Reports page; the report is primary.)
- The required actions to complete the typical task. (A checkout flow; "Place order" is primary.)
- Wayfinding chrome that orients the user.

### Usually primary

- Frequently-used controls.
- Status indicators that change meaningfully (notification counts, error states).
- Recently-used items (recents accelerate frequent tasks).

### Sometimes primary

- Customization options that vary by user role.
- Onboarding hints for new users (but not for veterans).
- Contextual help that depends on user state.

### Rarely primary

- Advanced configuration.
- Account management (move to a separate page).
- Marketing, upsells, "what's new."

## What earns tucking

Conversely, candidates for the secondary or tertiary layer:

- **Optional fields** in forms.
- **Power-user filters** in search/list UIs.
- **Customization** of layouts, themes, keyboard shortcuts.
- **Account / billing / security** controls (their own page, not a sidebar accordion).
- **Help and documentation links** (footer or help menu).
- **Legal / compliance links** (footer).
- **Settings the user changes once and forgets** (push to a "Preferences" page).

## A worked example: a settings page audit

Imagine the current Settings page exposes 34 fields across 5 sections in a single scroll-y view. A progressive-disclosure pass might restructure as:

```
Profile (always visible at top)
  Display name
  Email
  Time zone

Notifications (accordion, default closed for users who haven't changed it)
  Email digest
  Mention notifications
  Quiet hours

Workspace (accordion, default closed)
  Workspace name
  Members [link to separate page]
  Default project

Security (separate page; link in nav)
  Password
  2FA
  Sessions
  API tokens

Advanced (accordion, default closed; appears only for users with the appropriate role)
  Webhooks
  Custom CSS
  Feature flags

Danger zone (separate panel at bottom; visually demoted)
  Transfer ownership
  Delete workspace
```

Profile (3 fields) is primary because every user changes their email or name occasionally. Security goes to its own page because it's high-stakes and benefits from its own focused surface. Advanced is conditional. Danger zone is at the bottom and visually distinct — out of the way of accidental engagement.

## Tucking dynamic content

Some content can't be tucked because it changes — notifications, real-time updates, error states. Patterns:

- **Badge on the disclosure trigger.** A "Notifications (3)" trigger tells the user there's something behind it; they can choose to expand.
- **Toast / banner for transient changes.** Auto-dismissing surface that doesn't require user action.
- **Modal for blocking changes.** Forces the user to acknowledge.

Don't bury error states inside collapsed accordions. If a form section has an error, the section must be open (or auto-open on submit failure).

## The "Advanced" label question

When a section is labeled "Advanced," users self-select. Power users open it; novices don't. This is mostly good — it manages expectations. But beware:

- **"Advanced" can be condescending.** If a setting is just a bit unusual, calling it advanced may make users feel othered.
- **"Advanced" can be a dumping ground.** If everything ungrouped goes under Advanced, the label loses meaning. Keep Advanced focused on power-user tools.
- **"Advanced" should be findable for power users.** Don't bury Advanced inside Account inside Settings.

Alternative labels: "Optional," "More options," "Power tools," "For developers." Pick what fits the audience.

## Anti-patterns

- **Hiding the required.** Required form fields tucked behind disclosure. Submit fails; user is confused.
- **Disclosure for the sake of less.** Hiding genuinely-needed controls "to make it cleaner." The user can't do their job.
- **All accordions closed.** A page where every section is collapsed feels empty. Open the first one (or two) so the user lands.
- **Disclosure with no signal.** "More options" with no hint of what's behind. Pair labels with semantic clues ("Advanced filters," "Additional fields").
- **Changing what's primary without telling users.** A long-time user comes back to find a setting they relied on tucked into Advanced. Migration UX matters: announce the change.

## Heuristics

1. **The "what would the typical user need?" test.** For each visible element, ask: typical-user-typical-visit? If no, candidate for tucking.
2. **The analytics audit.** Look at click data per control. <5% of users engage → strong tuck candidate. <1% → strong removal candidate.
3. **The new-user test.** Walk a new user through the surface. Watch for which elements draw their attention vs. confuse them. Tuck the confusers.
4. **The expert-user test.** Walk a power user through the surface. Watch what they reach for that's hidden. Surface those, or improve the disclosure affordance.

## Related sub-skills

- **`progressive-disclosure`** (parent).
- **`progressive-disclosure-disclosure-affordances`** — the specific UI patterns for revealing tucked content.
- **`80-20-rule`** — the analytical method for identifying what's primary.
- **`hicks-law-defaults`** — defaulting disclosure state is itself a Hick's Law mitigation.
