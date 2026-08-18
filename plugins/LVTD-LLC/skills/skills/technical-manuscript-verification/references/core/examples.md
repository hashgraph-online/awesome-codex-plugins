# Technical Manuscript Verification Examples

Synthetic examples for technical manuscript audits.

## Finding Format

```text
[High] Backup command can overwrite the only copy
Location: Chapter 6, "Restore from backup"
Evidence: The command writes to /srv/app/data without confirming the target is empty.
Reader risk: Data loss.
Fix: Add a dry-run check, target directory verification, and rollback note before the restore command.
Status: Failed verification.
```

## Evidence Table

| Item | Location | Method | Result | Fix |
|------|----------|--------|--------|-----|
| `docker compose up -d` | Ch. 3 lab | Ran in clean Ubuntu VM | Pass | Add expected `docker compose ps` output. |
| DNS screenshot | Ch. 4 | Compared to current provider UI | Partial | UI labels changed; update screenshot or describe fields generically. |
| Firewall command | Ch. 5 | Static review only | Risk | Warn about locking out SSH; add current session check. |
| "Free tier" claim | Ch. 8 | Current pricing not checked | Untested | Verify against vendor pricing page before publication. |

## Link Verification Result

```text
Broken: https://example.com/old-install-guide
Replacement: https://docs.example.com/install
Manuscript fix: Link to the docs root and describe the navigation path instead of deep-linking to a volatile page.
```

## Environment Matrix

| Environment | Supported? | Notes |
|-------------|------------|-------|
| Ubuntu 24.04 x86_64 | Yes | Primary tested path. |
| Debian 12 x86_64 | Likely | Needs package-name check. |
| macOS Apple Silicon | No | Reader can use it as client only, not host path. |
| Raspberry Pi OS ARM64 | Partial | Test image names and performance notes. |

## Expected Output Before/After

### Weak

```text
Run the command and make sure it works.
```

### Strong

```text
Run:
curl -I https://notes.example.com

Expected:
HTTP/2 200 or HTTP/1.1 200 OK

If you see 502, the proxy is reachable but the app container is not. Check the app container logs next.
```

## Current-Info Dependency Examples

| Manuscript Detail | Risk | Better Treatment |
|-------------------|------|------------------|
| Exact cloud pricing | Changes often | Link to pricing page and explain cost model. |
| UI button labels | Changes often | Use generic field names and screenshot only when needed. |
| Package versions | Changes by distro | Pin tested version or specify supported range. |
| Security defaults | Changes by release | Verify against current release notes. |

## Severity Guide

| Severity | Use When |
|----------|----------|
| Critical | Data loss, security exposure, irreversible public harm. |
| High | Reader cannot complete core promise or may make unsafe choice. |
| Medium | Reader likely gets stuck but can recover. |
| Low | Confusing, stale, or inefficient but not blocking. |
