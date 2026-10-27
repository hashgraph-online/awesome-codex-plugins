# A-Evolve Official Documentation Reference

> This document consolidates key information from the official A-Evolve documentation
> at [github.com/A-EVO-Lab/a-evolve](https://github.com/A-EVO-Lab/a-evolve).

## Table of Contents

- [Project Overview](#project-overview)
- [Installation Guide](#installation-guide)
- [Quick Start Guide](#quick-start-guide)
- [Architecture Overview](#architecture-overview)
- [Agent Protocol](#agent-protocol)
- [Benchmark Adapters](#benchmark-adapters)
- [Evolution Engines](#evolution-engines)
- [Workspace Contract](#workspace-contract)
- [Configuration Reference](#configuration-reference)
- [Built-in Agents](#built-in-agents)
- [Built-in Benchmarks](#built-in-benchmarks)
- [Evolution Algorithms](#evolution-algorithms)
- [Skill System](#skill-system)
- [Memory System](#memory-system)
- [Version Control](#version-control)
- [Observation Pipeline](#observation-pipeline)
- [FAQ](#faq)

---

## Project Overview

A-Evolve is the universal infrastructure for evolving AI agents through self-improvement. It enables automatic, data-driven optimization of agents across any domain using any evolution algorithm.

### Design Principles

1. **File-system as contract**: All evolvable agent state lives as plain files in a workspace directory. No databases, no learned weights, no opaque parameters. Every mutation is an explicit edit to a text file.

2. **Pluggable everything**: Three interfaces — `BaseAgent`, `BenchmarkAdapter`, `EvolutionEngine` — enable any combination of agent, benchmark, and algorithm.

3. **Git for versioning**: Every evolution cycle creates git snapshots. Changes are diffable, rollbackable, and human-readable.

4. **LLM-in-the-loop**: The default evolution engine uses an LLM with bash tools to analyze observations and directly mutate workspace files. The evolver is itself an AI agent improving other AI agents.

5. **Zero manual engineering**: Once configured, evolution runs autonomously. The loop handles solving, evaluation, mutation, gating, and convergence detection.

### Key Results

Using Claude Opus 4.6 as both the solver and evolver model:

| Benchmark | Score | Leaderboard Position |
|-----------|-------|---------------------|
| MCP-Atlas | 79.4% | #1 |
| SWE-bench Verified | 76.8% | ~#5 |
| Terminal-Bench 2.0 | 76.5% | ~#7 |
| SkillsBench | 34.9% | #2 |

These results demonstrate that LLM-driven evolution of prompts, skills, and memory can produce state-of-the-art agent performance across diverse domains.

---

## Installation Guide

### Requirements

- Python >= 3.11
- Git (for workspace versioning)
- An LLM API key (Anthropic, OpenAI, or AWS Bedrock credentials)

### Installation Options

```bash
# Core package (matplotlib, pyyaml)
pip install a-evolve

# With specific LLM provider support
pip install a-evolve[anthropic]     # Anthropic Claude API
pip install a-evolve[openai]        # OpenAI API
pip install a-evolve[bedrock]       # AWS Bedrock (boto3)
pip install a-evolve[litellm]       # Multi-provider via LiteLLM

# With domain-specific dependencies
pip install a-evolve[swe]           # SWE-bench (strands-agents, datasets, swebench)
pip install a-evolve[mcp]           # MCP-Atlas (mcp, strands-agents, litellm)
pip install a-evolve[skillbench]    # SkillsBench (strands-agents)

# Everything
pip install a-evolve[all]

# Development
pip install a-evolve[dev]           # pytest, ruff, hypothesis
```

### From Source

```bash
git clone https://github.com/A-EVO-Lab/a-evolve.git
cd a-evolve
pip install -e ".[all,dev]"
```

### Verifying Installation

```python
import agent_evolve as ae
print(ae.__version__)  # Should print version
print(ae.Evolver)      # Should print class reference
```

---

## Quick Start Guide

### 3-Line Evolution

```python
import agent_evolve as ae

evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
results = evolver.run(cycles=10)
print(f"Final score: {results.final_score}")
```

This:
1. Copies the built-in SWE seed workspace to a working directory
2. Instantiates `SweAgent` from the workspace manifest
3. Runs 10 evolution cycles against SWE-bench Verified
4. Returns `EvolutionResult` with scores, convergence status, and details

### With Custom Configuration

```python
import agent_evolve as ae

config = ae.EvolveConfig(
    batch_size=15,              # 15 tasks per cycle
    max_cycles=25,              # Up to 25 evolution rounds
    evolve_prompts=True,        # Mutate system prompt
    evolve_skills=True,         # Discover and refine skills
    evolve_memory=True,         # Build episodic memory
    holdout_ratio=0.2,          # 20% held out for validation
    evolver_model="us.anthropic.claude-opus-4-6-v1",
    egl_threshold=0.02,         # Stop if < 2% improvement
    egl_window=5,               # Over 5 consecutive cycles
)

evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    config=config,
)
results = evolver.run()

# Inspect results
print(f"Cycles: {results.cycles_completed}")
print(f"Score: {results.final_score:.3f}")
print(f"Converged: {results.converged}")
print(f"Score history: {results.score_history}")
```

---

## Architecture Overview

### System Diagram

```
User Code (3 lines)
    │
    ▼
┌──────────────────────────────────────┐
│            Evolver API               │
│  - Resolves agent, benchmark, config │
│  - Creates EvolutionLoop             │
│  - Returns EvolutionResult           │
└──────────────┬───────────────────────┘
               │
    ┌──────────▼──────────┐
    │   EvolutionLoop     │
    │  For each cycle:    │
    │  1. Solve           │
    │  2. Observe         │
    │  3. Snapshot        │
    │  4. Evolve          │
    │  5. Snapshot        │
    │  6. Record          │
    │  7. Reload          │
    │  8. Converge?       │
    └──────────┬──────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
 Agent    Benchmark    Engine
solve()  evaluate()   step()
    │          │          │
    └──────────┼──────────┘
               │
               ▼
       Agent Workspace
       (filesystem + git)
```

### Component Interactions

**Forward flow (solve):**
1. `EvolutionLoop` calls `benchmark.get_tasks()` to get a batch of tasks
2. For each task, calls `agent.solve(task)` to get a `Trajectory`
3. Calls `benchmark.evaluate(task, trajectory)` to get `Feedback`
4. Bundles into `Observation(task, trajectory, feedback)` triples

**Evolution flow (mutate):**
1. `EvolutionLoop` passes observations to `engine.step()`
2. Engine reads workspace files, analyzes observations
3. Engine mutates workspace files (prompts, skills, memory)
4. Returns `StepResult(mutated, summary, metadata)`

**Reload flow (sync):**
1. `EvolutionLoop` calls `agent.reload_from_fs()`
2. Agent re-reads prompts, skills, memory from workspace
3. Next cycle uses evolved state

---

## Agent Protocol

### BaseAgent Abstract Class

All evolvable agents inherit from `BaseAgent`:

```python
from agent_evolve.protocol.base_agent import BaseAgent
from agent_evolve.types import Task, Trajectory

class MyAgent(BaseAgent):
    def __init__(self, workspace_dir: str):
        super().__init__(workspace_dir)
        # Initialize your LLM client, tools, etc.

    def solve(self, task: Task) -> Trajectory:
        """Solve a single task and return the trajectory.

        This is the only method you MUST override.
        """
        # Your solving logic here
        return Trajectory(
            task_id=task.id,
            output="solution",
            steps=[{"tool": "llm", "action": "generate"}],
        )
```

### Agent Lifecycle

1. **Construction**: `__init__(workspace_dir)` — set up LLM client, load initial state
2. **State loading**: `reload_from_fs()` — read prompts, skills, memory from workspace
3. **Solving**: `solve(task)` — process one task, return trajectory
4. **Memory buffering**: `remember(content, category)` — store lessons during solve
5. **State export**: `export_to_fs()` — flush buffered memories and skill proposals
6. **Hot reload**: `reload_from_fs()` — re-read after evolution mutates files

### Agent Properties

| Property | Type | Description |
|----------|------|-------------|
| `system_prompt` | `str` | Content of `prompts/system.md` |
| `skills` | `list[SkillMeta]` | Available skills from `skills/` directory |
| `memories` | `list[dict]` | Loaded episodic/semantic memories |

### Agent Best Practices

1. **Always use `self.system_prompt`** — don't hardcode prompts
2. **Inject skills into LLM context** — they're the primary evolution mechanism
3. **Call `remember()` for reusable lessons** — not for task-specific notes
4. **Keep `solve()` deterministic** when possible (temperature=0 for reproducibility)
5. **Truncate trajectories** — don't store full conversation if not needed for evolution

---

## Benchmark Adapters

### BenchmarkAdapter Abstract Class

```python
from agent_evolve.benchmarks.base import BenchmarkAdapter
from agent_evolve.types import Task, Trajectory, Feedback

class MyBenchmark(BenchmarkAdapter):
    def get_tasks(self, split="train", limit=10):
        """Return tasks from the benchmark dataset.

        Args:
            split: "train" or "test" (for holdout evaluation)
            limit: Maximum number of tasks to return (default 10)
        """
        return [Task(id="1", input="task description")]

    def evaluate(self, task, trajectory):
        """Evaluate an agent's trajectory on a task.

        Returns Feedback with:
        - success: bool (binary pass/fail)
        - score: float (0.0 to 1.0 continuous)
        - detail: str (human-readable explanation)
        """
        return Feedback(success=True, score=0.9, detail="Passed 9/10 tests")
```

### Benchmark Best Practices

1. **Rich feedback details** — the evolver reads `feedback.detail` to decide what to mutate
2. **Deterministic evaluation** — same input should produce same score
3. **Diverse task coverage** — include easy, medium, and hard tasks
4. **Strict train/test split** — no overlap between splits
5. **Score granularity** — continuous scores (0.0-1.0) are more useful than binary pass/fail

---

## Evolution Engines

### EvolutionEngine Abstract Class

```python
from agent_evolve.engine.base import EvolutionEngine
from agent_evolve.types import StepResult

class MyEngine(EvolutionEngine):
    def step(self, workspace, observations, history, trial):
        """Mutate the workspace based on observations.

        Args:
            workspace: AgentWorkspace — typed I/O for agent files
            observations: list[Observation] — recent (task, trajectory, feedback) triples
            history: EvolutionHistory — query past cycles and workspace versions
            trial: TrialRunner — optional live evaluation runner

        Returns:
            StepResult with mutated flag, summary, and metadata
        """
        # Analyze observations, mutate workspace
        return StepResult(mutated=True, summary="Updated prompts")

    def on_cycle_end(self, accepted: bool, score: float):
        """Optional callback after gating decision."""
        pass
```

### Engine Selection Guide

| Engine | When to Use | Compute Cost |
|--------|-------------|-------------|
| AEvolveEngine (default) | General-purpose, diverse domains | High (full LLM call) |
| GuidedSynthesisEngine | Skill discovery focus | Medium |
| AdaptiveEvolutionEngine | Noisy evaluation, fine control | Medium |
| AdaptiveSkillEngine | Skill-heavy domains | Medium |
| Custom | Domain-specific mutation logic | Variable |

---

## Workspace Contract

### Directory Structure

```
workspace/
├── manifest.yaml              # Required: agent metadata
├── prompts/
│   ├── system.md              # Main system prompt
│   └── fragments/             # Modular prompt pieces
│       ├── reasoning.md
│       └── output_format.md
├── skills/
│   ├── _drafts/               # Proposed skills pending review
│   │   └── new-skill.md
│   └── verify-solution/       # Accepted skills
│       └── SKILL.md
├── tools/
│   ├── registry.yaml          # Tool manifest
│   └── custom_tool.py         # Tool implementations
├── memory/
│   ├── episodic.jsonl         # Failure lessons
│   └── semantic.jsonl         # Domain knowledge
└── evolution/                 # Managed by loop
    ├── observations/
    │   ├── batch_0001.jsonl
    │   └── batch_0002.jsonl
    ├── history.jsonl
    └── metrics.json
```

### Manifest Format

```yaml
agent:
  type: reference                                    # Must be "reference"
  entrypoint: my_package.agents.MyAgent              # Dotted Python path

evolvable_layers:                                    # Which directories can be mutated
  - prompts                                          # System prompt + fragments
  - skills                                           # Skill library
  - memory                                           # Episodic/semantic memory
  # - tools                                          # Tool implementations (optional)

reload_strategy: hot                                 # "hot" (re-read files) or "cold" (restart)
```

### AgentWorkspace API

The `AgentWorkspace` class provides typed read/write access:

**Prompts:**
- `read_prompt() -> str` — reads `prompts/system.md`
- `write_prompt(content: str)` — writes `prompts/system.md`
- `read_fragment(name: str) -> str` — reads `prompts/fragments/{name}`
- `write_fragment(name: str, content: str)` — writes a fragment
- `list_fragments() -> list[str]` — lists fragment filenames

**Skills:**
- `list_skills() -> list[SkillMeta]` — lists skills with name, description, path
- `read_skill(name: str) -> str` — reads skill content (frontmatter stripped)
- `write_skill(name: str, content: str)` — writes or updates a skill
- `delete_skill(name: str)` — removes a skill directory

**Drafts:**
- `list_drafts() -> list[dict]` — lists pending skill proposals
- `write_draft(name: str, content: str)` — writes a draft proposal
- `clear_drafts()` — removes all pending drafts

**Memory:**
- `add_memory(entry: dict, category: str = "episodic")` — appends to category JSONL
- `read_memories(category: str = "episodic", limit: int = 100) -> list[dict]`
- `read_all_memories(limit: int = 100) -> list[dict]` — all categories combined

**Tools:**
- `read_tool_registry() -> list[dict]` — reads `tools/registry.yaml`
- `write_tool_registry(tools: list[dict])` — writes tool manifest
- `read_tool(name: str) -> str` — reads tool source code
- `write_tool(name: str, content: str)` — writes tool implementation

**Evolution Metadata:**
- `read_evolution_history() -> list[dict]` — reads `evolution/history.jsonl`
- `read_evolution_metrics() -> dict` — reads `evolution/metrics.json`

---

## Configuration Reference

### EvolveConfig Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `batch_size` | `int` | `10` | Tasks per solve round |
| `max_cycles` | `int` | `20` | Maximum evolution iterations |
| `holdout_ratio` | `float` | `0.2` | Fraction held out for validation |
| `evolve_prompts` | `bool` | `True` | Allow prompt mutation |
| `evolve_skills` | `bool` | `True` | Allow skill creation/modification |
| `evolve_memory` | `bool` | `True` | Allow memory writes |
| `evolve_tools` | `bool` | `False` | Allow tool implementation changes |
| `trajectory_only` | `bool` | `False` | Hide scores from evolver |
| `evolver_model` | `str` | `"us.anthropic.claude-opus-4-6-v1"` | LLM for evolution engine |
| `evolver_max_tokens` | `int` | `16384` | Max tokens for evolver calls |
| `egl_threshold` | `float` | `0.05` | Convergence epsilon |
| `egl_window` | `int` | `3` | Cycles for plateau detection |
| `extra` | `dict` | `{}` | Extension point for custom params |

### Loading from YAML

```yaml
# config.yaml
batch_size: 15
max_cycles: 30
evolve_prompts: true
evolve_skills: true
evolve_memory: false
evolver_model: us.anthropic.claude-opus-4-6-v1
egl_threshold: 0.03
egl_window: 5
extra:
  solver_proposed: true
  merge_threshold: 0.7
```

```python
config = ae.EvolveConfig.from_yaml("config.yaml")
```

### Configuration Strategies

**Conservative (stable improvement):**
```python
config = ae.EvolveConfig(
    batch_size=10,
    max_cycles=10,
    evolve_prompts=True,
    evolve_skills=False,
    evolve_memory=False,
    egl_threshold=0.05,
)
```

**Aggressive (maximum exploration):**
```python
config = ae.EvolveConfig(
    batch_size=20,
    max_cycles=50,
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=True,
    evolve_tools=True,
    egl_threshold=0.01,
    egl_window=7,
)
```

**Skill-focused (procedure discovery):**
```python
config = ae.EvolveConfig(
    batch_size=10,
    max_cycles=25,
    evolve_prompts=False,
    evolve_skills=True,
    evolve_memory=True,
)
```

---

## Built-in Agents

### SWE Agent (`seed_workspaces/swe/`)

**Domain**: SWE-bench code patching
**Model**: Claude Opus 4.6 via AWS Bedrock
**Framework**: Strands-agents (CodeDojo-compatible)

Key features:
- Verify-fix loop: runs tests before and after each edit
- Hypothesis-first approach: form theory before exploring
- Skill proposal generation: agent reflects on verification process
- Conversation capture with per-turn token tracking
- Dynamic tool loading from workspace `tools/registry.yaml`

**Tools available**: bash, submit, text_editor, python_exec

### Terminal Agent (`seed_workspaces/terminal/`)

**Domain**: Terminal-Bench 2.0 shell challenges
**Model**: Claude Sonnet 4 via AWS Bedrock
**Framework**: Strands-agents

Key features:
- Concurrent timeout enforcement via ThreadPoolExecutor
- Test file copying only during evaluation (prevents cheating)
- Pre-built skills: self-verification, environment-discovery, scientific-computing, debug-and-fix
- Memory injection disabled (time-sensitive tasks)
- Graceful timeout fallback

**Tools available**: bash, python, submit

### MCP Agent (`seed_workspaces/mcp/`)

**Domain**: MCP-Atlas tool calling
**Model**: Claude Opus 4.6 via AWS Bedrock
**Framework**: Strands-agents with MCP integration

Key features:
- MCP server connection management
- Tool discovery and invocation
- Multi-provider support via LiteLLM

---

## Built-in Benchmarks

### SWE-bench Verified

**Module**: `agent_evolve.benchmarks.swe_verified`
**Tasks**: Real GitHub issues from popular Python repositories
**Evaluation**: Runs test suite, checks if agent's patch fixes the issue
**Metric**: Pass rate (0.0 to 1.0)

### MCP-Atlas

**Module**: `agent_evolve.benchmarks.mcp_atlas`
**Tasks**: Tool calling scenarios with MCP servers
**Evaluation**: Checks correct tool selection and parameter passing
**Metric**: Accuracy (0.0 to 1.0)

### Terminal-Bench 2.0

**Module**: `agent_evolve.benchmarks.terminal2`
**Tasks**: Shell command challenges (file manipulation, system admin, scripting)
**Evaluation**: Runs test scripts to verify terminal state
**Metric**: Pass rate (0.0 to 1.0)

### SkillsBench

**Module**: `agent_evolve.benchmarks.skill_bench`
**Tasks**: Multi-step procedural tasks
**Evaluation**: Checks step-by-step correctness
**Metric**: Accuracy (0.0 to 1.0)

### ARC-AGI-3

**Module**: `agent_evolve.benchmarks.arc_agi3`
**Tasks**: Interactive game levels (25 games, 181 levels)
**Evaluation**: RHAE score (ratio of human to agent actions, squared)
**Metric**: Average RHAE across levels (0.0 to 1.0)

---

## Evolution Algorithms

### AEvolveEngine (SkillForge)

**Module**: `agent_evolve.algorithms.skillforge.engine`
**Strategy**: LLM-driven workspace mutation

The default engine gives an LLM full bash tool access to the workspace and asks it to improve the agent based on observations. This is the most flexible engine — it can make arbitrary changes to any workspace file.

**Context provided to the LLM:**
- Recent observations (task inputs, agent outputs, feedback)
- Current system prompt
- Current skill library
- Pending draft proposals
- Score history

**Mutation capabilities:**
- Edit system prompt (refine, consolidate, extend)
- Create new skills from observed patterns
- Merge overlapping skills
- Write episodic memory entries
- Review and curate draft proposals

### GuidedSynthesisEngine

**Module**: `agent_evolve.algorithms.guided_synth`
**Strategy**: Memory-first, curated skills

Emphasizes learning from failures before creating skills. Conservative approach that prevents skill bloat.

**Process:**
1. Extract lessons from failed tasks
2. Write episodic memory entries
3. After accumulating patterns, synthesize skill proposals
4. Curate proposals: ACCEPT, MERGE, or SKIP

### AdaptiveEvolutionEngine

**Module**: `agent_evolve.algorithms.adaptive`
**Strategy**: Reward tracking + observation filtering

Adjusts intervention intensity based on score trends. Makes smaller changes when improving, larger changes when plateaued.

### AdaptiveSkillEngine

**Module**: `agent_evolve.algorithms.adaptive_skill`
**Strategy**: Skill-centric discovery

Focuses exclusively on building the skill library. Identifies task categories where the agent fails and creates targeted skills.

---

## Skill System

### Skill File Format

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

### Skill Discovery Process

1. **Agent proposes**: During `solve()`, agent writes draft to `skills/_drafts/`
2. **Engine reviews**: During `step()`, engine reads drafts and decides:
   - **ACCEPT**: Move to `skills/{name}/SKILL.md`
   - **MERGE**: Combine with existing similar skill
   - **SKIP**: Discard (too narrow, redundant, or incorrect)
3. **Engine creates**: Engine can also create skills directly from observation analysis
4. **Refinement**: Existing skills are updated based on new observations

### Skill Library Management

Target: 5-10 broad, reusable skills per workspace. Avoid:
- 30+ narrow skills (library bloat)
- Skills that duplicate system prompt content
- Skills with no TRIGGER condition (always-on = should be in prompt)

---

## Memory System

### Episodic Memory

Records specific lessons from task attempts:

```json
{"content": "pytest --no-header flag needed for clean output", "category": "episodic", "task_id": "django-16379"}
{"content": "Off-by-one errors common in range() with len()", "category": "episodic", "task_id": "numpy-8823"}
```

### Semantic Memory

General domain knowledge:

```json
{"content": "Django uses reverse URL resolution via urlpatterns", "category": "semantic"}
{"content": "NumPy broadcasting rules: dimensions must match or be 1", "category": "semantic"}
```

### Memory Limits

- `BaseAgent.reload_from_fs()` loads up to 200 memory entries by default
- `AgentWorkspace.read_memories()` defaults to limit=100
- Old memories should be pruned or consolidated during evolution

---

## Version Control

### Git Tagging Convention

| Tag | When Created | Purpose |
|-----|-------------|---------|
| `pre-evo-1` | Before cycle 1 evolution | Snapshot of solve-only state |
| `evo-1` | After cycle 1 evolution | Snapshot of evolved state |
| `pre-evo-2` | Before cycle 2 evolution | Snapshot before next mutation |
| `evo-2` | After cycle 2 evolution | Snapshot of evolved state |

### Useful Git Commands

```bash
# See all evolution checkpoints
git tag -l "evo-*"

# Compare two evolution stages
git diff evo-1 evo-10

# See what changed in a specific cycle
git diff pre-evo-5 evo-5

# Read a file at a specific point in time
git show evo-3:prompts/system.md

# Revert to a known good state
git checkout evo-5 -- .
```

---

## Observation Pipeline

### JSONL Format

Each observation is stored in `evolution/observations/batch_{label}.jsonl`:

```json
{
  "task_id": "django__django-16379",
  "task_input": "Fix FileBasedCache has_key method...",
  "task_metadata": {},
  "agent_output": "--- a/django/core/cache/backends/filebased.py\n+++ ...",
  "steps": [
    {"tool": "bash", "action": "read_file", "file": "django/core/cache/backends/filebased.py"},
    {"tool": "text_editor", "action": "edit", "file": "django/core/cache/backends/filebased.py"}
  ],
  "success": true,
  "score": 1.0,
  "feedback_detail": "All 24 tests passed"
}
```

### Querying Observations

```python
history = EvolutionHistory("./my-workspace")

# All observations from last 3 cycles
recent = history.get_observations(last_n_cycles=3)

# Only failures
failures = history.get_observations(only_failures=True)

# Score curve
scores = history.get_score_curve()  # [(1, 0.62), (2, 0.68), ...]
```

---

## FAQ

### Can I use A-Evolve with any LLM?

Yes. The agent can use any LLM for solving. The evolver model is configurable via `EvolveConfig.evolver_model`. Supported providers: Anthropic (direct API), OpenAI, AWS Bedrock, LiteLLM (multi-provider).

### Does evolution require training data?

No in the traditional ML sense. You need a `BenchmarkAdapter` that provides tasks and evaluation, but there are no training/gradient steps. Evolution is purely file-system mutation guided by LLM reasoning.

### How many cycles should I run?

Start with 10 cycles and check convergence. If score is still improving, run more. Default convergence detection (`egl_threshold=0.05`, `egl_window=3`) stops automatically when improvement plateaus.

### Can I resume evolution after stopping?

Yes. The workspace retains its evolved state. Create a new `Evolver` pointing to the same workspace and call `run()` again.

### Is evolution deterministic?

No. LLM calls are inherently non-deterministic. Running the same config twice may produce different evolved agents with similar final scores.

### Can I evolve multiple agents simultaneously?

Yes, but each must have its own workspace directory. The evolution loop modifies workspace files directly, so concurrent access to the same workspace is not safe.

### What's the cost per evolution cycle?

Each cycle involves: (batch_size) agent solve calls + 1 evolver call. For batch_size=10 with Claude, expect ~$5-20 per cycle depending on task complexity and model used.

### Can I use A-Evolve without a benchmark?

Not directly. The evolution loop requires `BenchmarkAdapter.evaluate()` to produce `Feedback`. However, you can implement a custom benchmark that uses human evaluation, LLM-as-judge, or any other scoring mechanism.
