# Live Mode

Authorized source-variant iteration with the host's existing browser or native preview. This release has no live-helper process, polling protocol, config generation or CSP patching. Ordinary product code and host-discovered preview tools are the complete workflow.

## Prerequisites

- A target and permission for the proposed source changes; read-only preview never authorizes edits.
- A working existing preview, or explicit authorization to start one. Discover tools/URLs from the host and validate the origin before navigation.
- Project tokens/components and actual identity evidence; PRODUCT.md is optional.

Without a browser/native preview, useful static analysis remains possible; rendered results stay NOT_VERIFIED. Without MCP, load this file and the canonical command registry directly.

## Workflow

1. **Scope:** identify the decision and preserve approved identity, behavior and pre-existing changes.
2. **Compare:** when alternatives are requested, load `variant-prototyping`. Use the requested number; isolate prototype surfaces from the shipped application and production side effects.
3. **Implement:** authorized source edits reuse real tokens, components and data/clearly labeled fixtures. Do not mutate the served DOM and pretend those changes were persisted to source.
4. **Inspect:** use the discovered browser/native tools, exercise relevant states and viewports, and view any screenshots before describing them. Tool names vary by host.
5. **Decide:** record the user's choice or the previously delegated decision. No control selection silently authorizes additional writes or a new identity.
6. **Promote/clean:** apply the accepted design within scope and remove only task-owned prototype scaffolding. Preserve user-owned preview config and concurrent edits.
7. **Verify:** rerun affected checks against the final source and follow `verification-and-recovery`. Neither `detect_antipatterns` nor `anti_slop_checklist` is a rendered-readiness certificate.

## Isolation and cleanup

A route unlinked from navigation is still reachable and may ship in file-based frameworks. Keep prototypes in the project's story/test/development-only surface or another authorized location excluded from production builds; verify that boundary. A draft route must not invoke real payments, deletion, notifications or other production effects.

Remove task-created variant controls, fixtures, dead rules and temporary wrappers once their decision is complete. A persistent demo is a separate requested product surface, not leftover scaffolding. Use source tests and rendered inspection to verify accepted behavior survives cleanup.
