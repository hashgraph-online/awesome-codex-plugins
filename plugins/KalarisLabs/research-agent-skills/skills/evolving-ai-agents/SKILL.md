---
name: evolving-ai-agents
description: Provides guidance for automatically evolving and optimizing AI agents across any domain using LLM-driven evolution algorithms. Use when building self-improving agents, optimizing agent prompts and skills against benchmarks, or implementing automated agent evaluation loops.
license: MIT
metadata:
  version: 1.0.0
  category: llm-applications
  maintainer: Kalaris Labs
  contributor: A-EVO Lab
  tags: Agent Evolution, Self-Improving Agents, Prompt Optimization, LLM, Benchmark Evaluation, Skill Discovery, Agentic AI
  dependencies: a-evolve>=0.1.0, pyyaml>=6.0
---

# Evolving AI Agents with A-Evolve

## Overview

A-Evolve is universal infrastructure for evolving any AI agent across any domain using any evolution algorithm with zero manual engineering. It represents all evolvable agent state as files (prompts, skills, memory, tools), runs iterative solve-observe-evolve cycles against benchmarks, and uses LLM-driven mutation to improve agent performance automatically.

**Benchmark results** (Claude Opus 4.6):
- MCP-Atlas: 79.4% (#1)
- SWE-bench Verified: 76.8% (~#5)
- Terminal-Bench 2.0: 76.5% (~#7)
- SkillsBench: 34.9% (#2)

## When to Use A-Evolve

**Use A-Evolve when:**
- Optimizing agent prompts, skills, or memory against a measurable benchmark
- Building self-improving agents with automated gating and rollback
- Evolving domain-specific tool usage and procedures through LLM-driven mutation
- Running iterative solve-observe-evolve loops to maximize agent performance
- Needing reproducible, git-versioned evolution history for every change

**Key differentiator**: Other frameworks _build_ agents; A-Evolve _optimizes_ them. It sits on top of any agent framework and makes it better through automated evolution.

**Do NOT use A-Evolve for:**
- Building multi-agent orchestration from scratch (use CrewAI, LangGraph)
- One-shot agent tasks with no iteration needed (use LangChain, LlamaIndex)
- RAG pipeline optimization (use LlamaIndex, Chroma)
- Prompt-only optimization without skill/memory evolution (use DSPy)

## Quick Start

### Installation

```bash
pip install a-evolve                    # Core
pip install a-evolve[anthropic]         # With Claude support
pip install a-evolve[all]               # All providers
```

### Three-Line Evolution

```python
import agent_evolve as ae

evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
results = evolver.run(cycles=10)
print(f"Final score: {results.final_score}")
```

This copies the built-in SWE seed workspace, runs 10 evolution cycles against SWE-bench Verified, and returns the optimized agent.

## Core Concepts

### The Agent Workspace

All evolvable state lives as files in a workspace directory:

```
my-agent/
├── manifest.yaml          # Metadata + entrypoint
├── prompts/
│   ├── system.md          # Main system prompt (evolved)
│   └── fragments/         # Modular prompt pieces
├── skills/
│   └── skill-name/
│       └── SKILL.md       # Reusable procedure with frontmatter
├── memory/
│   ├── episodic.jsonl     # Lessons from failures
│   └── semantic.jsonl     # General knowledge
├── tools/
│   ├── registry.yaml      # Tool manifest
│   └── tool_name.py       # Tool implementations
└── evolution/             # Managed by engine (metrics, history)
```

### The Evolution Loop

Each cycle follows five phases:

1. **Solve** — Agent processes a batch of tasks from the benchmark
2. **Observe** — Benchmark evaluates trajectories, producing (task, trajectory, feedback) triples
3. **Evolve** — Evolution engine mutates workspace files based on observations
4. **Gate** — Validate mutations (git snapshot before/after for rollback)
5. **Reload** — Agent reinitializes from evolved filesystem state

### Three Pluggable Interfaces

```python
# 1. Agent — implements solve()
class MyAgent(ae.BaseAgent):
    def solve(self, task: ae.Task) -> ae.Trajectory:
        # Domain-specific solving logic
        return ae.Trajectory(task_id=task.id, output=result, steps=steps)

# 2. Benchmark — implements get_tasks() and evaluate()
class MyBenchmark(ae.BenchmarkAdapter):
    def get_tasks(self, split="train", limit=None) -> list[ae.Task]:
        return [ae.Task(id="1", input="...")]

    def evaluate(self, task: ae.Task, trajectory: ae.Trajectory) -> ae.Feedback:
        return ae.Feedback(success=True, score=0.95, detail="Passed")

# 3. Engine — implements step()
class MyEngine(ae.EvolutionEngine):
    def step(self, workspace, observations, history, trial):
        # Mutate workspace based on observations
        return ae.StepResult(mutated=True, summary="Updated prompts")
```

## Workflow 1: Evolve an Existing Agent

**Use when**: You have a working agent and want to optimize it against a benchmark.

**Critical Requirements:**
- [ ] Agent implements `BaseAgent.solve()` returning `Trajectory`
- [ ] Benchmark implements `BenchmarkAdapter` with `get_tasks()` and `evaluate()`
- [ ] Seed workspace has `manifest.yaml` with entrypoint and evolvable layers
- [ ] System prompt exists at `prompts/system.md`
- [ ] Workspace is a git repo (run `git init && git add -A && git commit -m "init"`)

### Steps

```python
import agent_evolve as ae

# Configure evolution parameters
config = ae.EvolveConfig(
    batch_size=10,           # Tasks per solve round
    max_cycles=20,           # Maximum evolution iterations
    evolve_prompts=True,     # Mutate system prompt
    evolve_skills=True,      # Discover and refine skills
    evolve_memory=True,      # Build episodic memory
    evolver_model="us.anthropic.claude-opus-4-6-v1",
)

# Point to your agent workspace and benchmark
evolver = ae.Evolver(
    agent="./my-agent-workspace",
    benchmark="swe-verified",     # Or custom BenchmarkAdapter instance
    config=config,
)

# Run evolution
results = evolver.run(cycles=10)

# Inspect results
print(f"Cycles completed: {results.cycles_completed}")
print(f"Final score: {results.final_score}")
print(f"Converged: {results.converged}")
for cycle_num, score in enumerate(results.score_history):
    print(f"  Cycle {cycle_num + 1}: {score:.3f}")
```

### Post-Evolution

The workspace is now optimized. Inspect what changed:

```bash
cd my-agent-workspace
git log --oneline              # See evo-1, evo-2, ... tags
git diff evo-1 evo-10          # Compare first and last evolution
cat prompts/system.md          # Read evolved prompt
ls skills/                     # See discovered skills
```

## Workflow 2: Add a Custom Benchmark

**Use when**: You want to evolve agents on your own domain-specific tasks.

**Critical Requirements:**
- [ ] Define task format (inputs, expected outputs)
- [ ] Implement scoring logic (0.0–1.0 scale)
- [ ] Prepare task dataset (train + holdout split)

### Steps

```python
import agent_evolve as ae

class CodeReviewBenchmark(ae.BenchmarkAdapter):
    """Evaluate agents on code review quality."""

    def get_tasks(self, split="train", limit=None):
        tasks = load_review_dataset(split)
        if limit:
            tasks = tasks[:limit]
        return [
            ae.Task(id=t["id"], input=t["diff"], metadata={"expected": t["comments"]})
            for t in tasks
        ]

    def evaluate(self, task, trajectory):
        expected = task.metadata["expected"]
        actual = trajectory.output
        precision, recall = compute_review_metrics(expected, actual)
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        return ae.Feedback(
            success=f1 > 0.7,
            score=f1,
            detail=f"P={precision:.2f} R={recall:.2f} F1={f1:.2f}",
        )

# Use with any agent
evolver = ae.Evolver(agent="./my-agent", benchmark=CodeReviewBenchmark())
results = evolver.run(cycles=5)
```

## Workflow 3: Create a Custom Evolution Engine

**Use when**: The default LLM-driven mutation doesn't suit your domain.

### Steps

```python
import agent_evolve as ae

class RuleBasedEngine(ae.EvolutionEngine):
    def step(self, workspace, observations, history, trial):
        failures = [o for o in observations if not o.feedback.success]
        if not failures:
            return ae.StepResult(mutated=False, summary="No failures to address")

        # Analyze failure patterns
        error_types = categorize_errors(failures)
        prompt = workspace.read_prompt()

        # Append learned rules to prompt
        new_rules = generate_rules(error_types)
        workspace.write_prompt(prompt + "\n" + new_rules)

        return ae.StepResult(
            mutated=True,
            summary=f"Added {len(new_rules)} rules from {len(failures)} failures",
        )

evolver = ae.Evolver(
    agent="./my-agent",
    benchmark="my-benchmark",
    engine=RuleBasedEngine(),
)
```

## Built-in Components

### Seed Agents

| Agent | Domain | Model | Key Feature |
|-------|--------|-------|-------------|
| `swe` | SWE-bench | Claude Opus 4.6 | Verify-fix loop, skill proposals |
| `terminal` | Terminal-Bench | Claude Sonnet 4 | Concurrent timeout, env discovery |
| `mcp` | MCP-Atlas | Claude Opus 4.6 | MCP server integration |

### Benchmarks

| Name | Domain | Metric |
|------|--------|--------|
| `swe-verified` | Code patching | Pass rate |
| `mcp-atlas` | Tool calling | Accuracy |
| `terminal2` | Shell tasks | Pass rate |
| `skill-bench` | Multi-step procedures | Accuracy |
| `arc-agi-3` | Interactive games | RHAE score |

### Evolution Algorithms

| Algorithm | Strategy | Best For |
|-----------|----------|----------|
| A-Evolve/SkillForge | LLM-driven workspace mutation | General-purpose |
| Guided Synthesis | Memory-first, curated skills | Skill discovery |
| Adaptive Evolution | Reward tracking, filtered observations | Fine-grained control |
| Adaptive Skill | Skill-centric refinement | Skill-heavy domains |

## Configuration Reference

```python
ae.EvolveConfig(
    batch_size=10,              # Tasks per solve round
    max_cycles=20,              # Max evolution iterations
    holdout_ratio=0.2,          # Test set split for gating
    evolve_prompts=True,        # Mutate system prompts
    evolve_skills=True,         # Discover/refine skills
    evolve_memory=True,         # Build episodic memory
    evolve_tools=False,         # Mutate tool implementations
    trajectory_only=False,      # Hide scores from evolver
    evolver_model="us.anthropic.claude-opus-4-6-v1",
    evolver_max_tokens=16384,
    egl_threshold=0.05,         # Convergence epsilon
    egl_window=3,               # Cycles for plateau detection
)
```

**Convergence**: Evolution stops early when score improvement is less than `egl_threshold` over the last `egl_window` cycles.

## Skill Format

Skills are reusable procedures discovered and refined during evolution:

```markdown
---
name: verify-edge-cases
description: "TRIGGER when: checking boundary conditions. DO NOT TRIGGER: for happy-path tests."
---

## Pattern
Test all falsy-but-valid values: 0, False, "", [], {}

## Process
1. List all input boundaries
2. Run each against the implementation
3. Check both output AND side effects
```

Skills accumulate in the workspace `skills/` directory. The evolver curates them: ACCEPT new skills, MERGE overlapping ones, SKIP redundant proposals. Target: 5–10 broad skills, not 30 narrow ones.

## Common Issues

### Evolution score plateaus early

**Cause**: Batch size too small or evolver doesn't see enough failure diversity.
**Fix**: Increase `batch_size` (try 15–20) and ensure benchmark tasks cover diverse failure modes. Set `trajectory_only=False` so the evolver sees scores.

### Agent workspace grows too large

**Cause**: Skill library bloat from accepting every proposal.
**Fix**: The default SkillForge engine curates skills automatically. If using a custom engine, implement merging logic to consolidate overlapping skills.

### Git conflicts during evolution

**Cause**: Multiple evolution runs on the same workspace.
**Fix**: Each `evolver.run()` should operate on its own workspace copy. Use `Evolver(agent="seed-name")` to auto-copy the seed each time.

### LLM provider errors during evolution

**Cause**: Rate limits or authentication issues with the evolver model.
**Fix**: Check `evolver_model` config. For Bedrock, ensure AWS credentials are configured. For Anthropic, set `ANTHROPIC_API_KEY`.

### Custom agent not picking up evolved state

**Cause**: Agent doesn't implement `reload_from_fs()`.
**Fix**: Override `reload_from_fs()` in your `BaseAgent` subclass to re-read prompts, skills, and memory from the workspace after each evolution cycle.

## Usage Instructions for Agents

When this skill is loaded:

1. **Read this entire file** before implementing any evolution workflow
2. **Start with the Quick Start** — get a minimal evolution running before customizing
3. **Use built-in seeds when possible** — `"swe"`, `"terminal"`, `"mcp"` have battle-tested configurations
4. **Always initialize git** in custom workspaces before running evolution
5. **Check convergence settings** — default `egl_threshold=0.05` with `egl_window=3` may be too aggressive for your domain
6. **Inspect evolved state** after each run — read `prompts/system.md` and `skills/` to understand what the evolver learned

**Pro Tips:**
- Set `trajectory_only=False` (default) so the evolver sees scores — this accelerates learning
- Start with `batch_size=10` and adjust based on task diversity
- Use `holdout_ratio=0.2` to prevent overfitting to training tasks
- After evolution, `git diff evo-1 evo-N` shows the cumulative effect of all mutations
- If the evolver isn't finding skills, enrich `feedback.detail` strings with specific failure reasons

**Warning Signs:**
- Score oscillating between cycles → benchmark evaluation may be non-deterministic
- Skills directory growing past 15+ skills → engine isn't merging/curating properly
- Prompt growing past 10K chars → evolution is appending without refactoring
- `converged=True` after 2-3 cycles → increase `egl_window` and decrease `egl_threshold`

## References

- **Architecture deep dive**: See [references/architecture.md](references/architecture.md)
- **API reference**: See [references/api.md](references/api.md)
- **Step-by-step tutorials**: See [references/tutorials.md](references/tutorials.md)
- **Real-world examples**: See [references/examples.md](references/examples.md)
- **GitHub issues & solutions**: See [references/issues.md](references/issues.md)
- **Design patterns**: See [references/design-patterns.md](references/design-patterns.md)
- **Release history**: See [references/releases.md](references/releases.md)

## Related skills

- `autogpt-agents`: Autonomous AI agent platform for building and deploying continuous agents.
- `research-skill-creator`: Create, improve and test agent skills for research workflows (paper writing, lab protocols, analysis pipelines, domain databases) that meet…
- `dspy`: Builds and optimizes language model programs with DSPy (Stanford NLP), using Signatures, modules (Predict, ChainOfThought, ReAct, ProgramOf…
