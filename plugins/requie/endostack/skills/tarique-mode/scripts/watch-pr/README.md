# watch-pr

`watch-pr` polls GitHub for one pull request, a connected stack of PRs, or a frozen merge-queue list, and exits as soon as the outcome is known. Each outcome has its own exit code, so you act on the code instead of polling by hand. The watcher only reads: it never merges, comments, resolves threads, or marks a PR ready.

It needs Node.js 22 or newer, an authenticated `gh` CLI, and `git` (to read the `origin` remote). It has no package dependencies. Only `github.com` remotes and PR URLs are accepted. On any other forge, use that forge's own commands.

## Usage

```
watch-pr [options]
```

| flag | meaning | default |
|---|---|---|
| `--owner <owner>` | repository owner | from `origin`, else `gh pr view` |
| `--repo <repo>` | repository name | from `origin`, else `gh pr view` |
| `--pr <n>` | PR number; `#12` is accepted | the current branch's PR |
| `--stack` | watch the open stack connected to the PR | off |
| `--queued-stack` | watch a captured stack until every PR merges | off |
| `--stack-prs <n,...>` | PR numbers for queued mode, lowest first, fixed for the whole run; `#` and spaces allowed | discovered once from `--pr` |
| `--interval <s>` | seconds between polls, > 0, fractions allowed | 60 |
| `--sweep-interval <s>` | seconds between whole-stack reads in queued mode, > 0 | 300 |
| `--timeout <s>` | overall deadline, >= 0; 0 means no deadline | 0 |
| `--max-query-errors <n>` | consecutive read failures allowed before giving up | 5 |
| `--status-only` | print one STATUS snapshot and exit 0 | off |
| `--allow-draft` | do not treat draft status as a merge gate | off |
| `--review-bot <login>` | account whose threads are review-bot threads; repeatable | none |
| `--approval-check <name>` | check name that waits on a human approval; repeatable | none |
| `--config <file>` | JSON config file | `.endostack/watch-pr.json` if it exists |
| `--pretty` | human-readable text instead of JSON | off |
| `-h`, `--help` | print help and exit 0 without calling GitHub | |

Usage errors print `error: ...` to stderr, print nothing to stdout, and exit 64. These include an unknown flag, an out-of-range number, `--stack` together with `--queued-stack`, `--stack-prs` without `--queued-stack`, a PR listed twice, and an empty list entry.

## Exit codes

| code | meaning |
|---|---|
| 0 | ready to merge (single or stack), every queued PR merged, or `--status-only` |
| 2 | merge conflicts |
| 3 | unresolved review threads |
| 4 | failing checks, including GitHub refusing the merge for a failed head commit that the checks list does not show |
| 5 | deadline passed |
| 6 | merge gate: closed without merge, draft, changes requested, or an approval check still open |
| 7 | GitHub could not be read within the error budget, or the context could not be resolved |
| 64 | usage error |

## Configuration

Review-bot identity and approval checks are configuration, because they differ per repository. A config file is a JSON object with these optional keys:

```json
{
  "reviewBots": ["my-review-bot"],
  "reviewBotHosts": ["github-actions[bot]"],
  "reviewBotMarkers": ["<!-- review-pass -->"],
  "approvalChecks": ["Owner approval"],
  "reviewCheckMarkers": ["security-review"],
  "passIdPattern": "(?:run|automation)[-_ ]?id\\s*[:=]\\s*([A-Za-z0-9._-]+)"
}
```

- `reviewBots`: a thread is a review-bot thread when its first comment's author login contains one of these names (case-insensitive). `--review-bot` adds to this list.
- `reviewBotHosts` and `reviewBotMarkers`: for bots that post through a shared account. A thread from a host account counts as a bot thread only when its body contains one of the markers.
- `passIdPattern`: regular expression whose first capture group identifies one review pass. The watcher counts distinct IDs across every thread on every page. When bot threads exist but none carries an ID, the count is 1. With no bot configured, the count is 0.
- `approvalChecks`: a check with one of these exact names, while pending or action-required, is reported as a merge gate (exit 6) instead of pending or failed, so the watcher does not wait forever on a human approval. There is no default. `--approval-check` adds to this list.
- `reviewCheckMarkers`: a pending check whose name contains one of these (or a `reviewBots` name) sets `reviewAutomationRunning` on the row.

Unknown keys and malformed values are usage errors.

## What it reads

For each PR it runs `gh pr view` for state, mergeability, review decision, and draft flag. Merged and closed PRs stop there. For open PRs it then reads:

1. Unresolved review threads through GraphQL, 100 per page, until the cursor ends. A page with no `pageInfo` is an error, never treated as the last page.
2. Checks through `gh pr checks --json`. If that is unusable (exit other than 0, 1, or 8, empty output, not a JSON array) or returns an empty list, it reads the head commit's status-check rollup through GraphQL. If both are empty the read fails with `checks-unavailable`. Unknown terminal states map to failed.
3. The last 50 commits' rollup states. GitHub refuses the merge when the merge state is `BLOCKED` and the head rollup is `FAILURE` or `ERROR`. The watcher also records whether an earlier commit was green. In queued mode, a PR with pending checks and no failures skips this query.

