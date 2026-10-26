# Eval & Simulation Code Patterns

Code anatomy and worked patterns for behavioral evaluation and simulation. The decision rules for *when* to use these live in SKILL.md; this file is the implementation reference.

## Eval anatomy

```python
@dataclass
class EvalTask:
    """A single eval case."""
    name: str                    # Descriptive scenario name
    input: dict                  # The input to the system under test
    expected_traits: list[str]   # What the output MUST exhibit
    forbidden_traits: list[str]  # What the output MUST NOT exhibit
    grader: str                  # "deterministic" | "llm-judge" | "human"

@dataclass
class EvalResult:
    task: EvalTask
    output: Any                  # Actual system output
    passed: bool                 # Did it meet all criteria?
    score: float                 # 0.0 - 1.0 granular score
    reasoning: str               # Why it passed/failed (from grader)
    trial_id: str                # For statistical analysis across runs
```

## LLM-as-Judge pattern

The caller reads the model from `${XDG_CONFIG_HOME:-$HOME/.config}/sno/models.toml`,
role `eval` in an optional `[models]` section (for example, `eval = "model-name"`). Pass that value as `judge_model`; use `None` for an absent
file, missing role, or empty value. In that case omit the model argument entirely
so the harness uses its current default. Never supply a fallback name. Shell
launchers use the shared `peer-review/scripts/lib/sno-model.sh` resolver, located
relative to their own skill directory, and add a model flag only for a nonempty result.

```python
async def llm_judge(output: str, rubric: str, task: EvalTask, judge_model: str | None = None) -> EvalResult:
    """Use a strong model to grade output against a rubric.

    Key: The judge model should be MORE capable than the system under test.
    """
    judge_prompt = f"""Grade this output against the rubric.

RUBRIC:
{rubric}

EXPECTED TRAITS (all must be present):
{task.expected_traits}

FORBIDDEN TRAITS (none may be present):
{task.forbidden_traits}

OUTPUT TO GRADE:
{output}

Respond with JSON: {{"passed": bool, "score": 0.0-1.0, "reasoning": "..."}}"""

    # Call judge model (via the configured environment, real API)
    model_options = {"model": judge_model} if judge_model else {}
    result = await llm_client.complete(judge_prompt, **model_options)
    return parse_judge_response(result)
```

## Simulation anatomy

```python
@dataclass
class SimScenario:
    """A multi-step behavioral test scenario."""
    name: str                      # e.g., "Auto-Capture on Session End"
    goal: str                      # What this scenario proves
    prerequisites: list[str]       # Config/state required before running
    steps: list[SimStep]           # Ordered actions
    expected_outcomes: list[str]   # Observable results after all steps
    debug_hints: dict[str, str]    # "What to check if it fails" → diagnosis

@dataclass
class SimStep:
    action: str          # What to do (human-readable)
    input: Any           # Concrete input data
    expected: str        # What should happen at this step
    verify: str          # How to verify (query, assertion, observation)
```

## Simulation patterns

```python
# Pattern 1: Lifecycle Hook Simulation
# Tests: plugin hooks fire in correct order with correct data

async def test_plugin_lifecycle_capture_recall():
    """Verify auto-capture on session end → auto-recall on next session start."""
    # Step 1: Store memorable content in session
    session = create_test_session()
    await session.send("My dog's name is Biscuit, a golden retriever born March 15, 2022")

    # Step 2: End session (triggers capture hook)
    await session.end()

    # Step 3: Verify capture happened (observable side effect)
    stats = await memory_service.get_stats()
    assert stats.total_memories >= 1

    # Step 4: Start new session (triggers recall hook)
    new_session = create_test_session()
    response = await new_session.send("What's my dog's name?")

    # Step 5: Verify recall injected context (behavioral contract)
    assert "Biscuit" in response.content or "golden retriever" in response.content
```

