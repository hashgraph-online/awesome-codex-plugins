# A-Evolve Design Patterns

This document describes common patterns for building effective agents and benchmarks with A-Evolve. These patterns are derived from the built-in agents that achieved top-ranking benchmark results.

---

## Pattern 1: Verify-Fix Loop

**Used by**: SWE Agent (76.8% on SWE-bench Verified)
**Applicable to**: Any domain with verifiable outputs

The agent runs verification after each edit, fixing issues iteratively instead of generating a single output.

### Implementation

```python
class VerifyFixAgent(ae.BaseAgent):
    def solve(self, task: ae.Task) -> ae.Trajectory:
        steps = []
        output = ""

        for attempt in range(self.max_attempts):
            # 1. Generate solution
            solution = self._generate_solution(task, output, steps)
            steps.append({"action": "generate", "attempt": attempt})

            # 2. Verify
            test_result = self._run_tests(solution)
            steps.append({"action": "verify", "passed": test_result.passed})

            if test_result.passed:
                output = solution
                break

            # 3. Fix based on test feedback
            fix_prompt = f"Tests failed:\n{test_result.errors}\n\nFix the solution."
            output = solution  # Keep last attempt
            # Next iteration will use test_result as context

        return ae.Trajectory(task_id=task.id, output=output, steps=steps)
```

### Why It Works

- Tests provide precise, actionable feedback for each attempt
- Each fix is informed by specific failure details, not generic retry
- Converges faster than single-shot generation
- Works with any domain that has automated verification

### Evolution Interaction

The evolver can improve this pattern by:
- **Prompt**: Teaching the agent better debugging strategies
- **Skills**: Adding "common fix patterns" for recurring failure types
- **Memory**: Recording which test failures indicate which root causes

---

## Pattern 2: Hypothesis-First Exploration

**Used by**: SWE Agent
**Applicable to**: Debugging, investigation, analysis tasks

Before exploring the codebase, the agent forms a hypothesis about the root cause and tests it directly.

### Implementation

```python
class HypothesisFirstAgent(ae.BaseAgent):
    def solve(self, task: ae.Task) -> ae.Trajectory:
        steps = []

        # 1. Form hypothesis from task description
        hypothesis = self._form_hypothesis(task.input)
        steps.append({"action": "hypothesize", "hypothesis": hypothesis})

        # 2. Design minimal test
        test_plan = self._design_test(hypothesis)
        steps.append({"action": "plan_test", "plan": test_plan})

        # 3. Execute test (targeted exploration)
        evidence = self._execute_test(test_plan)
        steps.append({"action": "test", "evidence": evidence})

        # 4. If hypothesis confirmed, fix directly
        # If refuted, form new hypothesis with new information
        if evidence.supports_hypothesis:
            solution = self._implement_fix(hypothesis, evidence)
        else:
            # Refine and retry
            solution = self._explore_and_fix(task, evidence)

        return ae.Trajectory(task_id=task.id, output=solution, steps=steps)
```

### Why It Works

- Reduces exploration time by 60-80% compared to breadth-first search
- Focuses the agent's limited context window on the most relevant code
- Forms a narrative (hypothesis → evidence → conclusion) that improves reasoning
- Failed hypotheses still provide useful information (rules out possibilities)

### System Prompt Pattern

Include this in the evolved prompt:

```markdown
## Approach
1. Read the issue carefully and form a SPECIFIC hypothesis about the root cause
2. Identify the MINIMUM number of files to read to test your hypothesis
3. Read those files and check if your hypothesis is correct
4. If correct, implement the fix. If wrong, form a new hypothesis.

NEVER: Start by listing all files in the repository
NEVER: Read more than 3 files before forming a hypothesis
```

---

## Pattern 3: Skill Injection via System Prompt

**Used by**: All built-in agents
**Applicable to**: Any domain

The agent reads evolved skills and injects them into the LLM's system prompt, making skill knowledge available at inference time.

### Implementation

```python
class SkillAwareAgent(ae.BaseAgent):
    def solve(self, task: ae.Task) -> ae.Trajectory:
        # 1. Build system prompt with all skills
        system = self.system_prompt

        # 2. Append skill content
        if self.skills:
            skill_sections = []
            for skill_meta in self.skills:
                content = self.get_skill_content(skill_meta.name)
                skill_sections.append(
                    f"### {skill_meta.name}\n"
                    f"*{skill_meta.description}*\n\n"
                    f"{content}"
                )
            system += "\n\n## Learned Skills\n\n" + "\n\n".join(skill_sections)

        # 3. Append relevant memories
        if self.memories:
            memory_text = "\n".join(
                f"- {m['content']}" for m in self.memories[-10:]
            )
            system += f"\n\n## Lessons Learned\n{memory_text}"

        # 4. Call LLM with enriched prompt
        response = self._call_llm(system=system, user=task.input)
        return ae.Trajectory(task_id=task.id, output=response)
```

