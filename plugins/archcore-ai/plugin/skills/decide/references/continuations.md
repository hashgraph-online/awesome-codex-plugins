# Decide — continuations

After an ADR is created, `/archcore:decide` offers two continuation cascades. Both are opt-in — never auto-invoke; always confirm with the user before creating additional documents.

## When to offer

After Step 3 (ADR creation), evaluate the decision content:

- **Standard cascade** (rule + guide) — the decision describes enforceable behavior, naming convention, coding pattern, or anything that should bind future code. Signal phrases: "we should always", "developers must", "the team should", "going forward all X must Y".
- **Architecture cascade** (spec + plan) — the decision establishes or changes a boundary contract (API, interface, schema, protocol) that other code depends on. A spec may capture the contract of existing code or specify one to build. Signal phrases: "the X system will provide", "the contract is", "the interface exposes", "the API will be".

If neither signal is present, do not offer continuations. The ADR alone is a valid endpoint.

If both signals are present, ask: "This decision could become a team standard (rule + guide) or a technical contract (spec + plan). Which fits better — or neither for now?"

## Standard cascade — rule + guide

Offer: "Want to codify this into a team standard? I can create a rule (mandatory behavior) and guide (how-to) based on this decision."

### Rule

- Read `skills/_shared/precision-rules.md` once before composing.
- Ask via `AskUserQuestion`: "What are the mandatory behaviors (MUST / MUST NOT statements)? How will each be verified — test, lint, CI signal, or manual review?"
- Compose rule content covering:
  - **Rule** — imperative directives (MUST / MUST NOT)
  - **Rationale** — why this is mandatory
  - **Examples** — Good/Bad grounded in actual code paths or scenarios
  - **Enforcement** — name the verifier per directive (test name, lint rule, CI step, or reviewer responsibility)
- Avoid forbidden lexicon per `precision-rules.md`.
- Create via `mcp__archcore__create_document(type="rule")`.
- Add relation: `mcp__archcore__add_relation` — rule `implements` adr.

### Guide

- Ask via `AskUserQuestion`: "What steps should developers follow? What are common pitfalls?"
- Compose content covering:
  - **Prerequisites**
  - **Steps** (numbered)
  - **Verification**
  - **Common Issues**
- Create via `mcp__archcore__create_document(type="guide")`.
- Add relation: `mcp__archcore__add_relation` — guide `related` rule.

## Architecture cascade — spec + plan

Offer: "Want to formalize this as a technical contract and plan? I can create a spec (contract surface) and plan (implementation phases) based on this decision."

### Spec

- Read `skills/_shared/precision-rules.md` and `skills/_shared/spec-contract.md` once before composing — the contract defines what a spec is (the contract of a depended-on boundary) and what does not belong in one.
- Ask via `AskUserQuestion`: "What is the contract surface (the boundary other code depends on)? What are the key constraints and invariants? How is error behavior defined?"
- Compose the mandatory sections defined in `spec-contract.md`:
  - **Purpose & Scope** — the boundary this spec governs, its external consumers, and what it excludes
  - **Contract Surface** (interfaces, types, signatures) — referenced by `@path`, not reproduced
  - **Normative Behavior** (MUST / SHOULD / MAY), each numbered
  - **Constraints & Invariants**
  - **Error Handling**
  - **Conformance** — what makes an implementation conformant
- Avoid forbidden lexicon.
- Create via `mcp__archcore__create_document(type="spec")`.
- Add relation: `mcp__archcore__add_relation` — spec `implements` adr.

### Plan

- Ask via `AskUserQuestion`: "What are the implementation phases? What are the dependencies and blockers?"
- Compose content covering:
  - **Goal**
  - **Tasks** (phased)
  - **Acceptance Criteria**
  - **Dependencies**
- Create via `mcp__archcore__create_document(type="plan")`.
- Add relation: `mcp__archcore__add_relation` — plan `implements` spec.

## Code-pattern shift (CPAT) — optional micro-continuation

When the decision describes a before/after code-pattern change (refactor, idiom migration, API shape shift), the standard cascade can include a CPAT between the ADR and the rule.

Offer between Step 3 (ADR) and the rule creation: "Does this decision represent a code-pattern change (before/after code shift)? If yes, I can document the pattern as a CPAT before drafting the rule."

If yes:
- Ask: "What pattern changed? Show the before and after."
- Compose content covering: **What Changed**, **Why**, **Before**, **After**, **Scope**.
- Create via `mcp__archcore__create_document(type="cpat")`.
- Add relations:
  - cpat `implements` adr
  - rule `related` cpat (added after the rule is created)

CPAT is purely additive — the standard cascade continues to the rule with no other behavior changes.

## Closing summary

After any continuation runs, summarize the chain: paths, relation edges, and one-line "recommended next" — e.g., *"Consider linking this rule to existing specs that enforce it, or capturing a guide example from `src/<path>`."*
