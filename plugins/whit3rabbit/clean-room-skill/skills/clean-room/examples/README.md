# Clean-Room Examples

These examples show artifact shape only. They are not outputs from a real source review and contain no source-derived content.

The `minimal-spec-package` directory contains clean-side artifact shapes only. Its handoff package is not a handoff-integrity fixture because it uses a placeholder checksum and a non-existent artifact path.

The `contaminated-side` directory contains controller and contaminated-side artifact shapes. Do not copy it into a clean workspace.

`role-session-brief.json` is a compact launch packet for one fresh role context. `controller-status.json` is Agent 0 contaminated-side resume state and must not be copied into a clean workspace.

The `valid-handoff-package` directory is the positive handoff-integrity fixture. It references an existing clean artifact with its real SHA-256 checksum.

The minimal `task-manifest.json` uses `speckit-feature-folder` as a non-normative example. Real tasks must record the user's actual `format_selection.target_profile` from OpenSpec, GSD, Spec Kit, or Kiro before agents start work.

The minimal `preflight-goal.json` and `init-config.json` are controller-side examples and may contain source or output details, so do not place them in clean-role readable roots. The minimal `clean-run-context.json` is the sanitized Agent 2/3/4 context.

The minimal `source-index.json` is a contaminated-side shape example. Real source indexes may contain source paths and private import/export names, so they must stay out of Agent 1.5 inputs and clean handoff packages.

The minimal `visual-index.json` is a contaminated-side visual fallback shape example. Real visual indexes may contain screenshot paths, dimensions, and image hashes, so they must stay out of Agent 1.5 inputs and clean handoff packages.

Use them to seed tests, docs, or dry runs:

- `minimal-spec-package/clean-run-context.json`
- `minimal-spec-package/behavior-spec.json`
- `minimal-spec-package/handoff-package.json`
- `minimal-spec-package/role-session-brief.json`
- `minimal-spec-package/skeleton-manifest.json`
- `minimal-spec-package/implementation-plan.json`
- `minimal-spec-package/implementation-report.json`
- `minimal-spec-package/polish-report.json`
- `minimal-spec-package/clean-room-result.json`
- `minimal-spec-package/qc-report.json`
- `minimal-spec-package/contamination-incident.json`
- `contaminated-side/task-manifest.json`
- `contaminated-side/preflight-goal.json`
- `contaminated-side/init-config.json`
- `contaminated-side/source-index.json`
- `contaminated-side/visual-index.json`
- `contaminated-side/evidence-ledger.json`
- `contaminated-side/coverage-ledger.json`
- `contaminated-side/controller-status.json`
- `valid-handoff-package/behavior-spec.json`
- `valid-handoff-package/handoff-package.json`
