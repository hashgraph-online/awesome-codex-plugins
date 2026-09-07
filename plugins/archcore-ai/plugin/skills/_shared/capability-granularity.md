# Capability Granularity — Sizing Contract for Δ Capability Lists

Plugin runtime asset. Loaded by the `plan` skill together with
`skills/_shared/delta-routing.md`. Companion to
`skills/_shared/spec-contract.md`.

## Anchor

A capability is one behavior an external consumer relies on — external code, a
team, users/UI, or a sibling module — recordable as one `spec` within the
120-line body cap of `skills/_shared/spec-contract.md`.

## Rules

1. Count one capability per consumer-relied behavior, not per file, module, or
   task.
2. WHEN one candidate capability cannot be specified within the spec body cap,
   split it by separable sub-surface and count each part — the same test
   `skills/_shared/spec-contract.md` applies under "Over the cap".
3. WHEN two candidate capabilities always change together and share one
   consumer set, count them as one. [assumption — merge heuristic; revisit
   against recorded routing traces]
4. WHEN `creates` holds more than 5 capabilities, the conductor MUST keep every
   capability and route the initiative as `umbrella`.
5. WHEN `creates` holds more than 5 capabilities, the conductor MUST report the
   count in the route summary, so the user re-scopes deliberately or proceeds.
6. The conductor MUST NOT drop, merge, or defer a capability to reach a count.
7. A behavior nobody outside the change relies on is not a capability; it
   needs no `spec`.

Rule 6 replaces a former soft cap that told the conductor to re-scope an initiative
above 5 capabilities. An initiative that honestly creates eight consumer-relied
behaviors needs eight `spec` documents; `skills/_shared/delta-routing.md` already
routes `creates ≥ 2` to an umbrella `prd` plus one `spec` per capability, at any
count. Refusing to route was a refusal to record the work, not a simplification of
it — the count belongs in the route summary, where the user can act on it.

## Worked boundary

Non-normative examples.

- "CSV export for reports" — one capability: one consumer-relied behavior,
  regardless of file count.
- "Notifications: email, webhook, in-app digest" — three capabilities: three
  consumer surfaces with distinct failure modes.
- "Refactor the retry helper" — zero capabilities: consumers see unchanged
  behavior; the decision delta may still license an `adr` or `cpat`.
