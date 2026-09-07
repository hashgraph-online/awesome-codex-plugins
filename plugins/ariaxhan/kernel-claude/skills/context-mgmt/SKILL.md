---
name: context-mgmt
description: "Context engineering and token management. Compaction strategies, progressive disclosure, structured note-taking via AgentDB. Triggers: tokens, compaction, memory, handoff, summarize, context window."
allowed-tools: Read, Bash, Task
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="context-mgmt">

<purpose>
Context is finite. Every token competes for attention.
Longer context makes things WORSE (30%+ accuracy drop for middle info).
Progressive disclosure: load what's needed when it's needed.

**Reasoning fidelity is the real metric, not token count.** Quality degrades at ~60-70% fill, not at the limit.
</purpose>

<prerequisite>
Monitor context usage. Compact or hand off proactively at ~60% capacity — not 80%, not at limit.
Use native /context command to check usage. This skill is for methodology.
</prerequisite>

<reference>
Skill-specific: skills/context-mgmt/reference/context-mgmt-research.md
Architecture: _meta/research/context-graph-architecture.md
Graph telemetry (shadow): JSON receipts → `agentdb graph-project` / `graph-suggest` (see orchestration/agentdb/graph-project.py). Canonical JSON manifests remain authoritative.
</reference>

<core_principles>
1. COMPACTION: Summarize and reinitialize. Keep architecture decisions, discard noise.
2. STRUCTURED NOTES: AgentDB + active.md persist across context resets.
3. MULTI-AGENT: Delegate research to subagents. They explore, report summaries.
4. MINIMAL READS: grep/glob to find, then read specific sections.
5. TOOL RESULT CLEARING: Old tool output rarely needs to stay in context.
</core_principles>

<token_budget>
- CLAUDE.md: <150 lines (always loaded)
- rules/: <100 lines (always loaded)
- Skills: metadata only at startup, full content on demand
- Commands: only when invoked
- Reference docs: only when skill explicitly reads them
</token_budget>

<compaction_protocol>
1. CHECK fill level via /context. (gate: <60% → continue; ≥60% → proceed to step 2)
2. Write critical state: `agentdb write-end '{"did":"X","next":"Y","blocked":"Z"}'`
3. Commit any uncommitted changes. (gate: clean working tree)
4. Generate handoff if complex work in progress: `/kernel:handoff`
5. Trigger compaction.
6. POST-COMPACT RESTORE:
   a. Read active.md for project context.
   b. Run `agentdb read-start` for failures, patterns, contracts.
   c. Check for pending checkpoints to review.
</compaction_protocol>

<fidelity_signals>
Watch for reasoning degradation BEFORE the token meter shows a problem:
- Hypothesis depth dropping: agent defaults to first idea, stops exploring alternatives
- Backtracking absent: errors patched in place instead of root-caused
- Step count contracting: multi-step plans collapse to one-shot attempts
- Cross-file awareness fading: agent forgets earlier files in the same session
- Inline checks disappearing: agent stops verifying assumptions before acting

Any one of these → compact or hand off NOW, even if /context shows <60% fill.
</fidelity_signals>

<what_to_preserve>
Never compact away:
- Current task context and goal
- Active decisions and their rationale
- Blocking issues and error states
- File paths currently being worked on
- Uncommitted changes description
- Contract IDs and branch names
</what_to_preserve>

<what_to_compact>
Aggressively compress:
- Exploratory searches → "searched X, found Y at path:line"
- File reads → "read file, key insight: Z"
- Successful operations → "completed: X"
- Debugging traces → "root cause: X, fix: Y"
- Tool call history → "N tool calls, outcome: X"
- Research context → offload to AgentDB, keep one-line summary
</what_to_compact>

<failure_modes>
1. Agent tries too much at once → context exhausted mid-work
   Fix: Incremental progress with commits at each step.
2. Later agent assumes done prematurely → work incomplete
   Fix: Explicit done-when criteria with evidence required.
</failure_modes>

</skill>
