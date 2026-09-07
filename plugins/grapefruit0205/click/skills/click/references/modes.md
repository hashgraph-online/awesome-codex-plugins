# Operating Modes

Click stores one user-level default outside the target repository. The setting persists across sessions; a per-turn bypass does not change it. The public modes are **Evidence**, **Guarded**, and **Off**.

## Default and migration

New and unset installations use Evidence mode without asking a setup question. Existing pre-v2 preferences preserve the user's authority choice: `on` migrates to Guarded and `manual` migrates to Off. A staged or incomplete Guarded contract is never unlocked by migration.

Use one of:

```text
click-gate default evidence
click-gate default guarded
click-gate default off
```

`click-gate default status` reports the stored value. Legacy `default on` and `default manual` remain command aliases for Guarded and Off when explicitly entered, and stored legacy values migrate to those same public names.

## Evidence (default)

Evidence mode does not stage or approve a Click contract. The host remains the execution authority. Click creates an intent session from the user prompt, records mutation revisions and exact verification receipts, prevents stale evidence from claiming completion, and exports an honest receipt with `approval_bound: false` and `execution_authority: host`.

The model chooses evidence ids and concrete argv during execution. Same-revision reuse requires the exact check, protected tree, environment, executable, and host-coverage bindings. Cross-revision reuse may use only a committed `.click/evidence-dependencies.json` mapping; an agent's runtime dependency guess is not authority in Evidence mode.

An in-scope or narrowing follow-up continues the same session and appends its prompt digest to the receipt lineage. When current evidence completes the session, the next software request starts a fresh Evidence session. Questions and explanations remain lightweight.

For a read-only code review, use `click-gate review`, remain read-only, and collect only relevant inspection evidence. A request that also asks for fixes follows Evidence mode and does not introduce Click approval.

## Guarded

Guarded applies one compact contract to software creation, modification, deletion, refactoring, and repair. The Hook blocks matched mutations until the opaque id emitted for the staged contract is passed from a later approving user turn. Plans remain available as non-authoritative guidance and cannot approve, replace, or widen the contract.

Show the user the Hook-generated Goal, Changes, Unchanged, and Completion checks projection. Keep canonical JSON behind optional Technical contract details. Once approved, in-scope details, narrowing instructions, files, tools, dependencies, and implementation tactics do not require reapproval. A material change to the outcome, visible behavior, boundary, must-hold promise, authority, or verification commitment requires a replacement contract. A recorded follow-up digest proves lineage, not the runtime's semantic judgment that the request stayed inside the boundary.

After every declared evidence source is current for the final mutation revision and no managed service remains active, a later change may stage a fresh contract. A contract with no argv source needs no ceremonial local batch. Missing, running, failed, or stale evidence—and an active managed service—still block replacement.

## Off

Ordinary work is fail-open while no Guarded contract is active. Apply Guarded when the user selects `@Click` or invokes `$click`; run `click-gate arm` and use the compact-contract workflow. Once staged or approved but incomplete, that contract blocks ordinary mutations across later turns. On approval or resume, pass the same emitted `contract_id`; do not resend the JSON. Ephemeral state may age out, but staged and approved-incomplete contracts are never removed by cleanup.

## User-authorized bypass and cancel

A bypass is authorized only when the first line of the current user prompt is either:

```text
@Click bypass
[@Click](plugin://click@click) bypass
```

The label and action are case-insensitive, but the plugin URI must be exactly `plugin://click@click`. The directive line contains no other text; the task may continue on later lines. Then run `click-gate bypass` once in that turn. The marker is one-use. Bypass leaves a staged or approved-incomplete contract intact and does not change the persistent Evidence, Guarded, or Off preference.

To discard an active contract, use the corresponding `cancel` form and run `click-gate cancel` once in that turn:

```text
@Click cancel
[@Click](plugin://click@click) cancel
```

A bare bypass or cancel command without its matching user directive is denied. Cancel clears active contract and review state but does not change the persistent mode.

The legacy `click-gate mode strict|adaptive` command remains available as a session-only compatibility control. Prefer the public persistent modes.
