---
name: hicks-law
description: 'Use this skill whenever a design has many options the user must choose among — menus, navigation, pickers, plan tiers, settings panels, action toolbars, lists of templates, anything that asks "which one?" Trigger when the user is laying out a navigation menu, designing a settings page, picking the structure of a wizard, building a country/timezone/currency picker, designing a pricing table, or reviewing a UI where users hesitate over which control to use. Trigger when there''s debate about "should we add another option?" — Hick''s Law is the principle that costs the option a price. Routes to sub-aspect skills for menus, defaults, and pricing.'
---

# Hick's Law

Hick's Law (more precisely, the Hick-Hyman Law) is the empirical observation that the time required to make a decision among a set of options grows with the logarithm of the number of options. Stated as a formula:

```
T = b · log₂(n + 1)
```

Where T is decision time, n is the number of equally likely choices, and b is a constant determined by the cognitive context. The +1 accounts for the time to begin processing the choice set at all. The logarithmic growth is the design-relevant insight: doubling the number of options does not double decision time, but it does add a roughly constant increment each time.

## Definition (in our own words)

When a user must select one option from a set, the time and cognitive effort required to make that selection rise as the set grows — but not linearly. The user can scan and pick from a small set quickly; they need progressively more time as the set grows; and beyond a certain size (typically around 7–10 options for a flat list) they switch from scanning to searching, which is a different and slower mode.

## Origins and research lineage

- **Hick (1952)** measured reaction time as a function of the number of stimulus alternatives in a simple keypress task. He found a logarithmic relationship.
- **Hyman (1953)** extended this with similar results across varied stimulus types, confirming the general law.
- **Card, Moran & Newell (1983)** in *The Psychology of Human-Computer Interaction* incorporated Hick's Law into the early model human processor framework that grounded decades of HCI design.
- **Modern critiques** (e.g., Seow 2005) note that Hick's Law strictly applies to highly practiced, equally-likely choices among visually distinguishable items. Real-world UI choices often violate these conditions — items aren't equally likely, users aren't fully practiced, items have semantic content the user must read. The law is a *guide*, not a measurement.

The takeaway: more options is more decision cost, the cost grows sub-linearly, and beyond about 7 options the dominant cost shifts from "scan and pick" to "search the list."

## Why Hick's Law matters

In product design, every option you put in front of the user is paid for in two currencies: **decision time** (the user must consider it) and **decision fatigue** (the user has fewer mental resources for the next decision). On a single screen, the cost of one extra option is small. Across a workflow with many decision points, the costs compound.

Designs that respect Hick's Law feel "easy" — users move through them without stalling. Designs that ignore it feel "complicated" — users hover, deliberate, and sometimes abandon.

## When to apply

- **Navigation IA.** Top-level navigation should typically be 5–7 items. Beyond that, the user can't hold the structure in working memory while scanning.
- **Action toolbars.** A toolbar with 12 buttons asks a Hick's Law question on every glance. Cap visible actions; tuck the rest into menus or palettes.
- **Pickers.** Country / timezone / currency / template pickers can have hundreds of items. Don't make the user choose from a flat list of 195 countries — switch to a different interaction (search, recents).
- **Wizards.** Multi-step flows with many branches at each step compound the law: 4 choices × 4 choices × 4 choices = 64 paths to consider, even if the user only walks one.
- **Settings.** A settings page with 30 toggles asks the user to evaluate 30 options. Group, default, and progressively disclose.

## When NOT to apply (or when to misapply it)

Hick's Law is sometimes invoked to justify removing options that users actually need. Beware of these failure modes:

- **The "fewer-is-always-better" trap.** Some tasks have irreducible complexity — a tax form genuinely has 50 fields. Hick's Law doesn't say "remove fields"; it says "structure the choices so the user faces fewer at once."
- **Assuming Hick's Law applies to text input.** Free-text input isn't choosing from a set; it's recall. Hick's Law doesn't apply directly. (Recognition over Recall does — see that principle.)
- **Assuming all options are equally weighted.** When one option dominates probability (e.g., 80% of users want "Pro" plan), the cost is closer to "scan for the obvious one and click" than to a pure Hick's Law decision. Strong defaults change the equation.
- **In expert contexts.** Practiced users on familiar tools can navigate large option sets quickly via spatial memory and shortcuts. A power-user IDE can have 200 menu items because experts don't *scan* them; they fly to known locations.

