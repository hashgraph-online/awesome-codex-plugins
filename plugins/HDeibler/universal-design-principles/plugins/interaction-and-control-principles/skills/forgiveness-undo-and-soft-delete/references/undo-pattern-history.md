# Undo and soft delete: pattern history and reference

A reference complementing `forgiveness-undo-and-soft-delete` with deeper context on how reversibility patterns evolved and where they fit.

## Brief history of undo

The earliest computer undo dates to the 1970s — Larry Tesler at Xerox PARC implemented one-step undo in the Gypsy text editor. The IBM Common User Access guidelines (1987) standardized Cmd-Z (Mac) and Ctrl-Z (Windows). Multi-level undo became standard in productivity software through the 1990s.

The pattern has continued to evolve:

- **Single-level undo** (early word processors): one step back, then irreversible.
- **Multi-level undo stack** (modern editors): unlimited or bounded backsteps.
- **Branching undo / version history** (Git, Photoshop's history palette, Google Docs): each state preserved; user can return to any.
- **Operational transforms / CRDTs** (collaborative editors): undo in multi-user environments respects concurrent edits.

Each evolution increased the "safe to explore" surface for users.

## Soft-delete as a database pattern

The soft-delete pattern (mark a row as deleted rather than removing it) has been standard in production databases for decades. It enables:

- User-initiated recovery within a window.
- Compliance / audit (some regulations require retaining deleted data for periods).
- Cascade-delete safety (if a related row was wrongly deleted, the cascade impact can be undone).
- Background cleanup decoupled from user action.

Implementation: a `deleted_at` timestamp column. Default queries filter out non-null. Background jobs hard-delete rows past the recovery window.

## "Undo Send" — Gmail's pattern

Gmail introduced "Undo Send" in Gmail Labs (2009), made it default in 2015. The pattern:

- User clicks Send.
- UI shows "Sending..." with an "Undo" link.
- For 5–30 seconds (configurable), the message is held in an outbox state.
- If Undo is clicked, the message returns to draft.
- After the window, the message actually transmits.

This was a quiet revolution because email had been considered irreversible since SMTP was designed in 1982. Gmail's "well, not really irreversible — we'll just delay a bit" reframing has since spread to messaging apps, comment systems, social posts.

## Recovery window calibration

The right recovery window depends on user context and storage cost:

| Action | Typical window | Reasoning |
|---|---|---|
| Toast undo for archive | 5–10 sec | Reflexive correction |
| Email undo-send | 5–30 sec | Catches "wait, that wasn't right" moments |
| Soft-deleted email / file | 30 days | Vacation-tolerant |
| Soft-deleted account | 30–90 days | Compliance + reconsideration window |
| Document version history | Unlimited | Storage cost is small; recovery value is high |

Shorter windows save storage; longer windows save user trust. For most consumer products, lean toward longer.

## Undo across collaborative editing

In multi-user editors (Google Docs, Figma), undo gets complicated:

- Whose actions does Cmd-Z reverse — yours or anyone's?
- What if your action depended on someone else's that's still pending?
- What if an undo creates a conflict with someone else's edit?

Modern collaborative editors solve this with operational transforms (OT) or conflict-free replicated data types (CRDTs). The user-facing rule typically: Cmd-Z reverses *your* actions only; you can't undo other people's edits.

## Discoverability of recovery

A reversibility mechanism users don't know exists doesn't help. Patterns:

- **Toast Undo button** — its own discovery; users see and learn.
- **Trash / Archive nav entry** — signals deleted items can be recovered.
- **Onboarding mention** — explicit teaching of version history.
- **Empty-state hints** — when a user lands in a recovery view, explain it.

If users file tickets to recover data they could have restored themselves, your recovery affordance is too quiet.

## Resources

- **Tesler, L.** historical writings on the Gypsy editor and the origin of undo.
- **Memon, A.** *Designing Undo* — pattern analysis.
- **Gmail's "Undo Send" engineering blog** — public account of the design choice.
- **Google Docs version history documentation** — illustrates the version-history pattern at scale.
