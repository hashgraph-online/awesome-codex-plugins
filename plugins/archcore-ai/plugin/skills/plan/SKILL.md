---
name: plan
argument-hint: "[feature or initiative] [--track product|feature|sources|iso]"
description: "Plan a feature or initiative: default product flow (idea → PRD → plan), feature flow with formal spec + task-type, sources flow (MRD → BRD → URD), or ISO 29148 cascade (BRS → StRS → SyRS → SRS). Use for 'plan the X redesign', 'create a roadmap', 'plan a new feature'. Pick a flow with --track. Not for recording a decision — use /archcore:decide."
---

# /archcore:plan

Plan a feature or initiative. Default is the product flow (idea → PRD → plan); switch with `--track`:

- `--track product` *(default)* — idea → PRD → plan (lightweight)
- `--track feature` — PRD → spec → plan → task-type (formal feature lifecycle)
- `--track sources` — MRD → BRD → URD (discovery research)
- `--track iso` — BRS → StRS → SyRS → SRS (ISO 29148 cascade for regulated work)

## When to use

- "Plan the auth redesign" → default product flow
- "Create a feature plan for the API migration" → default
- "I need market research before we plan" → `--track sources`
- "We need a formal feature spec with a repeatable task-type" → `--track feature`
- "We're regulated — start the ISO requirements cascade" → `--track iso`
- "Just a plan, skip the idea/PRD" → see Step 3 (single-plan shortcut)

**Not plan:**
- Recording a decision → `/archcore:decide`
- Documenting existing code → `/archcore:capture`
- Codifying a team standard → `/archcore:decide` (offers rule + guide continuation)
- Reading applicable rules/ADRs/specs before coding → `/archcore:context`
- Picking up where work left off → `/archcore:context`

## Routing table

| Signal | Route | Documents |
|---|---|---|
| Default — feature or initiative | → product flow | idea → prd → plan |
| `--track product` | → product flow | idea → prd → plan |
| `--track feature` | → feature flow | prd → spec → plan → task-type |
| `--track sources` | → sources flow | mrd → brd → urd |
| `--track iso` | → ISO 29148 flow | brs → strs → syrs → srs |
| User says "just a plan" or "only the plan document" | → single plan | plan only |
| Ambiguous arguments | → ask one question | "Full feature plan (idea + PRD + plan) or just a plan document?" |

For `--track sources` and `--track iso`, the chain may continue into a product or feature flow afterwards — the reference for each track documents the natural follow-ups.

## Execution

Content voice: default to architectural prose — decisions, rationale, intent.
See `skills/_shared/precision-rules.md` Rule 6. Code blocks only where the
document type requires it (`rule`, `guide`, `cpat`) or the user asks.

### Step 1: Resolve track

Parse `$ARGUMENTS`:

1. If `--track <name>` is present and valid (`product|feature|sources|iso`), record the chosen track.
2. Otherwise, default to `product`.
3. Drop `--track <name>` from `$ARGUMENTS` so the remainder is treated as the topic.

### Step 2: Read the matching flow reference

Open exactly one reference file based on track:

- `product` → `skills/plan/references/product-flow.md`
- `feature` → `skills/plan/references/feature-flow.md`
- `sources` → `skills/plan/references/sources-flow.md`
- `iso` → `skills/plan/references/iso-flow.md`

Follow the steps in that reference verbatim — they own check-existing, scope determination, per-document elicitation, content composition, and relation wiring.

### Step 3: Single-plan shortcut

If the user explicitly said "just a plan" or "only the plan document":

- Skip the reference. Ask: "What is the goal? What are the key phases and dependencies?"
- Compose content covering **Goal**, **Tasks** (phased), **Acceptance Criteria**, **Dependencies**.
- `mcp__archcore__create_document(type="plan")`.

### Step 4: Cross-link

After the chosen flow completes, suggest `mcp__archcore__add_relation` calls to link the chain into existing ADRs, specs, or related plans.

## Result

The matching chain of documents per the chosen track. Single-plan: one plan document. Report: paths, relations, recommended next actions (e.g., *"consider creating a spec for the technical contract — run `/archcore:decide` with 'and formalize the contract' for an ADR-spec-plan cascade"*).
