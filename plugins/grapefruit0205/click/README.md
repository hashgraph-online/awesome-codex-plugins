# Click

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Djunseok-pak%252Fclick%26metric%3Dtrust)](https://hol.org/go/guard/pjseok1219?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-PJSEOK1219%23upgrade&link_id=351107f3-00d1-4b0f-8aac-1bb449193d84&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)
[![CI](https://github.com/grapefruit0205/click/actions/workflows/ci.yml/badge.svg)](https://github.com/grapefruit0205/click/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [한국어](README.ko.md) | [简体中文](README.zh-CN.md)

> Keep proof in sync with the code.

Click gives coding agents **revision-aware evidence**: test and verification results that stay attached to the code they actually checked.

You keep working normally. Click remembers:

- what the agent was asked to do;
- when the workspace changed;
- which checks really ran;
- whether an old result is still safe to reuse.

It does not tell the model how to think or which files to read.

## The problem in one example

~~~text
revision 12  auth code changed   → auth tests run and pass
revision 13  README changed      → auth inputs unchanged, reuse the result
revision 14  auth code changed   → old result is stale, run the tests again
~~~

Without a revision-aware record, an agent may trust an old test after the code changed or rerun a large suite after an unrelated edit. Click keeps the result only while the inputs that made it valid still match.

That is the core of Click.

## How it feels to use

Click has three modes:

| Mode | Use it for | What you see |
| --- | --- | --- |
| **Evidence** (default) | Everyday coding | No Click approval step. Work normally and receive an evidence receipt. |
| **Guarded** | Risky or tightly bounded changes | Review one short contract before the agent can change anything. |
| **Off** | Work where Click is not needed | The host handles execution on its own. |

### Evidence: the normal default

Evidence mode uses the permissions already provided by Codex or the host. Click does not pretend it approved the work.

The final receipt says:

~~~text
approval_bound: false
execution_authority: host
~~~

### Guarded: one approval when the boundary matters

Use Guarded for payments, authentication, deletion, migrations, public API changes, or any task where changing the wrong thing would matter.

The approval view is written for people:

~~~text
Goal
What should be true when the task is done?

Changes
What may change?

Unchanged
What must remain compatible or untouched?

Completion checks
How will the result be verified?
~~~

The raw JSON contract is optional technical detail. Approval happens in a later user turn, and work inside the approved boundary continues without repeated approval prompts.

## Install

~~~bash
codex plugin marketplace add grapefruit0205/click
codex plugin add click@click
~~~

Restart Codex so its Hooks reload, then start a new task.

New installations use Evidence mode. You can change the default:

~~~text
click-gate default evidence
click-gate default guarded
click-gate default off
~~~

Then ask for work normally:

~~~text
Refactor the authentication parser and keep its public behavior unchanged.
~~~

Or explicitly choose Guarded:

~~~text
@Click Add order cancellation and prevent duplicate refunds.
~~~

## Update

Current release: **v0.50.0**

~~~bash
codex plugin marketplace upgrade click
codex plugin add click@click
~~~

Start a fresh task after updating.

See [release notes](RELEASE_NOTES.md) for version history.

## What makes evidence reusable?

A result is reused only when its important bindings still match, such as:

- the exact check;
- the relevant files and their contents;
- the workspace state;
- the environment and executable;
- the known host Hook coverage.

If Click cannot establish that match, it runs the check again.

Cross-revision reuse is intentionally conservative. Evidence mode uses a committed dependency map:

~~~text
.click/evidence-dependencies.json
~~~

The map says which files can invalidate a specific check. It is optional; leaving it out simply means that the check runs again after a mutation.

## Completion receipt

Click can export a receipt after current evidence is complete:

~~~text
click-gate receipt export
click-gate receipt verify ./completion-receipt.json
~~~

The receipt binds the request lineage, mutation revision, final workspace, checks, environment, executable identity, host coverage, and reuse lineage.

Receipt verification currently reports **unsigned-integrity-only**. It detects accidental or uncoordinated changes to the receipt, but it does not yet prove the publisher's identity.

## What Click enforces

Click keeps hard rules for things that need runtime integrity:

- approval and contract identity in Guarded mode;
- one-use execution claims and replay protection;
- mutation revisions and stale-evidence invalidation;
- exact verification receipts;
- managed local service cleanup;
- receipt integrity.

Suggestions about exploration, retries, planning, and verification depth remain advice. They do not block the model's search strategy.

## Antigravity

The repository also ships an experimental Google Antigravity adapter:

~~~bash
agy plugin install ./dist/antigravity
~~~

The adapter supports the same Evidence and Guarded model through Antigravity's available Hook surface. Host coverage is reported honestly; unsupported paths are not described as independently observed.

See [the Antigravity adapter guide](platforms/antigravity/README.md).

## Honest limits

Click is a workflow guardrail, not an operating-system sandbox.

It cannot prove hidden reasoning, semantic correctness, unmatched external tool activity, or the quality of a test chosen by the model. Hosted and manual evidence outside a matched Hook is recorded as an attestation rather than independent observation.

Use normal code review, CI, branch protection, deployment controls, and security boundaries where they belong.

## Technical reference

The README stays short on purpose. Protocol and architecture details live here:

- [Product Constitution](PRODUCT_CONSTITUTION.md)
- [Guard classification](GUARD_CLASSIFICATION.md)
- [Operating modes](skills/click/references/modes.md)
- [Guarded contract format](skills/click/references/directive-format.md)
- [Verification profiles](skills/click/references/verification-profiles.md)
- [Capability protocol](skills/click/references/capability-protocol.md)
- [Anti-loop policy](skills/click/references/anti-loop-policy.md)

## License

[MIT](LICENSE)
