# A-Evolve API Reference

## Top-Level Module: `agent_evolve`

```python
import agent_evolve as ae
```

### `ae.Evolver`

Main entry point for running evolution.

```python
class Evolver:
    def __init__(
        self,
        agent: str | BaseAgent,
        benchmark: str | BenchmarkAdapter,
        config: EvolveConfig | None = None,
        engine: EvolutionEngine | None = None,
        workspace_dir: str | None = None,
    ): ...

    def run(self, cycles: int | None = None) -> EvolutionResult: ...
```

**Parameters**:
- `agent`: One of:
  - Built-in seed name: `"swe"`, `"terminal"`, `"mcp"`
  - Path to workspace directory: `"./my-agent"`
  - `BaseAgent` instance
- `benchmark`: One of:
  - Built-in name: `"swe-verified"`, `"mcp-atlas"`, `"terminal2"`, `"skill-bench"`, `"arc-agi-3"`
  - `BenchmarkAdapter` instance
- `config`: Evolution configuration. Defaults to `EvolveConfig()`.
- `engine`: Custom evolution engine. Defaults to `AEvolveEngine`.
- `workspace_dir`: Override working directory for evolved state.

**Resolution logic**:
- String agent names are matched against built-in seed workspaces, then treated as paths
- Seed workspaces are copied to a working directory before evolution begins
- Manifest validation ensures `entrypoint` and `evolvable_layers` are present

---

## Core Types: `agent_evolve.types`

### `Task`

```python
@dataclass
class Task:
    id: str                    # Unique identifier
    input: str                 # Task description or input data
    metadata: dict = field(default_factory=dict)  # Extra context
```

### `Trajectory`

```python
@dataclass
class Trajectory:
    task_id: str               # Matches Task.id
    output: str                # Agent's final answer/patch/action
    steps: list[dict] = field(default_factory=list)  # Tool calls
    conversation: list[dict] = field(default_factory=list)  # Full messages
```

### `Feedback`

```python
@dataclass
class Feedback:
    success: bool              # Binary pass/fail
    score: float               # 0.0 to 1.0 continuous score
    detail: str = ""           # Human-readable explanation
    raw: dict = field(default_factory=dict)  # Benchmark-specific data
```

### `Observation`

```python
@dataclass
class Observation:
    task: Task
    trajectory: Trajectory
    feedback: Feedback
```

### `SkillMeta`

```python
@dataclass
class SkillMeta:
    name: str                  # Unique skill identifier
    description: str           # What it does and when to trigger
    path: str                  # Filesystem path to SKILL.md
```

### `StepResult`

```python
@dataclass
class StepResult:
    mutated: bool              # Whether workspace was changed
    summary: str               # Description of changes
    metadata: dict = field(default_factory=dict)
```

### `CycleRecord`

```python
@dataclass
class CycleRecord:
    cycle: int                       # Cycle number
    score: float                     # Average score this cycle
    mutated: bool                    # Whether workspace was changed
    engine_name: str = ""            # Name of the engine used
    summary: str = ""                # What the engine did
    observation_batch: str = ""      # Path to observation JSONL
    metadata: dict = field(default_factory=dict)
```

### `EvolutionResult`

```python
@dataclass
class EvolutionResult:
    cycles_completed: int
    final_score: float
    score_history: list[float] = field(default_factory=list)  # Score per cycle
    converged: bool = False
    details: dict = field(default_factory=dict)
```

---

## Protocol: `agent_evolve.protocol.base_agent`

### `BaseAgent`

