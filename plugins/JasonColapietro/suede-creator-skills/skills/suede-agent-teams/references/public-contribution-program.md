# Public Contribution Program

Use this mode to turn a stream of repository issues into small, verified
contribution packets without duplicate work or unapproved publication.

## Contents

1. Operating contract
2. State machine
3. Discovery and scoring
4. Ledger and leases
5. Repository preparation
6. Build and review loop
7. Outward artifact contract
8. Authority matrix
9. Contribution packet
10. Learning loop

## Operating contract

Collect these fields before opening a builder lane:

| Field | Required value |
|---|---|
| Objective | One issue or maintenance outcome with observable acceptance criteria |
| Target | Exact repository, remote, base ref, and local checkout/worktree |
| Ownership | `owned` or `external`; unknown is `external` |
| Authority | `local_only` by default; push, draft PR, ready PR, and merge are separate grants |
| Rules | Nearest `AGENTS.md`, `CONTRIBUTING.md`, security policy, PR template, DCO/CLA, and disclosure policy |
| Scope | Allowed files plus explicit no-touch paths |
| Proof | Repo-native tests, build, lint, review, and remote checks required for closure |

Ownership is never inferred from a local clone, login, organization
membership, or write-capable token. Use an explicit user statement or a
maintained allowlist. External publication through ready review requires
`reviewed` mode plus a separate, one-shot grant for every remote action. The
ledger never merges external work.

## State machine

```text
discover -> classify -> contract -> prepare -> claim -> build -> verify
  -> independent review -> package -> authority gate

owned + authorized -> publish -> checks -> merge or fix
owned + local_only -> packet_ready
external or uncertain -> packet_ready -> owner review
external + reviewed-mode grants -> push -> draft PR -> ready PR -> checks
```

Use the team orchestrator's status vocabulary for the implementation lane.
Use `queued`, `claimed`, `changed_locally`, `verified_locally`, `reviewed`,
`packet_ready`, `published`, `merged`, `closed`, `blocked`, and `superseded`
inside the ledger.

Failed verification or review returns to `changed_locally`. Allow at most three
genuinely different fix strategies for one root cause. A duplicate or already
landed change becomes `superseded`; do not force every task to ship.

## Discovery and scoring

Scout read-only first. Prefer tasks with:

- a reproducible issue and clear maintainer intent;
- a narrow blast radius and executable acceptance criteria;
- an existing test surface;
- no active overlapping PR or recent equivalent commit;
- high user value relative to review and maintenance cost.

Score each candidate from 1 to 5 for impact, confidence, effort, and risk. The
ledger calculates:

```text
score = impact*4 + confidence*3 - effort*2 - risk*3 + owned_bonus(8)
```

The owned bonus makes controlled repositories the throughput lane. It does not
turn a low-value task into a good contribution. Keep at most one active
external task per target repository until the workflow has a proven acceptance
record there.

## Ledger and leases

Use `scripts/contribution-ledger.mjs` for the shared task queue. Store the
ledger outside the target repository unless the project explicitly tracks
operations state. Do not put secrets, tokens, private paths, or copied issue
threads in it.

Initialize with publication disabled:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs init \
  --ledger <control-dir>/contributions.json \
  --publish-mode disabled
```

Add and rank a task:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs add \
  --ledger <control-dir>/contributions.json \
  --repo owner/repo --ref 123 --title "Handle empty metadata" \
  --scope owned --ownership-evidence "Owner named this repository" \
  --disclosure not-required \
  --disclosure-source "Checked CONTRIBUTING.md and the PR template" \
  --impact 4 --confidence 4 --effort 2 --risk 2

node skills/suede-agent-teams/scripts/contribution-ledger.mjs next \
  --ledger <control-dir>/contributions.json
```

Issue references such as `123`, `#123`, `Issue #123`, and the matching GitHub
issue URL normalize to one key. A URL for another repository is rejected.

Claim before creating a worktree. The atomic lease is the duplicate-work gate:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs claim \
  --ledger <control-dir>/contributions.json \
  --id <task-id> --worker <lane-id> --lease-minutes 45
