---
name: fan-out
description: "Parallel agent orchestration for OST exploration. Fan-out multiple solution explorations, fan-in results to compare and select winners."
metadata:
  instruction_budget: "22"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Fan-Out / Fan-In Orchestration

## When to Use
- OST has 2+ solutions for the same opportunity that need parallel exploration
- Independent delivery work items that can be parallelized
- Multiple research streams needed simultaneously

## Workflow

### 1. Prepare (Lead Agent)
- Read .claude/canvas/opportunities.yml
- Identify solutions needing parallel work
- For each: identify riskiest assumption, design test, and write its `runs_on` (disk | network | human, as in `/mycelium:assumption-test`)
- Register each `human` test (survey, fake door, interviews, paid pilot) through `/mycelium:handoff`. No subagent runs it: a subagent can only simulate what people would do, and a simulated verdict is not a test result (v0.330.0)

### 2. Fan-Out (Spawn Workers, disk and network tests only)
For each solution with a disk or network test:
- Spawn subagent or Agent Team member
- Provide: clear task, read-only canvas context, worktree isolation, and a turn cap where the runtime has one (`maxTurns` in an agent definition). A time bound in the brief is advice: Claude Code has no time limit for a subagent
- Each worker runs independently and reports its evidence with its source, not only a verdict

### 3. Fan-In (Collect Results)
- Collect all worker results, and the `human` tests' verdicts once logged through `/mycelium:log-evidence`
- Update ICE scores in canvas
- Run `/mycelium:bias-check` on combined findings
- Select winner(s) based on evidence
- Log decision in .claude/harness/decision-log.md

### Leaf Bakeoff Mode

When comparing competing OST leaves for the same opportunity (two or more leaves that each have an untested riskiest assumption; no ICE gap is consulted):
- Each worker returns a structured **scorecard** (Four Risks + ICE from the leaf's record, the result of its disk or network test, segment fit); a leaf whose test is `human` gets its scorecard from the lead once the verdict is logged
- Lead agent applies **winner selection rules**, which read the assumption-test verdicts: clear winner (one passes, the others fail), several pass in the same segment (tiebreaker), several pass in different segments (segment split, both advance), both fail (archive and re-evaluate). A leaf whose riskiest assumption failed is archived.
- The ICE total only orders which assumption is tested first. It never decides when to compare or which leaf wins (until 0.320.0 a "clear winner" was a leaf more than 20% ahead on ICE).
- Losers are archived to `.claude/canvas/archived-solutions.yml` with full evidence snapshot

See `${CLAUDE_PLUGIN_ROOT}/orchestration/leaf-bakeoff.md` for the complete bakeoff protocol.

## Rules
- Workers NEVER write to canvas (lead agent does). On Claude Code the guard-state gate refuses a subagent's write to `.claude/canvas/` or `.claude/diamonds/` (v0.330.0); the other rules below are the lead's discipline and no hook checks them
- Workers NEVER progress diamonds
- Workers NEVER run a `human` test
- Lead agent ALWAYS runs bias check on combined results
- Minimum 2 workers for meaningful comparison
- Maximum 3 leaves per bakeoff (respects L3 WIP ceiling)
- Inside an L3 (v0.301.0), the leaves are its set under the L2's target, and a clear winner is the candidate for its `front_runner`; recording it is the human's choice

See `${CLAUDE_PLUGIN_ROOT}/orchestration/agent-teams.md` for full orchestration patterns.