```python
# Pattern 2: Persona-Driven Simulation
# Tests: system handles diverse user behaviors correctly

PERSONAS = [
    Persona(name="expert", style="terse, uses jargon", patience="low"),
    Persona(name="novice", style="verbose, asks clarifying questions", patience="high"),
    Persona(name="frustrated", style="impatient, repeats requests", patience="none"),
]

async def test_system_handles_all_personas():
    """Each persona should get appropriate, helpful responses."""
    for persona in PERSONAS:
        scenario = build_scenario(persona, task="retrieve stored preferences")
        result = await run_simulation(scenario, max_turns=5)

        # Grade with LLM judge
        eval_result = await llm_judge(
            output=result.transcript,
            rubric="Agent must complete the task regardless of user tone. "
                   "Must not mirror frustration. Must not require more than 3 turns.",
            task=scenario.eval_task,
            judge_model=eval_model,  # Caller-resolved role eval; None means harness default.
        )
        assert eval_result.passed, f"Failed for persona {persona.name}: {eval_result.reasoning}"
```

```python
# Pattern 3: Noise Filtering Simulation
# Tests: system correctly filters trivial vs. substantive content

async def test_noise_filter_captures_only_substantive():
    """Trivial messages filtered, substantive ones captured."""
    session = create_test_session(auto_capture=True)

    # Send noise
    for msg in ["ok", "thanks", "yes", "got it", "sure"]:
        await session.send(msg)

    # Send signal
    await session.send(
        "The database migration requires PostgreSQL 15 with pgvector extension"
    )

    await session.end()
    stats = await memory_service.get_stats()
    assert stats.total_memories == 1  # Only substantive message captured
```

```python
# Pattern 4: Cross-Session Persistence Simulation
# Tests: data survives session boundaries

async def test_cross_session_memory_persistence():
    """Memories from session A are available in session B."""
    # Session A: store facts
    session_a = create_test_session()
    facts = ["I prefer dark mode", "My timezone is PST", "I use Neovim"]
    for fact in facts:
        await session_a.store_memory(fact)
    await session_a.end()

    # Session B: recall facts
    session_b = create_test_session()
    response = await session_b.send("What editor do I use?")

    # Verify cross-session persistence
    assert "Neovim" in response.content
```

## A/B evaluation

```python
async def ab_eval(
    task_set: list[EvalTask],
    system_a: Callable,  # Current version
    system_b: Callable,  # New version
    judge_model: str | None = None,
    trials_per_task: int = 3,
) -> ABResult:
    """Blind A/B comparison. Judge doesn't know which is A or B."""
    results = []
    for task in task_set:
        for trial in range(trials_per_task):
            output_a = await system_a(task.input)
            output_b = await system_b(task.input)

            # Randomize order to prevent position bias
            if random.random() > 0.5:
                first, second, order = output_a, output_b, "ab"
            else:
                first, second, order = output_b, output_a, "ba"

            judgment = await llm_judge_comparison(
                first, second, task.expected_traits, judge_model
            )
            results.append(ABTrialResult(task, judgment, order))

    return aggregate_ab_results(results)
```

## Concurrency test patterns

```python
async def test_concurrent_group_processing_maintains_isolation():
    """Two groups processed concurrently must not interfere."""
    async def process_group(group_id: str) -> dict:
        return await service.memorize(group_id=group_id, data=make_test_data())

    result_a, result_b = await asyncio.gather(
        process_group(f"group-a-{TEST_RUN_ID}"),
        process_group(f"group-b-{TEST_RUN_ID}"),
    )
    assert result_a["group_id"] != result_b["group_id"]
    # Verify no cross-contamination in DB
```

```python
async def test_lock_prevents_double_processing():
    """Same group submitted twice concurrently: second should wait or reject."""
    group_id = f"group-{TEST_RUN_ID}"
    results = await asyncio.gather(
        service.process(group_id),
        service.process(group_id),
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 1  # At least one succeeds
```
