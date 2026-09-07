# Circuit Breaker & Worktree Isolation — Reference

Sub-reference for the wave-executor skill. Defines safety mechanisms for agent execution.

## Circuit Breaker

1. **MaxTurns enforcement**: Read `max-turns` from Session Config (default: auto — housekeeping=8, feature=15, deep=25). Include this instruction in EVERY agent prompt:
   ```
   TURN LIMIT: You have a maximum of [N] turns. If you cannot complete within [N] turns, report PARTIAL with what you accomplished and what remains.
   ```
   The agent prompt must also include this status reporting instruction:
   ```
   STATUS REPORTING: When you finish, end your final message with exactly one of:
   - STATUS: done — <1-line summary of what was accomplished>
   - STATUS: partial — <what was accomplished> | REMAINING: <what still needs to be done>
   - STATUS: failed — <what went wrong>
   Do NOT omit the STATUS line. The coordinator uses it to track progress.
   ```
2. **Spiral detection**: After each wave, the coordinator checks agent results for:
   - Same file edited 3+ times **within a single agent's execution** (across its turns) → possible thrashing
   - Same error message repeated across turns → stuck
   - Agent reverted its own changes → loop
   If spiral detected: log in STATE.md, mark agent as SPIRAL, re-scope task narrower for next wave.

   > Spiral detection operates per-agent, not per-wave. The coordinator reviews each agent's output independently for spiral indicators after the wave completes. Two different agents editing the same file is expected (conflict resolution, not spiral).

## Status Detection Protocol

The coordinator determines each agent's status after the wave completes:

1. **Read the agent's final output** and look for the `STATUS:` line
2. **Map to status**:
   - `STATUS: done` → agent completed successfully
   - `STATUS: no-tests-needed` → **SUCCESS variant, treat exactly like `done`.** test-writer-specific: the agent found no nameable bug the existing suite misses, so writing a test was the wrong move (`.claude/rules/test-value.md`; enum in `agents/schemas/test-writer.schema.json`). NEVER map this to `failed` or carry it over.
   - `STATUS: partial` → agent hit turn limit or couldn't finish (PARTIAL)
   - `STATUS: failed` → agent encountered an error it couldn't recover from (FAILED)
   - No STATUS line found → infer from output: if agent produced changes, mark as `done`; if it reported errors, mark as `failed`; if output is truncated, mark as `partial`
3. **Spiral detection** (checked independently of the STATUS line):
   - After the wave, review each agent's git history in its worktree (or shared directory)
   - If the same file was edited 3+ times by a single agent → mark as SPIRAL (overrides other status)
   - Detection method: `git log --oneline --name-only` within the agent's execution scope
   - Two different agents editing the same file is NOT a spiral — that's expected coordination

### Status Definitions

| Status | Meaning | Trigger | Recovery |
|--------|---------|---------|----------|
| **done** | Agent completed all assigned work | Agent reports `STATUS: done` | None needed |
| **no-tests-needed** | SUCCESS variant of **done** — test-writer found no nameable gap, so no test was the correct outcome | Agent reports `STATUS: no-tests-needed` | None needed — never a failure, never a carryover |
| **partial** | Agent made progress but couldn't finish | Turn limit hit, or agent reports `STATUS: partial` | Carry forward remaining work to next wave with context |
| **failed** | Agent couldn't make meaningful progress | Tool errors, invalid assumptions, agent reports `STATUS: failed` | Re-dispatch with corrected instructions and narrower scope |
| **spiral** | Agent got stuck in an edit loop | Same file edited 3+ times (detected post-wave) | Revert agent's changes, narrow scope, split task if needed |

3. **Recovery protocol**:
   - FAILED agent → log in STATE.md, add fix task to next wave with corrected instructions, AND auto-create a carryover issue (see "Carryover Auto-Create" below) the first time this task is marked FAILED (check STATE.md Wave History for a prior `→ issue #NNN` on this task before filing).
   - PARTIAL agent → carry forward remaining work with context
   - SPIRAL agent → revert the agent's changes (`git checkout -- <affected-files>` or `git stash` the agent's worktree), narrow scope to a single file or function, re-dispatch in next wave. If the task spiraled twice, escalate to the user AND auto-create a carryover issue (see "Carryover Auto-Create" below).

