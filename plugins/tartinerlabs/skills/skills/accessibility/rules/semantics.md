---
title: Semantics, Names, and Roles
impact: CRITICAL
tags: screen-reader, roles, labels, headings, aria, native-elements
wcag: 1.3.1, 4.1.2, 2.4.6
---

**Rule**: Every interactive element exposes a name, a role, and its state to assistive technology. Use the platform's native elements, which do this for free; add accessibility attributes only where native elements cannot.

**Why**: A screen reader only knows what the code tells it. A `div` with a click handler is announced as plain text, an icon button without a label as "button" — the user cannot tell what it does. WCAG 4.1.2 (Name, Role, Value) and 1.3.1 (Info and Relationships) require this information to be programmatically available.

### When Building

- **Native first** — `<button>`, `<a href>`, `<input>`, `<select>` on the web; `Button`, `Toggle`, `Picker`, `Link` in SwiftUI; Material components in Compose; `Pressable` with a role in React Native. The first rule of ARIA: if a native element does the job, use it instead of ARIA
- **Every control has a name** that says what it does, not what it looks like — "Delete project", not "trash icon"
- **State is exposed** — selected, checked, expanded, disabled, busy — through the native element or the platform's state API, not only visually
- **Headings are marked as headings** so screen reader users can jump between sections (web `<h1>`–`<h6>`, SwiftUI `.isHeader`, Compose `heading()`, RN `accessibilityRole="header"`)
- **Group what belongs together** — a list row with title, subtitle, and value is one element with one combined label, not three separate stops
- **Hide decoration** from assistive technology (decorative images, dividers, duplicate icons)
- **Landmarks on the web** — `header`, `nav`, `main`, `footer` so users can skip to content

### When Auditing

- Click/tap handlers on non-interactive elements (`div`, `View`, `Text`) without a role
- Icon-only buttons and links with no accessible name
- Custom toggles, tabs, and menus that don't expose state
- Visual headings that are styled text, not headings
- Several focus stops for what is visually one item

### Incorrect

```tsx
<div className="icon-btn" onClick={remove}><TrashIcon /></div>
```

### Correct

```tsx
<button type="button" onClick={remove} aria-label="Delete project">
  <TrashIcon aria-hidden="true" />
</button>
```

### Alternatives

When a native element truly cannot be used (a complex custom widget), follow the matching WAI-ARIA Authoring Practices pattern exactly — role, states, and the full keyboard model. Partial ARIA is worse than none: it promises behaviour that isn't there.
