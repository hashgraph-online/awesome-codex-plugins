---
name: click
description: Record revision-aware evidence for software work by default, or bind higher-risk execution to one human-readable approval contract in Guarded mode. Use when Click Hook context enables Evidence or Guarded mode, or when the user explicitly selects Click. Do not use for questions or explanations.
---

# Click

Click is an evidence runtime first and an approval boundary when the user chooses Guarded mode. It records observable execution and verification without prescribing the model's search strategy or reasoning.

## Route by the active mode

Follow [operating modes](references/modes.md) whenever selecting, activating, applying, reviewing, resuming, bypassing, or cancelling Click.

- **Evidence** is the default. Do not stage a contract or ask for Click approval. Let the host authorize work, record prompt lineage and mutation revisions, register concrete verification evidence during execution, reuse only valid receipts, and return a receipt that clearly says `approval_bound: false` and `execution_authority: host`.
- In **Guarded**, use one approval-bound contract for software creation, modification, deletion, refactoring, and repair. The contract remains hard-locked until approved or cancelled.
- In **Off**, Click does not govern ordinary work. An explicit `@Click` or `$click` invocation may start the Guarded workflow.
- For code-review-only work in Evidence or Guarded mode, run `click-gate review`, remain read-only, reuse evidence, and report findings without a build contract. A request that also asks for fixes follows the active mode.

Do not treat a question about Click as a mutation. Bypass and cancel require the exact user-authorized first-line forms in the modes reference; never infer them from ordinary prose.

## Evidence mode: work first, bind evidence honestly

Use the current user prompt as the intent lineage. Do not invent a contract, contract approval, or approved dependency declaration. Choose concrete checks from repository evidence during execution and submit their stable evidence ids with `click-gate verify`; Evidence mode may register those argv sources dynamically. Same-revision reuse still requires exact receipt bindings. A committed `.click/evidence-dependencies.json` mapping remains candidate policy only in Evidence mode because authoritative observation requires an approved Guarded contract. Caller-supplied observation JSON, profiling output, and Shadow data never grant reuse authority.

An exact check may also use a committed `.click/evidence-reuse.json` safe-change entry without an observer. Treat that file only as repository-owner authority established before the baseline: never create, widen, or reinterpret it to skip checks for the current mutation. Click compares the baseline and current effective Git states, reports net changed paths, and reuses only when every path matches `reuse_if_only_changed`. Any unknown or unlisted path reruns automatically. A complete runtime observation is stronger and cannot be overridden by this declaration.

A repository may decompose an exact broad source through committed [Evidence Shards v1](references/evidence-shards-v1.md). Continue submitting the declared parent id and argv; Click validates and runs the children. The shard map authorizes decomposition only. After mutation, each child still needs the ordinary dependency-observation or safe-change authority before its prior pass can be reused.

For a supported repository that has no shard policy, use the JSON-free
`click-gate sharding init|status|refresh` workflow in
[automatic sharding setup](references/automatic-sharding-setup.md). Collection,
proposal generation, and bootstrap require an active Evidence runtime or a
separately approved Guarded contract. In Evidence, an explicit `refresh` may
apply the reviewed proposal under host authority; Guarded requires a later
digest-bound application approval. Keep proposal review, application, the
user's exact policy commit, bootstrap validation, and baseline evidence as
separate steps. Never stage, commit, push, overwrite user configuration, or
describe the first baseline as savings.

An in-scope or narrowing follow-up continues the same Evidence session and appends a prompt digest. Start a fresh session when the previous one is complete. The final receipt must distinguish host-authorized execution from Guarded approval.

## Guarded mode: compile the smallest faithful contract

Treat the user's requested result, visible behavior, scope, constraints, and authority as primary. A contract-only or handoff request does not authorize implementation. Inspect from the narrowest relevant repository entry point and widen only while consequential behavior is unresolved. Do not treat an existing system as a blank slate or include unrelated cleanup. Resolve ordinary technical choices from repository evidence instead of asking serial preference questions; ask before staging only when missing authority makes every safe faithful contract impossible. Expose other consequential assumptions or product choices in the one contract review.

For broad or cross-boundary work, read the [translation guide](references/translation-guide.md). Before every stage, read the canonical [contract format and approval lifecycle](references/directive-format.md) and [verification profiles](references/verification-profiles.md). Those references own the exact schema, optional-field rules, verification scale, structured evidence registry, and Browser receipt boundary; do not restate them as parallel sections.

Keep the contract proportional. Prefer an existing capable structure and add no speculative component. The contract fixes the approved semantic boundary while leaving necessary in-scope libraries, files, tools, dependencies, and low-level tactics open. Give every completion condition one cheapest sufficient primary evidence source, allow one source to cover several conditions, and avoid duplicate proof.

Choosing evidence and a qualitative verification profile before approval, then concrete argv during execution, is model strategy. The selected profile remains digest-bound as part of the contract. The Hook binds exact check groups and observed results to receipts but does not score verification sufficiency or use legacy units for authority or advice.

When repository evidence makes an argv source's dependency boundary clear, optionally declare its deterministic repository-relative `dependencies` in the contract. Approval binds that declaration. Use `*` only within one path segment, `**` only as a complete segment, or a trailing slash for a directory prefix. Omit the field rather than guess: omission merely reruns the check after a mutation. Never invent or change dependencies after approval to obtain a cache hit.

