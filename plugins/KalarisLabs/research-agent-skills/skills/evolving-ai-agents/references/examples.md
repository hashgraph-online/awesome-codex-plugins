# A-Evolve Real-World Examples

## Example 1: Evolve a SWE-Bench Agent

The most common use case — optimize an agent that solves GitHub issues.

### Minimal Run

```python
import agent_evolve as ae

evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
results = evolver.run(cycles=10)
print(f"Score: {results.final_score:.1%}")
```

### Full Configuration

```python
import agent_evolve as ae

config = ae.EvolveConfig(
    batch_size=15,
    max_cycles=30,
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=True,
    evolver_model="us.anthropic.claude-opus-4-6-v1",
    egl_threshold=0.03,    # Tighter convergence
    egl_window=5,          # Longer patience
)

evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    config=config,
)
results = evolver.run()

# Inspect evolution trajectory
for i, score in enumerate(results.score_history):
    print(f"Cycle {i + 1}: {score:.3f}")
```

### Expected Output

```
Cycle 1: 0.620 — Established baseline, no mutations
Cycle 2: 0.640 — Added verify-before-submit skill
Cycle 3: 0.680 — Refined system prompt to prioritize test discovery
Cycle 4: 0.720 — Added edge-case-testing skill, merged with verify
Cycle 5: 0.730 — Memory: common Django test patterns
Cycle 6: 0.740 — Prompt: explicit hypothesis-first workflow
Cycle 7: 0.740 — No improvement
Cycle 8: 0.745 — Minor skill refinement
Cycle 9: 0.750 — Converged (< 0.03 improvement over 5 cycles)
Final score: 0.750
```

---

## Example 2: Batch Solve Without Evolution

Run the agent across many tasks in parallel without evolving — useful for benchmarking a snapshot.

```python
import agent_evolve as ae
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load agent and benchmark
evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
agent = evolver._agent
benchmark = evolver._benchmark

# Get all tasks
tasks = benchmark.get_tasks(split="test", limit=50)

results = []
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(agent.solve, task): task for task in tasks}
    for future in as_completed(futures):
        task = futures[future]
        trajectory = future.result()
        feedback = benchmark.evaluate(task, trajectory)
        results.append((task.id, feedback.score, feedback.success))
        print(f"{task.id}: {'✓' if feedback.success else '✗'} ({feedback.score:.2f})")

# Summary
passed = sum(1 for _, _, s in results if s)
print(f"\nTotal: {passed}/{len(results)} ({passed/len(results):.1%})")
```

---

## Example 3: Sequential Evolution with Feedback Modes

Compare evolution with and without score visibility:

```python
import agent_evolve as ae

# Mode 1: Evolver sees full feedback (scores + details)
config_full = ae.EvolveConfig(
    batch_size=10,
    max_cycles=10,
    trajectory_only=False,
)
evolver_full = ae.Evolver(agent="swe", benchmark="swe-verified", config=config_full)
results_full = evolver_full.run()

# Mode 2: Evolver only sees trajectories (must infer quality)
config_blind = ae.EvolveConfig(
    batch_size=10,
    max_cycles=10,
    trajectory_only=True,
)
evolver_blind = ae.Evolver(agent="swe", benchmark="swe-verified", config=config_blind)
results_blind = evolver_blind.run()

print(f"Full feedback: {results_full.final_score:.1%}")
print(f"Blind mode:    {results_blind.final_score:.1%}")
```

---

## Example 4: Custom Agent for Code Review

Build an agent that reviews pull requests and evolve it:

```python
import agent_evolve as ae
import anthropic

class CodeReviewAgent(ae.BaseAgent):
    def __init__(self, workspace_path: str):
        super().__init__(workspace_path)
        self.client = anthropic.Anthropic()

    def solve(self, task: ae.Task) -> ae.Trajectory:
        # Build prompt with evolved system prompt and skills
        messages = [
            {"role": "user", "content": f"Review this diff:\n\n{task.input}"}
        ]

        # Inject skills into system prompt
        skill_text = "\n".join(
            f"## {s.name}\n{self.get_skill_content(s.name)}"
            for s in self.skills
        )
        system = f"{self.system_prompt}\n\n# Available Skills\n{skill_text}"

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            messages=messages,
        )
        output = response.content[0].text

        return ae.Trajectory(
            task_id=task.id,
            output=output,
            steps=[{"tool": "llm", "action": "review", "tokens": response.usage.output_tokens}],
        )


class CodeReviewBenchmark(ae.BenchmarkAdapter):
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path

    def get_tasks(self, split="train", limit=None):
        import json
        with open(f"{self.dataset_path}/{split}.jsonl") as f:
            items = [json.loads(line) for line in f]
        if limit:
            items = items[:limit]
        return [
            ae.Task(
                id=item["id"],
                input=item["diff"],
                metadata={"expected_comments": item["comments"]},
            )
            for item in items
        ]

    def evaluate(self, task, trajectory):
        expected = set(task.metadata["expected_comments"])
        actual = set(extract_comments(trajectory.output))
        tp = len(expected & actual)
        precision = tp / (len(actual) + 1e-9)
        recall = tp / (len(expected) + 1e-9)
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        return ae.Feedback(
            success=f1 > 0.6,
            score=f1,
            detail=f"Found {tp}/{len(expected)} issues (P={precision:.2f} R={recall:.2f})",
        )


# Set up workspace
# mkdir -p my-reviewer/prompts my-reviewer/skills my-reviewer/memory
# Write manifest.yaml and prompts/system.md

evolver = ae.Evolver(
    agent=CodeReviewAgent("./my-reviewer"),
    benchmark=CodeReviewBenchmark("./review-data"),
    config=ae.EvolveConfig(batch_size=5, max_cycles=15),
)
results = evolver.run()
```

