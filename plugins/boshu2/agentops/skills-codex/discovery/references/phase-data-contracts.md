# Phase Data Contracts

How each consolidated phase passes data to the next. Artifacts are
filesystem-based; no in-memory coupling between phases.

| Transition | Output | Extraction | Input to Next |
|------------|--------|------------|---------------|
| -> Discovery | Goal string + repo execution profile contract | Goal from the `$rpi` invocation; repo policy from `docs/contracts/repo-execution-profile.md`, `repo-execution-profile.schema.json`, and `repo-execution-profile.json` when present | `repo_profile` state is loaded before research/planning begins, including validation lane mutation metadata |
| Discovery -> Implementation | Dense execution packet + discovery summary | `.agents/rpi/phase-1-summary-*.md` + `.agents/rpi/execution-packet.json` (latest alias) or `.agents/rpi/runs/<run-id>/execution-packet.json` (run archive). Child outputs cross only as artifact paths. | `$crank <epic-id>` when `epic_id` exists; otherwise `$crank .agents/rpi/execution-packet.json` with density fields, repo policy, criteria, validation bundle, and `validation_lanes` already normalized |
| Implementation -> Validation | Completed/partial crank status + implementation summary + `execution_packet` | `bd children <epic-id>` or file-backed implementation state + `.agents/rpi/phase-2-summary.md` + `.agents/rpi/execution-packet.json` (latest alias) or `.agents/rpi/runs/<run-id>/execution-packet.json` (run archive) | `$validation <epic-id>` when `epic_id` exists; otherwise standalone `$validation` with the same repo execution profile fields, validation lanes, and done criteria |
| Validation -> Next Cycle (optional) | Vibe/post-mortem verdicts + harvested follow-up work + queue lifecycle fields (`claim_status`, `claimed_by`, `claimed_at`, `consumed`, `failed_at`) | Latest council reports + `.agents/rpi/next-work.jsonl` | Stop, loop (`--loop`), suggest next `$rpi` (`--spawn-next`), or hand work back to `$evolve` |

Execution packet v1 should remain additive. Recommended fields:

- `schema_version`
- `run_id`
- `objective`
- `density.intent`
- `density.boundary`
- `density.evidence`
- `density.decision`
- `density.constraint`
- `density.next_action`
- `artifacts.research_path`
- `artifacts.plan_path`
- `artifacts.pre_mortem_path`
- `epic_id` (optional when the tracker cannot mint an epic)
- `plan_path`
- `contract_surfaces`
- `validation_commands`
- `validation_lanes` (repo profile lane metadata: `read_only`,
  `writes_artifacts`, `isolated_agents_home`, `release_only`,
  `mutation_escape_hatch`)
- `tracker_mode`
- `tracker_health`
- `done_criteria`
- `pre_mortem_verdict`
- `test_levels`
- `ranked_packet_path`

Execution packet retention rule:

- `.agents/rpi/execution-packet.json` is the mutable latest alias for the
  current objective
- `.agents/rpi/runs/<run-id>/execution-packet.json` is the durable per-run
  packet archive when `run_id` exists

Validation lane selection rule:

- implementation and fast closeout phases prefer lanes where `read_only=true`,
  `writes_artifacts=false`, `release_only=false`, `cost_class` is `cheap` or
  `standard`, and `auto_select` is `default` or matches the changed surface
- lanes with `cost_class=expensive`, `auto_select=explicit`, or
  `auto_select=release-only` require an explicit operator request, a named plan
  acceptance criterion, or a release-readiness objective
- every selected lane should honor `timeout_seconds`; when a lane times out,
  record `[TIME-BOXED]` and continue with narrower evidence unless it was the
  only code-surface proof
- lanes with `isolated_agents_home=true` require isolated agent state before
  execution
- lanes with `writes_artifacts=true` or `release_only=true` are release/audit
  lanes; run them only when the packet objective or operator explicitly asks
  for release readiness
- lanes with a non-null `mutation_escape_hatch` require the escape hatch name
  in the validation report or handoff
- unclassified commands containing `go test -race`, `-shuffle`, `-count=N`
  where `N > 1`, eval runners, retrieval bench, headless runtime smoke, or
  release gates are explicit-only

Queue lifecycle rule:

- post-mortem writes new entries as available: entry aggregate
  `consumed=false`, `claim_status="available"`
- consumers treat item lifecycle as authoritative inside `items[]`; omitted
  item `claim_status` means available
- `$evolve` and `$rpi loop` claim an item before starting a cycle: item
  `claim_status="in_progress"`
- successful `$rpi` + regression gate finalizes that item claim: item
  `consumed=true`, `claim_status="consumed"`, `consumed_by`, `consumed_at`
- failed or regressed cycles release the claim back to available state and may
  stamp item `failed_at` for retry ordering
- consumers may rewrite existing queue lines to claim, release, fail, or
  consume items after initial write
- the entry aggregate flips to `consumed=true` only after every child item is
  consumed

Canonical schema contract: [`docs/contracts/next-work.schema.md`](../../../docs/contracts/next-work.schema.md) (v1.4)

## Rollback Discipline

When changing phase-boundary logic, ship phase-3 closeout updates FIRST and
remove phase-2 handoff logic SECOND. This keeps a working closeout path in
place during the transition window.
