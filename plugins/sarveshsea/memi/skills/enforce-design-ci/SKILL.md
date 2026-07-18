---
name: enforce-design-ci
description: Use when a repository needs deterministic pull-request checks for new accessibility, design-token, component-structure, responsive, and UI-state regressions with file-level evidence.
---

# Enforce Design CI

Add a reviewable design-quality gate that runs without an LLM. Memi writes a policy, baseline, universal agent skill, SARIF, and human-readable report artifacts.

## Initialize

Inspect the worktree first. When the task authorizes setup, run:

```bash
npx -y @memi-design/cli@2.6.2 init --team --kit universal --json
```

Review the generated policy and baseline before committing them. Existing debt remains visible but does not block unrelated pull requests.

## Verify Locally

```bash
npx -y @memi-design/cli@2.6.2 ci . --no-scope --report --json
```

The command may exit nonzero when findings exceed the configured gate. Treat that as a quality result, not a tool crash.

## Add GitHub Actions

Use the pinned major action in `.github/workflows/design.yml`:

```yaml
name: Design CI
on: [pull_request]
jobs:
  design:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: sarveshsea/memi@v2
        with:
          version: "2.6.2"
```

## Completion Criteria

- Policy and baseline are reviewed and committed.
- Local CI produces SARIF and a design-health report.
- The workflow passes on unchanged accepted debt and fails on a seeded regression.
- The final handoff names the gate threshold, suppressed baseline count, active findings, and artifact paths.
