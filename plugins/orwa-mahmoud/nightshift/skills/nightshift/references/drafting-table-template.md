# Drafting Table

> A staging file, not the enforced list. The clock-out gate reads only `punch-list.md` — nothing
> here is gated. Draft and agree items here first, then promote them into `punch-list.md` under
> `## Items` to start the shift.
> This is for known later work, including follow-ups with dependencies. It is not for unresolved
> owner decisions (`parking-lot.md`) or timed catalog work composed through Hunt (`work-orders.md`).

**Item shape** — one top-level checkbox per item; all detail as indented plain `-` sub-bullets
(never a nested checkbox — only the top line is a box, so the gate counts one open item per task).
Every item carries its own **Verify** line, plus a **Commit** line in repository mode or an
artifact receipt in artifact mode.

```text
- [ ] **1. <title>.**
  - <what to build, plainly>
  - Verify: <the commands that must pass before ticking>
  - Commit: `<type: message>`
```

In artifact mode record the receipt in `$NS/receipts/` with `runtime/write-receipt.sh` (native Windows:
`runtime\windows\write-receipt.ps1`) instead of a conventional git subject.

**Order = dependency order.** Top → bottom; nothing is built twice.

---

(empty — draft items here, then promote the agreed ones into the punch list)
