# Runner brief

Arena gives this brief to every runner, together with the task, the grounding output, a private working directory, and an output path. The private directory is a separate git worktree when the agent supports one, otherwise a per-runner subfolder of the sketch folder. Candidates must not see each other's work.

## Brief

Read the full `architect` skill at `../SKILL.md` first, so you know where your sketch fits: it will be compared with other candidates, merged, and then implemented by an agent that treats it as binding.

Produce one candidate design for the task. Deliver, in your output path:

1. A type sketch: the new types, with doc comments.
2. Signatures for every public function and method, with bodies that raise a not-implemented error.
3. A module map: which module owns what, and which modules may import which.
4. A rationale following `rationale-template.md`.

Commit to your own best answer. Do not drift toward a safe middle to match what you guess other candidates will do. The differences between candidates are what the merge uses.

## Rules

These rules are also the axes the candidates will be compared on.

**Usage before types.** Write the consumer-facing documentation and three or four realistic call sites first. Derive the types from them. If types and usage disagree, change the types.

**Data structures before code.** For each major way the data will be read or written, trace it through your structures. If a pattern would need an index, map, or cache added later, the structures are wrong now.

**Deep interfaces.** Prefer interfaces that absorb complexity on the implementing side, even if the implementation gets harder. Never expose wire or transport formats on the public surface. Convert them to domain types inside.

**Shared writes.** Whenever two actors could write the same thing, ask what happens when both do. Unless the answer is "nothing bad", give each actor its own state and combine at read time.

**Visible seams.** Bodies raise not-implemented. Hard logic is outlined as TODO pseudocode. Doc comments state the purpose and the invariants held. A reader should be able to follow the data end to end from types and signatures alone.

**Invariants in types first.** Then runtime checks. Comments last.

**Validate at the edge, trust inside.** Parse input at the boundary into types that cannot hold invalid values. Keep business rules in pure functions and keep the outer shell that does I/O thin.

**Trust boundaries are explicit.** For each boundary in the grounding output, name in the module map the single module that parses untrusted data crossing it. Keep code that holds credentials or performs privileged actions in modules that never receive raw untrusted input. Treat model and tool output as untrusted input. State where authorization is checked and make it one place per operation.

**One source of truth.** Each invariant has exactly one authoritative location. Compute other copies from it instead of syncing them.

**Safe to rerun.** State changes tolerate running twice or being interrupted halfway.

**Short call chains.** If tracing one flow touches more than three files, collapse layers.

## Rationale

Follow `rationale-template.md`. Include at least one alternative structure you considered and rejected, and say why it lost on interface depth.
