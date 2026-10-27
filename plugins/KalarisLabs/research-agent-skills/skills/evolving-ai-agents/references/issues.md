# A-Evolve: Common Issues & Solutions

## Issue 1: `ModuleNotFoundError: No module named 'agent_evolve'`

**Context**: Running evolution script after pip install.

**Solution**: Ensure you installed the package correctly:

```bash
# From source
pip install -e .

# From PyPI
pip install a-evolve

# With provider support
pip install a-evolve[anthropic]    # For Claude
pip install a-evolve[bedrock]      # For AWS Bedrock
pip install a-evolve[all]          # Everything
```

If using a virtual environment, verify activation:

```bash
which python   # Should point to your venv
python -c "import agent_evolve; print(agent_evolve.__file__)"
```

---

## Issue 2: Evolution Score Stays Flat After Multiple Cycles

**Symptoms**: Score doesn't improve beyond cycle 1-2 baseline.

**Root causes and fixes**:

1. **Batch too small**: With `batch_size=3`, the evolver sees too few observations to identify patterns. Increase to 10-15.

2. **Benchmark tasks too similar**: If all tasks test the same skill, there's no diversity signal. Ensure `get_tasks()` returns varied difficulties.

3. **Evolver can't see scores**: If `trajectory_only=True`, the evolver must infer quality from trajectories alone. Set `trajectory_only=False` for faster learning.

4. **Skills not loaded by agent**: Verify that `reload_from_fs()` actually re-reads skills and injects them into the LLM prompt. Common mistake: loading skills at `__init__` but not reloading them.

```python
# Debug: print what the agent sees after each cycle
class MyAgent(ae.BaseAgent):
    def reload_from_fs(self):
        super().reload_from_fs()
        print(f"Reloaded {len(self.skills)} skills")
        print(f"Prompt length: {len(self.system_prompt)} chars")
```

---

## Issue 3: `FileNotFoundError: manifest.yaml not found`

**Context**: Passing a workspace path to `Evolver`.

**Solution**: Every workspace must have a `manifest.yaml` at the root:

```yaml
agent:
  type: reference
  entrypoint: my_module.MyAgent
evolvable_layers:
  - prompts
  - skills
reload_strategy: hot
```

Verify the file exists:

```bash
ls -la ./my-workspace/manifest.yaml
```

---

## Issue 4: Git Errors During Evolution Snapshots

**Symptoms**: `fatal: not a git repository` or merge conflicts.

**Root causes**:

1. **Workspace not a git repo**: Initialize before running evolution:

```bash
cd my-workspace && git init && git add -A && git commit -m "Initial workspace"
```

2. **Dirty working tree**: Uncommitted changes from a previous run. Reset or commit:

```bash
cd my-workspace && git add -A && git commit -m "Clean state"
```

3. **Concurrent evolution on same workspace**: Each `evolver.run()` must operate on its own workspace copy. Use the built-in seed copy mechanism:

```python
# This auto-copies the seed to a fresh working directory
evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
```

---

## Issue 5: AWS Bedrock Authentication Failures

**Symptoms**: `botocore.exceptions.NoCredentialsError` when using Bedrock models.

**Solution**:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-west-2

# Option 2: AWS CLI profile
aws configure

