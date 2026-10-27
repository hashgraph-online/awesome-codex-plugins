# A-Evolve Tutorials

## Tutorial 1: Build and Evolve a Custom Agent from Scratch

This tutorial walks through creating a complete agent-benchmark-evolution pipeline for a custom domain: text summarization quality.

### Step 1: Create the Workspace

```bash
mkdir -p summarizer/{prompts/fragments,skills,memory,tools}
```

Write the manifest:

```yaml
# summarizer/manifest.yaml
agent:
  type: reference
  entrypoint: summarizer_agent.SummarizerAgent

evolvable_layers:
  - prompts
  - skills
  - memory

reload_strategy: hot
```

Write the initial system prompt:

```markdown
# summarizer/prompts/system.md
You are an expert text summarizer. Given a document, produce a concise summary that captures the key points.

## Guidelines
- Keep summaries under 3 sentences for documents under 500 words
- Preserve numerical data and proper nouns
- Use active voice
- Do not add information not present in the source
```

Initialize git:

```bash
cd summarizer && git init && git add -A && git commit -m "Initial workspace"
```

### Step 2: Implement the Agent

```python
# summarizer_agent.py
import agent_evolve as ae
import anthropic

class SummarizerAgent(ae.BaseAgent):
    def __init__(self, workspace_dir: str):
        super().__init__(workspace_dir)
        self.client = anthropic.Anthropic()

    def solve(self, task: ae.Task) -> ae.Trajectory:
        # 1. Build system prompt with evolved content + skills
        skill_text = ""
        for skill_meta in self.skills:
            content = self.get_skill_content(skill_meta.name)
            skill_text += f"\n## Skill: {skill_meta.name}\n{content}\n"

        system = self.system_prompt
        if skill_text:
            system += f"\n\n# Learned Skills\n{skill_text}"

        # 2. Include episodic memories if available
        if self.memories:
            memory_text = "\n".join(
                f"- {m.get('content', '')}" for m in self.memories[-5:]
            )
            system += f"\n\n# Lessons Learned\n{memory_text}"

        # 3. Call the LLM
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": f"Summarize this:\n\n{task.input}"}],
        )
        output = response.content[0].text

        # 4. Record trajectory
        return ae.Trajectory(
            task_id=task.id,
            output=output,
            steps=[{
                "tool": "llm",
                "model": "claude-sonnet-4-20250514",
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }],
        )
```

**Key points:**
- `self.system_prompt` reads from `prompts/system.md` — this gets evolved
- `self.skills` lists skills discovered by the evolution engine
- `self.memories` contains episodic lessons from past failures
- All state is loaded from the workspace filesystem

### Step 3: Implement the Benchmark

```python
# summarizer_benchmark.py
import json
import agent_evolve as ae

class SummarizerBenchmark(ae.BenchmarkAdapter):
    def __init__(self, data_path: str):
        self.data_path = data_path

    def get_tasks(self, split="train", limit=10):
        with open(f"{self.data_path}/{split}.jsonl") as f:
            items = [json.loads(line) for line in f]
        if limit:
            items = items[:limit]
        return [
            ae.Task(
                id=item["id"],
                input=item["document"],
                metadata={
                    "reference_summary": item["summary"],
                    "key_facts": item.get("key_facts", []),
                },
            )
            for item in items
        ]

    def evaluate(self, task: ae.Task, trajectory: ae.Trajectory) -> ae.Feedback:
        reference = task.metadata["reference_summary"]
        generated = trajectory.output
        key_facts = task.metadata.get("key_facts", [])

        # Score components
        brevity_score = self._score_brevity(generated)
        fact_score = self._score_facts(generated, key_facts)
        quality_score = self._score_quality(generated, reference)

        # Weighted average
        score = 0.3 * brevity_score + 0.4 * fact_score + 0.3 * quality_score

        detail_parts = [
            f"brevity={brevity_score:.2f}",
            f"facts={fact_score:.2f} ({sum(1 for f in key_facts if f.lower() in generated.lower())}/{len(key_facts)})",
            f"quality={quality_score:.2f}",
        ]

        return ae.Feedback(
            success=score > 0.7,
            score=score,
            detail=", ".join(detail_parts),
            raw={"brevity": brevity_score, "facts": fact_score, "quality": quality_score},
        )

    def _score_brevity(self, summary: str) -> float:
        words = len(summary.split())
        if words <= 75:
            return 1.0
        elif words <= 150:
            return 0.7
        else:
            return max(0.0, 1.0 - (words - 75) / 200)

    def _score_facts(self, summary: str, key_facts: list[str]) -> float:
        if not key_facts:
            return 1.0
        found = sum(1 for fact in key_facts if fact.lower() in summary.lower())
        return found / len(key_facts)

    def _score_quality(self, generated: str, reference: str) -> float:
        # Simple word overlap metric (replace with ROUGE in production)
        gen_words = set(generated.lower().split())
        ref_words = set(reference.lower().split())
        if not ref_words:
            return 0.0
        overlap = len(gen_words & ref_words)
        precision = overlap / (len(gen_words) + 1e-9)
        recall = overlap / len(ref_words)
        return 2 * precision * recall / (precision + recall + 1e-9)
```

