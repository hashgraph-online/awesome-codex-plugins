---
name: sbh
description: Inspect disk pressure with SBH and run one
---
# SBH — storage pressure specialist

SBH exposes disk-pressure status, ballast, scanning, and recovery commands. This
skill gathers evidence and performs at most the explicit action authorized by the
caller.

## Constraints

- Begin with `sbh --json status`, `sbh check`, or a dry run on the exact mount
  because recovery decisions need a factual baseline.
- Never run `clean --yes`, `emergency --yes`, ballast release, `tune --apply`,
  `unprotect`, or service/configuration changes without explicit authority
  because those operations mutate host state.
- Preserve `.git/`, open-file, young-file, non-writable-parent, and
  `.sbh-protect` vetoes because they prevent unsafe or ineffective cleanup.
- Confirm that ballast or reclaimed bytes affect the constrained mount because
  free space on another filesystem does not resolve the pressure.
- Run one action once, capture before/after evidence, and stop because the
  caller owns any further mutation. A negative result
  is returned to the caller; this skill does not retry or escalate it.

## Output

Return mount, free bytes, pressure state, dry-run candidates, authorization used,
exact command and exit code, bytes reclaimed, protection vetoes, and checked/not
checked surfaces.

Full command documentation: <https://github.com/Dicklesworthstone/storage_ballast_helper>
