---
title: Keyboard and Focus
impact: CRITICAL
tags: keyboard, focus, tab-order, modals, focus-trap, skip-link
wcag: 2.1.1, 2.1.2, 2.4.1, 2.4.3, 2.4.7, 2.4.11
---

**Rule**: Everything that works with a pointer works with a keyboard alone, in a logical order, with focus always visible and never hidden or trapped.

**Why**: Keyboard and switch users, many screen reader users, and power users navigate without a pointer. iPad, Mac, Android, and web all support keyboards. WCAG requires keyboard operability (2.1.1), no keyboard trap (2.1.2), a meaningful focus order (2.4.3), visible focus (2.4.7), and — new in WCAG 2.2 — focus that is not hidden behind sticky headers or overlays (2.4.11).

### When Building

- **Native interactive elements** are focusable and keyboard-operable by default; custom ones need focusability, Enter/Space handling, and a role (`rules/semantics.md`)
- **Focus order follows reading order** — DOM/view order matches visual order; avoid positive `tabindex`
- **Visible focus** — never remove the focus outline without an equally visible replacement (`:focus-visible` on the web)
- **Modals and sheets**: move focus into them on open, keep it inside while open, close with Escape, and return focus to the trigger on close
- **Menus, tabs, listboxes**: arrow-key navigation per the WAI-ARIA Authoring Practices pattern
- **Skip link** on web pages with repeated navigation ("Skip to content")
- **Not obscured** — sticky headers, cookie banners, and chat widgets must not cover the focused element (`scroll-padding-top` on the web)
- **Route changes in single-page apps** move focus to the new page's heading or main region

### When Auditing

- Tab through every primary flow with no mouse: can every action be reached and completed?
- `outline: none` / `outline: 0` without a replacement
- Custom controls built from `div`/`span` without `tabindex="0"` and key handlers
- Modals that let focus escape behind them, or lose focus on close
- Positive `tabindex` values; focus jumping out of visual order

### Incorrect

```css
*:focus { outline: none; }
```

### Correct

```css
:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }
```

### Alternatives

Touch-only phone apps still need a logical focus order for screen readers and switch control — the same rules apply to accessibility focus even where no hardware keyboard is expected.
