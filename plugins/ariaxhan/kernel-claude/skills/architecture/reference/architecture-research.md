# Architecture Reference: Research & Best Practices

Reference for structural decisions, pattern selection, and design review.
Read on demand. Not auto-loaded.

## Sources

Martin Fowler ("Refactoring," Feb 2026 fragments), Robert C. Martin ("Clean
Architecture"), SOLID principles, CodeScene code health research, Borg &
Tornhill peer-reviewed study (Jan 2026, arXiv 2601.02200), ThoughtWorks
Technology Radar Vol 33 (2026), JetBrains modular monolith guide (Feb 2026),
ADR guidance (Feb 6, 2026).

---

## AI-Code Health Nexus (Jan 2026 — Peer-Reviewed)

Borg & Tornhill (arXiv 2601.02200): Tested 5,000 Python files across 6 LLMs.
Key findings:
- **30%+ defect risk increase** when AI applied to unhealthy code.
- CodeHealth is the **strongest predictor** of AI refactoring success.
- One standard deviation increase in CodeHealth raises success odds by 20-40%.
- Claude is more conservative (~5% breaks regardless of code quality).

Threshold: **CodeHealth >= 9.5** (ideally 10.0) for AI-ready code.

loveholidays case study: Scaled from 0 to 50% agent-assisted code in 5 months
while maintaining quality by implementing CodeScene safeguards.

---

## Cognitive Debt (Fowler, Feb 2026)

New concept: When LLMs handle coding, teams risk losing deep system understanding.
"Cognitive debt" accumulates when developers don't build mental models.

TDD and refactoring serve as forcing mechanisms to maintain understanding.
Fowler: "TDD served a critical function: it kept me in the loop."

Anti-pattern: Outsourcing understanding to AI without verification loops.

---

## Core Architecture Principles

### Separation of Concerns
Each module has one job. UI doesn't know about database. Business logic
doesn't know about HTTP. This isn't pedantry; CodeScene data shows modules
that violate separation have 15x more defects.

### Coupling and Cohesion
Low coupling: modules can change independently.
High cohesion: related functionality grouped together.
Measure: if changing module A forces changes in module B, they're coupled.
If module A contains unrelated functions, it lacks cohesion.

### Dependency Direction
Dependencies point toward stable abstractions, not volatile implementations.
High-level modules don't depend on low-level modules; both depend on
interfaces. (Dependency Inversion Principle, Robert C. Martin.)

### Interface Stability
The most critical finding from architecture anti-pattern research (Drexel
University, 19 large-scale projects): Unstable Interface is the most
severe anti-pattern, contributing the most to bug-proneness and change-
proneness of all patterns studied.

Rule: if an interface changes frequently, it's not an interface. It's an
implementation detail leaking through a false abstraction.

---

## Modular Monolith Resurgence (2026)

CNCF 2025 survey: **42% of microservices adopters** are consolidating back.
Key drivers:
- Microservices cost 3.75-6x more than monoliths.
- Amazon Prime Video reduced costs 90% by consolidating.
- Modular monoliths provide 90% of microservices benefits at 10% ops cost.

Spring Modulith enables gradual extraction path. Recommended for teams < 15
developers without genuine independent scaling requirements.

---

## Architecture Decision Records (ADRs) — Feb 2026

ADRs now extend to AI/LLM governance:
- Security threat modeling ADRs (prompt injection, jailbreak defenses)
- Human escalation policy ADRs for AI systems
- Cost governance ADRs for token-based pricing
- Regulators expect documented AI oversight

---

## Architecture Anti-Patterns (Ranked by Impact)

1. Big Ball of Mud: no recognizable structure. Code works but nobody
   understands why. Usually from "just get started" without design.

2. Distributed Monolith: microservices that must deploy together. All
   the complexity of distribution with none of the independence.
   **2026 update**: 42% of microservices adopters now consolidating.

3. Golden Hammer: using a familiar tool for every problem. Kubernetes
   for a single server. GraphQL for CRUD. React for a static page.

4. Inner Platform Effect: building a system so configurable it becomes
   a bad replica of the language/framework it runs on.

5. Premature Abstraction: generalizing before understanding the domain.
   Creates wrong abstractions that are harder to fix than duplication.

6. Stovepipe System: ad-hoc point-to-point connections between components.
   No clear data flow. Changes cascade unpredictably.

---

## Architecture Decision Checklist (for tearitapart)

- Does each component have a single, clear responsibility?
- Can components be tested independently?
- Do dependencies point toward abstractions?
- Are interfaces stable (unlikely to change with implementation)?
- Is there a clear boundary between "inside" and "outside" the system?
- Can the system be deployed incrementally (no big-bang releases)?
- Can you delete a component without rewriting adjacent ones?
- Is the pattern consistent (same approach throughout, not mixed)?

---

## KERNEL Integration

- tearitapart: architecture review is phase 4. Checks coupling, cohesion,
  pattern consistency, dependency direction, interface stability.
- Scout agent: identifies architectural pattern during codebase discovery.
  Documents in active.md for future reference.
- Contracts: architecture decisions are constraints, not implementation
  details. Surgeon follows architecture; doesn't redesign it.