Write `plain_language` as a self-contained explanation in the user's language, not as a list of developer field names. It must faithfully carry every material outcome, in-scope change, exclusion, safeguard, and completion commitment from the canonical contract. Prefer this readable flow: a concrete example when useful, what will change or be recorded, the important safety guarantees, what will not be done, and a one-sentence summary. Translate verification depth into ordinary language. Do not hide a consequential constraint merely because the technical contract remains available on request.

## Guarded mode: stage once and approve by id

1. Run `click-gate stage '<Execution Contract JSON>'` once and capture the emitted `CLICK_CONTRACT_ID=ctr_<32hex>` plus the Hook-generated easy approval body.
2. Show the exact Hook-provided `plain_language` body once as the default contract, together with the exact `contract_id`. Do not independently summarize, expand, or repeat it. Keep the canonical JSON hidden unless the user asks to see the **original contract**.
3. End with one compact question in the user's language equivalent to: “The contract above is explained in plain language. Do you approve it as written, or would you like to see the original contract first?” Make approval, requested changes, cancellation, and original-contract viewing available responses, then stop without mutating project files.

The original request is not approval of an unseen proposal. A revision after another user response must be staged and shown again and receives a new id.

A request to view the original contract is not approval. Show the exact canonical JSON that was staged, with the same `contract_id`, without passing, changing, or restaging it; then offer the same approval/change/cancel choice. An explicitly requested original disclosure may contain the digest-bound `plain_language` field again because it is the canonical object, not a second default summary.

Only in a later turn whose user response explicitly approves the shown proposal, run `click-gate pass ctr_<32hex>` with the emitted id. Never resend or reconstruct the contract JSON in the approval turn. The Hook proves turn separation and binds the id to the staged digest; the Skill remains responsible for interpreting whether the user's words actually grant approval.

## Execute the approved boundary once

A completed Guarded contract may supply successful verification candidates to a new contract in the same host session and workspace. The new contract still requires its own later-turn approval and exact declared checks. Never treat retained facts as inherited execution authority or completion. Requalification and receipt v5 follow the capability protocol; dependency declarations, viewer history and timing cannot authorize reuse by themselves.

Before implementation, read the [anti-loop policy](references/anti-loop-policy.md) and [structured capability protocol](references/capability-protocol.md). Prefer focused follow-up after broad repository context; this is non-blocking strategy guidance, not contract authority. Implement continuously without a replacement plan or contract. Use their canonical inspect, mutate, managed-service, and verify forms rather than duplicating command details here.

Collect each assigned source once after the last mutation that can invalidate it. Reuse successful evidence, keep Browser or hosted work out of a shadow verification suite, and stop verification when each condition has current evidence. Treat repeat, retry, and timing notices as non-authoritative guidance, not permission failures; active runner conflicts, Browser receipt binding, and verification-time repository mutation remain hard. Stop any managed service before declaring completion. A failed or stale source may be repaired or replaced under the documented retry rules; it is not a reason to accumulate another proof path.

Verification `reporting` and `failure_collection` are presentation and bounded
execution-policy options, not new authority. Keep the compatibility defaults of
raw output and source-order fail-fast unless the user or task explicitly selects
the versioned alternatives. Actionable diagnostics may summarize only the
original one-time execution and point to owner-readable bounded local detail.
Bounded failure collection may continue only across caller-declared independent
submitted sources and must recheck claim, workspace, environment and executable
at every additional source boundary. Follow the schemas, limits, stop conditions,
dashboard privacy rules and whole-task measurement distinctions in
[Verification efficiency](references/verification-efficiency.md).

For a sharded broad source, always resubmit the approved parent id and exact parent argv. Never invoke internal shard ids directly or treat the shard map as permission to skip a stale child. A sibling pass may survive a same-revision failure; after a mutation, reuse remains subject to the existing per-child authority.

When submitting verification, include the actual repository directory as the top-level absolute `workdir` whenever the execution tool is launched outside the Hook session directory. This is required for Codex calls that select a per-call workdir because the Hook event exposes only the session cwd. The one-use runner checks that its real cwd matches the prepared binding before any check executes.

When the user asks to view Shadow data, use the explicit `click-gate dashboard start`, `status`, and `stop` controls described in the capability protocol. Treat its Evidence Map and ROI as current-lifecycle, non-authoritative telemetry, and stop the viewer when the inspection is complete.

Keep Observer collection separate from that viewer. New lifecycles default to
`click-gate observer off`; use the explicit `shadow` control only when Shadow
collection is intended. Use `click-gate observer authoritative` only after a
Guarded contract that covers the work has been separately approved, and only
for the exact supported profile in
[Authoritative Observer v2](references/authoritative-observer-v2.md). Enabling
the mode prepares a candidate runtime; only the one-use verification runner's
complete, signed and current observation can authorize reuse. Never interpret
the control, dashboard, caller JSON, or a Shadow record as authority.

In Guarded mode, do not request reapproval for an in-scope detail, a narrowing instruction, or a technical choice. Record the follow-up turn digest and continue. Reapproval is required only when the approved outcome, visible behavior, boundary, invariant, authority, or verification commitment materially changes. The digest proves that the follow-up was recorded, not that the Hook semantically proved it was inside the prior boundary; interpret that distinction faithfully. In Evidence mode there is no Click approval to repeat; follow the host's authority prompts.

The Hook enforces observable contract shape, id/digest binding, turn order, supported tool paths, one-use runners, and evidence receipts. It cannot prove semantic approval, hidden reasoning, unmatched connector behavior, architecture truth, implementation fidelity, or the optimal amount of verification. If Hook enforcement is unavailable, preserve the same ordering and disclose that limitation.
