# Automatic sharding setup

Click exposes one JSON-free setup surface for supported unittest, pytest, Vitest 5, and Jest 30 profiles:

```text
click-gate sharding init
click-gate sharding init -- python3 -m unittest discover -s tests -q
click-gate sharding init -- python3 -m pytest -q tests
click-gate sharding init -- npx --no-install vitest run
click-gate sharding init -- npx --no-install jest --runInBand
click-gate sharding status
click-gate sharding refresh
```

Installation and `init` without a command only inspect safe repository metadata.
They do not import project code, collect tests, create policy, or run a test.
Collection and proposal generation require an active Evidence runtime or a
separately approved Guarded contract. The exact argv after `--` is preserved as
the parent command.

Automatic collection uses a common shell-free, bounded process supervisor on
Linux, macOS, and Windows and accepts CPython 3.10 through 3.14. The unittest
adapter accepts bounded `discover` arguments. The pytest adapter accepts a
deliberately narrow `python -m pytest`, version-qualified `python3.x -m pytest`,
or Windows `py -3.x -m pytest` form,
one project directory, built-in discovery patterns, and a bounded set of
selection/reporting options. It runs `--collect-only` twice, disables ambient
plugin autoload, and binds the recorded proposal to the interpreter and
framework version. Missing pytest, custom discovery patterns, required external
plugins, unstable IDs, fixture ambiguity, or unsupported options leave the
parent command unchanged. Vitest and Jest require pinned, locally installed
runners and limited static configuration. They collect machine-readable file
inventories and generate exact file children; custom workspaces/projects,
dynamic configuration, watch/update modes, and ambiguous selection preserve
the parent command.

## Runtime ownership and public boundaries

The automatic setup path keeps collection, proposal state, policy resolution,
execution, and presentation separate. Maintainers should use these public
module boundaries instead of reaching into another module's underscored
helpers:

| Responsibility | Public boundary |
| --- | --- |
| Platform capability and bounded child processes | `click_collector_runtime.capability`, `cpython_supported`, and `supervise` |
| Command parsing, workspace snapshots, collection, and analysis | `click_test_inventory.parse_command`, `workspace_snapshot`, `run_bounded_command`, `collect_once`, and `analyze` |
| Candidate policy construction | `click_shard_proposal.propose` |
| Setup state machine and reviewed policy lifecycle | `click_sharding_setup.selection_report`, `status`, `plan`, `generate`, `apply`, and `bootstrap` |
| Committed policy resolution and child execution metadata | `click_evidence_shards.resolve_plan`, `resolve_active_plan`, `running_plan_error`, `source_metadata`, and `shard_set_for_plan` |
| Dependency manifest identity | `click_dependency_cache.manifest_group_digest` |
| Observer availability by assurance tier | `click_observer_backend.select_backend` and `support_report` |
| Incremental result state and display projections | `click_incremental` public state functions and `progress_projection`; `click_dashboard_projection.dashboard_projection` |

The setup controller owns persisted setup state. The committed policy modules
remain the execution authority, and display projections remain read-only. A
proposal receives one checked workspace snapshot; parent and child analysis
reuse it as their initial baseline and still perform the later mutation checks.
The report records both the scans performed and the initial scans avoided, so
the optimization does not become an unmeasured correctness shortcut.

## State transitions

The supported flow is:

```text
selection-required
  -> whole-suite-preferred
  or
  -> application-ready (Evidence) / approval-required (Guarded)
  -> commit-required
  -> baseline-required
  -> sharding-ready (exact reuse available for unchanged bindings)
  -> reuse-ready (complete authoritative observation also available)
```

The first authorized `init -- ...` performs bounded collection and stores a
review artifact outside the repository. Its report includes the exact proposed
files, previews, digests, scope, cost decision, and constraints. It is candidate
data only. Evidence applies it only on a later explicit `refresh`. Guarded keeps
the separate approval contract described below.

The initial cost rule measures the parent once. When that run is below 250 ms,
Click selects `whole-suite-preferred` and skips child and startup probes. For a
longer parent it measures one isolated interpreter startup and each proposed
child. Reusable siblings must clear both 100 ms and startup plus a 25 ms reserve.
The selected child's measured duration plus reserve must also be cheaper than
the parent by at least 100 ms. The estimate assumes one worst-duration shard changes and
is labeled as setup measurement, not savings. The three thresholds can be
tuned with `CLICK_SHARDING_MIN_PARENT_MS`,
`CLICK_SHARDING_MIN_AVOIDABLE_MS`, and
`CLICK_SHARDING_MANAGEMENT_RESERVE_MS`; their effective values are recorded in
status and a change causes reevaluation. Probe payback is separate from total
setup cost; it never proves a saving. Setup execution defaults to 1,800 seconds
(maximum 7,200), independently of collection, via
`CLICK_SHARDING_EXECUTION_TIMEOUT_SECONDS`.

Collection remains bounded at 50,000 workspace files, 128 MiB of snapshot input,
2,048 discovered modules, 64 generated shards, and a 16 MiB persisted review
artifact. Proposal status records parent and per-child analysis wall time, file
record count, and snapshot scan count. Child analysis reuses the already checked
proposal snapshot as its initial baseline, avoiding one full workspace scan per
child while retaining the post-collection mutation checks. Vitest/Jest group
at most 48 exact files per child and preserve unaffected file ownership during
refresh. Other adapters retain their existing grouping limits.

