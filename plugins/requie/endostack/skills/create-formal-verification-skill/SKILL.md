---
name: create-formal-verification-skill
description: Find the guarantee in a repo where a bug would hurt users most and tests are weakest, verify it with a fitting formal tool, and leave a proven project-local verify skill that reruns the check. Triggers: /create-formal-verification-skill, "prove this invariant", or a request to model-check a race.
disable-model-invocation: true
---

# create-formal-verification-skill

An example-based test exercises only the cases someone wrote down. A formal check exhausts a stated scope, which may be all interleavings of a model, all inputs below a size bound, or the entire input space. Apply one where that gap matters, then leave a skill that later agents rerun each time they edit the covered code.

Assume the user cannot read TLA+ or any proof language. Report everything using the names and concepts of the code itself, so they can judge the outcome and decide what to do without learning the tool.

Good targets: concurrency, retries, state machines, parsers, permission checks, and unsafe memory access, anywhere tests feel thin. If the area already has a generated verify skill, use the `maintain-formal-verification-skill` skill ([../maintain-formal-verification-skill/SKILL.md](../maintain-formal-verification-skill/SKILL.md)) instead.

## 1. Choose what to verify

Read the code first, and put questions to the user only where the code leaves a gap. When the user pointed at a particular area or defect, begin with it.

The best candidate is a guarantee the code makes, whose failure hurts users, and whose failing case tests rarely reach. Pick the highest-value candidate in the codebase, not the easiest to formalize. Security guarantees often rank highest: "a revoked token is never accepted after revocation commits", "a payout is never sent twice for one invoice", "a path from user input never resolves outside the upload root".

## 2. Match the tool to the question

Use the cheapest tool that can answer it:

- **Ordering questions** (can these events interleave badly?): a model checker on a small model of the design. Default to TLA+ with TLC, whatever language the code is in.
- **Whole-input questions about real code** (memory safety, overflow, data-structure invariants): a verifier that runs on source, such as Kani for Rust, CBMC for C, or Dafny where the code is written in it.
- **No source-level verifier for the language**: say so plainly, then run property-based tests with generated inputs against the actual code (Hypothesis, fast-check, QuickCheck, jqwik). Do not hand-write a model of the function instead.
- **Must hold for unbounded sizes**, where no finite bound is enough: a proof assistant (Lean, Coq, Isabelle) may be needed. Say what it costs before you start.

Prefer tools the project's developers could install and run themselves. Explain your choice to the user. Pin the tool version, and verify checksums when you download a toolchain.

## 3. Standards for the check

- **Traceable.** A reviewer can follow each element of the model or proof to a specific place in the code. A step the model handles atomically must also be atomic in the implementation. Name things with the repo's identifiers.
- **Shown able to fail.** For each property, make a deliberately broken copy of the guarded code (remove a guard, swap two steps) and watch the check reject it. A check never seen failing proves nothing.
- **Findings reported, never hidden.** If today's code violates the property, report the counterexample in the code's vocabulary. Never weaken the property or bend the model to get a pass. Product code stays untouched unless the user requests a change.
- **Scope stated.** Say what was verified, the bounds and assumptions, and what was left out. A pass speaks only for what was modeled, within its bounds.
- **Understandable to someone who never runs the tool.** One plain sentence gives the property, and a second gives what goes wrong if it breaks. A counterexample appears as a brief numbered sequence of steps described with the code's names.
- **Cheap to rerun.** One command, a pinned tool version, and a runtime short enough that agents will run it every time related code changes.
- **Tied to history.** For each check, list the files and functions it covers and the commit at which someone last confirmed the check matches them (the sync commit). A later agent compares that commit with HEAD to see whether covered code has moved.

## 4. Write the verify skill

Create a project-local skill in the project skills directory your agent reads (see `docs/agents/<agent>.md`), named for the verified area (for example `verify-token-revocation`). Its frontmatter must identify the verified area and describe when to invoke the skill, because agents only find skills through frontmatter.

On its own, the generated skill must let a later agent:

1. decide whether a change touches verified code (the coverage list);
2. run the check (the exact command);
3. tell a real defect from a modeling mistake (walk the counterexample through the code; if a step is impossible in the code, the model is wrong);
4. update the verification for an intended behavior change (edit the model to match the code first, change the property only with evidence the contract changed).

Embed the coverage list and the sync commit. Instruct later agents to advance the sync commit only once they have confirmed that the verification still agrees with the code at that newer commit. Use the repo's real commands, paths, and terms. Leave no placeholders.

## 5. TLA+ results go through statechart

When the check is TLA+, the generated skill sends every result through the `statechart` skill. That skill turns each violated invariant into its shortest path of states in plain words and, when everything passes, draws the state diagram. Refer to it only by name ("run the `statechart` skill on the spec"). Its commands, flags and paths change between versions and machines, so none of them belong in what you generate, whether skill text or script.

## 6. Prove the generated skill

Act as a future agent. Make a throwaway edit to real code that breaks the property, then follow the generated skill from the top. It must catch the break. Revert the edit and confirm the check returns to its earlier state (green, or red only for findings you will report).

When the generated skill fails to catch the planted break, or one of its steps will not run, repair the skill or the check. Never adjust the throwaway edit to make it detectable. A verify skill that has not passed this test is a draft.

## 7. Report

Tell the user:

- the guarantee verified, as one plain sentence, and the harm if it breaks;
- the tool and why you chose it;
- the bounds and assumptions;
- any findings, as numbered steps in code terms;
- the rerun command;
- coverage gaps.

Suggest one more candidate only if a closely related one came up. Mention that `maintain-formal-verification-skill` resynchronizes the check after changes that skipped it.

## Done when

One property is verified and shown able to fail, the generated skill caught a deliberate violation in one run-through, and the coverage list and sync commit are recorded in it.
