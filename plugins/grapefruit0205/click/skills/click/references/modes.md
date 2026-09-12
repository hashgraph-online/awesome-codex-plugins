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

The model chooses evidence ids and concrete argv during execution. Same-revision reuse requires the exact check, protected tree, environment, executable, and host-coverage bindings; observed ignored files are rechecked too. A committed dependency mapping only describes candidate inputs. Cross-revision reuse may use a complete signed native observation, an unchanged repository-owner reuse policy, or a separately attested conditional JS receipt. Conditional JS reuse discloses that input completeness is unproven and excludes known dynamic inputs and capture gaps. Caller-supplied observation JSON and raw diagnostics never authorize reuse. See [automatic observation](https://github.com/grapefruit0205/click/blob/main/docs/architecture/automatic-observation.md) and [conditional JS limits](https://github.com/grapefruit0205/click/blob/main/docs/architecture/node-runtime-observation.md).

An in-scope or narrowing follow-up continues the same session and appends its prompt digest to the receipt lineage. When current evidence completes the session, the next software request starts a fresh Evidence session. Questions and explanations remain lightweight.

New Evidence lifecycles select `observer auto`; explicit off and diagnostic choices survive completed Evidence turns in the same host session. Guarded starts with collection off. `observer authoritative` can prepare a supported native profile in active Evidence or an approved Guarded contract. Automatic preparation does not install tools, elevate privileges or replace an owner policy. A failed preparation is retried when relevant environment, tool, policy or runtime metadata changes; explicit `observer auto` also allows a retry. That scheduling metadata never authorizes reuse.

`observer status` and `status --json` report bounded preparation reasons and next actions; plain `status` prints a short localized summary. The dashboard explains the last recorded per-check decisions. These views do not probe or execute checks, verify current input completeness or grant authority; mode selection alone always reports `reuse_authorized: false`. The actual runner revalidates every reuse request.

For a read-only code review, use `click-gate review`, remain read-only, and collect only relevant inspection evidence. A request that also asks for fixes follows Evidence mode and does not introduce Click approval.

## Guarded

Guarded applies one compact contract to software creation, modification, deletion, refactoring, and repair. The Hook blocks matched mutations until the opaque id emitted for the staged contract is passed from a later approving user turn. Plans remain available as non-authoritative guidance and cannot approve, replace, or widen the contract.

Show the exact Hook-generated easy contract once as the default approval body, with its contract id. Keep canonical JSON hidden unless the user asks for the original contract; viewing it neither approves nor restages the proposal. Offer approval, requested changes, cancellation, and original-contract viewing. Once approved, in-scope details, narrowing instructions, files, tools, dependencies, and implementation tactics do not require reapproval. A material change to the outcome, visible behavior, boundary, must-hold promise, authority, or verification commitment requires a replacement contract. A recorded follow-up digest proves lineage, not the runtime's semantic judgment that the request stayed inside the boundary.

After every declared evidence source is current for the final mutation revision and no managed service remains active, a later change may stage a fresh contract. A contract with no argv source needs no ceremonial local batch. Missing, running, failed, or stale evidence—and an active managed service—still block replacement.

That completed contract may retain successful verification candidates for the next Guarded contract, never approval, execution claims, tokens or completion. The successor must be separately approved and request its own declared checks before current-binding requalification. Changing a dependency declaration does not inherit its predecessor's authority. See the capability protocol for v5 lineage and conservative rerun rules.

After approval, `click-gate observer authoritative` may explicitly prepare the
supported [Authoritative Observer v2](authoritative-observer-v2.md) profiles.
The switch itself grants no reuse. The original check must finish once under
the verified runner and produce a complete signed observation; every current
binding and observed input is checked again in the separately approved
successor contract. Unsupported or incomplete observation simply reruns the
check.

Automatic shard setup follows the active mode. In Evidence mode, `init` may
collect a bounded proposal under host authority and a later explicit `refresh`
may apply the reviewed proposal. In Guarded mode, collection, application, and
bootstrap require the separately approved contracts described in
[automatic sharding setup](automatic-sharding-setup.md). The public
`click-gate sharding init|status|refresh` controls preserve proposal review,
application, the user-owned commit, baseline, and observation boundaries. A
setup proposal is never approval or active repository policy. Status reports
command execution, automatic inventory/split, same-state exact reuse,
owner-committed policy reuse, and authoritative-observation reuse separately.
Observer may remain off when exact or committed-policy authority is sufficient.

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
