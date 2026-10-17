# gap-analysis.md — ELICIT's generation & detection layer (depth probe + gap probes)

The generation & detection half of ELICIT (`elicitation.md`): how to *measure* where the accumulated
intent falls short of the floor, and how to *generate* the "unsaid" candidates the input never named.
It runs **right after the floor is set** (to fill the initial question set) and **after every
integration** (to refresh it). The probes deliberately raise more than survives — every candidate
they produce clears `grounds-gate.md` before it becomes a confident question.

This is *detection*, not disposition: it surfaces gaps and candidates; ELICIT decides what to ask
(`elicitation.md`), and conflicts/traces handled elsewhere are not re-done here (structural grounding
is ORIENT's, spec↔plan trace is PLAN's trace gate, source conflicts are DECOMPOSE's flags).

## Depth probe — coverage vs floor, per axis

After CALIBRATE has set the floor, measure each axis (domain, technical, security, ...) for **depth
proportional to the project's character**: are the rules verifiable (a test case derivable from
each), or do they stay at generalities? The gap is `floor − coverage`, where *coverage* is the
**measured depth**, not the mere presence of content: DECOMPOSE supplies a **presence map** (what landed
per axis + a **form marker** — bare mention vs. full treatment), and a *touched* axis is **not**
automatically a *covered* one — the form marker is what keeps a thin mention from reading as coverage.

- **Domain depth** — are rules verifiable and edge cases concrete, or "handled appropriately"?
- **Security depth** — are auth / authorization concrete and project-specific, or a generality
  ("follows best practices")?
- **Architecture depth** — are components and their communication explicit, or named without a
  topology?
- **Convention depth** — do the rules carry a violation criterion, or are they preferences?

Output per axis: a **sufficient / insufficient** read + a concrete pointer to what is thin. An
insufficient axis feeds ELICIT's open question set. Unlike a structural fix, this does **not** auto-fill —
depth is added through dialogue, never invented.

## Three gap probes — generate the "unsaid"

Beyond measuring stated content, three probes catch what the dialogue has been *silent* on. They are
deliberately **liberal** — they raise more than survives — so every candidate clears `grounds-gate.md`.

- **Domain-silence probe** — does the accumulated intent stay SILENT on a standard *kind* of property
  this **deliverable's domain** implies? What that kind is depends on the domain (discovered, not
  assumed): for a service — lifecycle/state transitions, rejection cases, consistency, idempotency;
  for docs — coverage/freshness/cross-references; for infra — policy/least-privilege/drift; for data —
  schema/null-handling/lineage. If silent on a kind its domain implies, do **not** invent the rule
  (no fabrication) — surface the silence as a candidate.
- **Completeness sweep** — when a requirement is cross-cutting (auth, permission, row/tenant scoping,
  auditing, ...), enumerate **every** site it must apply to and flag any missing site.
- **Cardinality-coupling probe** — when the work **adds to or removes from a collection** (registry
  entries, enum members, a rule/command set, a route table), scan the existing code/tests for sites
  that **hard-code the old count or the exact member set** (a length assertion, a frozen name-set, a
  snapshot). Changing the cardinality breaks those — flag them so the plan updates them (or makes them
  count-agnostic). `go`'s integration gate is the backstop that *catches* this; surfacing it up front
  turns a mid-run gate failure into a planned task.

These three are **concrete slot-finders that populate `elicitation.md`'s decision-surface lenses** (the
behavioral kind-sweep and the structural colliding-pair walk) — the lenses say *what kinds* of
obligation to enumerate; these probes mechanically surface the candidates. Cross-stack testing showed roughly half of what they raise are false positives,
which is exactly why they are paired with the grounds gate: never escalate a candidate you can't
ground.

## When a summary isn't enough

If the in-session context can't settle whether an axis is thin (you need to see specific code),
read the narrow, specific path inline — ELICIT is inline (no subagent dispatch — those belong to the
two independent checks, intent-completeness and the 3-doc-gate). This is a pinpoint follow-up, kept small.

## Universality guard

Stack-agnostic. The axes, the silence kinds, and the collection cardinalities are whatever this
project actually is — discovered at runtime; no stack assumed, no fixed property checklist imposed.
