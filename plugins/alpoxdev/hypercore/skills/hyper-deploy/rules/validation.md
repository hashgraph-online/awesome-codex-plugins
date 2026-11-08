# Validation

Use this checklist before declaring a run complete. It owns the completion evidence each mode needs, the terminal-state rule, and the report check.

## 1. The Terminal-State Rule

A deployment is successful only when all of these hold for the deployment this run created:

1. the platform reports a terminal success state for that deployment ID or version (`SUCCESS` on Railway, the active version on Cloudflare with every container instance on the new version when Containers are used, `healthy` on Compose, a completed Kamal deploy)
2. the health check the target guide names returns success, where the target has one
3. the runtime log for that deployment shows no fatal error in a bounded window after it became active

An upload, a queued or started build, a started rollout, a CLI exit code of `0`, or a `--wait` that returned on a service with no health check is not success. A `SKIPPED`, `NEEDS_APPROVAL`, `SLEEPING`, `REMOVED`, or unknown state is reported as that state.

## 2. Completion Evidence By Mode

| Mode | Claim | Required evidence |
|---|---|---|
| `preflight` | "Ready" | A fresh full `deploy-check.sh` run after the last edit, exit `0`, `executed` above zero, every skipped gate named |
| `preflight` validate-only | "Blockers reported" | The full run result and the blocker list; no file edited except the report |
| `setup` | "Deployment configured" | The new configuration files, the local validator output where the guide names one, and a non-production deployment meeting section 1 |
| `deploy` | "Deployed" | The target identity stated before the command, the deployment ID, and section 1 |
| `change` | "Changed" | The value before, the planned diff or plan output, the value after, and section 1 for the redeploy |
| `diagnose` | "Fixed" | The symptom line before, the cause, the change, the same signal after, and section 1 for the redeploy |
| `diagnose` | "Exhausted" | Three attempts for the same root cause, each with its change and result, and the next evidence to collect |
| any | "Stopped for approval" | The exact command, what it changes, what it cannot undo, and the evidence behind it (`rules/safety-gates.md` §4) |
| any | "Does not apply" | The target root, the files read, and the output shape the request belongs to |

## 3. Report Check

- [ ] `.hyper/deploy/<slug>/report.md` exists and follows `references/report-template.md`.
- [ ] Every command in the report ran in this session, or is marked `not run` with the reason.
- [ ] Every log excerpt is bounded and redacted, and the redaction is noted.
- [ ] Every rollback proposal states that databases, volumes, and bound resources are not restored.
- [ ] Skipped gates, missing CLIs, and missing credentials are listed apart from passed checks.
- [ ] The final state line names the mode's terminal result: `ready`, `unproven`, `deployed`, `changed`, `fixed`, `exhausted`, `stopped-for-approval`, `blocked`, or `handoff`.

## 4. Repair Bound

A gate that fails sends the run back to the failing step at most within the mode's budget (`SKILL.md`, loop policy). A check that ran and failed stays visible in the report even when a later run passed.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Never report a deploy as successful without observing `SUCCESS` for that deployment | <https://github.com/railwayapp/railway-skills> |
| Deploy success means the rollout started, not that every container instance was replaced | <https://developers.cloudflare.com/containers/configuration/rollouts/> |
| `--wait` waits for services to be running or healthy; without a health check only running is observed | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| The completion chain and verification depth | `instructions/validation/index.md` |

### Evidence grade

`LOCAL` - the state list and the evidence table are this package's design over the cited platform documents.
