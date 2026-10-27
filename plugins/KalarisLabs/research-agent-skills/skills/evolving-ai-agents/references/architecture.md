# A-Evolve Architecture Deep Dive

## Design Philosophy

A-Evolve treats agent optimization as a **file-system mutation problem**. All evolvable state — prompts, skills, memory, tools — lives as plain files in a workspace directory. Evolution engines read observations, mutate files, and git-commit snapshots. This makes every change human-readable, diffable, and rollbackable.

There are no learned weights, no gradient updates, no opaque parameters. Every mutation is an explicit edit to a text file.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Evolver API                       │
│  evolver = ae.Evolver(agent, benchmark, config)     │
│  results = evolver.run(cycles=N)                    │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  EvolutionLoop  │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐  ┌──────▼──────┐  ┌───▼────┐
   │  Agent  │  │  Benchmark  │  │ Engine │
   │ solve() │  │ evaluate()  │  │ step() │
   └────┬────┘  └──────┬──────┘  └───┬────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
              ┌────────▼────────┐
              │ Agent Workspace │
              │  (filesystem)   │
              └─────────────────┘
```

## The Three Interfaces

### 1. BaseAgent

The `BaseAgent` class is the parent of all evolvable agents. It provides:

- **File system contract**: Loads system prompts, skills, memories from workspace paths
- **Memory management**: `remember()` buffers episodic entries during solve
- **Skill access**: `get_skill_content()` retrieves skill documents dynamically
- **Hot reload**: `reload_from_fs()` re-reads all state after evolution mutates files
- **Export**: `export_to_fs()` flushes accumulated state (memories, skill proposals)

Subclasses override `solve(task: Task) -> Trajectory` with domain logic.

```python
class BaseAgent:
    def __init__(self, workspace_path: str): ...
    def solve(self, task: Task) -> Trajectory: ...       # Override this
    def reload_from_fs(self): ...                         # Re-read after evolution
    def export_to_fs(self): ...                           # Flush state to disk
    def remember(self, content, category="episodic"): ... # Buffer episodic memory
    def get_skill_content(self, name: str) -> str: ...    # Read a skill
```

### 2. BenchmarkAdapter

Benchmarks provide tasks and evaluation:

```python
class BenchmarkAdapter:
    def get_tasks(self, split="train", limit=10) -> list[Task]: ...
    def evaluate(self, task: Task, trajectory: Trajectory) -> Feedback: ...
```

**Built-in benchmarks** use entry points registered in `api.py`:

| Registry Key | Class | Module |
|-------------|-------|--------|
| `swe-verified` | `SweVerifiedBenchmark` | `agent_evolve.benchmarks.swe_verified` |
| `mcp-atlas` | `McpAtlasBenchmark` | `agent_evolve.benchmarks.mcp_atlas` |
| `terminal2` | `Terminal2Benchmark` | `agent_evolve.benchmarks.terminal2` |
| `skill-bench` | `SkillBenchBenchmark` | `agent_evolve.benchmarks.skill_bench` |
| `arc-agi-3` | `ArcAgi3Benchmark` | `agent_evolve.benchmarks.arc_agi3` |

### 3. EvolutionEngine

Engines decide how to mutate the workspace:

```python
class EvolutionEngine:
    def step(self, workspace, observations, history, trial) -> StepResult: ...
    def on_cycle_end(self, accepted: bool): ...  # Optional callback
```

**Arguments received**:
- `workspace`: `AgentWorkspace` — typed read/write access to all agent files
- `observations`: List of `Observation` — recent (task, trajectory, feedback) triples
- `history`: `EvolutionHistory` — query facade over past cycles and workspace versions
- `trial`: Optional trial runner for expensive live validation

## Agent Workspace Contract

The `AgentWorkspace` class provides typed access to workspace files:

```python
workspace = AgentWorkspace("./my-agent")

# Prompts (reads/writes prompts/system.md)
prompt = workspace.read_prompt()
workspace.write_prompt(new_prompt)

# Prompt fragments (modular pieces in prompts/fragments/)
fragment = workspace.read_fragment("reasoning.md")
workspace.write_fragment("reasoning.md", content)

# Skills
skills = workspace.list_skills()          # Returns list of SkillMeta
content = workspace.read_skill("verify")  # Returns skill content
workspace.write_skill("verify", content)  # Write/update skill
workspace.delete_skill("obsolete")        # Remove a skill

# Memory
entries = workspace.read_memories("episodic")          # Read by category
workspace.add_memory({"lesson": "..."}, "episodic")    # Append entry
all_entries = workspace.read_all_memories(limit=100)   # All categories

