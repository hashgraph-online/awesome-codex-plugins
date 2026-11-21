# review-code `--apply-fixes` (fix subagents and the Post-Fix Workflow)

Read this only when the user passed `--apply-fixes` to review-code and its
orchestrator wrote `{prefix}_fix_tasks.json` (`fix_tasks.json` in the phase dir).
A review without `--apply-fixes` never needs this file: it goes from the core's step 7
straight to the report (the core's *Post-Fix Workflow* step 6).

**Commands.** This file is read as it is, so its commands are spelled from the
mode word on: `<prefix>` stands for the dispatcher prefix every command in the
core starts with (`uv run … --project "<skill dir>" -- python "<skill dir>/multi_llm.py"`,
flags and paths exactly as the core prints them). Copy it from any command in
the core, unchanged, and run each command bare, as the core runs its own.

## Core step 8: apply the fixes by spawning subagents

**Spawn one subagent per issue.** Before the fix loop, mark the phase start, where
`{total_fixes}` is the number of fix tasks:

```bash
<prefix> util metrics start --state-file "$STATE_FILE" --phase "review-code-fixes" --total-batches {total_fixes}
```

For each fix task in the JSON file:

a. Read the fix tasks JSON file to get the list of issues to fix.
b. For each task, spawn a subagent:
   ```
   Spawn one subagent with:
   - executor_role: "agent"
   - description: "Fix: {task.title}"
   - prompt: |
       Fix the following code issue:

       **Issue**: {task.title}
       **Type**: {task.type}
       **Importance**: {task.importance}
       **Description**: {task.description}
       **Location hints**: {task.location_hints}

       Plan file for context: {task.plan_path}

       1. Read the relevant files and understand the issue
       2. Make the necessary code changes to fix it
       3. Verify your changes don't break anything

       After fixing, report what you changed.
   ```
c. Track fix results (success/failure) for each task, and record metrics for each
   fix subagent, where `{N}` is the 1-based fix index:
   ```bash
   <prefix> util metrics record --state-file "$STATE_FILE" --phase "code-review" --label "Fix: {task_title}" --subagent-type "{executor_role}" --tokens {token_count} --tool-uses {tool_uses} --duration-ms {duration_ms} --total-batches {total_fixes} --batch-index {N}
   ```
   `token_count`, `tool_uses` and `duration_ms` come from whatever your subagent
   mechanism reports. Omit any flag it does not report. Never pass `0` for an
   unknown value; omit the flag: a made-up zero is averaged into the phase totals
   as a real measurement. The command prints an `[ETA]` line to stderr after each
   call.
d. After all fixes are attempted, mark the phase finish:
   ```bash
   <prefix> util metrics finish --state-file "$STATE_FILE" --phase "review-code-fixes"
   ```
e. Update the plan file with a "Review Fixes Applied" section documenting what was
   fixed.

## Post-Fix Workflow, steps 1 to 4

1. **Wait for all subagents to complete**, tracking the success or failure of each
   fix.
2. **Run verification**: the repository's own typecheck and lint commands, if any
   (for example `pnpm typecheck` and `pnpm lint:fix` in a pnpm project). This plan
   may have neither.
3. **Update `{plan}_code_review.md`** with the implementation status of each issue.
   For each issue in the code review file, add an "Implementation" subsection:

   ```markdown
   ### Issue N: [Original Title]
   **Type**: security | **Importance**: HIGH
   **Description**: [original description]
   **Location Hints**: [original hints]

   #### Implementation Status: FIXED
   **Files Modified**:
   - `path/to/file1.ts` - Added input validation
   - `path/to/file2.ts` - Updated error handling

   **Summary**: Added proper input sanitization to prevent SQL injection...
   ```

   Or, if not fixed:
   ```markdown
   #### Implementation Status: NOT FIXED
   **Reason**: Requires architectural changes beyond scope of this review
   ```

4. **Update the original plan file** by appending a reference section:

   ```markdown
   ---
   ## Code Review Applied

   A code review was performed on this implementation. See the full review and implementation details at:
   **[{plan}_code_review.md](./{plan}/{plan}_code_review.md)**

   **Summary**: X of Y issues were fixed.
   **Date**: [timestamp]
   ```

Then return to the core for the *Post-Fix Workflow*'s step 6, the report, and add
`fix_tasks.json` and the summary of fixes applied to it.
