---
name: rch
description: 'Use RCH once to offload a build or collect Triggers: "use RCH", "offload this build".'
---
# RCH — remote compilation specialist

RCH can offload one explicit compilation command or inspect the remote compiler
path. This skill reports what happened; it does not govern retries or repair.

Staged diagnosis works because the offload pipeline fails in order —
availability, configuration, hook, classification, sync, remote compile,
worker pressure — so the first failing stage localizes the fault and every
later stage is noise until it passes. Remediate in irreversibility order:
read-only probes and config inspection before daemon restarts, restarts before
cleanup, and destructive cleanup or worker mutation only with explicit caller
authority.

Named failure mode — **green-local blindness**: a passing `[RCH] local (...)`
build read as offload success; the local fallback hid that the remote claim
was never proved.

Anti-pattern: re-running the build hoping the fallback reason disappears.
Corrective: read the recorded fallback reason and fix that stage; the pipeline
fails deterministically, not moodily.

## Procedure

1. Capture `rch check`, `rch doctor --json`, worker status, and the relevant
   `[RCH]` summary before mutation.
2. For diagnosis, identify the first failing stage: availability, configuration,
   hook, classification, sync, remote compile, or worker pressure.
3. Run only the caller-authorized command or documented safe diagnostic once.
4. Capture the exact command, worker when known, exit code, local-fallback reason,
   and post-action status.
5. Stop and return the evidence.

`[RCH] local (...)` means the requested remote-offload claim was not proved even
when the local build succeeds. Destructive cleanup, worker deployment, daemon
configuration, and remote mutation require explicit caller authority.

`rch check` exit status adjudicates readiness (0 = ready, nonzero = not
offload-ready). Do not read `rch doctor --json` `success: true` as readiness — a
successful diagnostic report can coexist with a down daemon or unreachable
workers. Adjudicate on `rch check`; use `doctor` for the reasons behind it.

## Output

Return a factual packet with status (`remote`, `local_fallback`, `failed`, or
`not_proven`), commands and exit codes, worker, summary line, and checked/not
checked surfaces. Do not include a next action. `not_proven` here is a runtime
diagnosis status, not an AgentOps verdict; it carries no verdict weight and never
substitutes for a `verdict.v2`.

## References

The SKILL.md authority boundary above governs every reference below. Where a
reference lists a remediation, its read-only diagnostics run autonomously but its
remote, privileged, or irreversible steps (remote/`sudo` mutation, daemon
start/restart/reconfigure, worker or fleet deployment, toolchain sync,
destructive cleanup) still require explicit caller authorization first. A
reference never widens the autonomy the kernel grants.


- [Fail-open reasons](references/FAIL_OPEN.md)
- [Error catalog](references/ERROR_CODES.md)
- [Troubleshooting](references/TROUBLESHOOTING.md)
- [Recovery playbooks](references/RECOVERY_PLAYBOOKS.md)
- [Worker operations](references/WORKERS.md)
- [Configuration](references/CONFIGURATION.md)
- [Machine-readable surfaces](references/MACHINE_INTROSPECTION.md)