In Evidence mode, the next explicit `refresh` applies a proposal produced in
Evidence mode. Applying it in Guarded requires a fresh approved contract whose human-readable
promises contain the reported proposal digest. That contract must declare one
argv evidence source named `E_AUTO_SHARDING_BASELINE` for the selected parent
command. `sharding refresh` then creates only these absent files:

```text
.click/evidence-shards.json
.click/evidence-dependencies.json
```

For an initial setup Click creates only absent files. For a refresh it replaces
only policy bytes whose current digest exactly matches the prior committed
Click-generated artifact. It never replaces user-owned or modified policy,
stages it, commits it, pushes it, or modifies the Git index. The report remains
`commit-required` until the worktree, index, and `HEAD` copies all equal the
reviewed bytes. The user owns that exact Git action.

After the commit, the next authorized `refresh` collects the parent and every
generated child again, compares their inventories, and runs the parent.
Guarded additionally runs the children for its approved bootstrap comparison.
Evidence leaves the children explicitly baseline-pending so the following
runner executes them once. A mismatch or failure is not ready. Bootstrap is
setup cost, never saved time. The next `refresh` sends the declared parent evidence
through the ordinary Click verification runner. The committed shard map may
expand it into children, but all usual runner, receipt, and fallback checks
still apply.

A source-only commit with unchanged policy, discovery and runtime does not
repeat bootstrap. Its current child results still require ordinary verification.
See [verification economics](../../../docs/architecture/verification-economics.md)
for the six-stage implementation, input policy and measurement limits.

A successful baseline reports `sharding-ready` and makes same-revision exact
receipts available for unchanged bindings. Status reports exact,
owner-committed safe-change, and authoritative-observation routes separately.
With explicitly enabled [Authoritative Observer v2](authoritative-observer-v2.md),
every child must produce a complete, current, runner-signed observation before
setup reports observation-backed `reuse-ready`. Observer can remain off for
exact or committed-policy reuse. Shadow data, caller JSON, the setup artifact,
and the dashboard never create authority.

## Refresh and recovery

`init`, `status`, and `refresh` are resumable. State and proposal artifacts use
owner-only storage outside the project, atomic replacement, content digests,
and a nonblocking per-project lock. A partial application may leave only an
exact reviewed file; a later authorized refresh can resume without overwriting
a different file. Existing user configuration always returns for review.

Added, deleted, or renamed discovered files; added or removed test methods; a
changed parent command; a different runner; changed discovery conditions; or a
changed cost rule cause `review-required`. Ordinary source-content and test-body
edits do not regenerate the shard layout. Changed policy bytes are reported
separately and are never adopted as generated lineage. Verification never edits
policy. If a committed plan is absent, malformed, locally edited, incomplete, racing,
or awaiting refresh, ordinary verification uses the authorized parent command
instead of treating a candidate plan as active.

Generated refresh artifacts include bounded unified diffs against the prior
committed generated bytes. Application is resumable per file: a retry accepts
either the exact prior digest or the exact proposed bytes, so interruption after
one file does not require overwriting unrelated changes. Any third value stops
the update for review.

Dependency declarations remain scoped to their exact commands during refresh.
Every child inherits an explicit declaration for its parent, retains its own
previous declaration, and receives its collected transitive/configuration
candidates. Another child's or another suite's declaration is preserved in the
manifest without being added to unrelated children. Existing owner inputs are
never silently removed. Candidate imports alone do not authorize a skipped
test; ordinary complete observation or committed safe-change checks still do.

For the bounded Vitest/Jest profiles, layout status binds selected files and
runner configuration. Editing a test body or adding a case within an existing
file invalidates execution evidence without recollecting the file layout in
`status`. Added, removed or renamed files still require refresh. Python
test-case discovery structure remains separately checked. A valid committed
refresh can retain compatible child evidence as stale candidates, as described
in [child continuity](evidence-shards-v1.md#child-continuity-across-a-reviewed-refresh).

The dashboard keeps its existing result-first order. Its detail panel shows
initial setup, observer cost when measurable, Click processing, parent and
sequential-child bootstrap durations, and the signed parent-minus-children
comparison. A negative comparison remains visible. Request wall time and
separate paired measurements retain their own scopes; Click does not present
the bootstrap comparison as total wait savings.

## Successor validation

For partial reuse after setup, keep both tasks in Guarded mode. Complete the
baseline contract A, then stage a new contract B and obtain approval in a later
turn. Click carries only completed child facts as candidates. B receives no
approval, runner token, unfinished work, or completion state from A. After an
approved code change, submit the original parent request with `sharding
refresh`; the committed map expands it and the ordinary successor checks decide
each child independently. Related inputs run, while only children with current
complete observations may reuse.

The primary efficiency value is the prior compatible child-command time for
children that were actually reused. It excludes setup and management cost.
Request wall time, measured processing segments, same-final-code parent audits,
test-count reuse, shard reuse, and signed net comparison keep separate labels
and scopes. Very short suites can have a negative net result even when partial
reuse is correct; Click preserves that result and makes no universal speedup
claim.
