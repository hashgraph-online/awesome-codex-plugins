# GitHub Actions CI Patterns

> General-purpose CI patterns adapted for AgentOps release prep. Use this when wiring or auditing the validation workflow that gates a release (the workflow that produces signal for `--check` mode and pre-flight). For release-only patterns (tag triggers, asset upload, draft flow), read [`gh-actions-release-automation.md`](gh-actions-release-automation.md) instead.

This reference is methodology, not a copy-paste workflow. Pull only the patterns you need; do not graft an unrelated matrix into a repo that does not have the platforms to support it.

---

## When to consult this reference

- Adding or rewriting `.github/workflows/ci.yml` (or `validate.yml`).
- Tightening the pre-push gate so local + CI signal agree.
- Auditing an existing workflow that times out, leaks secrets, or produces flaky results.
- Adding a new platform to a matrix you already operate.

---

## Core skeleton

Every CI workflow worth shipping has the same five concerns: triggers, concurrency, permissions, timeouts, and a small set of named jobs. Skip any of these and the workflow becomes either expensive or unsafe.

```yaml
name: validate

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@<sha>  # pin to immutable SHA, not @v4
```

Notes:

- The default 6-hour job timeout will eventually bite. Always set a budget.
- `cancel-in-progress: true` is correct for CI. Flip it to `false` for release workflows so a tag push is not cancelled by a follow-up commit.
- `permissions: contents: read` is the safe default; widen only on jobs that need it.

---

## Matrix strategy

Two distinct uses, do not conflate them:

| Use | Shape | Notes |
|---|---|---|
| Cross-platform parity | `os: [ubuntu-latest, macos-14, windows-latest]` | Native ARM runners (`ubuntu-24.04-arm`, `macos-14`) avoid QEMU. |
| Toolchain coverage | `go: ['1.24', '1.25']` or `python: ['3.11', '3.12']` | Use sparingly; each cell is a full job-minute spend. |

Always set `fail-fast: false` when the matrix is for parity — you want every cell's failure surfaced, not the first one cancelling the rest. Use `include:` to attach platform-specific build targets and `exclude:` to skip impossible cells (e.g., a UNIX-only feature on Windows).

For AgentOps releases, the matrix that matters is the one that mirrors `scripts/ci-local-release.sh`. If local CI passes on Linux x64 only, do not pretend Windows is covered just because the matrix mentions it.

---

## Caching keys

A cache key is a contract: same inputs, same key, same artifacts. Three rules:

1. Include the runner architecture in cache keys when matrix builds touch multiple platforms — `runner.os` alone is not enough on hybrid x64/ARM matrices.
2. Hash the lockfile, not the manifest. `Cargo.lock` / `package-lock.json` / `go.sum` change with every dependency move; manifests do not.
3. Provide `restore-keys:` fallbacks so a partial hit still warms the cache.

```yaml
- uses: actions/cache@<sha>
  with:
    path: |
      ~/.cache/<tool>
      .build-cache
    key: ${{ runner.os }}-${{ runner.arch }}-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-${{ runner.arch }}-
```

Language-specific cache actions (`Swatinem/rust-cache`, the built-in cache in `actions/setup-go`, `setup-node` with `cache: 'npm'`) are preferred over hand-rolled `actions/cache` blocks; they encode the right paths automatically.

---

## Retries and timeouts

The two failure modes worth defending against are flaky steps and runaway jobs.

- **Step-level timeouts.** Wrap the long, hung-prone steps (browser tests, integration suites) with `timeout-minutes:` so a stuck step does not eat the job budget.
- **Job-level timeouts.** Always set. 10 minutes for lint, 20-30 for test, 60+ only for cross-platform release matrix jobs.
- **Selective retry.** Avoid blanket retries — they hide flakes that should be fixed. When you must retry, retry only the network-bound step (registry pulls, GitHub API), not the test step.
- **`continue-on-error`** is for genuinely advisory steps (optional security scanners, link checks). Pair it with `if: steps.<id>.outcome == 'failure'` to surface the result downstream.

---

## Secrets handling

The default posture is "secrets do not exist" — `permissions: contents: read`, no env vars exposed at the workflow level, secrets injected only at the step that needs them.

```yaml
- name: deploy
  if: github.event.pull_request.head.repo.full_name == github.repository
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
  run: ./scripts/deploy.sh
```

Specific guards:

- For fork PRs, `secrets.*` resolves to empty by default. Never paper over this with `pull_request_target` plus a head-SHA checkout — that pattern executes untrusted code with full secret access.
- Use `::add-mask::` when a step computes a secret-derived value that must not appear in logs.
- Prefer OIDC (`id-token: write` plus a cloud-provider action) over long-lived static tokens for any cloud auth.
- Pin every third-party action to a commit SHA. Tags are mutable; SHAs are not.

---

## Conditional steps and job dependencies

Two patterns that turn brittle workflows into composable ones:

```yaml
# Run a step only when the file it acts on exists.
- if: hashFiles('Cargo.lock') != ''
  run: cargo audit

# Pass version data between jobs without re-computing it.
jobs:
  resolve:
    outputs:
      version: ${{ steps.v.outputs.version }}
    steps:
      - id: v
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> "$GITHUB_OUTPUT"
  release:
    needs: resolve
    steps:
      - run: echo "Releasing ${{ needs.resolve.outputs.version }}"
```

For AgentOps, the resolved-version pattern is the right home for the audit trail values that `scripts/resolve-release-artifacts.sh` produces locally.

---

## Anti-patterns to refuse

| Don't | Reason |
|---|---|
| `uses: foo/bar@main` | Branch tip is not immutable; supply chain hole. |
| Default 6h timeout | One stuck job locks the runner; budget is never recovered. |
| QEMU for ARM builds | 5-10x slower than native ARM runners. |
| Workflow-level `secrets.*` env | Every step in every job sees the secret; tighten to step scope. |
| Skip `concurrency:` block | Stacked PR pushes pile up minutes you do not need. |

---

## Validation hooks

Two cheap commands keep CI honest:

```bash
actionlint .github/workflows/*.yml
gh workflow list && gh run list --workflow=validate.yml --limit 5
```

Run `actionlint` from the pre-push gate before you push a workflow change. Most "broken yaml" failures show up there, not on GitHub.

---

> Pattern adopted from `gh-actions` (ACFS skill corpus). Methodology only — no verbatim text.