---

## Example 5: Custom Evolution Engine

A rule-based engine that appends learned patterns to the system prompt:

```python
import agent_evolve as ae
import re
from collections import Counter

class PatternLearningEngine(ae.EvolutionEngine):
    def step(self, workspace, observations, history, trial):
        failures = [o for o in observations if not o.feedback.success]
        if not failures:
            return ae.StepResult(mutated=False, summary="All passed, no mutations needed")

        # Categorize failure patterns
        patterns = Counter()
        for obs in failures:
            detail = obs.feedback.detail.lower()
            if "timeout" in detail:
                patterns["timeout"] += 1
            elif "assertion" in detail or "test" in detail:
                patterns["test_failure"] += 1
            elif "syntax" in detail or "parse" in detail:
                patterns["syntax_error"] += 1
            else:
                patterns["unknown"] += 1

        # Generate rules for top patterns
        rules = []
        if patterns["timeout"] > 0:
            rules.append("- Before submitting, verify the solution completes within time limits")
        if patterns["test_failure"] > 1:
            rules.append("- Run ALL related tests, not just the failing one")
        if patterns["syntax_error"] > 0:
            rules.append("- Validate syntax after every edit")

        if not rules:
            return ae.StepResult(mutated=False, summary="No actionable patterns found")

        # Append rules to prompt
        prompt = workspace.read_prompt()
        rule_block = "\n\n## Learned Rules (Auto-Generated)\n" + "\n".join(rules)
        workspace.write_prompt(prompt + rule_block)

        return ae.StepResult(
            mutated=True,
            summary=f"Added {len(rules)} rules from {len(failures)} failures",
            metadata={"patterns": dict(patterns), "rules": rules},
        )

# Use the custom engine
evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    engine=PatternLearningEngine(),
)
results = evolver.run(cycles=10)
```

---

## Example 6: Inspecting Evolution History

After an evolution run, analyze what happened:

```python
import agent_evolve as ae

evolver = ae.Evolver(agent="./evolved-swe", benchmark="swe-verified")
results = evolver.run(cycles=5)

# Access workspace for post-mortem
workspace = evolver._workspace

# Read the evolved system prompt
final_prompt = workspace.read_prompt()
print(f"Final prompt length: {len(final_prompt)} chars")

# List discovered skills
for skill in workspace.list_skills():
    print(f"  Skill: {skill.name} — {skill.description}")

# Read evolution history
history = evolver._history
scores = history.get_score_curve()
for cycle, score in scores:
    print(f"  Cycle {cycle}: {score:.3f}")

# Compare workspace at different points
diff = history.get_workspace_diff("evo-1", "evo-5")
print(f"\nChanges from cycle 1 to 5:\n{diff}")

# Read prompt as it was at cycle 3
old_prompt = history.read_file_at("evo-3", "prompts/system.md")
```

---

## Example 7: Workspace Setup from Scratch

Create a new agent workspace manually:

```bash
mkdir -p my-agent/{prompts,skills,memory,tools}

# manifest.yaml
cat > my-agent/manifest.yaml << 'EOF'
agent:
  type: reference
  entrypoint: my_module.agent.MyAgent
evolvable_layers:
  - prompts
  - skills
  - memory
reload_strategy: hot
EOF

# System prompt
cat > my-agent/prompts/system.md << 'EOF'
You are an expert assistant. Analyze the given task carefully, break it into steps, and produce a high-quality solution.

## Approach
1. Understand the task requirements
2. Plan your approach
3. Execute step by step
4. Verify your solution
EOF

# Initialize git for version tracking
cd my-agent && git init && git add -A && git commit -m "Initial workspace"
```

Then point the evolver at it:

```python
evolver = ae.Evolver(agent="./my-agent", benchmark=MyBenchmark())
```