# Option 3: IAM role (on EC2/ECS)
# Ensure instance role has bedrock:InvokeModel permission
```

Verify access:

```python
import boto3
client = boto3.client("bedrock-runtime", region_name="us-west-2")
# Should not raise an error
```

---

## Issue 6: Anthropic Rate Limits During Evolution

**Symptoms**: `RateLimitError` or `429` responses mid-evolution.

**Solution**: The evolver makes LLM calls to mutate the workspace, in addition to agent solve calls. For high batch sizes, this can exceed rate limits.

Mitigation:
- Reduce `batch_size` (fewer concurrent solve calls)
- Add retry logic in your agent's `solve()` method
- Use Bedrock instead of direct Anthropic API (higher default limits)
- Stagger evolution cycles with short pauses between them

---

## Issue 7: Skills Not Being Discovered

**Symptoms**: After 10+ cycles, `skills/` directory remains empty.

**Root causes**:

1. **`evolve_skills=False`** in config. Enable it:

```python
config = ae.EvolveConfig(evolve_skills=True)
```

2. **Engine doesn't support skill creation**: The default `AEvolveEngine` does. Custom engines must explicitly write to `workspace.write_skill()`.

3. **Evolver lacks sufficient context**: Ensure observations include detailed failure feedback, not just pass/fail booleans. Richer `feedback.detail` strings help the evolver identify skill-worthy patterns.

---

## Issue 8: Agent Doesn't Pick Up Evolved Prompts

**Symptoms**: Agent behavior doesn't change between cycles despite prompt mutations.

**Root cause**: Agent caches the system prompt at initialization and doesn't re-read.

**Fix**: Implement `reload_from_fs()` properly:

```python
class MyAgent(ae.BaseAgent):
    def __init__(self, workspace_path):
        super().__init__(workspace_path)
        self._load_state()

    def _load_state(self):
        self._cached_prompt = self.system_prompt
        self._cached_skills = [
            self.get_skill_content(s.name) for s in self.skills
        ]

    def reload_from_fs(self):
        super().reload_from_fs()  # Re-reads files from disk
        self._load_state()        # Update cached state
```

---

## Issue 9: `EvolutionResult.converged=True` Too Early

**Symptoms**: Evolution stops after 3-4 cycles even though score is low.

**Cause**: Default convergence settings are too aggressive for slow-improving domains.

**Fix**: Increase the convergence window and decrease threshold:

```python
config = ae.EvolveConfig(
    egl_threshold=0.01,   # Require < 1% improvement to converge (default 5%)
    egl_window=5,          # Look at 5 cycles instead of 3
    max_cycles=50,         # Allow more cycles
)
```

---

## Issue 10: Memory Overflow with Large Trajectories

**Symptoms**: Python OOM when processing benchmarks with very long agent conversations.

**Root cause**: Full conversation history stored in `Trajectory.conversation` for every task.

**Mitigation**:
- Truncate conversations in your agent's `solve()` before returning
- Store only the final output and key tool calls in `steps`
- Use smaller batch sizes to limit concurrent memory usage

```python
def solve(self, task):
    # ... run agent ...
    return ae.Trajectory(
        task_id=task.id,
        output=final_answer,
        steps=key_steps_only,        # Not full conversation
        conversation=[],              # Skip if not needed for evolution
    )
```

---

## Issue 11: Workspace Too Large After Many Cycles

**Symptoms**: `.git` directory grows to several GB after 20+ cycles.

**Cause**: Git stores full snapshots of observation JSONL files (which can be large).

**Mitigation**:

```bash
# Clean up old observation batches (keep last 5 cycles)
cd my-workspace
find evolution/observations/ -name "batch_*.jsonl" -mtime +7 -delete
git add -A && git commit -m "Prune old observations"

# Alternatively, use git gc
git gc --aggressive
```

Or configure the evolver to not track observations in git:

```yaml
# In manifest.yaml
evolution:
  track_observations: false
```

---

## Issue 12: Custom Benchmark Returns Inconsistent Scores

**Symptoms**: Evolution oscillates — score goes up then down between cycles.

**Root cause**: Non-deterministic evaluation or tasks sampled differently each cycle.

**Fix**:
- Use a fixed random seed in `get_tasks()` for reproducible task selection
- Ensure `evaluate()` is deterministic (no randomness in scoring)
- Use `holdout_ratio` to keep a consistent test set:

```python
config = ae.EvolveConfig(holdout_ratio=0.2)  # 20% held out for validation
```

---

## Issue 13: Evolution Produces Overly Long System Prompts

**Symptoms**: System prompt grows to 10K+ characters after many cycles. Agent performance may degrade due to instruction overload.

**Root cause**: The default SkillForge engine sometimes appends rules without consolidating existing ones.

**Fix**:

1. **Manual pruning**: After evolution, review the prompt and remove redundant sections:
```bash
cd my-workspace
wc -c prompts/system.md    # Check size
git diff evo-1 evo-N -- prompts/system.md  # See what was added
```

2. **Run a consolidation cycle**: Use the evolver to refactor:
```python
# Create a config that focuses on prompt refinement
config = ae.EvolveConfig(
    batch_size=10,
    max_cycles=3,
    evolve_prompts=True,
    evolve_skills=False,
    evolve_memory=False,
    extra={"consolidate_prompt": True},
)
```

3. **Use fragments instead of one large prompt**: Split the prompt into modular fragments that the evolver can manage independently:
```
prompts/
├── system.md           # Core identity (keep short)
└── fragments/
    ├── reasoning.md    # Reasoning approach
    ├── output.md       # Output formatting
    └── domain.md       # Domain-specific rules
