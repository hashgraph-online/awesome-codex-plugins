---
title: Announcements and Status
impact: MEDIUM
tags: live-regions, toasts, loading, async, status-messages, screen-reader
wcag: 4.1.3
---

**Rule**: Changes that happen without a focus change — a toast, a saved state, search results, an error from the server — are announced to screen reader users, politely, without moving their focus.

**Why**: A sighted user sees "Saved ✓" appear; a screen reader user hears nothing unless the change is announced. WCAG 4.1.3 (Status Messages) requires status messages to be programmatically determinable so assistive technology can present them without receiving focus.

### When Building

- **Announce status changes** — "3 results", "Saved", "Uploading 40%", "Message sent" — via a live region on the web (`role="status"` / `aria-live="polite"`) or the platform's announcement API (platform guides)
- **Polite by default**; assertive only for urgent errors that need immediate attention
- **Don't move focus** for a status message — only move focus when the user must act (a dialog, the first form error)
- **Toasts stay long enough** to be read and announced, or can be dismissed and revisited; anything actionable in a toast is also reachable elsewhere
- **Loading states** — announce when loading starts for long waits and when content arrives; mark busy regions (`aria-busy`)
- **Don't over-announce** — one announcement per meaningful change, not every keystroke or progress tick

### When Auditing

- Toasts, snackbars, and inline "Saved" messages with no live region or announcement
- Search and filter results that update silently
- Spinners with no accessible label or completion announcement
- Live regions that announce on every keystroke

### Incorrect

```tsx
{saved && <span className="toast">Saved</span>}
```

### Correct

```tsx
<div role="status" aria-live="polite">{saved ? "Saved" : ""}</div>
```

The live region must exist in the page *before* its content changes; inserting a new live region with text already inside is often not announced.

### Alternatives

When the change happens where the user's focus already is (a toggle they just activated reporting its new state), the control's own state change is the announcement — don't add a second one.
