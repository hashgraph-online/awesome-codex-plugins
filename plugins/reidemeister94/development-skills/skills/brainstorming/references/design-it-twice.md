# Design It Twice

From "A Philosophy of Software Design" (John Ousterhout): your first idea is rarely the best. Generate multiple radically different designs, then compare.

**When to use**: during brainstorming Step 4 (Approach Sketch) when the task is designing something new or choose a new approach. Skip when the task is tweaking existing code.

## Workflow

### 1. Gather requirements

Before designing:

- What problem does the module solve?
- Who are the callers? (other modules, external users, tests)
- Key operations?
- Constraints? (performance, compatibility, existing patterns)
- What should be hidden inside vs exposed?

If answers are missing, return to Step 2 Q&A. Do not proceed blindly.

### 2. Generate 2-3 radically different designs

Spawn 2-3 parallel subagents via the `Task` tool in a single message. Each subagent receives a divergent constraint. **They do not implement code** — only the shape of the interface. If subagents are unavailable, generate the designs sequentially in-thread. Tool translations for non-Claude-Code platforms: see `../../using-development-skills/references/codex-tools.md`.

Orthogonal constraints to assign (one per agent):

- **Agent A**: "Minimize method count — aim for 1-3 methods max"
- **Agent B**: "Maximize flexibility — support many use cases"
- **Agent C**: "Optimize for the most common case — common path is trivially simple, edge cases may be more verbose"
- **Agent D** (optional): "Take inspiration from [specific paradigm/library]"

Prompt template per subagent:

```
Design an interface for: [module description]

Requirements: [requirements gathered in step 1]

Constraint for this design: [one of the constraints above]

Output format:
1. Interface signature (types/methods)
2. Usage example (caller-side code)
3. What this design hides internally
4. Trade-offs of this approach
```

### 3. Present the designs

Show each design **sequentially** (not in a comparison table):

1. Interface signature — types, methods, parameters
2. Usage examples — how callers actually use it in practice
3. What it hides — internal complexity kept inside

Let the user absorb each approach before moving to the comparison.

### 4. Compare

After showing all designs, compare them on:

- **Interface simplicity**: fewer methods, simpler params = easier to learn and use correctly
- **General-purpose vs specialized**: flexibility vs focus
- **Implementation efficiency**: does this shape allow efficient internals, or force awkward implementation?
- **Depth**: small interface hiding significant complexity (deep — good) vs large interface with thin implementation (shallow — bad)
- **Ease of correct use vs ease of misuse**: does the design push callers toward the right thing, or toward bugs?

Discuss in prose, not tables. Highlight where designs diverge most.

### 5. Synthesize

The best design often combines insights from multiple options. Ask:

- "Which design best fits your primary use case?"
- "Any elements from other designs worth incorporating?"

Final decision → return to brainstorming Step 5+ (optional research, plan write).

## Evaluation criteria

From Ousterhout's "A Philosophy of Software Design":

- **Interface simplicity**: fewer methods, simpler parameters = easier to learn and use correctly.
- **General-purpose**: handles future use cases without changes. Beware over-generalization.
- **Implementation efficiency**: does the interface shape allow efficient implementation, or force awkward internals?
- **Depth**: small interface hiding significant complexity = deep module (good). Large interface with thin implementation = shallow module (avoid).

## Anti-patterns

- **Sub-agents producing similar designs**: enforce radical difference by assigning orthogonal constraints.
- **Skipping the comparison**: the value is in the contrast. Don't lock onto a single design without putting them side by side.
- **Implementing during the design phase**: stop at the shape. Implementation comes later, in core-dev.
- **Evaluating based on implementation effort**: implementation effort doesn't matter at this stage. The shape does.
