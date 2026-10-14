# Verification allowance

Keep cumulative verification unlimited unless the user supplies an allowance.
Thorough work or unlimited time does not imply a cap. Per-command timeouts still apply.

Pass `--allowance-seconds TOTAL` to `implement-verify` with command argv. TOTAL
is finite, nonnegative seconds for the plan and target, shared across ordinary,
integration and compatibility captures in Codex and Claude Code. Accounting starts
when enabled; earlier runs are uncharged. Zero prevents another capture.

Later calls inherit the saved allowance when the flag is omitted. Repeating the
total never resets spending. Only an explicitly user-authorized higher total
extends it; this is the new total, not additional seconds. Do not lower, delete
or recreate accounting to continue.

Passed, failed and timed-out executions consume measured time. A caught preparation
failure before command execution releases its unused reservation if that update
can be saved; prior charges remain. A pending
allocation has unknown elapsed time and blocks further captures. Explicit
extension retains it as unmeasured. Remaining allowance limits each captured
command's timeout, but cleanup can overrun: this is not a hard wall-clock deadline
or proof that an interrupted process terminated.

When blocked, report remaining required checks and await explicit continuation.
Reuse fresh successful receipts; keep stale or missing checks incomplete. Never
bypass the allowance through shell execution, manual evidence or skipped checks.
Direct shell commands, external CI and detached-frozen execution are outside
enforcement. Accounting is saved in `implementation/verification/allowance.json`;
it is local workflow state, not an authenticated billing record.