### Why It Works

- Skills provide domain-specific procedures that the base model doesn't have
- Memory provides recent lessons that prevent repeated mistakes
- The system prompt grows organically with each evolution cycle
- Skills have TRIGGER conditions so the LLM knows when to apply them

### Skill Filtering (Advanced)

For agents with many skills, filter to relevant ones:

```python
def _get_relevant_skills(self, task: ae.Task) -> list[ae.SkillMeta]:
    """Select skills whose TRIGGER matches the task."""
    relevant = []
    for skill in self.skills:
        # Simple keyword matching
        trigger = skill.description.lower()
        task_text = task.input.lower()
        if any(keyword in task_text for keyword in self._extract_keywords(trigger)):
            relevant.append(skill)
    return relevant or self.skills[:5]  # Fallback to first 5
```

---

## Pattern 4: Concurrent Timeout Enforcement

**Used by**: Terminal Agent (76.5% on Terminal-Bench 2.0)
**Applicable to**: Tasks with wall-clock time constraints

Wraps the solve logic in a timeout to prevent hanging on difficult tasks.

### Implementation

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError

class TimedAgent(ae.BaseAgent):
    def __init__(self, workspace_dir, timeout_seconds=300):
        super().__init__(workspace_dir)
        self.timeout = timeout_seconds

    def solve(self, task: ae.Task) -> ae.Trajectory:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self._solve_inner, task)
            try:
                return future.result(timeout=self.timeout)
            except TimeoutError:
                return ae.Trajectory(
                    task_id=task.id,
                    output="TIMEOUT: Task exceeded time limit",
                    steps=[{"action": "timeout", "limit": self.timeout}],
                )

    def _solve_inner(self, task: ae.Task) -> ae.Trajectory:
        # Actual solving logic (may take a long time)
        ...
```

### Why It Works

- Prevents a single hard task from blocking the entire evolution cycle
- Returns a failed trajectory instead of hanging (evolver can learn from timeout pattern)
- Keeps cycle time predictable and bounded

---

## Pattern 5: Progressive Prompt Refinement

**Evolved pattern**: The evolver discovers this organically during evolution

Rather than rewriting the prompt from scratch, the evolver makes incremental additions:

### Cycle 1: Base prompt (as written by human)
```markdown
You are an expert software engineer.
```

### Cycle 3: Add approach section
```markdown
You are an expert software engineer.

## Approach
1. Form a hypothesis about the root cause
2. Verify with minimal exploration
3. Implement a targeted fix
```

### Cycle 5: Add error handling
```markdown
You are an expert software engineer.

## Approach
1. Form a hypothesis about the root cause
2. Verify with minimal exploration
3. Implement a targeted fix

## Common Mistakes to Avoid
- Don't modify test files
- Always run the full test suite, not just the failing test
- Check for import side effects before editing __init__.py
```

### Cycle 8: Consolidate and refactor
```markdown
You are an expert software engineer who fixes bugs systematically.

## Method
1. HYPOTHESIZE: Read the issue and predict the root cause before exploring code
2. VERIFY: Read ≤3 files to confirm. If wrong, re-hypothesize with new information
3. FIX: Make the minimal change that addresses the root cause
4. TEST: Run the full test suite. If tests fail, read the error and iterate

## Rules
- Never modify test files
- Never read more than 5 files before attempting a fix
- Always check import side effects in __init__.py files
```

### Why It Works

- Each cycle adds knowledge from observed failures
- The evolver can see which rules helped (via score improvements)
- Consolidation prevents prompt bloat
- The prompt becomes a distilled version of "what works"

---

## Pattern 6: Observation-Enriched Feedback

**Key insight**: The quality of evolution depends heavily on the quality of feedback.

### Poor Feedback (limits evolution)
```python
def evaluate(self, task, trajectory):
    return ae.Feedback(success=passed, score=1.0 if passed else 0.0, detail="")
```

### Rich Feedback (enables targeted evolution)
```python
def evaluate(self, task, trajectory):
    test_results = run_tests(trajectory.output)
    failures = [t for t in test_results if not t.passed]
    
    detail_parts = []
    if failures:
        for f in failures[:3]:  # Top 3 failures
            detail_parts.append(f"FAIL {f.test_name}: {f.error_type} — {f.message[:100]}")
    
    detail_parts.append(f"Passed {len(test_results) - len(failures)}/{len(test_results)} tests")
    
    if trajectory.output:
        detail_parts.append(f"Output: {len(trajectory.output)} chars, {trajectory.output.count('\\n')} lines")
    
    score = (len(test_results) - len(failures)) / max(len(test_results), 1)
    
    return ae.Feedback(
        success=len(failures) == 0,
        score=score,
        detail="; ".join(detail_parts),
        raw={"test_results": [t.to_dict() for t in test_results]},
    )
