# A-Evolve Release History

## v0.1.0 — Initial Public Release

**Date**: 2025

**Highlights**:
- Universal agent evolution infrastructure
- Three pluggable interfaces: `BaseAgent`, `BenchmarkAdapter`, `EvolutionEngine`
- File-system workspace contract with git versioning
- Four built-in evolution algorithms

**Benchmark Results** (Claude Opus 4.6):
- MCP-Atlas: 79.4% (#1 on leaderboard)
- SWE-bench Verified: 76.8% (~#5 on leaderboard)
- Terminal-Bench 2.0: 76.5% (~#7 on leaderboard)
- SkillsBench: 34.9% (#2 on leaderboard)

### Core Components

**Agent Protocol** (`agent_evolve.protocol.base_agent`):
- `BaseAgent` abstract class with `solve()`, `reload_from_fs()`, `export_to_fs()`
- Memory buffering via `remember()`
- Skill access via `get_skill_content()`
- Properties: `system_prompt`, `skills`, `memories`

**Benchmark Adapter** (`agent_evolve.benchmarks.base`):
- `BenchmarkAdapter` abstract class with `get_tasks()` and `evaluate()`
- Built-in adapters: SWE-bench Verified, MCP-Atlas, Terminal-Bench 2.0, SkillsBench, ARC-AGI-3

**Evolution Engine** (`agent_evolve.engine.base`):
- `EvolutionEngine` abstract class with `step()` and `on_cycle_end()`
- Default engine: AEvolveEngine (LLM-driven workspace mutation via bash tools)
- Additional engines: GuidedSynthesisEngine, AdaptiveEvolutionEngine, AdaptiveSkillEngine

**Evolution Loop** (`agent_evolve.engine.loop`):
- Orchestrates solve → observe → evolve → gate → reload cycles
- Git snapshot versioning (pre-evo-N, evo-N tags)
- Convergence detection with configurable threshold and window
- JSONL observation storage

**Agent Workspace** (`agent_evolve.contract.workspace`):
- `AgentWorkspace` class for typed file I/O
- Prompt read/write (system.md + fragments)
- Skill CRUD (list, read, write, delete)
- Draft management (propose, list, clear)
- Memory management (add, read by category)
- Tool registry and implementation management
- Evolution metadata access

**Configuration** (`agent_evolve.config`):
- `EvolveConfig` dataclass with YAML loading
- Controls: batch_size, max_cycles, holdout_ratio
- Layer toggles: evolve_prompts, evolve_skills, evolve_memory, evolve_tools
- Evolver model configuration (supports Anthropic, OpenAI, Bedrock, LiteLLM)
- Convergence: egl_threshold (default 0.05), egl_window (default 3)

**Top-Level API** (`agent_evolve.api`):
- `Evolver` class: 3-line setup and run
- Auto-resolution of agent seeds and benchmark names
- Workspace copying and manifest validation

### Built-in Seed Agents

| Agent | Domain | Framework | Model |
|-------|--------|-----------|-------|
| SWE Agent | SWE-bench | Strands | Claude Opus 4.6 (Bedrock) |
| Terminal Agent | Terminal-Bench | Strands | Claude Sonnet 4 (Bedrock) |
| MCP Agent | MCP-Atlas | Strands | Claude Opus 4.6 (Bedrock) |

### Evolution Algorithms

| Algorithm | Module | Strategy |
|-----------|--------|----------|
| A-Evolve/SkillForge | `algorithms.skillforge` | LLM with bash tools mutates workspace |
| Guided Synthesis | `algorithms.guided_synth` | Memory-first, curated skill proposals |
| Adaptive Evolution | `algorithms.adaptive` | Reward tracking, observation filtering |
| Adaptive Skill | `algorithms.adaptive_skill` | Skill-centric discovery and refinement |

### Installation Options

```bash
pip install a-evolve                # Core (matplotlib, pyyaml)
pip install a-evolve[anthropic]     # + anthropic>=0.30
pip install a-evolve[openai]        # + openai>=1.30
pip install a-evolve[bedrock]       # + boto3>=1.34
pip install a-evolve[litellm]       # + litellm>=1.0.0
pip install a-evolve[swe]           # + strands-agents, datasets, swebench
pip install a-evolve[mcp]           # + mcp, strands-agents, litellm
pip install a-evolve[all]           # Everything
pip install a-evolve[dev]           # + pytest, ruff, hypothesis
```

### Requirements

- Python >= 3.11
- Core dependencies: matplotlib >= 3.10.0, pyyaml >= 6.0
- Git (for workspace versioning)

### Known Limitations

- Evolution loop is single-threaded (sequential cycles)
- Convergence check uses hardcoded epsilon=0.01 in loop internals vs configurable egl_threshold in EvolveConfig
- No built-in distributed evaluation (parallelize via external orchestration)
- Workspace versioning requires git; non-git workflows not supported

### Links

- **Repository**: [github.com/A-EVO-Lab/a-evolve](https://github.com/A-EVO-Lab/a-evolve)
- **PyPI**: [pypi.org/project/a-evolve](https://pypi.org/project/a-evolve/)
- **Issues**: [github.com/A-EVO-Lab/a-evolve/issues](https://github.com/A-EVO-Lab/a-evolve/issues)
