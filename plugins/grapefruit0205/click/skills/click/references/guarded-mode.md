# Guarded Mode Workflow

This reference applies only when Guarded mode is active: the user invoked
`@Click` or `$click`, or the stored default is `click-gate default guarded`.
Evidence mode never stages a contract or asks for Click approval; follow the
main Skill there. Mode selection, resume, bypass, and cancel rules live in
[operating modes](modes.md).

In Guarded mode, use one approval-bound contract for software creation,
modification, deletion, refactoring, and repair. The contract remains
hard-locked until approved or cancelled. In Off mode, an explicit `@Click` or
`$click` invocation may start this workflow with `click-gate arm`. Bypass and
cancel require the exact user-authorized first-line forms in the modes
reference; never infer them from ordinary prose.

## Compile the smallest faithful contract

Treat the user's requested result, visible behavior, scope, constraints, and authority as primary. A contract-only or handoff request does not authorize implementation. Inspect from the narrowest relevant repository entry point and widen only while consequential behavior is unresolved. Do not treat an existing system as a blank slate or include unrelated cleanup. Resolve ordinary technical choices from repository evidence instead of asking serial preference questions; ask before staging only when missing authority makes every safe faithful contract impossible. Expose other consequential assumptions or product choices in the one contract review.

For broad or cross-boundary work, read the [translation guide](translation-guide.md). Before every stage, read the canonical [contract format and approval lifecycle](directive-format.md) and [verification profiles](verification-profiles.md). Those references own the exact schema, optional-field rules, verification scale, structured evidence registry, and Browser receipt boundary; do not restate them as parallel sections.

Keep the contract proportional. Prefer an existing capable structure and add no speculative component. The contract fixes the approved semantic boundary while leaving necessary in-scope libraries, files, tools, dependencies, and low-level tactics open. Give every completion condition one cheapest sufficient primary evidence source, allow one source to cover several conditions, and avoid duplicate proof.

Choosing evidence and a qualitative verification profile before approval, then concrete argv during execution, is model strategy. The selected profile remains digest-bound as part of the contract. The Hook binds exact check groups and observed results to receipts but does not score verification sufficiency or use legacy units for authority or advice.

When repository evidence makes an argv source's dependency boundary clear, optionally declare its deterministic repository-relative `dependencies` in the contract. Approval binds that declaration. Use `*` only within one path segment, `**` only as a complete segment, or a trailing slash for a directory prefix. Omit the field rather than guess: omission merely reruns the check after a mutation. Never invent or change dependencies after approval to obtain a cache hit.

Write `plain_language` as a self-contained explanation in the user's language, not as a list of developer field names. It must faithfully carry every material outcome, in-scope change, exclusion, safeguard, and completion commitment from the canonical contract. Prefer this readable flow: a concrete example when useful, what will change or be recorded, the important safety guarantees, what will not be done, and a one-sentence summary. Translate verification depth into ordinary language. Do not hide a consequential constraint merely because the technical contract remains available on request.

## Stage once and approve by id

1. Run `click-gate stage '<Execution Contract JSON>'` once and capture the emitted `CLICK_CONTRACT_ID=ctr_<32hex>` plus the Hook-generated easy approval body.
2. Show the exact Hook-provided `plain_language` body once as the default contract, together with the exact `contract_id`. Do not independently summarize, expand, or repeat it. Keep the canonical JSON hidden unless the user asks to see the **original contract**.
3. End with one compact question in the user's language equivalent to: “The contract above is explained in plain language. Do you approve it as written, or would you like to see the original contract first?” Make approval, requested changes, cancellation, and original-contract viewing available responses, then stop without mutating project files.

The original request is not approval of an unseen proposal. A revision after another user response must be staged and shown again and receives a new id.

A request to view the original contract is not approval. Show the exact canonical JSON that was staged, with the same `contract_id`, without passing, changing, or restaging it; then offer the same approval/change/cancel choice. An explicitly requested original disclosure may contain the digest-bound `plain_language` field again because it is the canonical object, not a second default summary.