### Carryover Auto-Create (#261)

When a task is escalated (2×SPIRAL or first-time FAILED with no prior carryover), the coordinator MUST call `createSpiralCarryoverIssue` so the work is tracked on the VCS platform even if the user is inactive. Escalating to the user alone is not enough — the user may miss the message, or the session may crash before they see it.

**Ownership split:** auto-create happens HERE (inline at detection time), not deferred to session-end. Session-end Phase 1.6 only *validates* that each SPIRAL/FAILED entry in Wave History has an `→ issue #NNN` suffix and retroactively files one if missing.

```js
import { createSpiralCarryoverIssue } from '$PLUGIN_ROOT/scripts/lib/spiral-carryover.mjs';

// On 2×SPIRAL detection for <task>:
const result = await createSpiralCarryoverIssue({
  taskDescription: '<agent task description>',
  kind: 'SPIRAL',
  context: '<relevant STATE.md Deviations entry>',
  priority: 'high',
  vcs: '<from Session Config: $CONFIG.vcs>'
});
// result.created === true            → append "→ issue #<id>" to the Wave History line for this agent
// result.skipped === 'duplicate'     → append "→ existing #<id>" (do NOT create a new one)
// result.skipped === 'error'         → log result.error to stderr + continue escalation (do NOT block the session)
```

For the FAILED branch, use the same call shape with `kind: 'FAILED'`. Before calling, scan STATE.md Wave History for an existing `→ issue #NNN` entry on the same task — if present, skip the call (the dedup check in the module will also catch it via the `<!-- task-hash: ... -->` marker, but skipping early avoids an unnecessary `glab`/`gh` round-trip).

The function never throws — it always returns a result object. Treat `skipped: 'error'` as a logged warning, not a session blocker.

## Worktree Isolation