```

Heartbeat long-running work. Release a task when abandoning it. Expired leases
return to the queue automatically. Never remove a live lock file; inspect the
recorded host, token, PID, and process start first. A crashed writer can be
recovered only with the explicit `recover-lock` command, the exact recorded
token, a locally verifiable dead process, and the minimum stale age. There is
no force option. Symlink paths resolve to the same canonical ledger and lock.
Hard-linked ledgers fail closed because multiple names can split an atomic
rename into divergent queues.

Advance only after evidence exists:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs transition \
  --ledger <control-dir>/contributions.json \
  --id <task-id> --worker <lane-id> --to verified_locally
```

Before `packet_ready`, record task-bound checks for the exact branch name,
commit message, and PR draft. Each check stores its content hash. Unknown
disclosure blocks packaging. A required disclosure must occur exactly once in
the PR draft; the exact statement is preserved while other markers are still
checked, and a hash-bound owner approval is required before packaging. The
generic shape gate also requires a valid Git branch ref, a conventional commit
subject, and nonempty `Summary`, `Why`, `Testing`, `Scope`, and `Risks` PR
sections. Apply any stricter upstream template rules in addition to these
minimums.

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs artifact-check \
  --ledger <control-dir>/contributions.json --id <task-id> \
  --worker <lane-id> --kind commit --input <commit-message.txt>

node skills/suede-agent-teams/scripts/contribution-ledger.mjs review-artifact \
  --ledger <control-dir>/contributions.json --id <task-id> --kind pr \
  --sha256 <checked-hash> --decision approve --actor <owner> \
  --review-note "Required statement is present exactly once"
```

The ledger-wide publish mode is only a kill switch. `owned` permits separately
granted publication for owned repositories. `reviewed` also permits an
external task to advance through push, draft PR, and ready PR after each action
receives its own one-shot grant. Enabling either mode requires a named actor and
note. Grants record actor, time, exact target, and packet hash; one task or
action cannot borrow another's grant. Recording an action also requires its
resulting GitHub URL and performer. Disabling the kill switch revokes unused
grants, so authority cannot cross publication runs. External merge grants and
merge transitions are always rejected.

For a fork push, bind the grant to both repository and branch with
`owner/repo@refs/heads/<branch>`. An unqualified `refs/heads/<branch>` target
means the task repository itself.

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs configure \
  --ledger <control-dir>/contributions.json --publish-mode owned \
  --actor <owner> --authority-note "Enable owned publishing for this run"

node skills/suede-agent-teams/scripts/contribution-ledger.mjs grant \
  --ledger <control-dir>/contributions.json --id <task-id> \
  --capability push --actor <owner> \
  --authority-note "Push this named branch only" \
  --target refs/heads/fix/parser-empty-metadata

node skills/suede-agent-teams/scripts/contribution-ledger.mjs transition \
  --ledger <control-dir>/contributions.json --id <task-id> --to published \
  --action push --authority-target refs/heads/fix/parser-empty-metadata \
  --remote-url https://github.com/owner/repo/tree/fix/parser-empty-metadata \
  --performed-by <publisher>
```

Repeat `grant` and the publication transition separately for `draft_pr`,
`ready_pr`, and `merge`. A push target is an exact `refs/heads/<branch>` ref.
Draft PR authority names the planned branch/PR operation because the PR number
does not exist yet. Ready and merge targets are the canonical same-repository
`https://github.com/owner/repo/pull/<number>` URL, and each recorded action must
stay on that PR. Names in `--actor` and `--performed-by` are audit attestations;
authentication and authorization of the caller remain the controller's
responsibility.

For an explicitly approved external run, enable reviewed publication before
granting the exact external task:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs configure \
  --ledger <control-dir>/contributions.json --publish-mode reviewed \
  --actor <owner> \
  --authority-note "Allow separately granted external PRs through ready review"