Only in a later turn whose user response explicitly approves the shown proposal, run `click-gate pass ctr_<32hex>` with the emitted id. Never resend or reconstruct the contract JSON in the approval turn. The Hook proves turn separation and binds the id to the staged digest; the Skill remains responsible for interpreting whether the user's words actually grant approval.

## Execute the approved boundary once

A completed Guarded contract may supply successful verification candidates to a new contract in the same host session and workspace. The new contract still requires its own later-turn approval and exact declared checks. Never treat retained facts as inherited execution authority or completion. Requalification and receipt v5 follow the capability protocol; dependency declarations, viewer history and timing cannot authorize reuse by themselves.

Before implementation, read the [anti-loop policy](anti-loop-policy.md) and [structured capability protocol](capability-protocol.md). Prefer focused follow-up after broad repository context; this is non-blocking strategy guidance, not contract authority. Implement continuously without a replacement plan or contract. Use their canonical inspect, mutate, managed-service, and verify forms rather than duplicating command details here.

Collect each assigned source once after the last mutation that can invalidate it. Reuse successful evidence, keep Browser or hosted work out of a shadow verification suite, and stop verification when each condition has current evidence. Treat repeat, retry, and timing notices as non-authoritative guidance, not permission failures; active runner conflicts, Browser receipt binding, and verification-time repository mutation remain hard. Stop any managed service before declaring completion. A failed or stale source may be repaired or replaced under the documented retry rules; it is not a reason to accumulate another proof path.

Verification `reporting` and `failure_collection` are presentation and bounded
execution-policy options, not new authority. Guarded keeps the compatibility
defaults of raw output and source-order fail-fast unless the user or task
explicitly selects the versioned alternatives; only Evidence defaults supported
unittest/pytest checks to the `actionable` summary. Actionable diagnostics may summarize only the
original one-time execution and point to owner-readable bounded local detail.
Bounded failure collection may continue only across caller-declared independent
submitted sources and must recheck claim, workspace, environment and executable
at every additional source boundary. Follow the schemas, limits, stop conditions,
dashboard privacy rules and whole-task measurement distinctions in
[Verification efficiency](verification-efficiency.md).

For a sharded broad source, always resubmit the approved parent id and exact parent argv. Never invoke internal shard ids directly or treat the shard map as permission to skip a stale child. A sibling pass may survive a same-revision failure; after a mutation, reuse remains subject to the existing per-child authority. Automatic shard collection, application, and bootstrap require the separately approved contracts described in [automatic sharding setup](automatic-sharding-setup.md).

When submitting verification, include the actual repository directory as the top-level absolute `workdir` whenever the execution tool is launched outside the Hook session directory. This is required for Codex calls that select a per-call workdir because the Hook event exposes only the session cwd. The one-use runner checks that its real cwd matches the prepared binding before any check executes.

Guarded lifecycles start with Observer collection `off`. Use
`click-gate observer authoritative` to prepare explicitly in a separately
approved Guarded contract, and only for the supported profile in
[Authoritative Observer v2](authoritative-observer-v2.md). Enabling the mode
prepares a candidate runtime; automatic preparation installs nothing, does not
request privileges, and never repeats a check to improve capture. Only the
one-use verification runner's complete, signed and current observation—or its
separately signed conditional JS receipt—can authorize observation-based
reuse. Always disclose the conditional receipt's unproven completeness; never
describe it as complete input evidence. Never interpret the control, dashboard,
caller JSON, or a Shadow record as authority. Do not change the requested
reporting mode merely to obtain a reuse receipt.

Do not request reapproval for an in-scope detail, a narrowing instruction, or a technical choice. Record the follow-up turn digest and continue. Reapproval is required only when the approved outcome, visible behavior, boundary, invariant, authority, or verification commitment materially changes. The digest proves that the follow-up was recorded, not that the Hook semantically proved it was inside the prior boundary; interpret that distinction faithfully.

The final receipt must distinguish this Guarded approval from host-authorized Evidence execution. The Hook enforces observable contract shape, id/digest binding, turn order, supported tool paths, one-use runners, and evidence receipts. It cannot prove semantic approval, hidden reasoning, unmatched connector behavior, architecture truth, implementation fidelity, or the optimal amount of verification. If Hook enforcement is unavailable, preserve the same ordering and disclose that limitation.