```

---

## Issue 14: Skill Proposals Never Get Accepted

**Symptoms**: Agent proposes skills via `_drafts/` directory, but the evolver never promotes them to `skills/`.

**Root cause**: The SkillForge engine may not be configured to read drafts, or the proposals are too narrow.

**Fix**:

1. Enable solver-proposed skills in config:
```python
config = ae.EvolveConfig(
    extra={"solver_proposed": True}
)
```

2. Improve proposal quality in your agent:
```python
def solve(self, task):
    # ... solve the task ...

    # Propose a skill if you learned something reusable
    if learned_pattern:
        draft_content = f"""---
name: {pattern_name}
description: "TRIGGER when: {trigger}. DO NOT TRIGGER: {exclusion}."
---

{pattern_description}

## Steps
{steps}
"""
        # Write to drafts directory
        workspace = AgentWorkspace(self._workspace_dir)
        workspace.write_draft(pattern_name, draft_content)
```

3. Use the GuidedSynthesisEngine which prioritizes skill curation:
```python
from agent_evolve.algorithms.guided_synth import GuidedSynthesisEngine
evolver = ae.Evolver(agent="./my-agent", benchmark=bm, engine=GuidedSynthesisEngine(config))
```

---

## Issue 15: Different Results on Each Evolution Run

**Symptoms**: Running the same config on the same seed produces different final scores.

**Root cause**: LLM-driven evolution is inherently non-deterministic. The evolver model, agent model, and benchmark task sampling all introduce randomness.

**Mitigation**:

1. **Fix task ordering** with a seed:
```python
class MyBenchmark(ae.BenchmarkAdapter):
    def get_tasks(self, split="train", limit=10):
        tasks = load_all_tasks(split)
        random.seed(42)          # Fixed seed
        random.shuffle(tasks)
        return tasks[:limit]
```

2. **Run multiple evolution trials** and compare:
```python
scores = []
for trial in range(5):
    evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
    result = evolver.run(cycles=10)
    scores.append(result.final_score)

print(f"Mean: {sum(scores)/len(scores):.3f}")
print(f"Std:  {(sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores))**0.5:.3f}")
```

3. **Use temperature=0** in your agent's LLM calls for deterministic behavior (note: evolution engine calls remain stochastic).

---

## Issue 16: Workspace Manifest Validation Errors

**Symptoms**: `ValueError: Missing required field 'entrypoint' in manifest.yaml`

**Root cause**: Manifest format doesn't match expected schema.

**Fix**: Ensure manifest has all required fields:

```yaml
# Required format
agent:
  type: reference                              # Must be "reference"
  entrypoint: my_module.my_agent.MyAgentClass  # Dotted Python path

evolvable_layers:                              # At least one layer
  - prompts
  - skills
  - memory

reload_strategy: hot                           # "hot" or "cold"
```

Common mistakes:
- Missing `agent.type` field (must be `"reference"`)
- `entrypoint` is a file path instead of a Python dotted path
- `evolvable_layers` is empty or missing
- YAML indentation errors (use 2 spaces, not tabs)

Validate your manifest:
```python
import yaml
with open("manifest.yaml") as f:
    manifest = yaml.safe_load(f)
