---
title: System Status & Micro-Feedback
impact: HIGH
tags: feedback, loading, progress, response-time, microinteractions, haptics
---

**Rule**: Every action gets a visible response, fast. Show what is happening during waits, confirm outcomes, and match the feedback to the response time.

**Evidence**: Nielsen's heuristic #1, visibility of system status. Response-time limits of ~0.1 s (feels instant), ~1 s (flow kept), ~10 s (attention lost) — Miller 1968 (AFIPS); Card, Robertson & Mackinlay 1991 (CHI); Nielsen, *Usability Engineering* (1993). Doherty & Thadani 1982, "The Economic Value of Rapid Response Time" (IBM report) — sub-second responses raised user productivity (the popular "400 ms threshold" is a later simplification). Saffer, *Microinteractions* (2013) — small feedback moments have a trigger, rules, feedback, and loops/modes.

### When Building

| Wait | Feedback |
|---|---|
| < 0.1 s | Pressed/active state only — the result itself is the feedback |
| 0.1–1 s | Subtle busy state on the control (spinner in the button, disabled to prevent double submit) |
| 1–10 s | Skeleton screen or progress indicator where the content will appear |
| > 10 s | Determinate progress (percent or steps), let the user leave, notify when done |

- **Micro-feedback** — confirm small outcomes where they happen: "Copied" next to the copy button, a checkmark on save, a toggle that visibly switches, a count that updates. Ask: would the user wonder whether it worked? If yes, it needs feedback
- **Optimistic updates** for likely-to-succeed actions (like, reorder, toggle) — update at once, roll back with a message on failure
- **Saved state is visible** — "Saved" / "Saving…" / "Offline — will sync" for auto-saving editors
- **Haptics on mobile** for meaningful outcomes, not every tap (platform APIs in the platform guides)
- **Errors are status too** — say what failed and what to do (`rules/microcopy.md`)

### When Auditing

- Buttons that trigger async work with no pending state (double-submit risk)
- Full-screen spinners where a skeleton or inline state would keep context
- Copy, save, delete, and send actions with no confirmation of success
- Background work (uploads, exports) with no progress or completion signal

### Incorrect

```tsx
<Button onPress={save}>Save</Button>
```

### Correct

```tsx
<Button onPress={save} disabled={saving}>
  {saving ? "Saving…" : saved ? "Saved ✓" : "Save"}
</Button>
```

### Why This Matters

Without feedback, users repeat actions (duplicate orders, double posts), abandon working flows, or assume the app is broken. Fast, visible feedback is what makes software feel responsive — often more than actual speed.

### Alternatives

Silent success is right when the result is itself visible (typing, dragging, a toggle whose state is the feedback). Extra confirmation there is noise. Motion design for the feedback — duration, easing, springs — belongs to an animation skill.