**Key design decisions:**
- Multiple scoring components give the evolver rich signal about *what* to improve
- `feedback.detail` includes component breakdowns — the evolver reads these to decide what to mutate
- `feedback.raw` stores structured data for post-hoc analysis

### Step 4: Prepare the Dataset

```python
# prepare_data.py
import json
import os

os.makedirs("data", exist_ok=True)

train_data = [
    {
        "id": "train-001",
        "document": "The Federal Reserve announced today that it will maintain...",
        "summary": "The Fed held interest rates steady at 5.25-5.50%...",
        "key_facts": ["5.25-5.50%", "Federal Reserve", "inflation target"],
    },
    # ... add 50-100 training examples
]

test_data = [
    # ... add 20-30 held-out test examples
]

with open("data/train.jsonl", "w") as f:
    for item in train_data:
        f.write(json.dumps(item) + "\n")

with open("data/test.jsonl", "w") as f:
    for item in test_data:
        f.write(json.dumps(item) + "\n")
```

**Pro Tips:**
- Training set should cover diverse document types (news, technical, narrative)
- Include edge cases: very short documents, documents with tables/lists, multi-topic documents
- Key facts should be objective and verifiable (numbers, names, dates)

### Step 5: Run Evolution

```python
# evolve_summarizer.py
import agent_evolve as ae
from summarizer_agent import SummarizerAgent
from summarizer_benchmark import SummarizerBenchmark

config = ae.EvolveConfig(
    batch_size=10,              # 10 documents per evolution cycle
    max_cycles=15,              # 15 rounds of improvement
    evolve_prompts=True,        # Mutate the system prompt
    evolve_skills=True,         # Discover summarization skills
    evolve_memory=True,         # Learn from failures
    holdout_ratio=0.2,          # 20% held out for validation
    evolver_model="us.anthropic.claude-opus-4-6-v1",
    egl_threshold=0.02,         # Stop if < 2% improvement
    egl_window=4,               # Over 4 consecutive cycles
)

evolver = ae.Evolver(
    agent=SummarizerAgent("./summarizer"),
    benchmark=SummarizerBenchmark("./data"),
    config=config,
)

results = evolver.run()

print(f"Evolution complete!")
print(f"  Cycles: {results.cycles_completed}")
print(f"  Final score: {results.final_score:.3f}")
print(f"  Converged: {results.converged}")
print(f"  Score trajectory: {[f'{s:.3f}' for s in results.score_history]}")
```

### Step 6: Inspect the Evolved Agent

```bash
# See what changed
cd summarizer
git log --oneline --decorate

# Compare initial vs final prompt
git diff evo-1 evo-15 -- prompts/system.md

# List discovered skills
ls skills/
# Example: skills/handle-numerical-data/SKILL.md
#          skills/multi-topic-structure/SKILL.md

# Read a discovered skill
cat skills/handle-numerical-data/SKILL.md
```

Example evolved prompt additions (actual results will vary):

```markdown
## Numerical Data Handling
When the source contains numbers, percentages, or dates:
1. Always include the exact figure in your summary
2. Provide context for the number (what it measures, comparison point)
3. Round only when the original uses approximate language

## Multi-Topic Documents
For documents covering multiple distinct topics:
1. Identify the primary topic (most space/emphasis in source)
2. Lead with the primary topic
3. Mention secondary topics only if they affect the primary narrative
```

### Step 7: Iterate and Refine

After reviewing the evolved state, you can:

1. **Run more cycles** on the same workspace:
```python
# The workspace retains its evolved state
results2 = evolver.run(cycles=10)  # 10 more cycles
```

