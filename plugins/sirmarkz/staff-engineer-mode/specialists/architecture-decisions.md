---
name: architecture-decisions
description: "Use when making system design decisions, ADRs, service/module/worker boundaries, or architecture tradeoffs"
---

# Architecture Decisions And Decision Records

## Iron Law

```
NO ARCHITECTURE DECISION WITHOUT FORCES, ALTERNATIVES, AND COST TO CHANGE COURSE
```

If the design lacks goals, constraints, alternatives considered, and a clear read on what would make you change course later, do not treat it as decided. For solo work, responsibility can name who runs the local checks and keeps the decision current.

## Overview

Architecture decision work turns "components and opinions" into explicit goals, tradeoffs, failure modes, and decisions future readers can understand. Works the same at any project size: the discipline is forces, alternatives, and cost to change course, not the formal process around it. Shape decisions by the forces they must satisfy: user outcomes, constraints, data, reliability, security, operability, evolvability, and cost.

## When To Use

- Making, shaping, or revisiting system design decisions, design proposals, ADRs, service boundaries, dependency direction, or tradeoff analysis.
- A change affects data responsibility, public contracts, reliability, deployment topology, security boundaries, or operational responsibility.
- Whether a monolith, module, service, workflow, platform component, or integration boundary "holds up".
- A prior decision needs to be recorded or revisited with current constraints.

## When Not To Use

- Live outage handling: use `incident-response-and-postmortems`.
- Code style, naming, formatting, or local implementation review: use `agent-pr-review` only for a concrete diff; use `code-readability-for-agents` when repository legibility is the design problem.
- Launch readiness aggregation: use `production-readiness-review`.
- Narrow API compatibility issue: use `api-design-and-compatibility`.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Problem statement, users, goals, non-goals, constraints, success criteria.
- Current and proposed architecture, data flows, trust boundaries, interfaces, dependencies, and runtime responsibility model.
- Interaction style: request/response, event, batch, stream, push, or local projection, and whether high-volume clients can avoid polling or fanout.
- Critical-path storage and runtime dependency choices, including latency, availability, failover, coupling, alternatives, and reversal or isolation plan.
- Operability notes: how the user or agent debugs, replaces, or degrades around the design, what the fallback path is, and where that path is tested or documented.
- Alternatives considered, including "do nothing", "keep modular", "split later".
- Reliability, security, privacy, deploy, data consistency, migration, operational risks.
- Existing incidents, SLOs, costs, scale limits, compliance constraints, roadmap pressures.

## When Inputs Are Referenced But Not Visible

If the user references an artifact (sketch, design proposal, diff, diagram) that is not in
the workspace or thread, do not stop at "please paste it." Produce a
strawman decision frame from the prompt's named subject with: (a) a Forces
table containing the likely forces and rationale, (b) an Alternatives table
with the current state and at least one real alternative, (c) a status of
`PROPOSED` or `UNDECIDED` rather than a fabricated decision, (d) likely
consequences and reversibility triggers, and (e) a responsibility field. Mark
inferred fields `ASSUMED` or `NEEDS CHECK` so the user can correct them.

## Workflow

1. **Frame the decision.** Write the decision as one clear question and list goals, non-goals, and constraints before evaluating solutions.
2. **Emit a compact ADR-shaped first answer.** Before asking for more artifacts, give the user a usable decision skeleton containing: decision question, context and forces with rationale, decision status, the current state and real alternatives, likely consequences, reversibility cost and reconsideration trigger, and responsibility owner or check path. Record a selected decision only when the user or local evidence supplies it; otherwise use `PROPOSED` or `UNDECIDED`. Mark unknowns as `ASSUMED` or `NEEDS CHECK`.
3. **Map the system.** Identify data flow, control flow, dependency direction, trust boundaries, failure domains, and operational checkpoints.
4. **Choose interaction style deliberately.** Before hardening a synchronous request path, ask whether eventing, batch, push, stream, or local projection would reduce overload, quota pressure, or retry ambiguity while still satisfying user semantics.
5. **Map domain contexts when model ownership drives the decision.** Name only the contexts, responsibility boundaries, neighboring relationships, and translation surfaces that affect the choice. Do not require a domain-pattern taxonomy for a local module, infrastructure choice, or other decision where it adds no evidence.
6. **Prefer simpler boundaries first.** Start with the simplest deployable boundary and explicit contracts. Add distribution only for a named scaling, release, responsibility, isolation, or blast-radius benefit that exceeds its operational cost. Classify hard-to-reverse and reversible choices so the verification and commitment level matches the cost to change course.
7. **Compare alternatives.** Evaluate at least two real options plus the current state. Include consequences, rejected alternatives, and what would make the decision wrong later.
8. **Specify material fitness functions.** Turn the invariants the decision relies on into testable checks. Each check names the property, threshold or rule, measurement source, evaluation trigger or cadence, failure response, and local check path. Include dependency direction, public compatibility, performance budgets, or isolation only when that property is part of the decision's rationale; do not manufacture checks to fill categories.
9. **Evaluate runtime dependency responsibility.** For any critical runtime dependency or storage choice, state how the user or agent can debug it, patch or change it, work around issues, isolate or reverse the decision, and exit or degrade if it fails. Keep this at design-time adoption criteria; timeout/retry policy goes to `dependency-resilience`, and launch details go to `production-readiness-review`.
10. **Evaluate cross-cutting risks.** Cover reliability, overload, data correctness, security, observability, deployment safety, recovery, cost, and maintainability.
11. **Record the decision state.** Create an ADR or design-decision summary with status, evidence-supported forces, the selected decision or the decision still needed, likely consequences, reversibility cost and reconsideration trigger, supporting details, applicable fitness checks, and focused follow-ups.
12. **Name focused follow-ups.** Record at most two unresolved surfaces that need a separate artifact. Do not load or apply a pile of adjacent specialists to make the current decision look complete.

