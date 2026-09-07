# Wave Agent Template

> Reference specification for agent definitions in session plans. Extracted from SKILL.md Step 4.

For each wave, define agents with:

```
[Role] (Wave N) Agent M:
  Task: [specific task description]
  Files: [exact file paths to read/modify]
  Acceptance: [what "done" looks like — measurable]
  Tools needed: [Read, Write, Edit, Bash, Grep, Glob, etc.]
  Dependencies: [output from which prior role/agent]
  Isolation: [worktree|none — read from Session Config, default: worktree for feature/deep, none for housekeeping]
  MaxTurns: [read from Session Config max-turns, default: housekeeping=8, feature=15, deep=25]
  status: brainstormed
```

- `Isolation: worktree` means the wave-executor will pass `isolation: "worktree"` to the Agent tool, giving each agent its own git worktree copy
- `MaxTurns` is enforced via the agent prompt — wave-executor includes a turn limit instruction in each agent's prompt
- `status` is the mission-status enum value for this wave-plan item (#340). Always `brainstormed` in the initial plan. Wave-executor updates it at gate transitions (validated → in-dev → testing → completed). Rollback to `brainstormed` is allowed from any state. The five values are listed in `SKILL.md` § Mission-Status Enum; nothing validates them mechanically — `setMissionStatus` writes the string it is given to both STATE.md surfaces on purpose, so keeping the value in-enum is the coordinator's job.
- The wave-plan item's `id` becomes the `taskId` every `setMissionStatus` call for this item uses, and `setMissionStatus` REFUSES ids outside `[a-z][a-z0-9]*(?:-[a-z0-9]+)*-\d+` (lowercase segments, single hyphens, trailing bare digits) with `refused: 'id-grammar'` and a stderr WARN — nothing is written. Mint ids matching it: `m-1`, `docs-2`, `w2-1`, `w2-a-10` all accepted; `w2-a10`, `w3-p2`, `W3-I1`, `Docs_2` all refused.

> **Deconfliction rule:** Before finalizing agent specs for a wave, verify that no two agents in the same wave list overlapping `Files:` paths. If overlap is found, either merge the agents into one or move one task to a later wave. Two agents editing the same file in parallel causes merge conflicts that require manual resolution.

## Agent Count by Session Type

| Session Type | Discovery | Impl-Core | Impl-Polish | Quality | Finalization |
|-------------|-----------|-----------|-------------|---------|-------------|
| housekeeping | — | 1-6* | — | — | — |
| feature | 4-6 | 6 | 4-6 | 4 | 2 |
| deep | 6-8 | 6-10 | 6-8 | 6 | 2-4 |

Read `agents-per-wave` from Session Config to cap the maximum.

> **The Quality column is a CAP, not a target.** Quality capacity is need-gated: the effective count is `min(<column cap>, ceil((HIGH + MED gaps from the most recent qa-strategist run) / 3))`. 0 gaps → 0 test-writing tasks and the wave is skipped (the read-only review panel is unaffected); no qa-strategist signal at all → a conservative 1-2, never the blind cap. Full rule: `SKILL.md` § Agent Count by Tier footnote.

> **Note:** For feature and deep sessions, prefer the complexity-based agent counts from Step 3. This table provides defaults when complexity scoring is skipped (housekeeping) or as a fallback.

> \* Housekeeping sessions use single-wave serial execution (see wave-executor). Agent counts are for the single consolidated wave, not per-role.
