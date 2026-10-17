# foundation-format.md — the Project Foundation section (handoff, first cycle only)

The format contract for the **Project Foundation** section of the handoff: the authoring form when
`ready` writes it, and the reading rules when `go` consumes it. Used **only in the first cycle** (no
harness exists yet). Shared byte-identical between `ready` and `go`.

**When it is written.** `ready` writes the Foundation into `handoff.md`'s Foundation section **at the
SPEC step — together with `spec.md`, not deferred to HANDOFF** — so the inline fidelity review can
verify a *written* Foundation (the rest of the handoff's governing parts still wait for the plan and
are filled at HANDOFF). In a first cycle the Foundation is **always produced**; `go` relies on that as
an invariant (see "First-cycle precondition" below).

## Purpose

The first cycle's CALIBRATE and the first-cycle foundation design in ELICIT produce project-wide
foundation knowledge that does *not* belong in spec.md. spec.md carries only **this task's**
execution contract; the **project-wide** foundation — the full domain model, architecture decisions,
security model, conventions, future scope — goes in the handoff's Project Foundation. This split
keeps `go` from over-implementing (it executes the task's spec, not the whole project) while giving
it project context to implement *within*.

## Structure — four fixed sections

Structure the Foundation as **four sections**. Do **not** organize it by `docs/` filename — naming
sections after harness files invites box-filling (reward-hacking) when `go` later builds the harness;
keep the Foundation about the *project*, and let `go` map it to files.

- **Section 1 — Project identity.** What, for whom, at what scale, under what constraints (the
  CALIBRATE result).
- **Section 2 — Domain model.** Entities, relationships, state transitions, rules, invariants, edge
  cases (the domain-design result) — the **whole project's** domain, as context. The thickest section.
  (Do **not** label individual entities `[implementation target]` / `[project context]` — those
  per-entity tags are clutter, and the distinction is already carried where it belongs: `spec.md` holds
  *this task's WHAT* (what `go` implements), and the Foundation as a whole is non-executable context.
  `go` builds the spec, reads the Foundation as context — no per-entity tag needed.)
- **Section 3 — Technical decisions.** Architecture, security model, conventions, operations (the
  technical-design result). **Only decisions the user confirmed.**
- **Section 4 — Future scope.** What is planned for the project but out of this task's scope. `go`
  does **not** implement it — it is the context for judging that the current implementation stays
  compatible with the future.

## Labeling rule — separate from the handoff's governing role

Begin the Foundation with an explicit label: *"Non-executable project context — `go` reads this
section as context + harness source, not as an implementation target."* The handoff's existing
governing parts (Document Roles, Hard Gates, conflict resolution, ...) stay clearly separated from the
Foundation, so `go` never confuses a governing instruction / hard gate with project context. The
Foundation is a **conditional expansion inside the handoff's "supplement" role**, not a new authority.

## How `go` uses it (dual use)

- **At execution.** `go` reads the Foundation when it first reads the handoff → it implements the
  spec's task *with* project context. (E.g. a Foundation that records a role-based permission model
  makes `go` design the spec's "auth implementation" with role support in mind.)
- **At harness creation.** Each Foundation area maps to `docs/` files per `go`'s `harness-format.md`:
  domain model → business-rules.md; technical decisions → architecture.md + security.md +
  standards.md + operations.md; identity → the entry-point overview; future scope → status.md's
  "remaining."

## Lifetime

Created in the first cycle only. After `go` creates the harness, the 3-doc (handoff included, with
its Foundation) is archived to `.dryforge/NNN/`. From the next cycle on, the harness takes over the
project-context role, so no Foundation is written.

## First-cycle precondition (Foundation is always present — no degrade)

The Foundation is a **required first-cycle artifact**, not optional: `ready` always produces it
through its first-cycle ELICIT loop. So `go` treats its presence as an **invariant**, not something to
work around. If `go` runs a first cycle (no `status.json`) and the handoff carries **no Foundation
section**, that is a **precondition violation, not a degrade path** — `go` does **not** guess a
Foundation from spec + code. It **stops and asks the user to regenerate the 3-doc via `ready`**
(escalate-don't-guess). (This is a fail-fast check, not a fallback mode — the operational rule lives
in `go`'s `harness-lifecycle.md`.)

## Content quality

The same content-quality bar that governs the harness (non-derivability, work-changing, density,
project-specificity, consequence-of-absence) applies to the Foundation too. A thick Foundation is
normal, but every sentence must carry a core fact — not padding.

## Universality guard

Stack-agnostic. The four sections hold project-specific identity, domain, decisions, and scope in the
project's own terms — no stack assumed, discovered at runtime.
