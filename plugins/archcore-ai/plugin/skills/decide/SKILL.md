---
name: decide
argument-hint: "[decision topic]"
description: "Record a decision: finalized → ADR (optionally rule + guide or spec + plan); open proposal → RFC. Use for 'we decided', 'record this decision', 'make it a standard', 'draft an RFC', 'should we switch to Y'. Not for feature planning or documenting existing code."
---

# /archcore:decide

Record a decision or a proposal for one. Routes between:

- **Finalized decision** → ADR (optionally followed by rule + guide as a standard, or spec + plan as an architecture cascade)
- **Open proposal** → RFC (for team review before a decision is made)

## When to use

- "Record the decision to use PostgreSQL"
- "We decided to go with microservices"
- "Document why we chose JWT over sessions"
- "Make this our team standard for error handling"
- "Draft an RFC for switching from REST to gRPC"
- "Proposing we adopt feature flags"
- "Should we move to Kubernetes?" (open → RFC)

**Not decide:**

- Planning a feature → `/archcore:plan`
- Documenting a component → `/archcore:capture`
- Reading applicable rules/ADRs/specs before coding → `/archcore:context`
- Picking up where work left off → `/archcore:context`

## Routing table

| Signal | Route | Documents |
|---|---|---|
| User describes a **finalized decision** (default) | → adr | Single ADR |
| User describes an **open proposal** ("thinking about", "should we", "proposing") | → rfc | Single RFC |
| User says "and make it a standard" or implies enforcement | → adr + standard cascade | ADR, then offer rule + guide |
| User says "and formalize the contract" or implies a spec is needed | → adr + architecture cascade | ADR, then offer spec + plan |

Default for finalized decisions: create a single ADR. After creation, evaluate the decision and offer the matching continuation per `skills/decide/references/continuations.md`.

## Execution

### Step 1: Check existing

`mcp__archcore__list_documents(types=["adr", "rfc"])` — check for existing decisions or proposals on this topic.

### Step 2: Route

If user language suggests the decision is still open ("thinking about", "should we", "proposing", "design proposal"), confirm with the user: "This sounds like an open proposal — draft an RFC for team review?" If yes, proceed to Step 3b. Otherwise continue with Step 3 (ADR).

### Step 3: Create ADR (finalized decision path)

- Read `skills/_shared/precision-rules.md` and `skills/_shared/adr-contract.md` once before composing. The contract specifies required structure; the rules specify forbidden lexicon and authoring conventions.
- Ask: "What was the decision (specific choice with version/name)? What alternatives were considered, and why was each rejected? What conditions would invalidate this decision?"
- Compose ADR content per the contract: fill Context with one concrete trigger and a code/measurement reference (or `[assumption]` if forward-looking), Decision in one specific sentence, Alternatives Considered with ≥2 named items each carrying an explicit rejection reason, Consequences split into positive + tradeoff with falsifiable claims (or `[expected]`), and Superseded when with ≥2 measurable conditions when feasible. Avoid forbidden lexicon from the rules.
- `mcp__archcore__create_document(type="adr")`

Then continue to Step 4.

### Step 3b: Create RFC (open proposal path)

- Ask: "What change are you proposing? What problem does it solve?"
- Compose content covering Summary, Motivation, Detailed Design, Drawbacks, Alternatives.
- `mcp__archcore__create_document(type="rfc")`
- Suggest relations: rfc `extends` existing ADR (if revising a past decision), or rfc `related` idea (if an idea inspired it).

RFC flow ends here — no rule + guide continuation (those belong to finalized decisions).

### Step 4: Relate (ADR path)

`mcp__archcore__add_relation` — link the ADR to existing RFCs, specs, plans, or other relevant documents.

### Step 5: Offer continuation (ADR path only)

Read `skills/decide/references/continuations.md`. Evaluate the decision content for the signal phrases listed there and offer the matching cascade:

- **Standard cascade** — rule + guide (decision describes enforceable behavior).
- **Architecture cascade** — spec + plan (decision describes a technical contract).
- **Both signals present** — ask the user which fits better, or neither for now.
- **Neither signal** — do not offer; the ADR alone is a valid endpoint.

Always confirm with the user before creating additional documents. Follow the per-cascade composition and relation rules in `continuations.md` exactly.

## Result

Minimum: one ADR or one RFC. Maximum: ADR + rule + guide (standard cascade) or ADR + spec + plan (architecture cascade). Report: paths, relations, recommended next actions.
