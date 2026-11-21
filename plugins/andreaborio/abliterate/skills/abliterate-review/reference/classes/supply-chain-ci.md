# Supply chain and CI/CD (CWE-829, CWE-494)

## Sources
- Untrusted text reaching a workflow: PR title/body/branch name/commit message, issue and comment bodies, `github.head_ref`, fork code and its `package.json`/Makefile/scripts, artifacts produced by fork runs, cache entries written by PR jobs.
- Dependency inputs: new/changed entries in manifests and lockfiles, registry resolution of internal package names, install-time scripts, git/URL dependencies, container base images, `curl | sh` installers.

## Sinks
| Area | Dangerous shape | Safer shape |
| --- | --- | --- |
| Script injection | `run: echo "${{ github.event.pull_request.title }}"` (also `head_ref`, `comment.body`, `issue.title`, `commits[*].message`, `head_commit.message`) | pass via `env:` and reference `"$TITLE"` in the shell; use `actions/github-script` with context object, not string interpolation |
| Privileged trigger + untrusted code | `on: pull_request_target` (or `workflow_run`, `issue_comment`) with `actions/checkout` of `${{ github.event.pull_request.head.sha/ref }}` then build/test/install | checkout base only; run untrusted code in plain `pull_request` (no secrets); split into unprivileged build and privileged comment/publish workflow with artifacts treated as data |
| Token scope | no `permissions:` block (default may be broad); `write-all`; `contents: write` where read is enough; `id-token: write` without need | top-level `permissions: {contents: read}`, grant per job |
| Secrets to forks | `secrets: inherit`, secrets in `env` for jobs that run PR code, `pull_request_target` with secrets | secrets only in jobs that run trusted code; use environments with required reviewers |
| Unpinned actions | `uses: org/action@main` / `@v1` tag (third party), `docker://image:latest` | pin to full commit SHA, for third parties at least; track updates via Dependabot/Renovate |
| Self-hosted runners | PR from forks on persistent self-hosted runner | ephemeral runners, no fork PRs |
| Cache/artifact poisoning | cache restored in a privileged workflow from a key writable by PR jobs; artifacts executed in privileged `workflow_run` | key by trusted ref, treat artifacts as data |
| Install scripts | new dependency with `preinstall/install/postinstall`, `setup.py` executing code, curl output piped to a shell in CI or Dockerfile | `--ignore-scripts` where feasible, review the scripts, pin digest/hash |
| Dependency confusion | internal package name without scope/registry pin; `--extra-index-url` (pip) | scoped names (`@org/x`), `.npmrc` registry per scope, `--index-url` only, `pip --require-hashes` |
| Lockfile drift | manifest changed but lockfile not; lockfile `resolved` URL pointing to a non-registry host or git ref; integrity hashes removed | `npm ci`/`yarn --immutable`/`pip --require-hashes`/`cargo --locked`; reject resolved hosts outside the registry |
| Provenance (494) | download then execute without checksum/signature; unpinned base image `FROM x:latest` | verify digest/signature, pin image by `@sha256:` |

## Guards that work / Look-alike guards
Work:
- Untrusted text passed through `env:` (shell variable) rather than expression interpolation into the script.
- `pull_request` trigger for anything executing PR code; privileged follow-up workflow that only reads artifacts as data and never executes them.
- Least-privilege `permissions:` set explicitly; environment protection with required reviewers for deploy secrets.
- SHA-pinned third-party actions; lockfile used with an immutable install command.
- Fork PR approval requirements are a policy control; mention them but do not treat them as proof (a maintainer approval runs the code).

Look-alike:
- Condition `if: github.event.pull_request.head.repo.full_name == github.repository` guarding only one step while others run.
- Checking out `github.event.pull_request.base.ref` and then running scripts from the workspace after a later checkout of head.
- Label-gating (`if: contains(labels, 'safe')`) when the label can be added before the push of new code (TOCTOU: checkout by branch ref rather than the approved SHA).
- Quoting the expression inside the shell string (`"${{ ... }}"`): expansion happens before the shell, quotes do not help.
- Pinned to a tag believed immutable; tags can move.
- `permissions: read-all` described as safe while a step uses a PAT secret with write access.
- Sanitizing the title with a regex inside the same `run:` after interpolation.

## Falsify before reporting
1. Which trigger? Does the workflow run with secrets and a write token (`pull_request_target`, `workflow_run`, `issue_comment`, `push`) or the restricted fork context (`pull_request`)?
2. Does untrusted code actually execute (checkout of head, `npm install`/`make`/test from the PR tree) in the privileged context? Quote the checkout `ref` and the step that runs it.
3. Is the interpolated expression attacker-controlled text (title, body, branch, message) or a trusted value (`github.sha`, `github.run_id`, `github.repository`)?
4. Is the permission or secret really used by a step that handles untrusted input? Unused write token in a read-only workflow is low.
5. Dependency: is the new package/version real and resolved from the intended registry, per the lockfile `resolved` and integrity fields? Do not install it. Do not attribute a CVE without an applicable advisory.
6. Confirm: a workflow lint test or script asserting no `${{ github.event.* }}` inside `run:`, explicit `permissions`, and that checkout ref is the base for `pull_request_target`.

## Severity cues
- Raises: privileged trigger plus PR-head execution (secret exfiltration, repo write, release tampering); script injection reachable by any commenter; publish/deploy jobs; self-hosted runner with network access.
- Lowers: no secrets and read-only token, trusted-contributor-only triggers, injection into a value that is not shell-evaluated, dependency drift limited to dev tooling.

## Regression test
- Lint test (actionlint-style or grep-based) over `.github/workflows/*.yml` that fails when `run:` blocks contain `${{ github.event.` or `${{ github.head_ref`, and when a `pull_request_target` workflow checks out `head`.
- Assert each workflow declares `permissions:` and third-party `uses:` are 40-hex SHAs.
- Lockfile: CI step `npm ci` (or equivalent) fails when manifest and lockfile disagree.
- Allowed case: normal PRs still run build/test with read-only token; trusted `workflow_run` comment job still posts using artifact data.
