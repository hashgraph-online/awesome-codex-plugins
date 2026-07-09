# Design It Twice

Ousterhout ("A Philosophy of Software Design"): your first idea is rarely the best. Use during brainstorming Step 3 when designing something new or choosing a new approach; skip when tweaking existing code.

## 1 — Requirements

What problem, who the callers are, key operations, constraints, what stays hidden vs exposed. If missing, return to Step 2 Q&A — don't design blind.

## 2 — Generate 2-3 divergent designs

Spawn 2-3 parallel subagents (`Task` tool, single message; on Codex `spawn_agent(agent_type="worker", message=…)` — see `../../using-development-skills/references/codex-tools.md`; sequential in-thread if unavailable). Each designs only the interface shape, not implementation. Assign one **orthogonal constraint** per agent to force divergence:

- **A:** minimize method count (1-3 max)
- **B:** maximize flexibility (many use cases)
- **C:** optimize the common case (common path trivially simple, edge cases may be verbose)
- **D** (optional): take inspiration from [specific paradigm/library]

Each returns: interface signature · caller usage example · what it hides internally · trade-offs.

## 3 — Present, compare, synthesize

Show each design sequentially (signature, usage, what it hides) so the user absorbs it before comparison. Compare in prose (not tables), focused on where they diverge most; favor depth (small interface hiding much over large interface, thin implementation).

The best design usually combines insights. Ask which fits the primary use case and which elements from others to fold in. Final decision → return to Step 5+ of brainstorming.