```python
class BaseAgent:
    def __init__(self, workspace_dir: str | Path): ...

    def solve(self, task: Task) -> Trajectory:
        """Override: solve a single task and return trajectory."""
        raise NotImplementedError

    def reload_from_fs(self):
        """Re-read prompts, skills, memory from workspace after evolution."""
        ...

    def export_to_fs(self):
        """Flush accumulated state (memories, skill proposals) to disk."""
        ...

    def remember(self, content: str, category: str = "episodic", **extra):
        """Buffer an episodic memory entry."""
        ...

    def get_skill_content(self, name: str) -> str:
        """Read a skill document by name."""
        ...

    @property
    def system_prompt(self) -> str:
        """Current system prompt loaded from workspace."""
        ...

    @property
    def skills(self) -> list[SkillMeta]:
        """List of available skills."""
        ...
```

---

## Benchmarks: `agent_evolve.benchmarks.base`

### `BenchmarkAdapter`

```python
class BenchmarkAdapter:
    def get_tasks(self, split: str = "train", limit: int = 10) -> list[Task]:
        """Return tasks from the benchmark dataset."""
        raise NotImplementedError

    def evaluate(self, task: Task, trajectory: Trajectory) -> Feedback:
        """Evaluate an agent's trajectory on a task."""
        raise NotImplementedError
```

---

## Engine: `agent_evolve.engine.base`

### `EvolutionEngine`

```python
class EvolutionEngine:
    def step(
        self,
        workspace: AgentWorkspace,
        observations: list[Observation],
        history: EvolutionHistory,
        trial: TrialRunner | None = None,
    ) -> StepResult:
        """Mutate workspace based on observations. Return what changed."""
        raise NotImplementedError

    def on_cycle_end(self, accepted: bool, score: float):
        """Optional: called after gating decision (accept/reject mutations)."""
        pass
```

---

## Configuration: `agent_evolve.config`

### `EvolveConfig`

```python
@dataclass
class EvolveConfig:
    # Batch and cycle control
    batch_size: int = 10
    max_cycles: int = 20
    holdout_ratio: float = 0.2

    # Evolvable layers
    evolve_prompts: bool = True
    evolve_skills: bool = True
    evolve_memory: bool = True
    evolve_tools: bool = False

    # Observation transparency
    trajectory_only: bool = False    # If True, hide score/feedback from evolver

    # Evolver LLM
    evolver_model: str = "us.anthropic.claude-opus-4-6-v1"
    evolver_max_tokens: int = 16384

    # Convergence
    egl_threshold: float = 0.05
    egl_window: int = 3

    # Extension point
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "EvolveConfig": ...
```

**YAML format**:

```yaml
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
```

---

## Workspace: `agent_evolve.contract.workspace`

### `AgentWorkspace`

```python
class AgentWorkspace:
    def __init__(self, path: str): ...

    # Prompts
    def read_prompt(self) -> str: ...                         # Reads prompts/system.md
    def write_prompt(self, content: str) -> None: ...         # Writes prompts/system.md
    def read_fragment(self, name: str) -> str: ...            # Reads prompts/fragments/{name}
    def write_fragment(self, name: str, content: str) -> None: ...
    def list_fragments(self) -> list[str]: ...

    # Skills
    def list_skills(self) -> list[SkillMeta]: ...
    def read_skill(self, name: str) -> str: ...
    def write_skill(self, name: str, content: str) -> None: ...
    def delete_skill(self, name: str) -> None: ...

    # Drafts (proposed skills pending review)
    def list_drafts(self) -> list[dict[str, str]]: ...
    def write_draft(self, name: str, content: str) -> None: ...
    def clear_drafts(self) -> None: ...

    # Memory
    def add_memory(self, entry: dict, category: str = "episodic") -> None: ...
    def read_memories(self, category: str = "episodic", limit: int = 100) -> list[dict]: ...
    def read_all_memories(self, limit: int = 100) -> list[dict]: ...

    # Tools
    def read_tool_registry(self) -> list[dict]: ...
    def write_tool_registry(self, tools: list[dict]) -> None: ...
    def read_tool(self, name: str) -> str: ...
    def write_tool(self, name: str, content: str) -> None: ...

    # Evolution metadata
    def read_evolution_history(self) -> list[dict]: ...
    def read_evolution_metrics(self) -> dict: ...

    # Manifest
    def read_manifest(self) -> dict: ...
```