2. **Adjust configuration** based on what you see:
```python
# If skills are too narrow, let the evolver merge them
config.extra["merge_threshold"] = 0.7

# If the prompt is growing too long, enable pruning
config.extra["max_prompt_length"] = 5000
```

3. **Add harder tasks** to the benchmark to push the agent further:
```python
# Add adversarial examples
hard_tasks = [
    {"id": "hard-001", "document": "...", "summary": "...",
     "key_facts": ["subtle fact buried in paragraph 4"]},
]
```

---

## Tutorial 2: Evolve a Built-in Agent on a Standard Benchmark

For a faster start, use one of the built-in agent + benchmark combinations.

### SWE-bench Evolution

```python
import agent_evolve as ae

# 1. Create evolver with built-in seed
evolver = ae.Evolver(
    agent="swe",                    # Uses seed_workspaces/swe/
    benchmark="swe-verified",       # SWE-bench Verified dataset
    config=ae.EvolveConfig(
        batch_size=10,
        max_cycles=20,
        evolve_skills=True,
    ),
)

# 2. Run evolution
results = evolver.run()

# 3. The evolved workspace is at evolver._workspace.path
print(f"Evolved workspace: {evolver._workspace.path}")
print(f"Score improvement: {results.score_history[0]:.3f} -> {results.final_score:.3f}")
```

**What happens under the hood:**
1. The `"swe"` seed workspace is copied to a working directory
2. `SweAgent` is instantiated with the workspace path
3. Each cycle: agent solves 10 SWE-bench tasks, benchmark evaluates patches
4. The SkillForge engine analyzes failures and mutates prompts/skills
5. Agent reloads evolved state and solves the next batch

### Terminal-Bench Evolution

```python
import agent_evolve as ae

evolver = ae.Evolver(
    agent="terminal",
    benchmark="terminal2",
    config=ae.EvolveConfig(
        batch_size=5,               # Terminal tasks are slower
        max_cycles=15,
        evolve_skills=True,
        evolve_memory=False,        # Terminal tasks are time-sensitive
    ),
)
results = evolver.run()
```

### MCP-Atlas Evolution

```python
import agent_evolve as ae

evolver = ae.Evolver(
    agent="mcp",
    benchmark="mcp-atlas",
    config=ae.EvolveConfig(
        batch_size=10,
        max_cycles=20,
    ),
)
results = evolver.run()
```

---

## Tutorial 3: Using Different Evolution Algorithms

A-Evolve ships four evolution algorithms. Choose based on your domain:

### Default: A-Evolve/SkillForge

Best for general-purpose evolution. Uses an LLM with bash tools to directly edit workspace files.

```python
# This is the default — no need to specify engine
evolver = ae.Evolver(agent="swe", benchmark="swe-verified")
```

### Guided Synthesis

Best for domains where skill discovery is the primary goal. Focuses on extracting lessons from failures and curating a minimal skill library.

```python
from agent_evolve.algorithms.guided_synth import GuidedSynthesisEngine

evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    engine=GuidedSynthesisEngine(config),
)
```

### Adaptive Evolution

Best for fine-grained control. Filters observations intelligently and tracks reward signals to adjust intervention density.

```python
from agent_evolve.algorithms.adaptive import AdaptiveEvolutionEngine

evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    engine=AdaptiveEvolutionEngine(config),
)
```

### Adaptive Skill

Best for skill-heavy domains where the primary improvement comes from building a procedure library.

```python
from agent_evolve.algorithms.adaptive_skill import AdaptiveSkillEngine

evolver = ae.Evolver(
    agent="swe",
    benchmark="swe-verified",
    engine=AdaptiveSkillEngine(config),
)
```

---

## Tutorial 4: Post-Evolution Analysis

After an evolution run, understanding what changed is crucial for deciding next steps.

### Score Trajectory Analysis

```python
import matplotlib.pyplot as plt

results = evolver.run(cycles=15)

# Plot score curve
plt.figure(figsize=(10, 5))
plt.plot(range(1, len(results.score_history) + 1), results.score_history, marker='o')
plt.xlabel("Cycle")
plt.ylabel("Score")
plt.title("Evolution Score Trajectory")
plt.grid(True, alpha=0.3)
plt.savefig("evolution_curve.png")
```

### Workspace Diff Analysis

```bash
cd my-workspace

# What changed overall?
git diff evo-1 evo-15 --stat

# Prompt changes
git diff evo-1 evo-15 -- prompts/system.md

# New skills
git diff evo-1 evo-15 -- skills/

# Memory entries
git diff evo-1 evo-15 -- memory/
```

