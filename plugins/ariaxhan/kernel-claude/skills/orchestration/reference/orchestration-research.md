# Orchestration Reference: Research & Best Practices

Reference for multi-agent coordination, the KERNEL architecture's foundation.
Read on demand. Not auto-loaded.

## Sources

Anthropic "Building Effective Agents" (Dec 2024), Anthropic "Effective Context
Engineering" (Sep 2025), Anthropic "Effective Harnesses for Long-Running Agents"
(2026), Anthropic 2026 Agentic Coding Trends Report (Feb 2026), Microsoft Agent
Framework (Feb 2026), Azure AI Agent Design Patterns (Feb 12, 2026), Google ADK
context-aware multi-agent framework (Dec 2025), OpenAI Agents SDK handoff patterns,
LangGraph agent supervisor patterns, A2A Protocol (Linux Foundation, 2026).

---

## Anthropic's Core Principle

"The most successful implementations use simple, composable patterns rather
than complex frameworks." And: "Do the simplest thing that works."

An agent is: an LLM autonomously using tools in a loop. Everything else
is orchestration around that core loop.

---

## Orchestration Patterns

### Sequential (Pipeline)
A → B → C → D. Each stage passes output to next.
When: clear dependencies, deterministic order.
Risk: single failure blocks everything downstream.
KERNEL use: tier 2 flow (surgeon → review).

### Parallel (Fan-out/Fan-in)
A, B, C run simultaneously. Results merged.
When: independent subtasks, no shared state.
Risk: merge conflicts, inconsistent results.
KERNEL use: parallel_orchestration for independent file groups.

### Supervisor (Hierarchical)
Orchestrator delegates to specialized workers, reviews results.
When: tasks require different expertise, quality gate needed.
Risk: orchestrator becomes bottleneck, context accumulates.
KERNEL use: the entire KERNEL architecture (orchestrator + agents).

### Adversarial (Verify)
Builder creates, verifier assumes broken, proves otherwise.
When: high-stakes changes, need confidence before shipping.
Risk: adversary too lenient (rubber stamp) or too strict (blocks everything).
KERNEL use: tier 3 flow (surgeon → adversary).

### Magentic (Dynamic) — NEW Feb 2026
Manager agent dynamically builds and refines task ledger.
Microsoft Agent Framework formalizes this pattern:
- Manager builds/refines task ledger dynamically
- Supports backtracking and iteration
- Includes stall detection and progress assessment
- Human-in-the-loop for plan review before execution
When: open-ended problems without predetermined solution path.
Risk: slow to converge, can stall on ambiguous goals.
KERNEL use: potential tier 3+ for exploratory features.

---

## Interoperability Standards (2026)

### Model Context Protocol (MCP)
Vertical integration: agent to tools. Standardizes tool discovery and invocation.
Adopted by OpenAI, Google, Microsoft, Anthropic. Now industry standard.

### Agent-to-Agent (A2A)
Horizontal integration: agent to agent. Standardizes cross-agent communication.
Launched by Google April 2025, now governed by Linux Foundation's Agentic AI
Foundation. Adopted by 50+ partners including Salesforce, PayPal, Atlassian.
Analogy: "MCP is USB-C for AI, A2A is HTTP for AI agents."

---

## Handoff Patterns (Between Agents)

### Context Transfer
Full history passed to next agent. Simple but wasteful.
Google ADK: "In default mode, ADK passes full contents of the caller's
working context." In none mode, sub-agent sees no prior history.

### Structured Briefing
Only essential state transferred: objectives, constraints, decisions, evidence.
More efficient but requires careful design of what's "essential."
KERNEL use: AgentDB as structured briefing mechanism.

### Narrative Casting (Google ADK)
Prior "Assistant" messages re-cast as narrative context. Tool calls from
other agents marked or summarized. Each agent assumes "Assistant" role
without misattributing the broader system's history to itself.

---

## The 4 Fault Tolerance Layers

From production agent research (DEV.to, Mar 2, 2026):

1. Retry with backoff: catches transient errors (503s, timeouts).
   Implementation: `RetryPolicy` with exponential backoff (0.5s initial, 2.0x factor, jitter).
2. Model/agent fallback: catches provider outages or agent failures.
   Implementation: `ModelFallbackMiddleware` maintaining conversation context.
3. Error classification: routes errors correctly (transient vs. logic vs. human-needed).
   Categories: transient, LLM-recoverable, user-fixable, unexpected.
4. Checkpointing: survives crashes by restoring from saved state.
   Recovery strategies: exact point restore vs. MessageHistoryOnly restart.

Without all four, you have gaps. Metric: "Unrecoverable failures decreased from
23% to under 2%" after implementing all 4 layers (DEV.to 2026).

KERNEL implements:
- Retry: error_recovery protocol with max 3x backoff.
- Fallback: re-spawn surgeon with new context on failure.
- Classification: 5 failure types (transient, scope, test, blocked, divergent).
- Checkpointing: AgentDB write-end is mandatory for every agent.

---

## Common Multi-Agent Failure Modes

### Context Loss Between Agents
Agent A's reasoning doesn't transfer to Agent B. B starts from scratch
or makes different assumptions. This is the #1 failure mode.
Fix: AgentDB. Structured state, not conversation summaries.

### Cascading Bad Output
Agent A produces subtly wrong output. Agent B builds on it. Agent C
validates A's assumptions. Error compounds through the pipeline.
Fix: output validation at every stage. KERNEL requires checkpoint
field validation before passing downstream.