## Strategies for reducing Hick's Law cost

### 1. Reduce the count

The most direct strategy. Audit the option set: which options are rarely used? Hide them behind "More" / "Advanced" / a command palette. The remaining set should be small enough to scan at a glance.

The 80/20 rule pairs naturally with Hick's Law here: surface the 20% of options that handle 80% of cases; tuck the rest.

### 2. Group the options

A flat list of 30 items is hard. Three groups of 10 items, each with a heading, is much easier — the user makes a fast group choice (Hick's Law on 3), then a slower within-group choice (Hick's Law on 10).

```
Flat (Hick's cost: log₂(31) ≈ 4.95)
  Item 1 … Item 30

Grouped (Hick's cost: log₂(4) + log₂(11) ≈ 2 + 3.46 = 5.46)
  Group A
    Item 1 … Item 10
  Group B
    Item 11 … Item 20
  Group C
    Item 21 … Item 30
```

The arithmetic suggests grouping is *worse* by raw Hick's Law math. It isn't, in practice, because:

- The user often only needs items in one group (cognitive load is on log₂(4) + log₂(11), not their sum).
- Group headings make the structure recognizable and learnable — repeat visits are faster.
- Visual chunking aids working memory.

The math underestimates how badly humans handle long flat lists.

### 3. Provide a strong default

If you can pre-select the most likely option, you've cut the choice from N to "1 (the default) or N−1 (everything else)." Most users accept the default, so most users pay almost no decision cost.

This is the single highest-leverage Hick's Law strategy: a good default eliminates the decision for most users.

### 4. Switch interaction mode for very large sets

Beyond ~10 options, scanning becomes search. The right interaction is no longer a `<select>` or radio group — it's a typeahead `combobox` or a `command palette` where the user types to filter. Filter-as-you-type collapses Hick's Law into the much faster Recognition-over-Recall.

```
≤ 5 options:  radio buttons or segmented control (all visible, instant pick)
≤ 10 options: select dropdown
≤ ~20 options: select with categories
> 20 options: combobox / typeahead / command palette
```

### 5. Defer choices to the right moment

A common Hick's Law mistake: presenting many options up-front when the user hasn't yet supplied the context that would narrow them. Defer.

- A "Send a notification" form that asks "channel? (email/SMS/push/Slack/Teams) frequency? (instant/digest/weekly) audience? (everyone/admins/me)" before the user even has a draft — high Hick's cost. Better: let the user write the message first, then pick channel.

### 6. Predict and rank

If you can predict which options the user is likely to want (from their history, role, recency), put those at the top with a "Recent" or "Suggested" group. The user often finds their option without scanning the full list.

## Worked examples

### Example 1: country picker

```html
<!-- Anti-pattern: 195 countries in a flat select -->
<select>
  <option>Afghanistan</option>
  <option>Albania</option>
  …
  <option>Zimbabwe</option>
</select>
```

Decision cost is high (effectively a search, not a scan). Plus, the dropdown UI doesn't allow type-to-find effectively.

```html
<!-- Right: combobox with typeahead, plus recents -->
<combobox>
  <input placeholder="Search country" />
  <listbox>
    <group label="Recent">
      <option>United States</option>
      <option>Canada</option>
    </group>
    <group label="All countries">
      <option>Afghanistan</option>
      …
    </group>
  </listbox>
</combobox>
```

The user types "ger," sees Germany, picks it. Hick's Law collapsed to recognition.

### Example 2: navigation

```html
<!-- Anti-pattern: 14 top-nav items -->
<nav>
  <a>Home</a><a>Dashboard</a><a>Projects</a><a>Tasks</a><a>Reports</a>
  <a>Calendar</a><a>Files</a><a>Inbox</a><a>Notifications</a><a>Team</a>
  <a>Customers</a><a>Vendors</a><a>Settings</a><a>Help</a>
</nav>
```

User can't decide where to start; eyes sweep, fatigue.

