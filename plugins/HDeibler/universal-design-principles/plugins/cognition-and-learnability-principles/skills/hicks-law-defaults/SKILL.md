---
name: hicks-law-defaults
description: 'Use this skill when the question is what to *pre-select* in a list of options — radio groups, dropdowns, configuration UIs, plan pickers, sign-up flows, settings. A strong default is the highest-leverage Hick''s Law mitigation: most users accept the default, paying almost no decision cost. Trigger when picking what''s selected on first load, when stakeholders argue "shouldn''t we let the user choose?", when designing wizards or onboarding, or when a UI has many options but most users want the same one. Sub-aspect of `hicks-law`; read that first if you haven''t already.'
---

# Hick's Law: defaults as the primary mitigation

Strong defaults are the highest-leverage way to reduce Hick's Law cost. When the system pre-selects the most likely option, the user faces a much smaller decision: "accept the default" or "look at the alternatives." Most users accept; the decision is effectively zero cost. The minority who don't accept now do face the original Hick's Law cost — but only when their preferences differ from the default.

## When to invest in a default

A good default is worth the design effort when:

- **One option is significantly more likely than the others.** If 60–80%+ of users want option X, defaulting to X serves most of them at no cost.
- **The cost of "wrong" is recoverable.** Users can change the default after the fact without losing work.
- **You can predict the right default from context.** User's locale, previous behavior, role, or the immediate task often disclose the right answer.
- **The decision is low-stakes.** Financial commitments, irreversible actions, and privacy-affecting choices should *not* be defaulted; they should be deliberate.

A bad default appears when:

- Options are roughly equiprobable. Picking any one biases the user without serving them.
- The cost of accepting the wrong default is high or hidden.
- The default is set to serve the business (auto-checked "share my data with partners") rather than the user.

## Levels of default

Defaults vary in strength and cognitive cost:

### Level 1: pre-selection (no commitment)

The default option is highlighted/selected, but the user must explicitly confirm to proceed.

```html
<form>
  <fieldset>
    <legend>Email digest</legend>
    <label><input type="radio" name="digest" value="off" /> Off</label>
    <label><input type="radio" name="digest" value="daily" checked /> Daily (recommended)</label>
    <label><input type="radio" name="digest" value="weekly" /> Weekly</label>
  </fieldset>
  <button>Continue</button>
</form>
```

The user sees "Daily" pre-selected. They can change it; they must press Continue regardless. Low-pressure, ethical, effective.

### Level 2: implicit acceptance

The default is set silently; if the user doesn't change it, it takes effect when they continue.

This is appropriate for non-consequential settings (sort order, theme preference). Less appropriate for material commitments.

### Level 3: opt-out (the user must take action to escape the default)

The default takes effect unless the user actively unchecks or selects another option. Common in privacy and notification settings.

This crosses an ethical line in many contexts. Reserve it for choices where the default genuinely serves the user (e.g., critical security notifications on by default).

### Level 4: forced default with disclosure

A choice is made for the user with explicit disclosure — "We've set this for you based on your role; you can change it in settings."

Useful when defaults are derived from earlier signals and the user might wonder why the system "knows" their preference.

## Strategies for choosing the right default

### Use known data

If you know the user's locale, you know their currency, date format, language, timezone. Default to those.

```html
<select name="currency">
  <option value="USD" selected>USD ($)</option>      <!-- defaulted from IP -->
  <option value="EUR">EUR (€)</option>
  <option value="GBP">GBP (£)</option>
  …
</select>
```

If you know the user's role, you know which features they're likely to use; default the dashboard view to those.

### Use the most popular choice

Run analytics. If 70% of teams pick "Standard" plan, default to Standard. If 80% of users want "All notifications," default to All.

This works *until* the popular choice is popular only because it was the default — a feedback loop. Periodically test by flipping the default to a different option and measuring the new acceptance rate; if it's still 70%+, the default is genuinely matching preferences.

### Use the safer choice

When in doubt, default to the option that's hardest to recover from an "incorrect default." Defaulting to "private" is safer than "public" — public-by-mistake leaks; private-by-mistake just requires sharing later.

### Use the recently-used choice

If the user picked an option last time, default to it this time. "Recently used templates," "last upload directory," "previous report filter."

### Use a "Recommended" badge

Pair the default with an explicit signal that it's the recommended choice:

```html
<RadioGroup defaultValue="pro">
  <Option value="starter">Starter</Option>
  <Option value="pro">
    Pro
    <Badge>Recommended</Badge>
  </Option>
  <Option value="enterprise">Enterprise</Option>
</RadioGroup>
```

This is honest — you're disclosing that you have a recommendation — and it tells users "if you don't have a strong opinion, this one's safe."

## When *not* to default

There are cases where forcing the user to choose is the right move:

