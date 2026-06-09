# Codex Executor Path

Use this reference when an RPI run fails because the external agent harness
failed, while the repo checks or slice behavior are still recoverable through
Codex direct execution.

## Decision Rule

If Claude Code or another executor fails with process pressure, missing
worktree, or session-runtime errors, do not classify that as a code regression
until Codex direct checks reproduce a source-level failure.

## Codex Recovery Steps

1. Identify the clean branch worktree and avoid the dirty canonical root.
2. Use the source-built CLI explicitly:

   ```bash
   AO_BIN=/Users/bo/go/bin/ao
   "$AO_BIN" rpi status
   ```

3. If the RPI run worktree is missing, treat the run as an executor artifact
   and continue from the branch worktree.
4. Run the program or slice validation bundle directly from Codex.
5. If validation fails for source code, create or update a bead with the failing
   gate and fix it test-first.
6. If validation passes, record acceptance evidence and do not re-open the
   already-satisfied bead.

## Non-goals

- Do not resurrect missing temporary RPI worktrees.
- Do not invoke Claude Code as the executor for the recovery run.
- Do not convert a runtime artifact into a source-code failure without a
  reproducible gate.
