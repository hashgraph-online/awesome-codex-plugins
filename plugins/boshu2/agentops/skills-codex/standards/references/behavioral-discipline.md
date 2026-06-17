# Behavioral Discipline for Agentic Work

**Purpose:** Reduce common agent failure modes during implementation and review. Use this alongside language standards, not instead of them.

## When to Apply

Apply this reference for:

- non-trivial `$implement`, `$review`, `$validate`, and `$pre-mortem` work
- ambiguous requests where different interpretations would change the solution
- agent-authored diffs, broad refactors, or any task with blast-radius risk

## 1. Think Before Coding

Do not silently pick an interpretation and run with it.

- State the task in your own words before editing.
- Name assumptions that materially affect the solution.
- If two reasonable interpretations lead to different code, ask or present options.
- Surface tradeoffs when the requested path looks heavier than necessary.
- Stop when repo reality contradicts the prompt. Resolve the mismatch first.

### AgentOps Translation

- Check whether the capability already exists before proposing or building it.
- Prefer runtime truth (`cli/**`, `hooks/**`, `scripts/**`, generated docs) over memory or explanatory docs.
- If a simpler file boundary exists, choose it and explain why.

## 2. Simplicity First

Choose the smallest change that satisfies the request.

- Reuse existing helpers, commands, hooks, and patterns before adding new ones.
- Do not add configurability, abstractions, or extension points without a present requirement.
- Do not build a framework for a one-off need.
- Do not add defensive branches for impossible or unobserved scenarios just to look thorough.
- If the patch keeps growing, pause and ask whether there is a smaller cut.

### Quick Test

Would a senior engineer call this solution obviously larger than the problem? If yes, simplify.

## 3. Surgical Changes

Keep the blast radius tight.

- Define what files or surfaces are in scope before editing.
- Every changed line should map to the request, acceptance criteria, or cleanup made necessary by your change.
- Do not fold in adjacent refactors, formatting passes, or comment rewrites unless they are required.
- Match local style and structure unless the task explicitly includes a style correction.
- Only remove dead code or imports that your own change made obsolete.
- If you find an unrelated problem, record it separately instead of bundling it into the patch.

### AgentOps Translation

- If unrelated follow-up work appears, create a bead instead of smuggling the fix into the current change.
- Avoid touching generated or mirrored artifacts unless the workflow requires it.

## 4. Goal-Driven Execution

Turn requests into verifiable outcomes.

- Rewrite the task as success criteria before editing.
- Prefer evidence: tests, smoke commands, parity checks, schema validation, or focused diffs.
- For multi-step work, pair each step with a verification check.
- Do not claim completion without the evidence that matches the requested outcome.
- If validation could not be run, say so explicitly and explain the gap.

### AgentOps Translation

- "Fix the CLI bug" becomes "add a reproducer, patch it, run the targeted test."
- "Improve this skill" becomes "update the contract, validate skill integrity, then check the shipped runtime copy."
- "Clean up the hook" becomes "preserve the contract, edit only the required files, then run the hook/doc parity gate."

## Before/After Examples

### Example 1: Hidden Assumptions

**Request:** "Make search faster"

**Before**

- picks one meaning of "faster" without clarifying
- adds caching, async work, and new knobs all at once
- verifies only that the code still runs

**After**

- asks whether "faster" means latency, throughput, or perceived speed
- picks the smallest change that matches the answer
- verifies against the metric that actually mattered

### Example 2: Overbuilt Solution

**Request:** "Add a discount helper"

**Before**

- introduces strategies, factories, and extension points for a one-off need
- adds flexibility nobody asked for

**After**

- starts with a small helper that solves the current requirement
- defers abstraction until a real second use case exists

### Example 3: Drive-By Editing

**Request:** "Fix empty emails crashing the validator"

**Before**

- rewrites adjacent validation logic
- edits comments and formatting unrelated to the bug
- leaves a large diff for a narrow request

**After**

- adds a reproducer for the empty-email case
- fixes only the email path plus cleanup caused by that fix
- records unrelated cleanup separately instead of bundling it into the patch

### Example 4: Weak Proof

**Request:** "Improve this AgentOps skill"

**Before**

- edits the skill doc and stops
- forgets the mirrored Codex artifact or validation step

**After**

- updates the shared contract and the checked-in Codex copy
- regenerates affected artifact metadata when needed
- runs the relevant validation commands before claiming completion

## Review Questions

Use these four questions when validating a plan, patch, or PR:

1. What assumptions is this change making, and were they surfaced or silently chosen?
2. Could the same outcome be achieved with a smaller or more local change?
3. Does every changed line trace back to the stated goal?
4. Is the verification checking the behavior that was claimed, or only that the code compiles?
