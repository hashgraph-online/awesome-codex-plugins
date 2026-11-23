# Promote PR merge wait

A staging→main promote PR that waits for the operator merge (the `/git-prod` PR path, a factory wrapper such as `/kit-prod`, the `/run-plan-all` ship lane) uses one bounded wait. GitHub can refuse a merge for a ruleset reason while it reports `MERGEABLE`/`CLEAN` and every check is green, so an open-ended wait can run forever.

## Ruleset preflight

Before the promote PR (or the local merge into `main`), run `agent-kit promote rules --base main`. It reads `gh api repos/<owner>/<repo>/rules/branches/main` and prints one `ruleset advisory` line per rule parameter the kit has no model for, by name (for example `pull_request.require_extra_approval_for_unattributed_changes = true`), and any rule type it does not model. Missing `gh`, no auth, offline or an API error prints one `skipped` note. It is advisory: it always exits 0 and never blocks the promote. Copy any advisory line into the summary before the merge.

## Wait

Run `agent-kit promote wait --pr <N>` (add `--repo <owner/name>` outside the checkout's repo). It is read-only: it polls `gh pr view <N>` with backoff from 30 s up to 5 min and stops at the cap, `promoteMergeWaitMs` in `.cursor/context/config.json` (default 3600000, 60 min; range 1 min to 24 h). `--cap-minutes <n>` overrides the cap for one run.

| Exit | Meaning | Next |
|------|---------|------|
| `0` | Merged | Continue the promote routine (tag, staging sync, verification) |
| `1` | Closed without a merge | Stop. Do not tag, do not reopen the PR. Report |
| `3` | Cap reached | Ask `promote-merge-wait` (below) |

Never hand-roll an unbounded `gh pr view` loop. On a CLI without `promote wait`, poll `gh pr view <N> --json state` with the same backoff and cap.

## GitLab origin

`agent-kit promote rules` and `agent-kit promote wait` are GitHub-only (they call `gh`); a forge-aware CLI is not shipped. On a GitLab origin:

- Create the staging→main MR with `squash=false` and `remove_source_branch=false`. GitLab project defaults (squash on, delete source branch on) break a promote: a squash drops the staging history from `main`, and a deleted `staging` breaks the staging sync. Set both on the MR explicitly, for example `glab api --method POST projects/:id/merge_requests -f source_branch=staging -f target_branch=main -f title="<title>" -F squash=false -F remove_source_branch=false`.
- Skip the ruleset preflight (no GitLab model); note `promote rules: skipped (GitLab)` in the summary.
- Wait with a bounded MR-state poll: read `state` from `glab api projects/:id/merge_requests/<iid>` with the same backoff (30 s up to 5 min) and the same `promoteMergeWaitMs` cap. `merged` = exit `0` row, `closed` = exit `1` row, cap reached = exit `3` row (the Ask below). For `Show the merge box reason`, print the MR's `detailed_merge_status` and `has_conflicts` instead of the `gh` fields.

## Ask `promote-merge-wait`

Labels, in order: `Keep waiting` / `Show the merge box reason` / `Stop and hand off`. Numbered fallback and `HITL_GATE:` sentinel: [SKILL.md](./SKILL.md).

- `Keep waiting`: run the same command once more (one more cap window), then this Ask again on exit 3.
- `Show the merge box reason`: print `gh pr view <N> --json mergeStateStatus,mergeable,reviewDecision` and `agent-kit promote rules --base main`, and ask the operator for the merge box text on the PR page. `CLEAN` plus green checks is not proof GitHub accepts the merge; the API does not name the ruleset rule that refuses it. Then Ask again.
- `Stop and hand off`: write HANDOFF `Mode: STOPPED: awaiting operator merge of PR #<N>` with the last merge state, and stop. A `/run-plan-all` queue holds its cursor.

Never merge the PR yourself, never bypass or edit a ruleset, never run `/git-prod` from this Ask. In `/run-plan-all` this Ask is the expired-wait point; it is not a red stop and does not start the next plan.