- **Account creation passwords.** Don't pre-fill or suggest; the user must compose.
- **Payment amounts.** Don't pre-fill values for charity donations or tip amounts beyond a small set of explicit options.
- **Permissions and visibility.** Don't default to "public" or "share with team" without an active selection.
- **High-stakes irreversible actions.** Don't pre-select "Delete" in a confirmation dialog. (Actually invert: pre-select "Cancel" so the destructive path requires deliberate effort.)
- **Where the system genuinely doesn't know.** Asking the user is more honest than guessing.

For these cases, leave the choice unset and disable the proceed button until the user picks. The Hick's Law cost is real but justified.

## Worked examples

### Example 1: a sign-up plan picker

Three plans, one is by far the most popular. Default to it; mark it as recommended.

```html
<form>
  <fieldset class="plan-picker">
    <legend class="sr-only">Pick a plan</legend>
    <label class="plan">
      <input type="radio" name="plan" value="starter" />
      <strong>Starter</strong>
      <p>Free for 14 days. Single user.</p>
    </label>
    <label class="plan plan--recommended">
      <input type="radio" name="plan" value="pro" checked />
      <strong>Pro</strong>
      <span class="recommended-badge">Recommended</span>
      <p>$29/mo. Up to 5 users.</p>
    </label>
    <label class="plan">
      <input type="radio" name="plan" value="team" />
      <strong>Team</strong>
      <p>$99/mo. Up to 25 users.</p>
    </label>
  </fieldset>
  <button class="primary">Continue with Pro</button>
</form>
```

Note the button label *reflects* the default ("Continue with Pro"), so the user is reminded what they're committing to. If they change selection, the label updates.

### Example 2: a notification settings panel

Most users want notifications on, but not at maximum frequency. Default to a sane middle.

```html
<form>
  <fieldset>
    <legend>How often should we email you?</legend>
    <label><input type="radio" name="freq" value="instant" /> Real-time (may be a lot)</label>
    <label><input type="radio" name="freq" value="daily" checked /> Daily digest <span class="hint">(default)</span></label>
    <label><input type="radio" name="freq" value="weekly" /> Weekly digest</label>
    <label><input type="radio" name="freq" value="off" /> Off</label>
  </fieldset>
</form>
```

The explicit "(default)" annotation removes any guessing about why "Daily digest" is selected.

### Example 3: a date range picker

For a "Reports" page, default to a sensible range based on context.

- On first visit: "Last 30 days" (covers most curiosity).
- On return visit: the range the user last selected (recency bias).
- After clicking a "Compare to" toggle: pre-fill the comparison range as "Previous 30 days."

```js
const lastUsedRange = localStorage.getItem('reports.range');
const defaultRange = lastUsedRange ?? 'last_30_days';
```

### Example 4: a "Send to" picker in a messaging app

The user is most likely to message the same people they recently messaged. Surface those as a "Recent" group at the top of the picker; the default is to type to filter.

```
[Search recipient________________]
Recent
  ● Maria Mendoza
  ● Marketing team
  ● Lin Chen
All people
  ● …
```

Recents collapse Hick's Law nearly to zero for repeat tasks.

## Anti-patterns

- **The pre-checked subscription.** "Subscribe to our newsletter" pre-checked at sign-up. Conversion goes up; trust goes down. Don't.
- **The defaulted upsell.** A higher-priced plan pre-selected when the user's stated needs match a cheaper plan. The user finds out at checkout; ill will follows.
- **The hidden default change.** Changing the default in a software update without telling users. Users feel the system "did something" without their consent.
- **The opt-out for material consequences.** Pre-checked "auto-renew at full price" with the opt-out hidden three pages deep. Regulators are paying attention.
- **The incoherent default set.** Defaults across a settings page that contradict each other (notifications ON, but email digest OFF, but in-app quiet hours ON 24/7). Means the system can't actually deliver the user's intent.

## Heuristics

1. **The acceptance-rate test.** Periodically measure: of users who land on this default, what percent accept it? If <50%, the default is wrong; pick a different one. If >85% across many users for many months, the default is doing its job.
2. **The "who does this serve?" check.** For each default, ask: does this default primarily serve the user, or the business? If it's the business, examine whether the user would consent if asked clearly.
3. **The "describe in one sentence" test.** Can you describe what the default *is* and *why* in one plain sentence? If yes, it's defensible. If you can't, it's probably opaque to users too.

## Related sub-skills

- **`hicks-law`** (parent).
- **`hicks-law-menus`** — the complementary case where defaults aren't appropriate (the menu is a list of actions, not a choice with one obvious answer).
- **`hicks-law-pricing`** — defaults are central to pricing tier selection.
- **`satisficing`** — the cognitive principle that explains why defaults work: users accept the first acceptable option.
- **`framing`** — how the default is *labeled* (e.g., "Recommended") affects acceptance rate.
- **`nudge`** (interaction) — defaults are the canonical nudge; treat them as a design responsibility.