---

## Built-in Algorithms

### `agent_evolve.algorithms.skillforge.engine.AEvolveEngine`

Default LLM-driven evolution. Uses Claude with bash tool access to analyze observations and directly edit workspace files.

### `agent_evolve.algorithms.guided_synth.GuidedSynthesisEngine`

Memory-first evolution: extracts minimal episodic memory from failures, then curates skill proposals.

### `agent_evolve.algorithms.adaptive.AdaptiveEvolutionEngine`

Observation filtering + reward tracking + adaptive intervention density.

### `agent_evolve.algorithms.adaptive_skill.AdaptiveSkillEngine`

Skill-centric: focuses exclusively on skill discovery and refinement.

---

## Built-in Registries

Agent and benchmark resolution uses registries in `api.py`:

```python
AGENT_REGISTRY = {
    "swe": "seed_workspaces/swe",
    "swe-verified": "seed_workspaces/swe",
    "terminal": "seed_workspaces/terminal",
    "terminal2": "seed_workspaces/terminal",
    "mcp": "seed_workspaces/mcp",
    "mcp-atlas": "seed_workspaces/mcp",
    "arc": "seed_workspaces/arc",
    ...
}

BENCHMARK_REGISTRY = {
    "swe-verified": "agent_evolve.benchmarks.swe_verified.SweVerifiedBenchmark",
    "mcp-atlas": "agent_evolve.benchmarks.mcp_atlas.McpAtlasBenchmark",
    "terminal2": "agent_evolve.benchmarks.terminal2.Terminal2Benchmark",
    "skill-bench": "agent_evolve.benchmarks.skill_bench.SkillBenchBenchmark",
    "arc-agi-3": "agent_evolve.benchmarks.arc_agi3.ArcAgi3Benchmark",
    ...
}
```

---

## Evolution Loop: `agent_evolve.engine.loop`

### `EvolutionLoop`

```python
class EvolutionLoop:
    def __init__(
        self,
        agent: BaseAgent,
        benchmark: BenchmarkAdapter,
        engine: EvolutionEngine,
        config: EvolveConfig,
        workspace: AgentWorkspace,
    ): ...

    def run(self, cycles: int | None = None) -> EvolutionResult:
        """Run the full evolution loop for the specified number of cycles.

        Each cycle:
        1. SOLVE - Agent solves a batch of tasks
        2. OBSERVE - Benchmark evaluates, creates Observation triples
        3. PRE-SNAPSHOT - Git commit with pre-evo-N tag
        4. ENGINE.STEP - Engine mutates workspace
        5. POST-SNAPSHOT - Git commit with evo-N tag
        6. RECORD - Log CycleRecord
        7. RELOAD - agent.reload_from_fs()
        8. CONVERGE - Check score plateau
        """
        ...
```

### Convergence Function

```python
def _is_score_converged(
    scores: list[float],
    window: int = 3,
    epsilon: float = 0.01,
) -> bool:
    """Check if scores have plateaued.

    Returns True if the difference between max and min scores
    in the last `window` entries is less than `epsilon`.

    Note: The `epsilon` parameter defaults to 0.01 in the function
    signature. The `EvolveConfig.egl_threshold` (default 0.05) is
    passed as the `epsilon` argument when called from the loop.
    """
    if len(scores) < window:
        return False
    recent = scores[-window:]
    return (max(recent) - min(recent)) < epsilon
```

---

## Observer: `agent_evolve.engine.observer`

### `Observer`

Collects and persists observations during evolution.

```python
class Observer:
    def __init__(self, workspace_path: str | Path): ...

    def record(self, task: Task, trajectory: Trajectory, feedback: Feedback):
        """Buffer a single observation."""
        ...

    def flush(self, batch_label: str = ""):
        """Write buffered observations to JSONL file.

        Files are written to: evolution/observations/batch_{label}.jsonl
        """
        ...

    def get_observations(self) -> list[Observation]:
        """Return buffered observations (not yet flushed)."""
        ...
```

