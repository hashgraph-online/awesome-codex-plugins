# Go CLI Release Automation Guidelines

## Workflows

| Task | Workflow |
|---|---|
| Validate release configuration safely | `workflows/validate-release-config.md` |
| Publish a versioned release | `workflows/publish-tagged-release.md` |
| Update Homebrew delivery | `workflows/publish-homebrew-package.md` |
| Repair partial publication | `workflows/recover-failed-release.md` |

## By Symptom

| Symptom | Load |
|---|---|
| Local archives differ from CI | `references/release-automation/knowledge.md` |
| Release job has broad repository access | `references/release-automation/rules.md` |
| Package formula points at missing bytes | `workflows/recover-failed-release.md` |
| Build tag hides debug server | `references/release-automation/rules.md` |
| Tag exists but release is incomplete | `workflows/recover-failed-release.md` |

## Release State

```text
source approved → tag created → artifacts built → release published
→ package metadata updated → installations verified
```

At every transition, record the durable identifier and verify the prior state.

## File Index

| File | Purpose |
|---|---|
| `references/release-automation/knowledge.md` | Release model and artifact handoff |
| `references/release-automation/rules.md` | Security, reproducibility, recovery |
| `references/release-automation/examples.md` | Configuration patterns |