Blockers are checked in tier order: conflicts, unresolved threads, failing checks, merge gates. Across a stack the scan is tier-major: a conflict on any PR outranks a CI failure on any other. A draft PR with pending checks waits for them to settle before the draft gate is reported.

## Output

Every line is one JSON object (NDJSON while polling). All objects share:

```
{ "schema": 1, "seq": <n>, "at": "<ISO time>", "mode": "single|stack|queued", "kind": "<KIND>", "terminal": <bool>, "exitCode": <n, terminal only>, ... }
```

| kind | terminal | body fields |
|---|---|---|
| `STATUS` | only with `--status-only` | `rows`: per PR `pr`, `url`, `status`, `ci` (`state`, `pending`, `failed`, `approvalChecks`, `githubRefuses`, `headRollup`, `wasGreenBefore`), `threads`, `botPasses`, `reviewAutomationRunning`, `reviewDecision`, `draft`, `merge` |
| `WAITING` | no | `reason` (`checks` or, in queued mode, `merge-queue`), `pr`, and `pending` or `unmerged` |
| `READY` | yes (0) | `prs`: one proof per PR (mergeability, zero threads, clean CI with GitHub allowing, `OPEN`, review decision, and `draft` set to `ready-for-review`, or `draft-permitted` when `--allow-draft` let a draft through), or `{ pr, merged: true }` |
| `BLOCKER` | yes (2, 3, 4, 6, 7) | `blocker` (`conflict`, `threads`, `checks`, `gate`, `status-query`), `pr`, kind-specific detail (threads with `id`, `path`, `line`, `author`, `bot`, `botPasses`, `body`; failed checks with `name`, `state`, `description`, `link`; GitHub refusal; gate `reason`; query `error` and `failures`), and `action` |
| `QUEUE` | no | `prs`: the captured bottom-to-top list |
| `ADVANCE` | no | `merged`, `frontier`, `remaining` |
| `RETRY` | no | `error` (`kind`, `detail`, `retryable`, `raw` when an unknown enum value was seen), `failures`, `backoffSeconds` |
| `COMPLETE` | yes (0) | `merged` |
| `TIMEOUT` | yes (5) | `reason` (`deadline` or `status-unavailable`), `pr`, and `pending` or `unmerged` |

`--pretty` renders the same objects as text. STATUS becomes a Markdown table with the columns PR, Checks, Threads, and Mergeability. BLOCKER becomes a headline, `key=value` lines, one line per thread or failed check (bodies cut to their first line, 180 characters), and an `action=` line. The other kinds are one line each.

## Modes

- Single (default): poll the PR. A blocker or READY ends the run. Pending checks emit WAITING and sleep one interval.
- Stack (`--stack`): rediscover the stack each poll from open PRs (a PR's parent is the same-repository PR whose head is its base; fork PRs are never parents and never have children attached), emit a non-terminal STATUS, then decide tier-major. WAITING names the first PR with pending checks and lists that PR's own checks.
- Queued stack (`--queued-stack`): emit QUEUE, then sweep every unmerged PR at start and every `--sweep-interval` seconds, polling only the lowest unmerged PR in between. A failed read resumes at the same PR. Any blocker on an unmerged PR ends the run. When the lowest unmerged PR changes, ADVANCE is emitted and the next read happens without sleeping. Pending checks above a blocker-free frontier do not hold it up; the watcher reports WAITING with reason `merge-queue`. Identical consecutive waits are printed once. Queued mode never emits READY.

## Retries and deadline

A read failure (non-zero `gh` exit, bad JSON, missing or unknown field, checks unavailable) increments a counter that any successful poll resets. When the counter reaches `--max-query-errors`, or the failure cannot be retried (`gh` returned a PR URL outside `github.com`), the run ends with a `status-query` BLOCKER, exit 7. Otherwise it emits RETRY and waits before the next read. The first wait equals the poll interval, raised to 60 seconds if the interval is shorter. Each further consecutive failure doubles the wait, up to a ceiling of 300 seconds.

With `--timeout`, every sleep is capped at the time left, and the deadline is checked after each waiting poll and each retry.

## Layout

| file | role |
|---|---|
| `watch-pr` | POSIX launcher; follows symlinks, runs `watch-pr.mjs` with Node |
| `lib/args.mjs` | flag parsing and help text |
| `lib/config.mjs` | config file loading and validation |
| `lib/exec.mjs`, `lib/github.mjs` | process runner and the `gh`/`git` calls |
| `lib/context.mjs` | owner, repo, and PR resolution; stack discovery |
| `lib/snapshot.mjs` | reading one PR: fields, threads, checks, merge assessment |
| `lib/proof.mjs` | checked constructors for merge assessments, CI results, and ready proofs; exit codes |
| `lib/classify.mjs` | tier order and stack decisions |
| `lib/verdicts.mjs`, `lib/render.mjs` | verdict objects and `--pretty` text |
| `lib/watch.mjs` | the polling loop for all three modes |

`lib/proof.mjs` stands in for type-level guarantees: a refusal cannot be built without a failing head rollup, clean CI cannot carry a refusal, READY cannot carry a blocker exit code, and a ready verdict cannot be built without every proof field. Each violation throws when the value is made.

## Tests

`node --test skills/tarique-mode/scripts/` runs the whole suite. The watcher's tests in `test/` drive the loop with a fake reader and a fake clock and never touch the network.