```html
<!-- Right: 5 top-level groups, with sub-nav under each -->
<nav>
  <a>Work</a>           <!-- Dashboard, Tasks, Calendar, Files -->
  <a>Inbox</a>          <!-- Notifications, Messages -->
  <a>People</a>         <!-- Team, Customers, Vendors -->
  <a>Reports</a>
  <a>Settings</a>
</nav>
```

Five groups; user picks one in <1 second; sub-nav resolves the within-group choice.

### Example 3: settings

```html
<!-- Anti-pattern: 30 toggles in a flat list -->
<form>
  <label><input type="checkbox" /> Send daily summary email</label>
  <label><input type="checkbox" /> Send weekly summary email</label>
  <label><input type="checkbox" /> Notify on mention in any channel</label>
  …(27 more)
</form>
```

The user is asked to evaluate 30 boolean choices, most of which they don't care about.

```html
<!-- Right: grouped, with strong defaults pre-selected -->
<form>
  <fieldset>
    <legend>Email digest</legend>
    <label><input type="radio" name="digest" value="off" /> Off</label>
    <label><input type="radio" name="digest" value="daily" checked /> Daily (recommended)</label>
    <label><input type="radio" name="digest" value="weekly" /> Weekly</label>
  </fieldset>

  <fieldset>
    <legend>Push notifications</legend>
    <label><input type="radio" name="push" value="off" /> Off</label>
    <label><input type="radio" name="push" value="mentions" checked /> Mentions only (recommended)</label>
    <label><input type="radio" name="push" value="all" /> All activity</label>
  </fieldset>

  <details>
    <summary>Advanced (Slack, calendar, custom rules)</summary>
    …(advanced settings, hidden by default)…
  </details>
</form>
```

Now the user faces 3 + 3 = 6 visible choices, both with sensible defaults. Most users accept the defaults. Power users open the disclosure.

### Example 4: a wizard

A 4-step wizard with 4 choices at each step has 256 logical paths. The user sees only 4 at a time, so per-step cost is manageable. But cumulative decision fatigue can be high.

Mitigations:
- Show progress (Stepper) so the user knows the end is in sight.
- Default each step's choice based on prior steps when possible.
- Allow "I'll come back to this" with a save-and-resume.

## Anti-patterns

- **The "kitchen-sink" toolbar.** All possible actions visible at once. Users freeze; the toolbar becomes wallpaper.
- **The "expert mode by default" trap.** A new user is shown the same option-rich interface as a power user. They bounce.
- **Hidden costs in disclosure.** Putting 20 options inside a "More" disclosure doesn't reduce Hick's Law cost; it just makes the user pay it after a click. Sometimes correct (advanced rarely-used settings), sometimes a procrastination of the real fix.
- **Asking before you have to.** A configuration step at sign-up that asks 8 questions before the user has used the product. Defer until the user has context to answer.

## Heuristics

1. **The 7-second test.** Time how long it takes a fresh user to pick the right item from your list. >7 seconds suggests Hick's Law cost is too high; restructure.
2. **The Pareto check.** Look at usage analytics. If 80% of usage is concentrated in 20% of options, surface that 20%; demote the rest.
3. **The "default-acceptance" rate.** Pick a setting where you have a default. What percent of users keep the default? If high, the default is doing its Hick's Law work. If low, your default is wrong (or the question shouldn't have a default).

## Related principles

- **`80-20-rule`** — partner principle; identifies *which* options to surface and which to demote.
- **`recognition-over-recall`** — the cognitive shift that lets typeahead collapse Hick's Law for very large sets.
- **`progressive-disclosure`** — the structural strategy for hiding the long tail.
- **`chunking`** — the perceptual basis for why grouped options outperform flat ones.
- **`satisficing`** — users pick the first acceptable option; defaults exploit this.
- **`flexibility-usability-tradeoff`** (interaction) — adding options gives flexibility *and* costs usability; Hick's Law quantifies the cost.

## Sub-aspect skills

- **`hicks-law-menus`** — applying the law to dropdowns, command palettes, navigation menus.
- **`hicks-law-defaults`** — using defaults as the primary Hick's Law mitigation.
- **`hicks-law-pricing`** — applying the law to plan/tier selection where the choice itself is the conversion event.
