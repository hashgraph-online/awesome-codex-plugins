# Independent Skill Behavior Testing

Read this reference only when a complex or high-risk skill benefits from an
independent evaluator and subagent support is available. It refines the
behavior-validation path in `SKILL.md`; it does not create a code TDD route.

## Evaluation Packet

Give each evaluator only what the scenario requires:

- a realistic user request and permitted side effects;
- the skill version under test, or an explicit no-skill control;
- the minimum project artifacts needed to act;
- target host/model configuration;
- observable success, safety, routing, and stop conditions.

Do not include the intended answer, suspected defect, proposed rewrite, or
prior evaluator conclusions unless the task itself requires them. Use an
isolated temporary workspace when the scenario generates files.

## Comparable Runs

For a new skill, compare:

1. no-skill control;
2. candidate skill.

For an existing skill, compare:

1. current version;
2. candidate version;
3. optional no-skill ablation when testing whether the skill adds value.

Hold the user request, model, tool access, host settings, and sampling controls
as stable as the environment permits. Record differences and environment-bound
unknowns rather than forcing a binary pass.

## Scenario Set

Use the smallest set that covers the real risk:

- positive invocation: an intended request discovers and applies the skill;
- negative invocation: a near-miss remains on its proper route;
- application: the agent completes the workflow or retrieves the needed rule;
- pressure: time, sunk cost, authority, or convenience tests a real governance
  boundary without manufacturing false urgency;
- counter-example: the agent recognizes when the skill should not apply.

Concrete choices can make a safety boundary observable, but do not design a
scenario merely to coerce a predetermined answer.

## Evaluation Record

Capture:

- route and resources actually used;
- decision and resulting artifact or evidence;
- missed constraint, unsafe workaround, or unnecessary ceremony;
- fresh verification performed;
- confidence and uncovered scope.

Judge behavior and artifacts, not whether the response copied headings or
specific phrases from the skill.

## Iteration Rule

Change only what an observed gap supports. When a candidate regresses routing,
safety, execution depth, portability, or verification:

1. identify the missing obligation or ambiguous trigger;
2. restore or clarify the smallest owning instruction;
3. re-run the same scenario;
4. add a new scenario only for a genuinely distinct failure class.

Stop when the representative set passes with no material regression, or report
`needs-verification` / `blocked`. Independent evaluation is advisory evidence;
it does not grant deployment or completion authority.