### Skill Library Review

```python
workspace = evolver._workspace

for skill in workspace.list_skills():
    content = workspace.read_skill(skill.name)
    print(f"\n{'='*60}")
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"{'='*60}")
    print(content[:500])  # First 500 chars
```

### Cycle-by-Cycle Breakdown

```bash
# Compare consecutive cycles to see what each evolution step did
for i in $(seq 1 14); do
    next=$((i + 1))
    echo "=== Cycle $i -> $next ==="
    git diff evo-$i evo-$next --stat
done
```

### Identifying Key Mutations

Look for the cycles where score jumped most:

```python
scores = results.score_history
for i in range(1, len(scores)):
    delta = scores[i] - scores[i-1]
    if delta > 0.03:  # Significant improvement
        print(f"Cycle {i+1}: +{delta:.3f} (check evo-{i} -> evo-{i+1})")
```

Then inspect those specific diffs to understand which mutations were most impactful.

---

## Tutorial 5: Configuring Evolution for Different Domains

Different domains require different evolution configurations. This tutorial covers how to tune the key parameters.

### Fast-Feedback Domains (Classification, Summarization)

When tasks are cheap to evaluate and take seconds per solve:

```python
config = ae.EvolveConfig(
    batch_size=20,              # More tasks per cycle = richer signal
    max_cycles=30,              # More cycles since they're cheap
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=True,         # Memory helps for pattern recognition
    egl_threshold=0.01,         # Fine-grained convergence
    egl_window=5,               # Long patience window
)
```

**Why these settings:**
- Large batches give the evolver more observations to find patterns
- Memory is valuable because the agent sees many similar tasks
- Tight convergence threshold avoids stopping too early

### Slow-Feedback Domains (Code Generation, Multi-Step Reasoning)

When tasks take minutes per solve and evaluation is expensive:

```python
config = ae.EvolveConfig(
    batch_size=5,               # Fewer tasks to keep cycle time manageable
    max_cycles=15,              # Fewer cycles, each more impactful
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=False,        # Skip memory for time-sensitive tasks
    egl_threshold=0.05,         # Larger threshold — significant improvements only
    egl_window=3,               # Shorter patience
    evolver_max_tokens=32768,   # More tokens for complex analysis
)
```

**Why these settings:**
- Small batches keep wall-clock time reasonable
- Memory disabled because tasks are diverse enough that past lessons rarely transfer
- Generous convergence threshold — each improvement is expensive to achieve

### Skill-Discovery Focused Domains

When the agent's core reasoning is good but it needs domain-specific procedures:

```python
config = ae.EvolveConfig(
    batch_size=10,
    max_cycles=25,
    evolve_prompts=False,       # Keep prompt stable
    evolve_skills=True,         # Focus entirely on skills
    evolve_memory=True,         # Memory informs skill creation
    evolve_tools=False,
)
```

Use the `AdaptiveSkillEngine` for this:

```python
from agent_evolve.algorithms.adaptive_skill import AdaptiveSkillEngine

evolver = ae.Evolver(
    agent="./my-agent",
    benchmark=my_benchmark,
    config=config,
    engine=AdaptiveSkillEngine(config),
)
```

### Trajectory-Only Evolution (Blind Mode)

When you want to test if the evolver can improve the agent without seeing scores:

```python
config = ae.EvolveConfig(
    trajectory_only=True,       # Hide scores from evolver
    batch_size=10,
    max_cycles=20,
)
```

**Why use this:**
- Tests whether the evolver can infer quality from behavior alone
- Prevents the evolver from "gaming" the metric
- More realistic — mirrors how humans improve agents (by reading outputs, not scores)

---

## Tutorial 6: Multi-Stage Evolution

For complex agents, run multiple evolution stages with different configurations.

### Stage 1: Prompt Optimization

First, optimize the core system prompt without skills:

```python
import agent_evolve as ae

# Stage 1: Prompt-only evolution
config_prompt = ae.EvolveConfig(
    batch_size=10,
    max_cycles=10,
    evolve_prompts=True,
    evolve_skills=False,        # No skills yet
    evolve_memory=False,
)

evolver = ae.Evolver(
    agent="./my-agent",
    benchmark=my_benchmark,
    config=config_prompt,
)
results_prompt = evolver.run()
print(f"After prompt optimization: {results_prompt.final_score:.3f}")
```

### Stage 2: Skill Discovery

Now evolve skills on top of the optimized prompt:

```python
# Stage 2: Skill evolution (workspace retains optimized prompt)
config_skills = ae.EvolveConfig(
    batch_size=10,
    max_cycles=15,
    evolve_prompts=False,       # Lock the prompt
    evolve_skills=True,         # Focus on skills
    evolve_memory=True,
)

# Re-create evolver pointing to the same evolved workspace
evolver_skills = ae.Evolver(
    agent=evolver._workspace.path,   # Use the evolved workspace
    benchmark=my_benchmark,
    config=config_skills,
)
results_skills = evolver_skills.run()
print(f"After skill discovery: {results_skills.final_score:.3f}")
```

### Stage 3: Joint Refinement

Finally, fine-tune everything together:

```python
# Stage 3: Joint refinement
config_joint = ae.EvolveConfig(
    batch_size=15,              # Larger batches for fine-tuning
    max_cycles=10,
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=True,
    egl_threshold=0.01,         # Very tight convergence
    egl_window=5,
)

evolver_joint = ae.Evolver(
    agent=evolver_skills._workspace.path,
    benchmark=my_benchmark,
    config=config_joint,
)
results_final = evolver_joint.run()
print(f"Final score: {results_final.final_score:.3f}")
print(f"Total improvement: {results_prompt.score_history[0]:.3f} -> {results_final.final_score:.3f}")
```

**Why multi-stage:**
- Prompt optimization first establishes a strong baseline
- Skills built on a good prompt are more targeted
- Joint refinement catches interactions between prompt and skills
- Total cycles may be fewer than single-stage evolution to the same quality

---

## Tutorial 7: Workspace Organization Best Practices

### Prompt Fragments

Instead of one monolithic system prompt, use fragments for modular evolution:

```
my-agent/prompts/
├── system.md              # Core identity and approach
└── fragments/
    ├── reasoning.md       # Step-by-step reasoning instructions
    ├── output_format.md   # Output formatting rules
    └── domain_rules.md    # Domain-specific constraints
```

Your agent can compose these:

```python
class MyAgent(ae.BaseAgent):
    def _build_system_prompt(self):
        base = self.system_prompt  # From prompts/system.md
        workspace = AgentWorkspace(self._workspace_dir)
        fragments = workspace.list_fragments()
        for frag_name in fragments:
            content = workspace.read_fragment(frag_name)
            base += f"\n\n{content}"
        return base
```

### Skill Organization

Skills should be broad procedures, not narrow fixes:

```
skills/
├── verify-solution/         # Good: broad procedure
│   └── SKILL.md
├── handle-edge-cases/       # Good: reusable pattern
│   └── SKILL.md
└── debug-and-fix/           # Good: general workflow
    └── SKILL.md
```

**Avoid:**
```
skills/
├── fix-django-test-runner/     # Too narrow
├── handle-empty-list-input/    # Too narrow
├── use-pytest-fixtures/        # Too narrow
└── ...30 more narrow skills    # Library bloat
```

The default SkillForge engine merges overlapping skills automatically. If using a custom engine, implement merging:

```python
def _should_merge(self, existing_skill: str, new_skill: str) -> bool:
    """Check if two skills cover overlapping procedures."""
    # Compare skill descriptions and content for overlap
    overlap = compute_similarity(existing_skill, new_skill)
    return overlap > 0.6

def _merge_skills(self, workspace, existing_name: str, new_content: str):
    """Merge a new skill into an existing one."""
    existing = workspace.read_skill(existing_name)
    merged = llm_merge(existing, new_content)  # Use LLM to combine
    workspace.write_skill(existing_name, merged)
```

### Memory Categories

Use categories to organize episodic memory:

```python
# During solve
self.remember("Test runner requires --no-header flag", category="tool_quirks")
self.remember("Django uses reverse URL resolution", category="domain_knowledge")
self.remember("Off-by-one in loop caused test failure", category="common_errors")

# During prompt composition
tool_memories = workspace.read_memories(category="tool_quirks", limit=10)
error_memories = workspace.read_memories(category="common_errors", limit=20)
```

### Git Tagging Strategy

The evolution loop creates `pre-evo-N` and `evo-N` tags. You can add custom tags:

```bash
# Tag a particularly good checkpoint
git tag "best-v1" evo-7

# Tag before a major config change
git tag "pre-stage2" evo-10
```

This makes it easy to compare across stages:

```bash
git diff best-v1 evo-15 -- prompts/system.md
git diff pre-stage2 evo-20 -- skills/
```