### Scope Creep Across Agents
Surgeon touches files outside contract. Adversary fixes bugs instead
of documenting them. Orchestrator writes code for tier 2+.
Fix: explicit role constraints. Anti-patterns enforced per agent.

### Silent Failure
Agent writes nothing to AgentDB. Orchestrator assumes completion.
Reality: agent errored out, was blocked, or produced nothing.
Fix: never assume completion without reading AgentDB entry.

---

## Context Transfer Problem (Feb 2026)

Key insight from 2026 research: "Agent B doesn't know what Agent A considered
and rejected. It doesn't know the constraints that shaped the implementation."

"Every agent boundary is a lossy compression of context" - adding agents creates
coordination overhead similar to Brooks's mythical man-month.

Solution framework:
1. Keep looping within single agent when context accumulation matters.
2. Split only when boundaries are "clean interfaces, not shared context."
3. Evaluate: Does downstream work need to understand WHY, or just WHAT?

---

## Microsoft Agent Framework (Feb 2026)

Merges Semantic Kernel and AutoGen into a single framework. Provides 5 built-in
orchestration patterns: Sequential, Concurrent, Handoff, Group Chat, Magentic.
Reached Release Candidate status (API stable). Supports .NET and Python.

Start simple complexity levels:
| Level | Description |
|-------|-------------|
| Direct model call | Single LLM call, no agent |
| Single agent with tools | One agent, dynamic tool use |
| Multi-agent orchestration | Multiple specialized agents |

---

## Azure's Agent Design Guidelines (Microsoft, Feb 2026)

- Validate agent output before passing to next agent. Low-confidence,
  malformed, or off-topic responses cascade through a pipeline.
- Consider circuit breaker patterns for agent dependencies.
- Surface errors instead of hiding them.
- Implement timeout and retry mechanisms.
- Include graceful degradation for agent faults.
- Design agents to be as isolated as practical from each other.

---

## KERNEL Integration

This reference IS the KERNEL architecture's theoretical foundation.
Every design decision maps to patterns above:

- Tier system: determines which orchestration pattern applies.
- AgentDB: implements structured briefing handoff pattern.
- Contract format: defines scope to prevent scope creep.
- Error recovery: implements all 4 fault tolerance layers.
- Output validation: prevents cascading bad output.
- Anti-patterns: prevent scope creep and silent failure.
- Adversary agent: implements adversarial verification pattern.
- Parallel orchestration: implements fan-out/fan-in with merge.

---

## max_budget_usd Invariant (moved from SKILL.md 2026-05-28)

`max_budget_usd` is mandatory infrastructure, not optional config. Treat it like a circuit
breaker, not a preference. One stuck retry loop at $0.40-0.60/query × hundreds of retries
becomes a silent four-figure invoice. The cap is the only thing standing between you and that.

Required for:
- Any /kernel:forge autonomous run (heat → hammer → quench → temper → anneal loops)
- Any multi-agent spawn (tier 2+) where total cost is unbounded by the human in the loop
- Any "run overnight" or "let it iterate until done" pattern
- Any agentdb antibody-search-driven loop where match counts determine spawn counts

Why this is an invariant, not a guideline: cost overruns are silent until billing fires.
There is no in-session signal that something is going wrong. The cap is the signal.

---

## Entropy Adaptive — Detail (moved from SKILL.md 2026-05-28)

entropy signals:
- agentdb learning count in domain (high count = low entropy)
- test coverage for affected files (high coverage = low entropy)
- number of recent failures in domain (high failures = high entropy)
- file co-change complexity (many co-changes = high entropy)
- triage agent classification (low/medium/high/epic)

adaptation detail:
  low_entropy:
    skip: researcher, scout
    use: surgeon directly (tier 1 behavior even for tier 2 file counts)
    rationale: known territory, don't waste tokens on research

  medium_entropy:
    standard: researcher → surgeon → validator
    skip: adversary (unless security-sensitive)
    rationale: some unknowns but manageable risk

  high_entropy:
    full: researcher + scout → triage → surgeon → adversary → reviewer
    add: coroner on failure (automatic post-mortem)
    rationale: maximum coverage, expect failures, learn from them

integration:
- triage agent outputs entropy estimate alongside complexity
- forge heat phase measures entropy before choosing approach count
- ingest classify step uses entropy to decide research depth

rule: entropy decreases as learnings accumulate. Reward the system for learning.

---

## Checkpoint Schema (moved from SKILL.md 2026-05-28)

checkpoint_schema:
  agent_id: which agent was working
  step: last completed step number
  state: JSON blob of current progress
  files_modified: list of files changed so far
  tests_passing: count of passing tests at this point
  timestamp: when checkpoint was written

integration:
- surgeon writes checkpoint after each file modification
- forge checks for checkpoint before each heat cycle
- orchestrator reads checkpoint to determine resume point

---

## Budget Tracking Detail (moved from SKILL.md 2026-05-28)

tracking:
- agentdb emit tracks token usage per agent per session
- orchestrator monitors cumulative cost across spawned agents
- budget injected into agent context: "Remaining budget: ~{N} tokens"

self_regulation:
- agent sees remaining budget in injected context
- high budget: explore multiple approaches
- low budget: pick simplest viable approach
- exhausted: checkpoint and report to human
