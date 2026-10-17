---
name: recognition-recents-and-suggestions
description: 'Use this skill when designing surfaces that accelerate repeat tasks through recents, frequently-used items, and contextual suggestions. Trigger when designing pickers used repeatedly, command palettes, navigation that should adapt to user behavior, or any surface where a returning user shouldn''t have to retype their frequent destinations. Sub-aspect of `recognition-over-recall`; read that first.'
---

# Recents, frequents, and contextual suggestions

Recognition is fastest when the user doesn't even have to scan a long list — when the system anticipates and surfaces the likely options first. Recents, frequents, and predictive suggestions all leverage this: the user's likely target is at the top, often without typing anything.

## Patterns

### Recents

A list of items the user has recently interacted with. Surfaced at the top of pickers, navigation, or empty search inputs.

```html
<combobox label="Recipient">
  <input placeholder="Search recipients..." />
  <listbox>
    <group label="Recent">
      <option>Maria Mendoza (last sent: yesterday)</option>
      <option>Marketing Team (last sent: 3 days ago)</option>
    </group>
    <group label="All">...</group>
  </listbox>
</combobox>
```

Most users compose for a small set of recipients repeatedly; recents collapse the recall task.

### Frequents

Items used most often (regardless of recency). Useful when usage is clustered around a small set but not necessarily recent.

```
Frequently used apps:
  • Email
  • Slack
  • Code editor
  • Browser
```

A common laptop dock pattern.

### Recommended / suggested

System-predicted likely options based on context. Examples:

- A "for you" feed.
- "People you may know."
- "Suggested replies" in messaging.
- "Suggested tags" when categorizing.

Recommendations work when the prediction is good. Bad recommendations (irrelevant, wrong) are worse than none — they distract and erode trust.

### Pinned / favorites

User-curated frequently-accessed items. Less algorithmic than recents/suggestions; user-explicit.

```
Pinned:
  ★ Q4 Planning Doc
  ★ Team OKRs
  ★ Customer feedback dashboard
```

Combine with recents and suggestions for a complete fast-access surface.

### Smart defaults

Pre-fill fields with predicted values based on context (signed-in user, recent inputs, time of day, location).

```html
<form>
  <label>Country
    <select name="country">
      <option value="US" selected>United States</option>
      <!-- selected because of user's IP location -->
    </select>
  </label>
</form>
```

The user can change but rarely needs to.

## When recents/suggestions hurt

- **When the prediction is bad.** Wrong recents distract; the user has to filter past them.
- **When privacy matters.** Recents reveal user history; in shared-device contexts this can leak information.
- **When the option set is critical to the task.** A "recent" suggestion in a destructive action might bias the user toward the wrong choice.

For high-stakes actions, present the full set without privileging recents.

## Privacy and recents

Recents reveal user activity to anyone with screen access. Considerations:

- **Don't surface recents on shared/public devices** unless explicitly opted in.
- **Provide a "clear recents" option.**
- **Don't leak across tenants** (a recent in workspace A shouldn't appear when the user switches to workspace B).
- **Be cautious with sensitive contexts** (health apps, finance apps, dating apps).

## Anti-patterns

- **Stale recents** that include items the user no longer cares about, never expiring.
- **Recents that span privacy boundaries** (work email recents in personal context).
- **Suggestions that don't update** as the user's behavior changes.
- **Surfacing recents in wrong contexts** (showing "recent files" on a different user's account).

## Heuristics

1. **The "would the user pick this without typing?" check.** For each picker, ask: in the median case, can the user get to their target without typing? If yes, recents are doing their job.
2. **The recents-quality audit.** Sample your recents lists. Are they actually relevant to current intent?
3. **The privacy review.** What do recents reveal? Should they be hidden by default in some contexts?

## Related sub-skills

- **`recognition-over-recall`** (parent).
- **`recognition-pickers-and-palettes`** — picker patterns recents augment.
- **`satisficing`** — recents enable satisficing by surfacing acceptable options first.
- **`hicks-law-defaults`** — defaults and recents both reduce decision cost.
