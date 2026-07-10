# Feature flow — PRD → spec → plan → task-type

Full feature lifecycle: requirements, formal specification, implementation plan, repeatable pattern. Best for well-scoped features that need a formal contract and recurring delivery pattern.

## Step 1: Check existing

`mcp__archcore__list_documents(types=["prd", "spec", "plan", "task-type"])` — see what exists. If `$ARGUMENTS` provided, check for duplicates on this topic.

## Step 2: Determine scope

If related documents already exist (e.g., a PRD without a spec), pick up where the chain left off — don't recreate.

For small, well-understood features, compress the flow — a short feature-scoped prd (or skip straight to the spec when the "why" is already recorded upstream) → spec → plan. Vary the weight, never the types.

## Step 3: PRD

Use `AskUserQuestion` to ask: "What problem does this solve? What are the success metrics?"

Compose content covering **Vision**, **Problem Statement**, **Goals and Success Metrics**, **Requirements**. Create via `mcp__archcore__create_document(type="prd")`.

**Scope rule:** a prd covers one unit of product decision — a whole product OR a single feature. Size never changes type: for a small feature write the same four sections, compressed (target ≤ 40 lines). A product-level prd links its feature-scoped prds via `add_relation`.

## Step 4: Spec

Read `skills/_shared/spec-contract.md` once before composing — it defines what a spec is (behavior others rely on right now), the routing gate against `prd`, and the notation.

Use `AskUserQuestion` to ask: "Who depends on this, and what is its surface — the interface, or the parts/states/fields that drive behavior? What are the key constraints, invariants, and failure behaviors?"

Compose the six sections defined in `spec-contract.md`: **Purpose & Scope**, **Surface**, **Normative Behavior** (EARS clauses + BCP 14 keywords), **Constraints & Invariants**, **Failure Behavior**, **Conformance**. Create via `mcp__archcore__create_document(type="spec")`.

Add relation: `mcp__archcore__add_relation` — spec `implements` prd.

## Step 5: Plan

Use `AskUserQuestion` to ask: "What are the implementation phases? What are the blockers?"

Compose content covering **Goal**, **Tasks** (phased), **Acceptance Criteria**, **Dependencies**. Create via `mcp__archcore__create_document(type="plan")`.

Add relation: `mcp__archcore__add_relation` — plan `implements` spec.

## Step 6: Task-type

Use `AskUserQuestion` to ask: "What's the recurring implementation pattern? What are the key steps each time?"

Compose content covering **Context**, **Steps**, **Checklist**, **Pitfalls**. Create via `mcp__archcore__create_document(type="task-type")`.

Add relation: `mcp__archcore__add_relation` — task-type `related` plan.

## Step 7: Relate to existing

Check for ADRs, rules, or other documents that should be linked. Suggest additional `add_relation` calls.

## Result

Four linked documents: PRD → spec → plan → task-type (spec `implements` prd, plan `implements` spec, task-type `related` plan).
