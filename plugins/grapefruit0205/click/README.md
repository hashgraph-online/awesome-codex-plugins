# Click

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Djunseok-pak%252Fclick%26metric%3Dtrust)](https://hol.org/go/guard/pjseok1219?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-PJSEOK1219%23upgrade&link_id=351107f3-00d1-4b0f-8aac-1bb449193d84&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)
[![CI](https://github.com/grapefruit0205/click/actions/workflows/ci.yml/badge.svg)](https://github.com/grapefruit0205/click/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [한국어](README.ko.md) | [简体中文](README.zh-CN.md)

> Less repetition. More progress.

Click provides **incremental verification** for coding agents. It records which checks ran, what changed, and whether an earlier result still applies through **revision-aware evidence**. Evidence mode is the default and works under the host's existing permissions. Guarded mode adds an explicitly approved work boundary when needed.

The goal is to complete the same agreed work with less time, token use, and intervention. Reused checks are one part of that result; they do not by themselves demonstrate a faster completed task.

- **Reuse with an explanation:** retain a valid result only when its execution bindings and reuse rules still hold.
- **Automatic sharding:** propose and maintain groups for supported suites, retaining the full-suite fallback when splitting is unsupported or not worthwhile.
- **Useful verification feedback:** show executed, reused, failed, and outstanding checks; optionally summarize failures.
- **A local dashboard:** inspect results, reuse reasons, measurements, and shareable reports in Korean, English, or Simplified Chinese.

Click does not prove that the code is correct or that the selected tests are sufficient.

## Install and update

Install from the Codex CLI:

```sh
codex plugin marketplace add grapefruit0205/click
codex plugin add click@click
```

Restart Codex and start a new task so the installed Hooks and skill reload. Review pending Click Hooks in the CLI's `/hooks` view before relying on them; see [Hook troubleshooting](#hook-troubleshooting).

Current release: **v0.93.0**. To update:

```sh
codex plugin marketplace upgrade click
codex plugin add click@click
```

Restart and use a fresh task after updating. v0.93.0 rejects malformed evidence revisions, binds safe-change and successor reuse to their exact current inputs, confirms those inputs again before reuse, and improves explicit process termination and fallback-report cleanup. Automatic sharding and authorized shard reuse remain supported. See [release notes](RELEASE_NOTES.md) and the [review-hardening record](docs/review-hardening/reports/phase-6.md) for validation, measurements, and their limits.

## Start with everyday work

Ask Codex normally, for example:

```text
Refactor the authentication parser and preserve its public behavior.
Run the repository's relevant tests with Click Evidence and show click-gate status.
```

The `click-gate` lines in this guide are Click controls for the agent to issue inside the Codex task. Installation commands above run in your terminal.

| Mode | Behavior |
| --- | --- |
| **Evidence — default** | Records work and verification under host permissions, without an additional Click approval step. |
| **Guarded — opt in** | Stages a readable contract and waits for explicit approval in a later user turn before work inside that contract. |
| **Off** | Leaves execution to the host without Click's workflow enforcement. |

To change the default, choose one:

```text
click-gate default evidence
click-gate default guarded
click-gate default off
```

To explicitly request Guarded work:

```text
@Click Use Guarded mode to add order cancellation and prevent duplicate refunds.
```

You can approve the proposed contract, request changes, cancel, or view its original representation. A subsequent Guarded task needs its own contract and approval. Successful checks can become reuse candidates after requalification; approval and unfinished work do not transfer. See [operating modes](skills/click/references/modes.md).

## When can a result be reused?

Click checks the exact command, workspace and mutation state, relevant inputs, environment, executable identity, and known host Hook coverage. A previous success or a dashboard entry alone is insufficient.

| Route | Required basis |
| --- | --- |
| Same revision | A successful receipt for the exact check whose current bindings still match. |
| Committed safe-change policy | An unchanged `.click/evidence-reuse.json` policy committed **before the baseline**, permitting every net changed path for that exact check. No Observer is required. |
| Authoritative input observation | A complete signed input snapshot from a supported, explicitly enabled Guarded run, with all reuse conditions rechecked. |

For example, if a policy for the exact authentication test command was committed before revision 12 and permits `README.md` changes:

```text
revision 12  authentication code changed → run the check and record a pass
revision 13  only README.md changed       → reuse if policy and bindings still match
revision 14  authentication code changed → run again; the policy does not allow this change
```

An unlisted path, changed policy, ambiguous Git state, changed executable or environment, or later workspace drift requires real execution. The safe-change declaration is repository-owner policy, not automatic dependency discovery.

The optional `.click/evidence-dependencies.json` map, or dependencies in an approved Guarded contract, declares candidate input boundaries. A map alone does not establish observation authority. Approval-bound contract dependencies and concrete manifest paths remain hard dependencies; complete authoritative observation can refine expanding manifest patterns. For this observation-based route, missing or incomplete authority cannot justify reuse after a mutation. See [verification profiles and reuse rules](skills/click/references/verification-profiles.md) and [Authoritative Observer v2](skills/click/references/authoritative-observer-v2.md).

A committed [Evidence Shards map](skills/click/references/evidence-shards-v1.md) can split an exact parent suite into children. A passed sibling can remain reusable while another fails, subject to the same per-child rules. Invalid maps fall back to the original suite.

## Automatic sharding: init → status → refresh

Start with metadata inspection, or provide the repository's exact supported test command:

```text
click-gate sharding init
click-gate sharding init -- python3 -m unittest discover -s tests -q
click-gate sharding status
click-gate sharding refresh
```

`init` without a command reads repository metadata only: it does not import project code, collect tests, run a suite, or write policy. With a command, initialization requires active Evidence or approved Guarded execution; bounded collection and cost measurement can execute the parent and proposed children. Short suites may return `whole-suite-preferred`.

For an eligible proposal, the normal sequence is:

1. Review the proposal; `refresh` applies eligible policy in Evidence, or under the separately approved Guarded scope.
2. At `commit-required`, commit the exact proposed policy through your normal Git workflow. The setup controller does not run `git add`, `commit`, or `push`.
3. `refresh` performs parent/child bootstrap, then reports `baseline-required`. Bootstrap is setup cost.
4. `refresh` obtains baseline verification for the current revision. Passing children can reach `sharding-ready` with reuse unavailable; `reuse-ready` additionally requires complete authoritative observations for every child.

Read `status` between steps and follow its next action. Automatic setup's reuse readiness is separate from the ordinary exact-receipt and safe-change routes above. Later discovery changes produce a bounded diff; refresh updates only policy matching Click's previously committed lineage and does not overwrite user-owned or modified policy.

The collector supports bounded unittest discovery and a conservative pytest collect-only profile on CPython 3.10–3.14. Unsupported or ambiguous collection retains the parent command. See the [automatic sharding guide](skills/click/references/automatic-sharding-setup.md) and [two-project E2E record](docs/auto-sharding-e2e.md).

## Can Observer stay off?

**Yes. Off is the default.** Evidence recording, ordinary verification, the dashboard, and qualifying exact-receipt or safe-change reuse work with Observer off.

```text
click-gate observer status
click-gate observer off
```

Optional modes have different purposes:

- `click-gate observer shadow` collects non-authoritative telemetry on supported Linux, macOS, and Windows backends. Predictions never authorize reuse.
- `click-gate observer authoritative` requires a separately approved Guarded contract, a supported direct CPython **3.12.3** unittest command, and the platform's native prerequisites. Enabling it alone is insufficient: reuse requires a complete signed observation.

Linux strace 6.8, macOS privileged `fs_usage`, and Windows inbox ETW profiles have native-host validation records. The automatic-sharding E2E record is Linux-scoped. Click does not install prerequisites or elevate privileges. Incomplete observation preserves the test's actual result, but does not establish future reuse authority. See [platform requirements and validation scope](skills/click/references/authoritative-observer-v2.md).

## Dashboard: results and measured effect

```text
click-gate dashboard start
click-gate dashboard status
click-gate dashboard stop
```

Open the local URL reported by the control. The dashboard shows the current task, verification-group states, reuse reasons, and work history. Each completed group is persisted while later groups run. A viewer can remain connected across successive Evidence tasks in the same host session and workspace.

The **top-right language selector** offers **한국어 · English · 简体中文**. Korean is the default; the browser remembers the preference for the same origin when local storage is available. Reports follow the selected language, while user-authored task and check names retain their original text.

The first cards show **net task time** and **token savings rate**. They remain unmeasured until a suitable whole-task comparison is imported. The separate **test execution savings** row estimates avoided reruns from actually reused groups and eligible previous successful durations.

| Measurement | What supports it |
| --- | --- |
| Whole-task time | Equivalent completion conditions and valid task start/end boundaries. |
| Token reduction | A comparable baseline and complete usage for the selected task scope. This is checked separately from time. |
| Avoided test execution | Prior successful durations tied to actual reuse; an estimate, with coverage shown. |
| Hook processing time | A partial runtime interval, not the host's entire wait or total development time. |

To prepare a public whole-task comparison from an internal measurement file:

```sh
python3 benchmarks/task_efficiency.py INTERNAL.json --public-output PUBLIC.json
```

Import `PUBLIC.json` in the dashboard. This is an explicit measurement workflow; Click does not automatically collect complete task time or token usage. Missing measurements stay unmeasured. Losses, failures, cancellations, incomplete samples, and first-use costs remain visible. Different modes, baselines, and scenarios are kept separate.

Sharing supports a copied summary, public JSON, and standalone HTML. The public reports exclude raw commands and logs, input paths, environment values, raw usage, and absolute token counts. Dashboard imports accept public task-efficiency v1 and benchmark v4 workflow/v2 paired reports, up to 4 MiB; dashboard export v5 JSON is not an import format. Viewing, importing, exporting, or switching language does not grant approval or reuse authority. See [measurement and privacy boundaries](VERIFICATION_EFFICIENCY.md).

## Verification status and failure feedback

Use `click-gate status` for a compact read-only view of checks that ran, were reused, did not run, or remain unrequested, including invalidation after mutations. It reports registered evidence, not whole-task correctness.

Raw output and source-order fail-fast are the defaults. Opt-in actionable reporting for supported unittest/pytest output summarizes failed tests with bounded local details. Optional bounded failure collection continues only across explicitly submitted, caller-declared independent sources within stated limits; automatic shards are not assumed independent. Setup errors, cancellation, drift, and unknown output stop collection. See [reporting and failure collection](skills/click/references/verification-efficiency.md).

Click also caches supported explicit local reads such as `cat`, bounded `sed -n`, and `rg`. Reuse binds the request, contents, directory inventory, ignore rules, and execution conditions. Unsupported, stale, failed, or oversized reads run normally. This cache is local and never becomes verification evidence. See the [anti-loop policy](skills/click/references/anti-loop-policy.md).

## Completion receipts and reproducible benchmarks

After current evidence is complete:

```text
click-gate receipt export
```

Ask the agent to save the returned JSON as `completion-receipt.json`, then verify that file:

```text
click-gate receipt verify ./completion-receipt.json
```

Receipts bind the request, revision, final workspace, checks, execution conditions, coverage, and reuse lineage. Evidence successors use v4; an applied Guarded successor uses v5 with requalified candidate and shard provenance when present. Legacy receipts remain readable. Verification reports **unsigned-integrity-only**: it can detect inconsistent receipt contents, but does not prove publisher identity.

To reproduce a completed Guarded A → B comparison from the source checkout:

```sh
python3 benchmarks/incremental_verification.py --guarded-workflow --iterations 3 --warmups 1 --workload-rounds 40000 --output /tmp/click-workflow.json --html-output /tmp/click-workflow.html
```

The benchmark uses independent real Hook/runner fixtures, not approval in your active task. It compares no Click, Guarded with default reuse settings, and Guarded with precommitted shards/safe-change policy; Evidence remains the product default. The sequence includes unrelated and related edits, environment changes, failures, repair, and unchanged retries, audited against the same-state full suite. Setup, transition, audit costs, warmups, and slower results remain in the report. Current v4 workflow and v2 paired reports can be imported in the dashboard. These samples do not establish universal development-time or token savings.

## Hook troubleshooting

On Windows, confirm that Click is enabled and at least one Python 3 launcher works. The bundled launcher tries `py -3`, then `python`, then `python3`:

```powershell
codex --version
codex plugin list --json
py -3 --version
python --version
python3 --version
```

Restart Codex after an installation or update. In the CLI, use `/hooks` to review and trust pending Click definitions. Trust follows the current Hook hash. `[features].hooks = false` disables Hooks; administrator policy `allow_managed_hooks_only = true` skips plugin Hooks. See the official [Codex Hooks guide](https://learn.chatgpt.com/docs/hooks).

Then start a new task, perform a small real verification, and inspect `click-gate status`. An enabled plugin alone does not demonstrate that its Hooks ran. Windows CI coverage and native Observer validation are described in the [release notes](RELEASE_NOTES.md); they do not replace checking the user's installed host and configuration.

## Antigravity

An experimental Google Antigravity adapter is available from the source checkout:

```sh
agy plugin install ./dist/antigravity
```

It uses the host's available Hook surface for Evidence and Guarded workflows. Unsupported coverage is not reported as independent observation. See the [Antigravity adapter guide](platforms/antigravity/README.md).

## Limits and technical reference

Click is a workflow guardrail, not an operating-system sandbox. It cannot prove hidden reasoning, semantic correctness, test sufficiency, or external activity outside matched Hooks. Manual or hosted evidence without independent observation remains an attestation. Keep normal code review, CI, branch protection, and deployment controls.

Protocol details and implementation boundaries:

- [Product Constitution](PRODUCT_CONSTITUTION.md) and [guard classification](GUARD_CLASSIFICATION.md)
- [Operating modes](skills/click/references/modes.md) and [Guarded contract format](skills/click/references/directive-format.md)
- [Verification profiles](skills/click/references/verification-profiles.md) and [capability protocol](skills/click/references/capability-protocol.md)
- [Automatic sharding setup](skills/click/references/automatic-sharding-setup.md) and [Evidence Shards v1](skills/click/references/evidence-shards-v1.md)
- [Authoritative Observer v2](skills/click/references/authoritative-observer-v2.md), [Shadow Observer v1](skills/click/references/observer-v1.md), and [Shadow Intelligence v1](skills/click/references/shadow-intelligence-v1.md)
- [Verification efficiency](skills/click/references/verification-efficiency.md), [anti-loop policy](skills/click/references/anti-loop-policy.md), and [runtime architecture and optimization](docs/runtime-optimization.md)

## License

[MIT](LICENSE)