### `EvolutionHistory`

Query facade over past evolution cycles.

```python
class EvolutionHistory:
    def __init__(self, workspace_path: str | Path): ...

    def get_observations(
        self,
        last_n_cycles: int | None = None,
        only_failures: bool = False,
    ) -> list[Observation]:
        """Read observations from stored JSONL files."""
        ...

    def get_score_curve(self) -> list[tuple[int, float]]:
        """Return (cycle_number, score) pairs for all completed cycles."""
        ...

    def get_workspace_diff(self, from_label: str, to_label: str) -> str:
        """Get git diff between two version labels (e.g., 'evo-1', 'evo-5')."""
        ...

    def read_file_at(self, version_label: str, path: str) -> str:
        """Read a workspace file as it existed at a given version."""
        ...
```

---

## Version Control: `agent_evolve.engine.versioning`

### `VersionControl`

```python
class VersionControl:
    def __init__(self, workspace_path: str | Path): ...

    def init(self): ...
    def commit(self, message: str, tag: str | None = None): ...
    def get_diff(self, from_ref: str, to_ref: str) -> str: ...
    def show_file_at(self, ref: str, path: str) -> str: ...
    def list_tags(self, prefix: str = "evo-") -> list[str]: ...
    def get_log(self, max_entries: int = 50) -> list[dict]: ...
```

---

## Skill Format Specification

Skills are stored as `skills/{name}/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name                    # kebab-case identifier
description: "TRIGGER when: condition. DO NOT TRIGGER: exclusion."
---
```

### Skill Lifecycle

1. **Proposal**: Agent writes to `skills/_drafts/` during `solve()`
2. **Review**: Evolution engine reads drafts during `step()`
3. **Accept**: Engine moves draft to `skills/{name}/SKILL.md`
4. **Merge**: Engine combines similar skills to prevent bloat
5. **Refine**: Engine updates skill content based on new observations

### Skill Loading

```python
# In agent's solve() method
for skill_meta in self.skills:
    content = self.get_skill_content(skill_meta.name)
    # Returns SKILL.md content (frontmatter stripped)
```

### Skill Injection Patterns

**Append to system prompt:**
```python
skill_text = "\n".join(
    f"## {s.name}\n{self.get_skill_content(s.name)}"
    for s in self.skills
)
system = f"{self.system_prompt}\n\n# Skills\n{skill_text}"
```

**Selective injection based on task:**
```python
relevant_skills = [
    s for s in self.skills
    if task_matches_skill(task, s.description)
]
```

---

## Memory System

### Memory Categories

| Category | File | Purpose |
|----------|------|---------|
| `episodic` | `memory/episodic.jsonl` | Lessons from specific task attempts |
| `semantic` | `memory/semantic.jsonl` | General domain knowledge |
| Custom | `memory/{category}.jsonl` | User-defined categories |

### Memory in the Agent

```python
# Writing memory during solve()
self.remember(
    "File locks on NFS require fcntl.flock with LOCK_EX",
    category="domain_knowledge",
)

# Reading memory (loaded automatically by reload_from_fs)
for mem in self.memories:
    print(f"[{mem.get('category')}] {mem.get('content')}")
```

### Memory in the Workspace

```python
workspace = AgentWorkspace("./my-agent")

# Add a memory entry
workspace.add_memory(
    {"content": "Always run full test suite", "source": "cycle-5-failure"},
    category="episodic",
)

# Read memories
recent = workspace.read_memories(category="episodic", limit=20)
all_mems = workspace.read_all_memories(limit=100)
```

### Memory Evolution

When `evolve_memory=True`, the evolution engine can:
- Add new episodic entries summarizing failure patterns
- Consolidate redundant memories
- Promote episodic memories to semantic (general knowledge)
- Remove stale or misleading memories