1. **When to use — graduated default (#194)**: Resolve isolation per wave via `resolveIsolation({ agentCount, sessionType, collisionRisk, configIsolation })` from `scripts/lib/wave-sizing.mjs`. User-explicit `isolation: worktree` or `isolation: none` in Session Config overrides the graduation. Plan-level `collision-risk: high` forces `worktree` even at ≤2 agents.

   | agentCount | sessionType | resolved isolation |
   |---|---|---|
   | ≤ 2 | any | `none` (coordinator-direct / in-place) |
   | 3–4 | housekeeping | `none` |
   | 3–4 | feature / deep | `worktree` |
   | ≥ 5 | any | `worktree` |

   Rationale: the verified learning `coordinator-over-worktree-on-shared-files` (confidence 0.75) shows that small waves on partitioned scopes merge cleaner when run in-place. Two consecutive deep-session regressions (2026-04-20 07:30, 09:00) were worktree base-ref staleness on ≤2-agent waves editing the same SKILL.md. Graduated default makes worktree the tool for parallelism, not the default tax on every wave.

2. **Enforcement auto-promote (#194)**: Call `resolveEnforcement({ isolation, configEnforcement })` from the same module. When isolation resolves to `none` and the user has not explicitly set `configEnforcement: 'off'`, enforcement auto-promotes from `warn` → `strict`. Worktrees provide filesystem-level isolation; in-place dispatch relies on the scope hook as the only barrier — it must be hard, not informational. Write the resolved value into `wave-scope.json` `enforcement`.

3. **Dispatch with isolation**: When resolved isolation is `worktree`, add `isolation: "worktree"` to Agent tool calls:
   ```
   Agent({
     description: "...",
     prompt: "...",
     subagent_type: "general-purpose",
     run_in_background: true,
     isolation: "worktree"
   })
   ```
   When resolved isolation is `none`, omit the `isolation` parameter (agents run in the coordinator's working tree).

   `isolation` and `run_in_background` are orthogonal: worktree isolation partitions the filesystem, backgrounding decides when the coordinator's turn returns. A backgrounded worktree agent still merges back on completion — but do NOT read the immediate launch ack as "the worktree merged". Wait for the agent's task-notification before step 4 below (`wave-loop.md § Started-Set Verification`).

4. **Post-wave merge**: After wave completes, worktree changes are automatically available. If agents made changes in worktrees:
   - Review each agent's changes for conflicts using `git diff` between worktree branches
   - **Merge strategy**: Apply agent changes sequentially (by agent number). For each agent:
     a. Attempt fast-forward merge. If clean, proceed.
     b. If conflicts: prefer the later agent's version for new code, prefer the earlier agent's version for modified existing code. When unclear, keep both versions and add a fix task to the next wave.
   - After all agents merged, run incremental quality checks
   - Document any conflict resolutions in the wave progress update
5. **Fallback**: If worktree creation fails (e.g., git state issue), fall back to shared directory with a warning logged.

## Stagnation Patterns

> Detection rules applied at two different moments, by two different producers of the SAME `stagnation_detected` record (`wave-loop.md` § "Review Agent Outputs" carries the schema; `source` says which).
>
> - **Coordinator heuristics (3):** Pagination Spiral, Turn-Key Repetition, Error Echo. LLM heuristics, not executable code — the coordinator interprets them contextually from agent output and tool-call history during post-wave review (step 2 of `wave-loop.md`). Recorded with `source: "coordinator"`.
> - **Tail-mechanical (2):** PSA-007 Git-Write and Status-Partial (§ 4 / § 5 below). Executable regexes run live by `scripts/lib/wave-transcript-tail.mjs` against the session's subagent transcripts — no model call, no judgement. Recorded with `source: "tail"`.
> - **Error Echo is BOTH.** The coordinator's contextual reading of it is unchanged, and the tailer additionally matches its repeated-failure signature mechanically. One wave can therefore produce an error-echo record from either producer; the records are otherwise identical and are told apart only by `source`.

### 1. Pagination Spiral

**Indicator:** An agent issues 3+ `Read` or `Grep` calls against the same file path with only `offset`, `limit`, `start_line`, or `end_line` arguments changing — and produces no `Edit` or `Write` between them.

**Example:** `Read(file=foo.ts, offset=0)` → `Read(file=foo.ts, offset=200)` → `Read(file=foo.ts, offset=400)` with no edits in between.

**Action:** Mark agent as STAGNANT. In the next dispatch, narrow scope to specific line ranges or function names so the agent does not need to page through the file.

### 2. Turn-Key Repetition

Serialize each tool call into a comparable "turn key" of the form `<tool>:<primary_args>` and **strip pagination args** (`offset`, `limit`, `start_line`, `end_line`, `number`) before comparing. Three identical consecutive turn keys = stagnation.

**Example:** `Bash:pnpm test` → `Bash:pnpm test` → `Bash:pnpm test` with no other tool calls between them — the agent is re-running the same command without changing anything.

**Action:** Mark agent as SPIRAL per the existing recovery protocol (revert changes, narrow scope, re-dispatch). Same handling as the existing per-file spiral detection in the Circuit Breaker section.

### 3. Error Echo

Same error message returned 3 times, with the agent attempting the same fix (or a trivial variant) each time.

**Example:** `Edit failed: old_string not found in file` → agent re-reads the file → tries `Edit` with the same `old_string` → fails the same way → repeats.

**Action:** Mark agent as FAILED. Escalate to next wave with the error context and a hint that the agent's mental model of the file is wrong (the file does not contain what the agent thinks it contains).

**Error-Class Taxonomy:** When Error-Echo fires, the coordinator classifies the error into exactly one of:

- `edit-format-friction` — error text contains `old_string not found`, `not unique`, or whitespace-related mismatches.
- `scope-denied` — hook exit code 2 / scope-violation message from `enforce-wave-scope.sh`.
- `command-blocked` — denial from `enforce-commands.sh` (blocked command list).
- `other` — fallback when none of the above match.

The `error_class` value is used by the stagnation event-write rule in `wave-loop.md` § "Review Agent Outputs". The taxonomy belongs to Error Echo **alone** — the four patterns below and above it omit the field entirely rather than falling back to `other`.

### 4. PSA-007 Git-Write (source: tail)

**Indicator:** a subagent's Bash call runs a git-write command — `git add`, `git commit`, `git stash`, `git push`, and equally `git mv` / `git rm` / `git reset` / `git checkout -- <file>`. `.claude/rules/parallel-sessions.md` § PSA-007 forbids all of them for dispatched agents: the git index and stash are shared resources of the working copy, not a per-agent workspace. Fleet evidence (2 repos, 2026-07, conf ≥ 0.9) records `index.lock` collisions and stash operations that silently discarded a sibling agent's work-in-progress.

**Detected by:** the tailer, mechanically, on the FIRST occurrence — not by post-wave review, and not on a repetition threshold. Today the coordinator learns of a subagent git-write only when the agent volunteers it in its own report.

**Action:** surface it in the wave progress update at once and inspect the shared index (`git status --porcelain`, `git stash list`) before the next dispatch. Do NOT re-dispatch into the same shared tree until the index state is understood — a stash the agent created is one the sibling cannot find. No `error_class`; `occurrences: 1` is the normal value.

### 5. Status-Partial (source: tail)

**Indicator:** the agent's own transcript contains `STATUS: partial` (or `STATUS: failed`) — a **self-reported** failure, not an inferred one, so there is nothing to interpret.

**Detected by:** the tailer, mechanically. The value here is **durability, not earliness**: when maxTurns kills an agent after it wrote the line but before its final report reaches the coordinator, the finding is lost today. The `events.jsonl` record survives that kill.

**Action:** treat exactly as the § Status Detection Protocol `partial` / `failed` branch above — carry forward the remaining work, or re-dispatch with narrower scope. A tail record is a **backstop for** the agent's report, never a replacement: when the report does arrive, the report wins and the tail record is corroboration (do not double-count one failure as two). No `error_class`; `occurrences: 1`.

### Decision Table

| Pattern | Indicator | Action | Error Class | Source |
|---------|-----------|--------|-------------|--------|
| Pagination Spiral | 3+ Read/Grep on same file with only pagination args, no Edit between | STAGNANT — re-dispatch with line-range scope | N/A | coordinator |
| Turn-Key Repetition | 3 identical consecutive turn keys (pagination-stripped) | SPIRAL — revert, narrow, re-dispatch | N/A | coordinator |
| Error Echo | Same error 3x, same fix attempted | FAILED — escalate with error context | see taxonomy above | coordinator **and** tail |
| PSA-007 Git-Write | Subagent Bash runs `git add`/`commit`/`stash`/`push` (or `mv`/`rm`/`reset`/`checkout --`) | Surface immediately; inspect shared index before next dispatch | N/A | tail |
| Status-Partial | Agent transcript carries `STATUS: partial` / `STATUS: failed` | Same as the Status Detection Protocol `partial`/`failed` branch; backstop for a lost report | N/A | tail |

### Detection Discipline

- The three **coordinator** checks run during step 2 of `wave-loop.md` ("Review Agent Outputs"), per agent, after the wave completes — not during the agent's execution. The two **tail** checks (§ 4 / § 5) run live and are the exception to that timing, which is exactly why they survive a maxTurns kill.
- **Tail silence is not a clean wave.** Transcripts flush per turn, so an agent inside one long tool call is unobservable for that call's duration (`.claude/rules/loop-and-monitor.md` § LM-002). Absence of tail records never substitutes for the post-wave review.
- Two different agents reading the same file is **not** a spiral. That is coordination across agents, not stagnation within an agent.
- A legitimate sequential read of a large file (e.g., reading lines 1-200, then 200-400 to gather full context for an upcoming edit) is **not** a pagination spiral if the agent eventually edits the file. The pattern triggers only when paging continues without ever producing an edit.
- These patterns are heuristics. When in doubt, prefer false negatives (let the agent finish) over false positives (kill productive work).
