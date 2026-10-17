---
date: 2026-05-28
source: skills/context-mgmt/SKILL.md (extracted) + context-research.md
---

# Context Management: Deep Reference

Consult on demand. Not auto-loaded. See SKILL.md for the executable flow.

---

## Why 60%, Not 70–80%: The Fidelity Cliff

- HF Daily Papers research: solve rate drops 65%→21% when architectural mental model gets evicted from context.
- Fidelity shallowing starts at ~60% fill — the agent still produces output, but stops backtracking, exploring alternatives, or maintaining hypothesis depth.
- By the time native compaction fires (typically near limit), the degraded reasoning has already shipped to code.
- Token count is the lagging indicator. Hypothesis depth and step count are leading indicators.

---

## Compaction Strategies

### Progressive Disclosure
- Start with summary, expand on demand
- Use AgentDB for full context, conversation for highlights
- Pattern: "Details in AgentDB:contracts:{id}" or "See AgentDB:findings:{id}"

### AgentDB Offloading Pattern
When context grows heavy:
1. Write detailed findings: `agentdb learn pattern "finding" "evidence"`
2. Keep one-line summary in conversation
3. Reference: "See AgentDB:patterns for full trace"

### Compaction Format Examples
```
Before: [full exploration, multiple tool calls, iterations, dead ends]
After:  "Explored X → Found Y at path/to/file:line → Key insight: Z"

Before: [read 5 files, searched patterns, traced imports]
After:  "Traced dependency: A→B→C. Issue in B:42. Fix: add null check."
```

### Phase Transition Compaction

| Transition | Compact? | Why |
|------------|----------|-----|
| Research → Planning | Yes | Research bulk served its purpose; plan is distilled output |
| Planning → Implementation | Yes | Plan is in contract/file; free context for code |
| Implementation → Testing | Maybe | Keep if tests reference recent code |
| Debugging → Next feature | Yes | Debug traces pollute unrelated work |
| Mid-implementation | No | Losing file paths, variable names, partial state is costly |
| After failed approach | Yes | Clear dead-end reasoning before new approach |

---

## Research & Quantitative Backing

### Sources
Anthropic "Effective Context Engineering for AI Agents" (Sep 2025),
Anthropic "Effective Harnesses for Long-Running Agents" (2026),
Anthropic AWS re:Invent 2025 talks, Claude Opus 4.6 with 1M context (Feb 5, 2026),
Claude Context Windows Documentation (2026), Chroma Research "Context Rot" (Jul 2025),
MECW Paper (Jan 19, 2026, arXiv 2509.21361), GAM Dual-Agent Architecture (2025),
Mastra Observational Memory (Feb 4, 2026), ACP Protocol (Feb 2026).

### The Core Problem: Context Rot (Quantified Jan 2026)

Anthropic's research: "As the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."

Chroma Research (Jul 2025): Tested 18 models including GPT-4.1, Claude 4, Gemini 2.5. Key finding: **30%+ accuracy drops** for middle-positioned information. Models achieve highest accuracy at sequence start/end ("U-shaped curve").

MECW Paper (Jan 2026, arXiv 2509.21361): Maximum Effective Context Window is drastically different from advertised MCW. Some models failed with as little as 100 tokens in context. All tested models fell short of MCW by **>99%** in some conditions.

The agent doesn't forget because it ran out of space. It forgets because signal got drowned by accumulation.

### The Three Strategies (Anthropic)

**1. Compaction**
Summarize conversation history and reinitialize context. Claude Code does this: compresses while preserving architectural decisions, unresolved bugs, and implementation details. Lowest-hanging fruit: tool result clearing. Once a tool has been called deep in history, raw output rarely needs to be seen again.

**2. Structured Note-Taking**
External memory files (NOTES.md, active.md, AgentDB). Enable persistence across context resets. Claude playing Pokemon maintained precise tallies across thousands of game steps using structured notes. In KERNEL: AgentDB is the structured note-taking system.

**3. Multi-Agent Architectures**
Specialized sub-agents handle focused tasks with clean context windows. Research agent explores codebase in separate context, reports back summary. Main context stays clean for implementation.

### New Memory Architectures (2026)

**Observational Memory (Mastra, Feb 4, 2026)**
Two-agent system: Observer watches and records, Reflector extracts patterns. Achieves **3-40x compression** while outperforming RAG on benchmarks. Cuts costs 10x compared to long-context approaches.

**GAM Dual-Agent (NeurIPS 2025)**
Memorizer + Researcher architecture. JIT retrieval outperforms static summaries. Outperforms both RAG and long-context LLMs on benchmarks.

**Server-Side Compaction (Anthropic Beta, Jan 2026)**
Automatic context compaction when approaching token thresholds. In 100-turn evaluations: **84% token reduction** while completing workflows that would otherwise fail.

**Context Editing**
Server-side clearing of stale tool calls/results. 29% improvement alone; **39% improvement** combined with memory tool.

**Token Budget Awareness**
Claude 4.5+ receives real-time token updates after each tool call:
`<system_warning>Token usage: 35000/200000; 165000 remaining</system_warning>`

### Practical Rules for KERNEL

- CLAUDE.md: always loaded, under 150 lines. The index, not the encyclopedia.
- Rules: always loaded. Only universally applicable invariants and heuristics.
- Skills: metadata at startup (~100 tokens each). Full content on demand.
- Commands: only when user invokes.
- Reference docs: only when skill explicitly reads them.
- Delegate research to subagents. Research consumes heavy context.
- Use grep/glob/find instead of reading entire files.
- After compaction: read active.md and AgentDB to restore critical state.
- Anthropic's #1 prompt tip for 2025-2026: "90% of the time when a system doesn't work, the instructions simply don't make sense when read by someone unfamiliar with the domain."

### Two Failure Modes (Anthropic, Long-Running Agents)

1. Agent tries to do too much at once. Runs out of context mid-implementation. Next session starts with half-implemented, undocumented feature. Fix: incremental progress with commits and documentation at each step.

2. Later agent sees progress, declares the job done prematurely. Fix: explicit done-when criteria in contract. Agent must prove completion with evidence, not just observe that files exist.
