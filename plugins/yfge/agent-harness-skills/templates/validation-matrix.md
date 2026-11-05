# Validation Matrix Template

Harness role: validation

| Change type | Minimum check | Escalation trigger | Evidence |
| --- | --- | --- | --- |
| Documentation | `{DOCS_CHECK}` | Public guidance or templates changed | Command output |
| Contracts or interfaces | `{CONTRACT_CHECK}` | Shared schema, API, or boundary changed | Report path or CI job |
| Implementation | `{UNIT_OR_LINT_CHECK}` | Behavior, control flow, or dependencies changed | Test output |
| Runtime-sensitive | `{RUNTIME_CHECK}` | User-facing flow, external dependency, or stateful path changed | Run artifact or skip reason |

## Fallback Policy

If a check cannot run, record the blocker, the nearest substitute check, and the residual risk.