```

### Why It Works

- The evolver reads `feedback.detail` to understand *why* the agent failed
- Specific error messages help the evolver create targeted skills
- Partial scores (0.7 instead of 0.0) show progress even when not fully passing
- `raw` data enables the evolver to do deeper analysis if needed

---

## Pattern 7: Multi-Model Agent Architecture

**Advanced pattern**: Use different models for different tasks within the same agent.

### Implementation

```python
class MultiModelAgent(ae.BaseAgent):
    def __init__(self, workspace_dir):
        super().__init__(workspace_dir)
        self.planning_model = "claude-opus-4-6-20250514"      # Strong reasoning
        self.execution_model = "claude-sonnet-4-20250514"      # Fast execution
        self.review_model = "claude-haiku-4-5-20251001"        # Quick validation

    def solve(self, task: ae.Task) -> ae.Trajectory:
        steps = []

        # 1. Plan with strong model
        plan = self._call(self.planning_model, 
            f"Analyze this task and create a plan:\n{task.input}")
        steps.append({"phase": "plan", "model": self.planning_model})

        # 2. Execute with fast model
        solution = self._call(self.execution_model,
            f"Execute this plan:\n{plan}\n\nTask:\n{task.input}")
        steps.append({"phase": "execute", "model": self.execution_model})

        # 3. Review with lightweight model
        review = self._call(self.review_model,
            f"Check this solution for obvious errors:\n{solution}")
        steps.append({"phase": "review", "model": self.review_model})

        if "error" in review.lower():
            # Fix errors with strong model
            solution = self._call(self.planning_model,
                f"Fix these issues:\n{review}\n\nSolution:\n{solution}")
            steps.append({"phase": "fix", "model": self.planning_model})

        return ae.Trajectory(task_id=task.id, output=solution, steps=steps)
```

### Cost Optimization

| Phase | Model | Cost | Reasoning Quality |
|-------|-------|------|------------------|
| Planning | Opus | High | Maximum |
| Execution | Sonnet | Medium | Good |
| Review | Haiku | Low | Sufficient |
| Fix (if needed) | Opus | High | Maximum |

Typical cost reduction: 40-60% vs using Opus for everything.

---

## Pattern 8: Workspace Partitioning for Multi-Stage Evolution

Run different evolution stages on different workspace layers.

### Stage 1: Prompt evolution only
```python
config_stage1 = ae.EvolveConfig(
    evolve_prompts=True,
    evolve_skills=False,
    evolve_memory=False,
    max_cycles=10,
)
```

### Stage 2: Skill discovery (prompt locked)
```python
config_stage2 = ae.EvolveConfig(
    evolve_prompts=False,
    evolve_skills=True,
    evolve_memory=True,
    max_cycles=15,
)
```

### Stage 3: Joint refinement
```python
config_stage3 = ae.EvolveConfig(
    evolve_prompts=True,
    evolve_skills=True,
    evolve_memory=True,
    max_cycles=10,
    egl_threshold=0.01,  # Fine-grained convergence
)
```

### Why It Works

- Prompt optimization first establishes a strong foundation
- Skills built on a good prompt are more focused
- Joint refinement catches interactions between layers
- Total cost may be lower than single-stage evolution

---

## Anti-Patterns

### Anti-Pattern 1: Unbounded Prompt Growth

**Problem**: Evolver keeps appending rules without consolidating.
**Symptom**: Prompt grows to 15K+ chars, agent performance degrades.
**Fix**: Periodically run a consolidation-focused cycle, or set max prompt length in config.

### Anti-Pattern 2: Skill Library Bloat

**Problem**: Every failure gets its own skill.
**Symptom**: 30+ narrow skills like "handle-empty-list" and "check-null-return".
**Fix**: Use the default SkillForge engine which merges overlapping skills. Target 5-10 broad skills.

### Anti-Pattern 3: Memory Without Curation

**Problem**: Every observation generates a memory entry.
**Symptom**: Hundreds of entries, many contradictory or outdated.
**Fix**: Only `remember()` lessons that are genuinely reusable. Let the evolver curate and consolidate.

### Anti-Pattern 4: Overfitting to Training Tasks

**Problem**: Agent scores 95% on training but 60% on holdout.
**Symptom**: Skills are too specific to training task patterns.
**Fix**: Use `holdout_ratio=0.2` to maintain a validation set. Ensure training tasks are diverse.

### Anti-Pattern 5: Ignoring Convergence

**Problem**: Running 50 cycles when score plateaued at cycle 10.
**Symptom**: Wasted compute, no improvement in last 40 cycles.
**Fix**: Set appropriate `egl_threshold` and `egl_window`. Check `results.converged` flag.
