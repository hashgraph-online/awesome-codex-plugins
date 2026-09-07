# Context Engineering Reference: Research & Best Practices

Reference for managing context in agentic systems. Directly from Anthropic's
research. Read on demand. Not auto-loaded.

## Sources

Anthropic "Effective Context Engineering for AI Agents" (Sep 2025),
Anthropic "Effective Harnesses for Long-Running Agents" (2026),
Anthropic AWS re:Invent 2025 talks, Claude Opus 4.6 with 1M context (Feb 5, 2026),
Claude Context Windows Documentation (2026), Chroma Research "Context Rot" (Jul 2025),
MECW Paper (Jan 19, 2026, arXiv 2509.21361), GAM Dual-Agent Architecture (2025),
Mastra Observational Memory (Feb 4, 2026), ACP Protocol (Feb 2026).

---

## The Core Problem: Context Rot (Quantified Jan 2026)

Anthropic's research: "As the number of tokens in the context window
increases, the model's ability to accurately recall information from
that context decreases."

Chroma Research (Jul 2025): Tested 18 models including GPT-4.1, Claude 4, Gemini 2.5.
Key finding: **30%+ accuracy drops** for middle-positioned information. Models achieve
highest accuracy at sequence start/end ("U-shaped curve").

MECW Paper (Jan 2026, arXiv 2509.21361): Maximum Effective Context Window is
drastically different from advertised MCW. Some models failed with as little as
100 tokens in context. All tested models fell short of MCW by **>99%** in some conditions.

Longer context windows make things WORSE, not better. Every token competes
for attention. Critical information from step 3 gets buried by noise from
steps 4 through 40.

The agent doesn't forget because it ran out of space. It forgets because
signal got drowned by accumulation.

---

## The Three Strategies (Anthropic)

### 1. Compaction
Summarize conversation history and reinitialize context. Claude Code does
this: compresses while preserving architectural decisions, unresolved bugs,
and implementation details.

The art: what to keep vs. discard. Overly aggressive compaction loses
critical context. Start by maximizing recall, then improve precision.

Lowest-hanging fruit: tool result clearing. Once a tool has been called
deep in history, raw output rarely needs to be seen again.

### 2. Structured Note-Taking
External memory files (NOTES.md, active.md, AgentDB). Enable persistence
across context resets. Claude playing Pokemon maintained precise tallies
across thousands of game steps using structured notes.

In KERNEL: AgentDB is the structured note-taking system. Write decisions,
findings, state. Read from AgentDB when needed; don't carry everything
in conversation.

### 3. Multi-Agent Architectures
Specialized sub-agents handle focused tasks with clean context windows.
Research agent explores codebase in separate context, reports back summary.
Main context stays clean for implementation.

---

## New Memory Architectures (2026)

### Observational Memory (Mastra, Feb 4, 2026)
Two-agent system: Observer watches and records, Reflector extracts patterns.
Achieves **3-40x compression** while outperforming RAG on benchmarks.
Cuts costs 10x compared to long-context approaches.

### GAM Dual-Agent (NeurIPS 2025)
Memorizer + Researcher architecture. JIT retrieval outperforms static summaries.
Outperforms both RAG and long-context LLMs on benchmarks.

### Server-Side Compaction (Anthropic Beta, Jan 2026)
Automatic context compaction when approaching token thresholds. In 100-turn
evaluations: **84% token reduction** while completing workflows that would
otherwise fail.

### Context Editing
Server-side clearing of stale tool calls/results. 29% improvement alone;
**39% improvement** combined with memory tool. Claude Code uses this: clears
tool result clearing after each compaction.

### Token Budget Awareness
Claude 4.5+ receives real-time token updates after each tool call:
`<system_warning>Token usage: 35000/200000; 165000 remaining</system_warning>`
Enables better long-running task persistence.

---

## Two Failure Modes (Anthropic, Long-Running Agents)

1. Agent tries to do too much at once. Runs out of context mid-implementation.
   Next session starts with half-implemented, undocumented feature.
   Fix: incremental progress with commits and documentation at each step.

2. Later agent sees progress, declares the job done prematurely.
   Fix: explicit done-when criteria in contract. Agent must prove completion
   with evidence, not just observe that files exist.

---

## Practical Rules for KERNEL

- CLAUDE.md: always loaded, under 150 lines. The index, not the encyclopedia.
- Rules: always loaded. Only universally applicable invariants and heuristics.
- Skills: metadata at startup (~100 tokens each). Full content on demand.
- Commands: only when user invokes.
- Reference docs: only when skill explicitly reads them.

Progressive disclosure at every layer. If information isn't needed for the
current step, don't read it into context.

- Delegate research to subagents. Research consumes heavy context.
- Use grep/glob/find instead of reading entire files.
- Offer handoff proactively at ~70% context usage.
- After compaction: read active.md and AgentDB to restore critical state.
- Anthropic's #1 prompt tip for 2025-2026: "90% of the time when a system
  doesn't work, the instructions simply don't make sense when read by
  someone unfamiliar with the domain."