# Tools
registry = workspace.read_tool_registry()
workspace.write_tool("my_tool.py", code)
```

### Manifest Format

Every workspace has a `manifest.yaml`:

```yaml
agent:
  type: reference
  entrypoint: agent_evolve.agents.swe.agent.SweAgent

evolvable_layers:
  - prompts
  - skills
  - memory

reload_strategy: hot    # or "cold"
```

- `entrypoint`: Dotted Python path to the agent class
- `evolvable_layers`: Which directories the engine is allowed to mutate
- `reload_strategy`: Whether agent re-reads state mid-cycle (hot) or restarts (cold)

## Evolution Loop Internals

The `EvolutionLoop` orchestrates each cycle:

```
For each cycle 1..N:
  1. SOLVE:     agent.solve(task) for each task in batch
  2. OBSERVE:   benchmark.evaluate(task, trajectory) -> Feedback
  3. SNAPSHOT:  git commit as "pre-evo-{N}"
  4. EVOLVE:    engine.step(workspace, observations, history, trial)
  5. SNAPSHOT:  git commit as "evo-{N}"
  6. RECORD:    Log cycle number, score, engine metadata
  7. RELOAD:    agent.reload_from_fs()
  8. CONVERGE:  If score plateau for egl_window cycles -> exit
```

### Convergence Detection

The loop tracks scores over a sliding window:

```python
# Converged if no improvement > epsilon in last window cycles
scores = [cycle.score for cycle in history[-egl_window:]]
if max(scores) - min(scores) < egl_threshold:
    return EvolutionResult(converged=True, ...)
```

Default: `egl_threshold=0.05`, `egl_window=3`.

### Observation Format

Observations are stored as JSONL in `evolution/observations/`:

```json
{
  "task_id": "django__django-16379",
  "task_input": "Fix FileBasedCache has_key ...",
  "agent_output": "--- a/django/core/cache/backends/filebased.py\n+++ ...",
  "steps": [
    {"tool": "bash", "action": "read_file", "file": "src/main.py"},
    {"tool": "bash", "action": "edit_file", "file": "src/main.py"}
  ],
  "success": true,
  "score": 0.95,
  "feedback_detail": "All tests passed"
}
```

## Version Control Integration

Every evolution cycle creates git snapshots:

- `pre-evo-N`: State before engine mutates the workspace
- `evo-N`: State after engine mutates the workspace

This enables:
- **Rollback**: `git checkout evo-3` to revert to cycle 3
- **Diff analysis**: `git diff evo-1 evo-10` to see cumulative evolution
- **History queries**: `history.get_workspace_diff("evo-3", "evo-7")`
- **File time travel**: `history.read_file_at("evo-5", "prompts/system.md")`

## Default Engine: A-Evolve/SkillForge

The default `AEvolveEngine` uses an LLM with bash tool access to mutate workspaces:

1. **Analyze observations**: Read recent task results, failures, and trajectories
2. **Build context**: Construct multi-part prompt with observations, existing skills, and draft proposals
3. **LLM mutation**: Claude with bash tools directly edits workspace files
4. **Track changes**: Compare skill counts and file diffs before/after

The engine effectively turns the LLM into a "developer" who reads test results and improves the agent's code/prompts accordingly. This is powerful because the evolver can make nuanced, context-aware changes that rule-based systems cannot.

## Observer and History

The `Observer` collects observations as JSONL batches:

```python
observer = Observer(workspace_path)
observer.record(task, trajectory, feedback)
observer.flush()  # Writes to evolution/observations/batch_XXXX.jsonl
```

The `EvolutionHistory` provides query access:

```python
history = EvolutionHistory(workspace_path)
history.get_observations(last_n_cycles=3)
history.get_observations(only_failures=True)
history.get_score_curve()                        # List of (cycle, score)
history.get_workspace_diff("evo-1", "evo-5")     # Git diff
history.read_file_at("evo-3", "prompts/system.md")
```

## Multi-Provider LLM Support

A-Evolve supports multiple LLM providers for both the solving agent and the evolution engine:

| Provider | Config Key | Auth |
|----------|-----------|------|
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` env var |
| OpenAI | `openai` | `OPENAI_API_KEY` env var |
| AWS Bedrock | `bedrock` | AWS credentials (boto3) |
| LiteLLM | `litellm` | Provider-specific keys |

The evolver model is configured separately from the agent's model:

```python
config = ae.EvolveConfig(
    evolver_model="us.anthropic.claude-opus-4-6-v1",  # Evolution engine model
    evolver_max_tokens=16384,
)
```

Agent models are configured within the seed workspace (e.g., in `manifest.yaml` or the agent code).

## Evolution Algorithm Details

### A-Evolve/SkillForge (Default)

The default engine treats evolution as a code editing problem. It gives an LLM access to bash tools and the workspace filesystem, then asks it to improve the agent based on observations.

