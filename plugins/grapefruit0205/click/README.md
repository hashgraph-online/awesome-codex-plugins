# Click

[![HOL Guard](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Djunseok-pak%252Fclick%26metric%3Dtrust)](https://hol.org/go/guard/pjseok1219?dest=%2Fguard%2Fbilling%3Fpromo%3DGUARD20-PJSEOK1219%23upgrade&link_id=351107f3-00d1-4b0f-8aac-1bb449193d84&utm_source=insights_share&utm_medium=affiliate_cta&utm_campaign=share20)
[![CI](https://github.com/grapefruit0205/click/actions/workflows/ci.yml/badge.svg)](https://github.com/grapefruit0205/click/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English | [한국어](README.ko.md) | [简体中文](README.zh-CN.md)

> **The same test never runs twice. Its output is never read twice. And nothing is skipped by guess.**

You change one part of a project. Your coding agent runs the whole test suite again,
then reads the whole output again. Another small edit, and the same wait and the
same context spend repeat.

**Click is a workflow guardrail for verification and reuse that leaves your
model selection and reasoning settings unchanged.** The model still decides how
to implement. Click records each check's exact receipt, decides at execution time
which checks must run again, and replaces a skipped run with one line instead of
its full output. A check is skipped only when an exact same-state receipt, a
signed input observation, or a committed owner policy proves it still holds;
anything ambiguous runs.

This is **incremental verification**, backed by **revision-aware evidence**:
a record of what passed and whether it remains valid now. Every decision carries
a reason code, and the dashboard shows where reuse was lost. Savings target
repeated execution and repeated reading; Click does not switch you to a weaker
model or lower its reasoning settings.

## What changes in your workflow?

Suppose a project has 12 verification groups and you edit only authentication:

```text
First run       → establish passing results for all 12 groups
Edit auth code  → run the 3 affected groups
                → reuse 9 groups whose evidence still holds
```

This is an example, not a benchmark. It requires a complete split and valid
per-group input or policy evidence. A shared change may run all groups; an
unverifiable split runs the original full suite.

- **Less waiting between edits:** avoid eligible unchanged checks while rerunning affected ones.
- **Less context spent:** a reused check returns one receipt line; supported Python runners report a bounded failure summary instead of raw output by default in Evidence mode.
- **Never a wrong skip:** reuse needs an exact receipt, a signed input observation, or a committed owner policy; ambiguity always runs.
- **A reason for each decision:** see what ran, what was reused, and why, including the rerun-reason distribution over retained history.
- **Continuity across tasks:** carry successful results forward as candidates and recheck them.
- **A visible outcome:** inspect verification, estimated avoided execution time, and output the host did not read again in a local dashboard.

Click fits projects with **slow checks, repeated edit/test cycles, and separable
test groups**. If your entire suite takes two seconds, setup and bookkeeping may
cost more than rerunning it. The goal is less time spent completing the same work;
production minutes and token savings still need representative measurement.

## Install and update

Click ships as a plugin for **Codex CLI** and **Claude Code**. Both hosts run
the same runtime, evidence rules, and `click-gate` commands.

### Codex CLI

```sh
codex plugin marketplace add grapefruit0205/click
codex plugin add click@click
```

Restart Codex and start a new task so the installed Hooks and skill reload. Review pending Click Hooks in the CLI's `/hooks` view before relying on them; see [Hook troubleshooting](#hook-troubleshooting).

To update:

```sh
codex plugin marketplace upgrade click
codex plugin add click@click
```

### Claude Code

```sh
claude plugin marketplace add grapefruit0205/click
claude plugin install click@click
```

Start a new Claude Code session so the installed Hooks and skill load. Every
`click-gate` command is an ordinary Bash command that the installed `PreToolUse`
Hook rewrites onto Click's runner; Evidence state lives under
`~/.claude/plugins/data/click-click/`. Linux and macOS are supported; see
[Click for Claude Code](platforms/claude/README.md) for the host limits.

To update:

```sh
claude plugin marketplace update click
claude plugin update click@click
```

Current release: **v0.96.1**. Restart and start a new task after updating.

This README also describes the **unreleased v0.97 candidate** source on `main`: automatic observation, conditional JS reuse and recovery. The published release remains **v0.96.1**; updating it does not install candidate changes. See [release notes](RELEASE_NOTES.md).

## Try it on your next change

After installation, ask Codex or Claude Code:

```text
Use Click Evidence for this change. Run the relevant tests, show which checks
ran or were reused, and open the Click dashboard.
```

**Evidence is the default.** It uses the host's existing permissions without an
extra Click approval step. The first successful execution establishes a baseline;
reuse becomes possible only when a later request satisfies its rules. Automatic
test splitting is a separate setup step for supported suites.

The `click-gate` commands below are controls for the agent inside a Codex task.
For a large suite, ask it to inspect `click-gate sharding init`, then follow
`click-gate sharding status` and the [setup guide](skills/click/references/automatic-sharding-setup.md).

## See what Click did

```text
click-gate status
click-gate status --json
click-gate dashboard start
```

`click-gate status` prints a few short lines in the dashboard language: executed
and reused counts with the estimated avoided time, the mode and revision, and
the next action. `--json` returns the full report. Open the local URL returned
by the dashboard command. See executed, reused,
failed and outstanding groups, their reuse reasons, and the next action when
input collection is not ready. The top-right language selector offers
**한국어 · English · 简体中文**.

Avoided test execution is estimated from actual reuse and prior successful
durations. Whole-task time and token savings stay **unmeasured** until you import
a suitable comparison. Reusing 75% of groups does not mean a 75% faster task.

## Which projects can use it?

| Project | Current scope |
| --- | --- |
| Python backends and libraries | Splitting and reuse for supported unittest/pytest commands. Automatic input observation uses bounded CPython 3.12 profiles. |
| JS/TS frontends and Node projects | Supported Vitest/Jest suites can split and requalify each child. Observation-only conditional reuse is limited to eligible Linux Node 22.23.2 executions. |
| Go services | `go test` execution and qualifying result reuse. No automatic test splitting. |
| Mixed-language repositories | Decide execution and reuse per registered check; no claim of discovering every dependency across languages. |

Rust, Java, .NET and C/C++ command profiles and their tool CI coverage appear in
the detailed table below. Executing a command, splitting its tests and authorizing
reuse from input observation are separate capabilities.

## What happens automatically?

Installed Hooks record work and execution. **On the next verification request**,
Click follows this flow:

```text
Requested check  → record its success and execution conditions
Code edit        → record the changed workspace state
Next request     → recheck command, environment, inputs and reuse evidence
                 → run required groups + reuse groups with current evidence
                 → record actual results and reasons
```

Supported automatic input observation can establish evidence without project
JSON. Conditional JS reuse learns and compares inputs in two eligible requested
executions. Automatic sharding needs initial setup and a baseline; when tools
must be installed or policy committed, status explains the next action. Click
does not install tools on its own.

Automation depends on the tool and input profile:

| Capability | Scope |
| --- | --- |
| Record verification | Default Evidence mode under host permissions. |
| Split a suite | Supported unittest, pytest, Vitest and Jest profiles, after setup. |
| Observe Python inputs | Bounded CPython 3.12 and unittest/pytest profiles with platform prerequisites. |
| Conditional JS reuse | Eligible Linux Node 22.23.2 executions; observed inputs are rechecked and incomplete coverage is disclosed. |
| Existing repository policy | Declared reuse policies retain their own checks. Observer can stay off. |

Settings, dynamic imports and ignored files can be tracked in supported profiles.
Worker and dynamic-input limitations remain. [The source-derived support table](docs/architecture/runtime-support.md)
separates execution, splitting and reuse; a language name alone does not guarantee all three.

<details>
<summary>Modes, reuse rules, sharding and Observer recovery</summary>

| Mode | Behavior |
| --- | --- |
| **Evidence — default** | Records work and verification under host permissions, without an additional Click approval step. |
| **Guarded — opt in** | Plan mode with enforcement: stages a readable contract, waits for explicit approval in a later user turn, then blocks mutations outside the approved boundary, binds the promised checks to receipts, and prevents self-approval through turn separation and digests. You notice it only on the day something would have gone wrong. |
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
| Declared file inputs (policy v2) | The committed policy's allowed changes and complete owner-declared file boundary both match the baseline, including ignored inputs. This is owner policy, not automatic dependency discovery. |
| Authoritative input observation | A complete signed input snapshot from supported automatic Evidence capture or an approved Guarded run, with all reuse conditions rechecked. |
| Conditional JS observation | Eligible requested executions establish a separately attested observed-input receipt, then recheck inputs and execution bindings. Reports disclose that input completeness is unproven. |
| Conditional Python observation | A native observation whose only gaps are a followed child process, threads, or dynamic introspection keeps its input snapshot as a conditional receipt. Reuse stays limited to unchanged observed inputs and is disclosed as completeness-unproven. |
| Input identity and environment | Observed inputs are identified by content, type and membership, not timestamps or inodes. Receipts fingerprint interpreter, toolchain, locale, path and proxy variables plus an owner's `.click/environment.json`; other session variables are runtime assumptions. |

For example, if a policy for the exact authentication test command was committed before revision 12 and permits `README.md` changes:

```text
revision 12  authentication code changed → run the check and record a pass
revision 13  only README.md changed       → reuse if policy and bindings still match
revision 14  authentication code changed → run again; the policy does not allow this change
```

An unlisted path, changed policy, ambiguous Git state, changed executable or environment, or later workspace drift requires real execution. The safe-change declaration is repository-owner policy, not automatic dependency discovery.

The optional `.click/evidence-dependencies.json` map, or dependencies in an approved Guarded contract, declares candidate input boundaries. A map alone does not establish observation authority. Approval-bound contract dependencies and concrete manifest paths remain hard dependencies; complete authoritative observation can refine expanding manifest patterns. For this observation-based route, missing or incomplete authority cannot justify reuse after a mutation. See [verification profiles and reuse rules](skills/click/references/verification-profiles.md) and [Authoritative Observer v2](skills/click/references/authoritative-observer-v2.md).

With no dependency policy, supported automatic Evidence capture can establish a
complete input receipt for each check. Changed or uncertain children execute;
unaffected children may reuse. Recorded inputs are rechecked even for identical
Git trees, including ignored data. This is profile-limited, not a claim that all
project inputs or external services can be discovered. Parent splitting still
uses the existing automatic-sharding workflow.

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
4. `refresh` obtains baseline verification for the current revision. Passing children reach `sharding-ready`; an unchanged request can use exact receipts even when Observer is off. Committed-policy and authoritative-observation readiness are reported separately.

Read `status` between steps and follow its next action. Status separates command execution, automatic inventory/split, exact reuse, committed-policy reuse, and authoritative-observation reuse; one ready route does not imply the others are ready. Later discovery changes produce a bounded diff; refresh updates only policy matching Click's previously committed lineage and does not overwrite user-owned or modified policy.

Automatic inventory and exact splitting are locally verified for bounded unittest, pinned Vitest 5, and pinned Jest 30 profiles. The conservative pytest collect-only profile has pinned integration and observation CI coverage; actual eligibility depends on the command and configuration. Vitest and Jest use profile-limited static configuration; unsupported or ambiguous collection retains the parent command. See the [automatic sharding guide](skills/click/references/automatic-sharding-setup.md) and [two-project E2E record](docs/history/auto-sharding/e2e.md).

Support is tracked by tool profile rather than by language name alone:

| Tool/profile | Execution evidence | Automatic inventory/split |
| --- | --- | --- |
| CPython unittest | Verified | Profile-limited |
| pytest | Bounded collect-only profile; pinned integration CI | Profile-limited |
| Vitest 5 / Jest 30 | Verified with pinned fixtures | Profile-limited, exact file children |
| Node test/check, npm test, Go test | Verified | Parent execution only |
| JSON/YAML/Markdown/SVG project validators, jq | Verified fixtures | Parent execution only |
| Cargo, Gradle, .NET, TypeScript, CMake/CTest | Linux CI tool smoke; not full Click reuse integration | None |
| xmllint, ImageMagick identify | Linux CI tool smoke | None |
| Maven, direct SQL linters | Recognized command/runtime profile; no dedicated native CI fixture | None |

A tool smoke is narrower than a Hook-to-runner reuse test. The [.NET smoke](.github/workflows/ci.yml) uses a class library and does not establish test discovery. A recognized profile alone proves neither. Current coverage is assigned in [CI](.github/workflows/ci.yml); earlier phase evidence is in the [multilanguage expansion history](docs/history/multilang-expansion/README.md).

## Can Observer stay off?

**Yes.** New Evidence tasks select automatic capture for supported checks; Guarded defaults to off. Evidence recording, ordinary verification, the dashboard, and qualifying exact-receipt or safe-change reuse work with Observer off. An explicit off selection survives completed Evidence turns in the same session.

Preparation failure reasons and recovery actions appear in `click-gate observer status`, `click-gate status --json`, and the dashboard. These read-only views never grant reuse permission. The [code-derived support matrix](docs/architecture/runtime-support.md) separates execution, splitting, complete observation and conditional JS reuse, with platform prerequisites. A failed preparation retries when relevant capabilities change; explicit `click-gate observer auto` also permits a retry.

```text
click-gate observer status
click-gate observer off
```

Optional modes have different purposes:

- `click-gate observer auto` prepares available local capture and retries after relevant capability changes, without installing tools or asking for privileges. With no owner dependency policy, complete signed inputs can support reuse without writing JSON. Incomplete capture leaves the original check running normally.
- `click-gate observer shadow` collects non-authoritative telemetry on supported Linux, macOS, and Windows backends. Predictions never authorize reuse.
- `click-gate observer authoritative` explicitly prepares capture in active Evidence or an approved Guarded contract. Native profiles cover CPython **3.12.3–3.12.14** with direct `python -m unittest` or supported `python -m pytest` commands. Runtime, platform and input completeness still determine eligibility; enabling the mode grants no reuse.

Output retention and input observation share one execution, including actionable diagnostics. The pytest input profile covers versions 8.4.2 and 9.1.1; cache writes, capture files, timing-sensitive plugins or workers can leave a check ineligible. Click preserves its original options and result. In automatic mode, Node/Vitest/Jest collect file and worker **candidates** with bounded diagnostic attempts; eligible seeds continue learning on requested executions. Raw candidates do not authorize reuse; separately attested conditional receipts can permit reuse without claiming input completeness. See [framework rollout and limits](docs/architecture/automatic-observation.md).

Default `auto` verification also collects Linux Node 22.23.2 clock, random and shared-memory diagnostics, including workers and VM contexts, on the first actual execution of each check. Selected APIs record consumed-value digests; a matching native reader adds per-realm PRNG state and shared-byte samples. These samples do not prove all JavaScript inputs complete. Existing verified receipts and committed repository input policies continue to permit automatic reuse; raw diagnostics alone do not supply JavaScript reuse authority. `observer runtime` explicitly retries collection. See [default collection, conditional reuse and limits](docs/architecture/node-runtime-observation.md).

Linux strace 6.8, macOS privileged `fs_usage`, and Windows inbox ETW profiles have native-host validation records. The automatic-sharding E2E record is Linux-scoped. Click does not install prerequisites or elevate privileges. Incomplete observation preserves the test's actual result, but does not establish future reuse authority. See [platform requirements and validation scope](skills/click/references/authoritative-observer-v2.md).

Automatic preparation respects existing `evidence-reuse.json` owner policy.
Structured diagnostics and bounded failure collection retain output from the
same execution used for native input capture.

On supported Linux Node 22.23.2 profiles, default JavaScript observation can
produce **conditional reuse** receipts without owner JSON. Two eligible, normally
requested executions learn and compare observed inputs; later requests recheck
them. Settings, dynamic imports and ignored files are covered when captured.
Environment changes can rerun multiple children because environment binding is
conservative. Known clock/random/shared-memory inputs and unsupported workers
remain ineligible; collecting diagnostic values does not make them reusable.

A child that already uses conditional observation keeps requiring that evidence
after an edit introduces unsupported worker inputs. It executes until usable
evidence recovers. Removing the worker lets automatic mode retry a previously
started Inspector capture on the next requested execution, without resetting
Click state. A new task alone does not trigger that recovery capture. Unsupported
launchers and diagnostic-only mode retain their collection limits. No extra test
is launched to learn. See [conditional scope and recovery](docs/architecture/node-runtime-observation.md).


</details>

<details>
<summary>Dashboard measurements, receipts, benchmarks and troubleshooting</summary>

## Dashboard: results and measured effect

```text
click-gate dashboard start
click-gate dashboard status
click-gate dashboard stop
```

Open the local URL reported by the control. The first screen separates command, auto-inventory, exact-reuse, committed-policy, and observation readiness and shows the next action. It also shows the current task, verification-group states, reuse reasons, and work history. Each completed group is persisted while later groups run. A viewer can remain connected across successive Evidence tasks in the same host session and workspace.

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

`click-gate status` prints a short read-only summary: executed and reused counts with the estimated avoided time, the mode and mutation revision, and the next action, in the dashboard language selected by `CLICK_LANGUAGE` or the POSIX locale (Korean by default). `click-gate status --json` returns the full report of checks that ran, were reused, did not run, or remain unrequested, including invalidation after mutations, per-check reason codes, and actionable failure details. Both report registered evidence, not whole-task correctness, and neither grants reuse.

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

On Claude Code, `claude plugin list` shows the installed plugin and `/hooks` lists the `[plugin:click]` Hook definitions; `claude plugin validate ./dist/claude --strict` checks a source build. The Hook command runs `python3`, so confirm `python3 --version` works in the shell Claude Code uses. Hook output and errors appear in the transcript as `click hook error` lines.

## Antigravity

An experimental Google Antigravity adapter is available from the source checkout:

```sh
agy plugin install ./dist/antigravity
```

It uses the host's available Hook surface for Evidence and Guarded workflows. Unsupported coverage is not reported as independent observation. See the [Antigravity adapter guide](platforms/antigravity/README.md).


</details>

## Limits and technical reference

Click does not prove that the code is correct or that the selected tests are sufficient.

Click is a workflow guardrail, not an operating-system sandbox. It cannot prove hidden reasoning, semantic correctness, test sufficiency, or external activity outside matched Hooks. Manual or hosted evidence without independent observation remains an attestation. Keep normal code review, CI, branch protection, and deployment controls.

Protocol details and implementation boundaries:

- [Product Constitution](PRODUCT_CONSTITUTION.md) and [guard classification](GUARD_CLASSIFICATION.md)
- [Operating modes](skills/click/references/modes.md), [Guarded workflow](skills/click/references/guarded-mode.md), and [Guarded contract format](skills/click/references/directive-format.md)
- [Verification profiles](skills/click/references/verification-profiles.md) and [capability protocol](skills/click/references/capability-protocol.md)
- [Automatic sharding setup](skills/click/references/automatic-sharding-setup.md) and [Evidence Shards v1](skills/click/references/evidence-shards-v1.md)
- [Authoritative Observer v2](skills/click/references/authoritative-observer-v2.md), [Shadow Observer v1](skills/click/references/observer-v1.md), and [Shadow Intelligence v1](skills/click/references/shadow-intelligence-v1.md)
- [Documentation map](docs/README.md), [verification efficiency](skills/click/references/verification-efficiency.md), [anti-loop policy](skills/click/references/anti-loop-policy.md), and [runtime architecture and optimization](docs/architecture/runtime-optimization.md)
- [Verification lifecycle modules](docs/architecture/verification-lifecycle.md): preparation, one-use claims, execution and result recording behind the existing API.

## License

[MIT](LICENSE)