```

## Repository preparation

1. Fetch the exact remote and resolve its default branch.
2. Read repository and nearest-directory instructions completely.
3. Inspect open PRs and recent commits for overlap.
4. Record dirty and untracked files before touching the checkout.
5. Create an isolated branch/worktree from the current remote base.
6. Copy only required ignored configuration; never copy credential stores.
7. Assign exact file ownership before opening parallel builders.

Use conventional branch names such as `fix/parser-empty-metadata`,
`docs/config-example`, or `test/token-refresh`. Add a neutral numeric suffix
when a name already exists.

## Build and review loop

Use the smallest useful roster:

```text
Scout -> Builder -> Code Reviewer -> Release Verifier -> Handoff Writer
```

Add parallel worker lanes only when the task splits into high-volume,
independent units. Fleet workers remain sandboxed, write only their assigned files, and
never push. Keep one owner for shared manifests, generated indexes,
lockfiles, or other collision magnets.

Run the repository's existing checks. Test generated artifacts as well as the
generator when applicable. Require independent review for authentication,
payments, user data, release automation, CI workflows, and unusually large
diffs. Review findings must map to a fix commit and a fresh verification result.

## Outward artifact contract

Branch names, commits, and PR copy describe the project change, not the tooling
used to produce it.

- Use a conventional title such as `fix(parser): handle empty metadata`.
- Structure PR bodies as `Summary`, `Why`, `Testing`, `Scope`, and `Risks`.
- Omit voluntary tool-origin footers, model badges, automation branding,
  robot markers, and model/tool co-author trailers.
- Keep the configured human Git identity; never forge authorship, signatures,
  review approval, or timestamps.
- Never assert "handwritten", "no AI", or another provenance claim the
  evidence does not establish.
- If upstream rules require assistance disclosure, preserve the exact required
  disclosure and stop the external lane at owner review.
- Add `Signed-off-by` only when DCO requires it and the signer can truthfully
  attest.

Check each outward artifact only after the task's disclosure requirement is
recorded in the ledger:

```bash
node skills/suede-agent-teams/scripts/contribution-ledger.mjs artifact-check \
  --ledger <control-dir>/contributions.json --id <task-id> \
  --worker <lane-id> --kind commit --input <artifact.txt>
```

`unknown` stops packaging. `required` records `owner_review_required` for the
PR artifact and blocks `packet_ready` until the current hash is explicitly
approved. It records the hash and exits nonzero so an unattended shell cannot
mistake the check for completion. The checker reports line numbers and rule
identifiers; it does not rewrite text or remove required disclosure. Use
`--kind branch` for the branch
name and `--kind pr` for the PR draft so branch-only automation prefixes are
checked without applying a broad word filter to legitimate product copy.

## Authority matrix

| Target and authority | Allowed outcome |
|---|---|
| Any target, `local_only` | Local branch, tests, review, contribution packet |
| Owned, explicit push approval | Push named branch only |
| Owned, explicit PR approval | Open named PR; ready/merge remain separate |
| External or uncertain, no reviewed-mode grant | Packet ready for owner review; no publication |
| External after explicit reviewed-mode grants | User-controlled fork, draft PR, then ready PR; never merge |

Never force-push, rewrite shared history, change branch protection, merge an
external PR, deploy, or delete a worktree unless the governing workflow and
target ownership allow it. External merge remains outside this ledger even
when a user separately authorizes other publication actions.

## Contribution packet

```text
CONTRIBUTION_PACKET
Target: <repo, remote, base, head>
Ownership: <owned|external + evidence>
Authority: <applied grant and remaining boundary>
Packet: <reviewed packet SHA-256 bound to every grant>
Issue: <reference and acceptance criteria>
Branch: <conventional branch>
Commits: <hash + conventional subject>
Changed: <every file + diffstat>
Verification: <commands + results>
Review: <findings, fixes, recommendation>
Artifacts: <branch, commit, and PR hashes + artifact-check results>
Disclosure: <rule source + required statement disposition + owner review hash>
Caveats: <known limits>
Status: <exact state>
Next: <one exact action>
```

## Learning loop

After merge, close, or supersession, record only reusable facts:

- task type and estimated versus actual effort;
- tests or review checks that caught real defects;
- maintainer feedback and accepted house patterns;
- duplicate-work cause;
- lead time, review cycles, and merge outcome.

Do not optimize for raw commit count. Optimize for accepted, useful changes
that survive current-main CI and reduce repeat work in the next contribution.
