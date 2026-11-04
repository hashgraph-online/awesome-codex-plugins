# Grading Contract

## Step 6: Grade (full and `--grade-only`)

Score each lane A-F, then one overall. For non-Suede work, read "domain truth"
as whatever invariants the product publishes.

- **Correctness:** behavior, edge cases, error paths, async, routing, data
  flow, regression risk.
- **Security and permissions:** auth, secrets, payment, injection, SSRF,
  permission, data exposure fail closed.
- **Data and state:** schemas, migrations, caches, jobs, queues, webhooks,
  retries, idempotency.
- **Domain truth:** public copy, rights, provenance, licensing, product claims
  match the implementation.
- **UX and release behavior:** loading, empty, error, success, mobile, route
  states hold together.
- **Tests and verification:** changed behavior has meaningful tests, builds,
  screenshots, simulator runs, or live readbacks.
- **Deploy readiness:** env vars, flags, migrations, rollback notes, docs, and
  release order are clear.

**What each letter means.** **A:** all lanes pass, runtime-verified, no
follow-ups. **B:** no blockers; named, bounded follow-ups. **C:** a real defect
or unverified risk that could reach production; recommend hold. **D:** a
serious defect likely to cause data loss, auth bypass, broken payments, or a
visible production failure; recommend against shipping and put the choice to
the user. **F:** core behavior broken, an Instant-F hit, or no evidence on a
critical surface.

**Gate follows the grade:** A → `ship`; B → `ship-with-caveats`; C, D, F →
`hold`. A Deploy Safety block or a DIRTY commit rating also moves the gate to
`hold`.

**Grade caps by surface** (state them when they apply):

- **Auth** (login, session, token, middleware, roles): A needs the bypass or
  escalation path tested; B needs happy path plus named caveats; otherwise
  cap at C.
- **Payments and wallets:** A needs failed charge, decline, and replay tested,
  server-side amount and recipient validation, and no silent swallowing; B
  needs happy path plus documented error-path risk; otherwise cap at C.
- **Data migrations:** A needs a documented rollback and a restore tested on
  production-like data (or a justified waiver); B needs a rollback plan; no
  plan caps at D.
- **Public API changes:** A needs verified backward compatibility or a
  versioned migration path; a breaking change with no path caps at C.

**Technical debt** weighs by location. The same pattern costs more where the
risk lives:

| Pattern | Location | Impact |
|---|---|---|
| Function or class doing 5+ unrelated jobs | Payment module | D in Correctness |
| Same | Utility helper | B in Correctness |
| Same 20-line block in 3+ places | Auth flow | C in Security |
| Same | UI component | B in Correctness |
| Reaching across 3+ abstraction layers | Data migration | C in Data and state |
| Hidden module-level state | API handler | C in Correctness |
| Unnamed magic number | Payment amount | C in Correctness |
| Unnamed magic number | UI spacing | P3 only |
| Dead code | Anywhere | Flag only, unless it shadows live code |

Debt alone never blocks a ship unless it hides a P0 or P1. Name it in Required
Upgrades. Never report a C, D, or F without the upgrade that would move it.
