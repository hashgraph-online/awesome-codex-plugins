# Execution Profile — ship-loop

You are running the bot-paired fast lane PR cycle. Operator typed `$ship-loop` or asked you to ship a single-scenario internal PR.

## Mode

- **Lane:** internal-ship (same-repo, branch off main, auto-merge to main). NOT a fork-based OSS contribution.
- **Default approval:** autonomous; the bot review fires automatically on PR open.
- **Stop conditions:** the 9-step cycle completes, OR a gate fails with a real blocker (not a pre-existing F2-class side-quest), OR the work won't fit one scenario.

## Run

1. Read `bd ready` and `.agents/rpi/next-work.jsonl`. Pick highest-severity unblocked item. Claim it: `bd update <id> --claim`.
2. `git checkout main && git pull --rebase`. Branch: `git checkout -b <type>/<slug>-<bead-id>`.
3. Write the first FAILING test. Confirm it fails for the right reason.
4. Write the minimal implementation. Confirm the test now passes.
5. Run `scripts/pre-push-gate.sh --fast`. If a pre-existing blocker fires on content you didn't change, STOP and file an atomic side-quest fix PR first.
6. Commit with conventional-commit scope. Body reproduces the failure mode.
7. Push + `gh pr create`. `gh pr merge <num> --squash --auto`.
8. `bd close <id>` after the PR auto-merges.

## Guardrails

- Reject work that touches >5 non-uniform files or introduces a new shape (schema, contract surface, struct field). Surface to operator for slow-lane routing instead.
- Reject tests that assert local-only file existence (`[ -f .agents/learnings/<x>.md ]`). Use `grep -q '<slug>' "$SCRIPT"` to assert the rationale reference in the script body instead.
- Reject "I'll add the test after" — write the failing test FIRST.

## Verification

- Local: `bats <test.bats>` AND `scripts/pre-push-gate.sh --fast` both pass before push.
- Remote: `claude-review` and the full `validate.yml` suite via `gh pr view <num> --json statusCheckRollup`.

## Output

A merged PR on `origin/main` and a closed bead. If the chain has >=3 PRs in flight, invoke `scripts/gh-merge-chain.sh` to serialize them.