**How it works:**

1. **Context assembly**: Builds a prompt containing:
   - Recent observations (task inputs, agent outputs, feedback scores and details)
   - Current system prompt content
   - Current skill library with full SKILL.md content
   - Pending draft proposals from the agent
   - Score history across cycles

2. **LLM interaction**: Calls the evolver model (default: Claude Opus 4.6) with bash tool access. The LLM can:
   - Read and edit `prompts/system.md`
   - Create, modify, or delete skills in `skills/`
   - Write episodic memory entries
   - Review and accept/reject draft skill proposals

3. **Mutation tracking**: After the LLM finishes, the engine:
   - Counts skill additions, modifications, and deletions
   - Measures prompt length change
   - Records a summary of what was changed and why

4. **Git snapshot**: All changes are committed as `evo-N`

**Strengths:**
- Can make nuanced, context-aware changes
- Understands relationships between prompt sections and skill content
- Can refactor and consolidate (not just append)

**Weaknesses:**
- Expensive per cycle (full LLM call with large context)
- Quality depends on evolver model capability
- Non-deterministic (same observations may produce different mutations)

### Guided Synthesis

A memory-first approach that emphasizes learning from failures before creating skills.

**How it works:**

1. **Failure extraction**: Identifies failed tasks and extracts minimal lessons
2. **Memory population**: Writes episodic memory entries for each failure pattern
3. **Skill proposal**: After accumulating enough memories, synthesizes skill proposals
4. **Curation**: Reviews proposals against existing skills, accepts, merges, or skips

**Best for:**
- Domains where the agent's base reasoning is sound but needs domain knowledge
- Scenarios where skill bloat is a concern
- When you want a conservative evolution strategy

### Adaptive Evolution

Combines intelligent observation filtering with reward tracking.

**How it works:**

1. **Observation filtering**: Selects the most informative observations (diverse failures, novel patterns)
2. **Reward tracking**: Monitors score trends to adjust intervention density
3. **Adaptive intervention**: When score is improving, makes smaller changes; when plateaued, makes larger changes
4. **Multi-objective**: Can optimize for multiple metrics simultaneously

**Best for:**
- Fine-grained control over evolution pace
- Domains with noisy evaluation signals
- When you need to balance exploration vs exploitation

### Adaptive Skill

A skill-centric engine that focuses exclusively on building the skill library.

**How it works:**

1. **Skill gap analysis**: Identifies task categories where the agent consistently fails
2. **Targeted discovery**: Creates skills specifically addressing identified gaps
3. **Skill refinement**: Iteratively improves existing skills based on new observations
4. **Library management**: Merges overlapping skills, prunes unused ones

**Best for:**
- Domains where procedural knowledge is the primary bottleneck
- Building reusable skill libraries across agents
- When the system prompt is already well-optimized

## Workspace Lifecycle

### Creation

Workspaces are created in one of three ways:

1. **From seed**: `Evolver(agent="swe")` copies `seed_workspaces/swe/` to a working directory
2. **From path**: `Evolver(agent="./my-agent")` uses the directory directly
3. **From agent**: `Evolver(agent=MyAgent("./workspace"))` uses the agent's workspace

### During Evolution

Each cycle modifies the workspace:
- **Files changed**: prompts, skills, memory (as configured by `evolve_*` flags)
- **Files added**: new skills, memory entries, observation batches
- **Git history**: two commits per cycle (pre-evo-N, evo-N)

### After Evolution

The workspace contains the optimized agent state:
- Evolved system prompt at `prompts/system.md`
- Discovered skills in `skills/`
- Episodic memories in `memory/`
- Full evolution history in `evolution/`
- Complete git history with tagged checkpoints

The workspace is a standalone directory that can be:
- Copied and reused for future evolution runs
- Deployed as-is (the agent reads from the workspace at runtime)
- Version-controlled independently
- Shared with other developers

## Error Handling and Recovery

### Cycle Failure

If a cycle fails mid-execution (LLM error, timeout, etc.):
- The pre-evo snapshot has already been committed
- The workspace reverts to the pre-evo state
- The cycle is marked as failed in the history
- Evolution continues with the next cycle

### Agent Failure

If the agent fails to solve a task:
- The trajectory is recorded with empty output and error details
- The benchmark evaluates it as a failure (score 0.0)
- The failure observation is still useful for the evolver

### Engine Failure

If the evolution engine fails:
- The workspace remains at the pre-evo snapshot
- The cycle is recorded with `mutated=False`
- Evolution continues (the engine may succeed on the next cycle)

### Recovery from Corrupted State

If the workspace is in a bad state, recover using git:

```bash
# Reset to last known good state
git checkout evo-5 -- .

# Or reset to before any evolution
git checkout evo-1 -- .
```