## Synthesized Default

Use a compact design decision plus ADR. Keep the system modular and technology-agnostic until the design shows it needs distribution. When distribution is justified, make responsibility, contracts, failure modes, observability, and deployability explicit before endorsing the split.



## Exceptions

- Exploratory prototypes can use a lightweight decision note if explicitly non-production and disposable.
- Regulated, security-sensitive, externally committed, or sensitive-data systems need a fuller risk register using the shared risk-register format and a change trail.
- Reversible local implementation choices may be documented in code or PR context instead of an ADR.
- If the system is already failing operationally, incident or reliability work may precede full architecture cleanup.

## Response Quality Bar

- Lead with the architecture decision, decision status, or highest-severity blockers.
- Cover goals, alternatives, responsibility, boundaries, data flow, and failure modes before optional architecture breadth.
- Make recommendations actionable with checks, stop conditions, and follow-up decisions.
- Name the details to inspect, such as SLOs, traffic, incidents, data contracts, threat boundaries, and migration checks; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside the design or decision. Add at most two specialist follow-ups, only for material unresolved surfaces.
- Be concise: prefer compact ADRs, decision tables, and risk registers over generic architecture theory. Risk-register fields follow the shared risk-register format.
- For pre-build, ticketing, or milestone-readiness requests, distinguish implementation tasks from unresolved architecture decisions. Use compact decision, risk/tradeoff, alternative, responsibility, and check tables; do not expand into a full narrative ADR unless asked.
- Scale the artifact to the decision: every answer needs the question, status, forces, alternatives, consequences, reversibility, and responsibility; add system maps, domain-context maps, fitness functions, and a broad risk register only when the decision depends on them.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Architecture decision summary with context, goals, non-goals, and constraints.
- ADR with status, selected decision or explicit `UNDECIDED` field, alternatives, consequences, and a concrete responsibility value (user, local check path, or supplied project role; if unknown, use `ASSUMED: <component> responsibility` rather than a blank or `TBD`).
- System map covering the data flow, dependencies, trust boundaries, and responsibility affected by the decision when those boundaries are material.
- Interaction-style decision covering synchronous, event, batch, stream, push, or local projection alternatives when overload or quota pressure is material.
- Runtime dependency adoption criteria covering supportability, changeability, fallback, and exit or degradation when the decision adds a critical runtime dependency.
- Critical-path storage or dependency entry with forces, alternatives, failure model, and reversal or isolation when that path is in scope.
- Domain-context map naming responsibility, neighboring relationships, and translation surfaces when model ownership affects the decision.
- Fitness-function specification for the architectural invariants the selected decision relies on, with property, threshold or rule, measurement source, evaluation trigger or cadence, failure response, and local check path.
- Risk register with likelihood, impact, mitigation, and records for material risks using the shared risk-register format.
- Decision table showing default, alternatives rejected, and exception conditions.
- Follow-up checks capped at two, each tied to a specific unresolved surface.

## Checks Before Moving On

- `decision_record`: the ADR states context, decision, status, alternatives, and consequences.
- `goal_alignment`: every recommended architecture element maps to a goal, constraint, or risk.
- `boundary_check`: service/module boundaries have responsibility, contracts, data responsibility, and failure behavior.
- `interaction_style`: overload- or quota-sensitive designs compare synchronous calls with event, batch, stream, push, or projection alternatives.
- `context_map`: when model ownership affects the decision, relevant contexts have responsibility, neighboring relationships, and explicit translation surfaces where models disagree.
- `fitness_functions`: each architectural invariant the decision depends on has a property, threshold or rule, measurement source, evaluation trigger or cadence, failure response, and local check path; no invariant is added only to fill a category.
- `risk_coverage`: reliability, security, data, deploy, observability, and operations risks are considered.
- `dependency_responsibility`: critical runtime dependencies have supportability, change path, fallback path, and exit or degradation plan.
- `critical_path_tradeoff`: critical-path storage and dependency choices state forces, alternatives, failure behavior, and reversal or isolation path.
- `follow_up_cap`: no more than two follow-up skills are recommended unless the output is a sequencing plan.

## Red Flags - Stop And Rework

- Components are named without their contracts, data flows, or failure modes. (Solo work: the responsibility value can be "user + local checks"; the rule is no anonymous components, not formal headcount.)
- A distributed design is chosen because it is fashionable, not because constraints require it.
- Alternatives are missing or all alternatives are strawmen.
- The design pushes complexity into operations without on-call responsibility or runbooks.
- A critical runtime dependency is accepted even though the user or agent has no path to debug, change, replace, or degrade around it from local tools and records.
- Security, observability, migration, and rollback are left as "implementation details" for a high-risk decision.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Treating diagrams as decisions | Record the decision, forces, consequences, and responsibility. |
| Distributing by default | Keep the simplest deployable boundary until a named benefit exceeds the operational cost. |
| Approving distribution too early | Prefer modular boundaries until scale, responsibility, release, or blast-radius needs justify it. |
| Hiding rejected options | State what was rejected and why, so future readers do not repeat the debate. |
