# Spec Content Contract

Plugin runtime asset. Loaded by skills creating specs: `capture` (Step 3, spec path),
`decide` (architecture cascade in `skills/decide/references/continuations.md`).
Companion to `skills/_shared/precision-rules.md`.

## What a spec is

The durable contract of a **boundary other code or teams depend on** — one API,
interface, schema, protocol, or component with externally-observable behavior. A spec
exists so anyone touching that boundary reads one authoritative description of how it
must behave, instead of re-deriving it from drifting code or from an ADR (which records
only *why*). A spec may be written **after** code (capture the contract of what exists)
or **before** it (specify the contract to build). One subject per spec.

## When NOT to write a spec

- Requirements / what is needed → `prd` (or ISO `syrs` / `srs`)
- Task breakdown / execution order → `plan`
- Rationale / why a choice was made → `adr`
- Non-normative reference (tables, registries, glossaries) → `doc`
- Team-wide human practice ("always do X") → `rule`
- An internal helper with no external consumers → not a spec

## Mandatory sections

1. **Purpose & Scope** — the one boundary this spec is normative for, and what it does
   not cover. MUST name the subject and its external consumers.
2. **Contract Surface** — the externally-observable interface: inputs, outputs, and the
   canonical identifier (`@path/to/file`) of each interface. MUST reference, not
   reproduce, source definitions — copied signatures go stale against the code.
3. **Normative Behavior** — behavioral requirements in RFC 2119 language
   (MUST / SHOULD / MAY), each numbered for traceability.
4. **Constraints & Invariants** — hard limits (each with a rationale) and conditions
   that MUST always hold, listed separately.
5. **Error Handling** — error conditions with response and recovery; failure semantics
   (retriable? idempotent? timeout behavior?).
6. **Conformance** — what makes an implementation correct: satisfies all MUST
   requirements, all invariants, and all error-handling rules.

## Body cap

- **Default: ≤ 80 lines.** Six mandatory sections above, each a handful of
  numbered/bulleted points — the "reference, don't reproduce" rule (Forbidden
  section below) is what keeps a spec this short even for a complex boundary.
- **Flagship (size/churn-gated, `/archcore:init` hotspot synthesis only): ≤ 120
  lines.** A hotspot module clearing `LOC > 3000` OR top-quartile churn
  (`skills/init/lib/detect-hotspots.md` "Flagship specs") MAY compose at this
  raised cap instead of splitting — see that catalog for the decomposition
  alternative (≤ 3 sub-specs by separable sub-surface, each back at the default
  ≤ 80-line cap). The extra room goes to Normative Behavior / Constraints &
  Invariants, never to reproducing source.

## Status (init-synthesized specs)

A hotspot `spec` synthesized by `/archcore:init` (Tier-2) is created with
`status: draft` in every case — it is derived heuristically from source + tests,
not authored or reviewed, so the user confirms it before it becomes canon. Same
rationale, and same default, as a heuristic-derived cross-cutting `rule`
(`skills/_shared/rule-contract.md`). This status default is specific to init's
synthesis path; a spec authored via `/archcore:capture` or `/archcore:decide`
follows that skill's own status convention.

## Forbidden in the body

- Decision rationale ("we chose JWT because…") → belongs in a linked `adr`.
- General reference material (glossaries of everything, inventories) → belongs in a `doc`.
- Sequential how-to steps ("first call X, then Y") → belongs in a `guide`.
- A section enumerating other `.archcore/` documents (`## Related Documents`,
  `## References` listing ADRs/specs/rules). Cross-document links live in the relation
  graph via `mcp__archcore__add_relation`. The body MAY cite source code
  (`@path/to/file`), schemas, and external authorities. See
  `skills/_shared/precision-rules.md` Rule 5.

## Rationale

The contract surface + RFC 2119 normative behavior + conformance criteria follow the
form used by interface specifications (OpenAPI, protobuf, RFC-style protocol specs):
precise enough to implement against and to check compliance. The "reference, don't
reproduce" rule keeps the spec from becoming a second, drifting copy of the code it
describes — the spec states the *contract*, the code remains the implementation. The
"depended-on boundary with external consumers" gate is what separates a spec from a
`doc` (reference) or an `adr` (rationale): write one when other code must trust how this
boundary behaves.

## Examples

### Good (scope)

```markdown
## Purpose & Scope
This spec defines the webhook **delivery** contract: payload format, delivery
guarantees, retry policy, and signature verification. Normative for the delivery
service (@internal/webhooks/deliver.go); consumed by external subscriber endpoints.
Out of scope: the webhook **management** API (separate spec).

## Contract Surface
- `Deliver(event Event) (Receipt, error)` — see `@internal/webhooks/deliver.go`.
- Payload schema: `@internal/webhooks/schema.json` (referenced, not reproduced).

## Normative Behavior
1. The service MUST sign every payload with HMAC-SHA256 over the raw body.
2. The service MUST retry failed deliveries with exponential backoff, up to 5 attempts.
3. A 2xx response MUST be treated as delivered; all other codes MUST trigger retry.

## Constraints & Invariants
- Constraint: payload size MUST NOT exceed 256 KB (downstream gateway limit).
- Invariant: each event is delivered at-least-once; the receipt ID is stable across retries.

## Error Handling
- 5xx / timeout → retriable; retry per the backoff schedule. Delivery is idempotent by event ID.
- Retries exhausted → mark `failed`, emit `delivery.failed`; no further automatic attempts.

## Conformance
An implementation is conformant when it satisfies behaviors 1–3, preserves the
at-least-once invariant, and follows the error-handling rules above.
```

### Bad (scope)

```markdown
## Purpose
This spec covers the webhook system. We chose webhooks because polling was slow.
First, register an endpoint, then send events to it. See the table of all event types.
```

(Too broad, mixes rationale + how-to + reference. Split by subject — one subject per
spec; move the "why" to an `adr`, the steps to a `guide`, the event table to a `doc`.)