assert "agent" in manifest
assert "entrypoint" in manifest["agent"]
assert "evolvable_layers" in manifest
print("Manifest OK")
```

---

## Issue 17: Agent Cannot Import Custom Modules

**Symptoms**: `ModuleNotFoundError` when the evolver tries to instantiate the agent from `manifest.yaml` entrypoint.

**Root cause**: The custom agent module is not on the Python path.

**Fix**:

1. Install your agent as a package:
```bash
pip install -e .   # If your project has a pyproject.toml
```

2. Or add the directory to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/my/agent"
```

3. Or use an absolute import path in the manifest:
```yaml
agent:
  entrypoint: my_package.agents.custom.CustomAgent
```

Verify the import works:
```python
import importlib
module_path, class_name = "my_package.agents.custom.CustomAgent".rsplit(".", 1)
mod = importlib.import_module(module_path)
cls = getattr(mod, class_name)
print(f"Found: {cls}")
```

---

## Issue 18: Evolution Takes Too Long Per Cycle

**Symptoms**: Each evolution cycle takes 30+ minutes.

**Root causes and fixes**:

1. **Large batch_size**: Each task requires a full agent solve. Reduce:
```python
config = ae.EvolveConfig(batch_size=5)  # Fewer tasks per cycle
```

2. **Agent is slow per task**: Profile your `solve()` method:
```python
import time

class MyAgent(ae.BaseAgent):
    def solve(self, task):
        start = time.time()
        result = self._actual_solve(task)
        elapsed = time.time() - start
        print(f"Task {task.id}: {elapsed:.1f}s")
        return result
```

3. **Evolver model is too large**: Try a smaller model:
```python
config = ae.EvolveConfig(
    evolver_model="us.anthropic.claude-sonnet-4-6-v1",  # Faster evolver
)
```

4. **Observations too large**: Truncate trajectories before observation:
```python
def solve(self, task):
    # ... solve ...
    return ae.Trajectory(
        task_id=task.id,
        output=result,
        steps=steps[-10:],       # Only last 10 steps
        conversation=[],          # Skip full conversation
    )
```

---

## Issue 19: Skills Conflicting with System Prompt

**Symptoms**: Agent behavior degrades after skill discovery because skills contradict the base prompt.

**Root cause**: The evolver created skills with instructions that conflict with the system prompt's approach.

**Fix**:

1. **Review and remove conflicting skills**:
```python
workspace = ae.AgentWorkspace("./my-agent")
for skill in workspace.list_skills():
    content = workspace.read_skill(skill.name)
    print(f"\n--- {skill.name} ---")
    print(content[:300])
    # Manually delete: workspace.delete_skill(skill.name)
```

2. **Lock the prompt during skill evolution**:
```python
config = ae.EvolveConfig(
    evolve_prompts=False,   # Don't change the prompt
    evolve_skills=True,     # Only evolve skills
)
```

3. **Add constraints to skill descriptions**:
Skills with clear TRIGGER/DO NOT TRIGGER conditions are less likely to conflict:
```markdown
---
name: verify-output-format
description: "TRIGGER when: agent has produced final output. DO NOT TRIGGER: during intermediate reasoning steps."
---
```

---

## Issue 20: Holdout Set Leaking into Training

**Symptoms**: Training score and holdout score are suspiciously close, or holdout score drops when training score increases.

**Root cause**: Benchmark `get_tasks()` returns overlapping tasks for different splits.

**Fix**: Ensure strict separation:

```python
class MyBenchmark(ae.BenchmarkAdapter):
    def __init__(self, data_path):
        all_data = load_data(data_path)
        # Deterministic split
        random.seed(42)
        random.shuffle(all_data)
        split_idx = int(len(all_data) * 0.8)
        self._train = all_data[:split_idx]
        self._test = all_data[split_idx:]

    def get_tasks(self, split="train", limit=10):
        data = self._train if split == "train" else self._test
        if limit:
            data = data[:limit]
        return [ae.Task(id=d["id"], input=d["input"]) for d in data]
```

Verify no overlap:
```python
train_ids = {t.id for t in benchmark.get_tasks("train", limit=None)}
test_ids = {t.id for t in benchmark.get_tasks("test", limit=None)}
assert len(train_ids & test_ids) == 0, "Train/test overlap detected!"
```
