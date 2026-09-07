# Execution Contract Presentation

Use this internal format only for Guarded mode. Evidence mode has no approval contract. Keep every field proportional to the work.

## Canonical contract object

Stage one JSON object with exactly these fields:

```json
{
  "outcome": "concrete result and user-visible behavior",
  "boundary": {
    "in_scope": ["approved behavior or system boundary"],
    "out_of_scope": ["explicitly unchanged behavior or excluded work"]
  },
  "must_hold": ["observable requirement or compatibility promise that must remain true"],
  "build": {
    "approach": ["smallest repository-aware implementation route"]
  },
  "verification": {
    "scale": "focused",
    "evidence": [
      {
        "id": "E1",
        "kind": "argv",
        "description": "one cheapest sufficient source",
        "dependencies": ["src/**/*.py", "tests/", "pyproject.toml"]
      }
    ],
    "done_when": [
      {
        "condition": "observable completion condition",
        "primary_evidence": "E1"
      }
    ]
  },
  "plain_language": "Faithful easy explanation of the compact contract and verification scale."
}
```

`outcome`, `boundary.in_scope`, `must_hold`, `build.approach`, `verification.scale`, `verification.evidence`, `verification.done_when`, and `plain_language` are required. `boundary.out_of_scope` is required but may be empty when nothing material needs exclusion. `verification.scale` must be `quick`, `focused`, or `full`.

Declare each source once in `evidence` with `id`, `kind`, and `description`. IDs start with a letter, use at most 32 letters, digits, underscores, or hyphens, and are unique. `kind` is one of `argv`, `browser`, `hosted`, `manual`, or `existing`. An `argv` source may also include a non-empty `dependencies` list when repository evidence supports a precise boundary; other kinds must omit it. Approval binds those patterns into the contract digest. `*` matches within one path segment, `**` is accepted only as a complete segment and crosses directories, and a trailing slash selects a directory prefix. Absolute paths, traversal, backslashes, `?`, character classes, partial `**`, duplicates, and unmatched patterns fail closed to an ordinary verification run. Omit `dependencies` when uncertain; it is an optimization declaration, not a sufficiency claim.

Each `done_when` object has exactly one non-empty `condition` and one `primary_evidence` id that resolves to the registry. Every source must be referenced, while one id may be reused by several conditions. Do not add a second source for the same condition merely to repeat proof through another tool or surface. Bind every `argv` check to its declared source with `evidence_id` in the final verification batch. The chosen profile communicates intended depth qualitatively; it creates no numeric source or cumulative-work ceiling. Use at most one `browser` source and reference that id from every condition covered by its metered representative session. After the last relevant mutation, explicitly finalize a successful Browser source or attest one collected hosted, manual, or existing source with the evidence-completion capability. The Hook independently executes argv checks and observes its matched Browser path; other kinds remain explicit agent attestations rather than independently proven external events.

The Hook treats `condition`, `description`, and the other contract prose as opaque text. Enforcement follows typed fields, ids, references, valid profile names, and explicit capability argv; natural-language keywords do not grant permissions or create numeric limits. Exact executable names, options, tool names, and explicit Click directives remain protocol syntax rather than semantic prose.

Only when material, add `build.semantics` as a non-empty list for state, failure, security, concurrency, migration, or compatibility meaning; `build.order` as a non-empty list for a real sequencing constraint; or `verification.intermediate_gate` as a non-empty string for one irreversible boundary. Otherwise omit them. Do not add unsupported fields.

## One semantic contract, not many checkpoints

Show the authoritative fields top-down: outcome and boundary; must-hold conditions; the compact build approach and any material semantics or order; then verification.

The contract fixes the result, boundary, must-hold conditions, material behavior, and verification commitment. Its selected profile records intended verification depth qualitatively; the Hook neither scores that choice nor creates a numeric argv ceiling from it. It does not freeze every library, tool, file, or low-level tactic. Necessary in-scope dependencies, MCP tools, external services, graders, and implementation choices are authorized by approval unless the contract explicitly excludes them.

Do not split the build approach into phases, steps, tasks, or another mirrored plan. The contract exists to approve the result and its boundary, not to make the user review several versions of the same implementation description.

## Human approval surface

Keep `plain_language` inside the canonical digest-bound object, but do not show raw JSON by default. Render one faithful four-section view in the user's language:

1. **Goal** — the concrete result and visible behavior;
2. **Changes** — the in-scope boundary and broad implementation route;
3. **Unchanged** — out-of-scope behavior plus every must-hold promise;
4. **Completion checks** — the qualitative scale and human-readable evidence conditions.

Offer the canonical JSON only as optional **Technical contract** details. The human view is a projection of the exact staged object, not a second or weaker contract. Use the projection supplied by the successful stage Hook response instead of independently reconstructing it.

## Single approval

Run `click-gate stage '<Execution Contract JSON>'` once. The Hook validates and binds the canonical contract digest, creates a fresh opaque lifecycle handle, emits the ID marker below, and injects the exact four-section projection into the successful stage Hook context:

```text
CLICK_CONTRACT_ID=ctr_<32 lowercase hex characters>
```

`contract_id` is not a contract field and does not replace the stored digest. Show the emitted id with the Hook-generated four human sections, then end with one compact question equivalent to:

> Do you approve contract `ctr_...` and its verification scale? If approved, I will implement it in one shot and run the completion checks once.

Stop without mutation. The original request is not approval of an unseen contract. Staging records `staged_turn_id`; the Hook rejects pass and a replacement stage in that same `UserPromptSubmit` turn. A materially revised proposal receives a new id. An in-scope detail or narrowing follow-up is digest-recorded on the existing contract and does not require reapproval. That digest proves the request was recorded; the runtime does not semantically prove that it was in scope.

Only after a later user turn explicitly approves the shown proposal, run `click-gate pass ctr_<32hex>`. Pass only the exact emitted id—never resend or reconstruct the contract JSON. The Hook matches the id to the staged digest, records `approved_turn_id`, and preserves the derived verification state. An approved but incomplete contract reuses the same id when implementation resumes in a later turn. Turn separation proves that another user response occurred; the Skill still must interpret that response faithfully because the Hook does not semantically classify approval words.
