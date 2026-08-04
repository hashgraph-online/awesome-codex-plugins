# Spec reviewer dispatch

Triggered by `design` after spec exists on disk. Each reviewer runs as an independent subagent with a focused charter. The coordinator merges findings and patches the spec once.

## Trigger table

Run every reviewer whose trigger condition matches the spec under review. Conditions are additive — a spec that triggers 4 conditions gets 4 reviewers.

| # | Trigger | Reviewer | Charter |
|---|---------|----------|---------|
| 1 | **Always** | `spec-compliance` | Verify every contract/invariant has an acceptance test. Check the spec covers contract, data, failure modes, and scope boundaries. |
| 2 | Spec defines **≥3 state enums or state machines** | `state-machine` | Enumerate every legal state transition. Flag missing edges, dead states, unspecified initial/terminal states, and unreachable transitions. |
| 3 | Spec contains **≥2 rules that cross-reference the same behavior** | `consistency` | Find every pair of rules that govern the same action. Check for contradictions, undefined priority, and implicit ordering assumptions. |
| 4 | **`topology=multi-module` or spec declares shared contracts** | `boundary` | Verify shared-contract ownership, versioning, serialization compatibility, and cross-module assumptions. Flag copied or divergent definitions. |
| 5 | Spec involves **durable writes, external side effects, or commit semantics** | `safety` | Trace every write path. Check partial-commit recovery, idempotency boundaries, data-loss scenarios, and crash-after-write ambiguity. |
| 6 | Spec is **scope=complex or the coordinator expects to dispatch subagents** | `implementability` | Read as an implementer seeing the spec for the first time. Flag missing data structures, ambiguous sequencing, and underspecified error handling. |

Count trigger matches before dispatch. If only trigger 1 fires, behavior is identical to the single reviewer already in `subagents` — no overhead.

## Model tier

| Reviewer | Tier | Rationale |
|----------|------|-----------|
| `spec-compliance` | `balanced` | Matching contracts to acceptance is pattern recognition |
| `state-machine` | `strongest` | Exhaustive transition enumeration requires precise reasoning |
| `consistency` | `strongest` | Cross-reference contradiction detection needs deep comparison |
| `boundary` | `balanced` | Version/ownership checks are structural |
| `safety` | `strongest` | Crash-recovery and partial-commit reasoning is subtle |
| `implementability` | `balanced` | Reading for ambiguity is comprehension, not deep reasoning |

Resolved via `.praxis/model-tiers.yaml`. No config file → all reviewers use harness default model.

## Dispatch format

Each reviewer receives:

```
ROLE: <reviewer name>
CHARTER: <one-paragraph from charters below>
SPEC: docs/staging/specs/YYYY-MM-DD-<topic>.md
OUTPUT: one finding per line. BLOCK (must-fix) | GAP (missing definition) | CONFLICT (two rules disagree).
        Each line references the spec section. No narrative, no suggestions.
```

## Reviewer charters

### spec-compliance

Verify the spec is complete enough for handoff. Check:
- Every `contract:` has a corresponding `test:`
- Every state-changing action has a defined error mode
- Scope boundaries are explicit (what's in, what's deferred)
- Data shapes are concrete (field names, types, constraints)

Report: contracts missing tests, scope leaks, vague data shapes.

### state-machine

Given every state enum in the spec, enumerate the full transition matrix. Check:
- Every state appears in at least one legal transition
- Every state has a path to a terminal state
- No transition references a state not in the enum
- The initial state is declared

Report: missing transitions, dead states, unreachable states, unstated initial states.

### consistency

Find every pair of rules, contracts, or invariants that constrain the same behavior. Check:
- If two rules give conflicting instructions, which wins?
- If rule A says "X must hold" and rule B says "except when Y", are the exceptions complete?
- Cross-reference: does the text at line N contradict the table at line M?

Report: contradictions, undefined priority, incomplete exception lists.

### boundary

Applicable when multiple modules or repositories share contracts. Check:
- Every shared type has exactly one owner (no duplicate definitions)
- Versioning rules are explicit (schema_version, protocol_version)
- Serialization format is specified (canonical JSON, field order, normalization)
- Cross-module assumptions are stated (e.g., "runner never imports domain code")

Report: duplicate definitions, missing version rules, unstated cross-module dependencies.

### safety

Trace every path that produces a side effect. Check:
- If the process crashes after a write but before recording the receipt, what happens?
- If two attempts write overlapping data, is the result defined?
- If a downstream consumer reads while a write is in progress, what do they see?
- For every commit/rollback boundary, is the atomicity guarantee explicit?

Report: crash-recovery gaps, undefined concurrent access, missing atomicity contracts.

### implementability

Read the spec as a developer about to implement it. Check:
- For every data structure mentioned, is its shape defined somewhere?
- For every sequence ("first X, then Y"), is the ordering enforced or just convention?
- For every error condition, is the handling explicit or left to "use common sense"?
- If a field is optional, is the None/default behavior specified?

Report: undefined data structures, ambiguous ordering, unspecified error handling, missing None semantics.

## Coordinator synthesis

After all reviewers return, the coordinator thinks critically about every finding before acting:

1. **Evaluate each finding.** Is it actually a problem, or did the reviewer misunderstand? Two reviewers flagging the same section from different angles is a stronger signal than a single isolated flag.
2. **Resolve conflicts.** When reviewers disagree — one says a transition is missing, another implies it's covered elsewhere — decide which is correct. Do not pick a side mechanically; reason from the spec text.
3. **Spot what was missed.** The coordinator sees the full picture. Reviewers each had a narrow lens. Ask: what category of problem could fall between their charters?
4. **Judge severity.** Classify each confirmed finding:
   - `BLOCK`: must fix before handoff (missing contract, contradiction, crash-recovery gap)
   - `DEFER`: notable but not blocking (ambiguous wording that implementation can resolve, edge case unlikely in practice)
5. **Fix the spec.** Apply fixes in one pass. When a finding is valid but the reviewer's suggested fix is wrong, write a better one.
6. **Report.** Tell the user: which triggers fired, which reviewers ran, what was found, what was fixed, what was deferred and why.

The coordinator does not summarize reviewer output — it judges it. Every deferred finding comes with a reason, not just a label.

**Judgment principles:**
- The coordinator has final authority. Reviewers advise; the coordinator decides. Consensus is not required.
- When unsure about a finding, escalate to the user rather than silently deferring. Present the finding, the coordinator's reasoning, and ask. One sentence each.
- If the coordinator overrides a reviewer BLOCK, record the override and reason in working notes. This creates an audit trail — if the override proves wrong during implementation, the pattern is learnable.
- The synthesis step runs exactly once. No back-and-forth with reviewers. This prevents deadlock and bounds the token cost.
