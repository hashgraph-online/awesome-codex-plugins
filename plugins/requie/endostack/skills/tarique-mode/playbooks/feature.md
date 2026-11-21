# Feature

You own the design, review, and verification. Implementation is delegated. Large cross-cutting efforts and work the user will leave unattended go to the `figure-it-out` skill instead; behavior-preserving restructures go to [refactoring.md](refactoring.md).

1. **Understand the subsystem.** Run the `how` skill over it.
2. **Compare designs.** Use the `architect` skill, which has several agents sketch competing designs at once.
3. **Threat-model if it touches a trust boundary.** New inputs, endpoints, permissions, file or network access, dependencies, or an agent that acts on content it reads: run the `threat-model` skill now. Each high-ranked threat becomes a design change or a test that proves the mitigation, and both go into the delegate's scope in step 5. If nothing crosses a boundary, write one todo line naming the boundaries you checked.
4. **Record the throughput checkpoint** in your todo list as these four entries. Keep every entry even when it does not fit this job (for example, a one-file change with nothing to parallelize), and write "not applicable" plus the reason next to it.
   - Prerequisites: work that has to be complete before anything runs in parallel.
   - Parallel tracks: pieces that touch separate files, services, or layers and can proceed at the same time. Anything that writes to the same place runs one after another.
   - Shared state that changes: first try to split what is being written (`principle-separate-before-serializing-shared-state`), and fall back to ordering the writers only when a real invariant demands it.
   - Fewest workers that stay safe: if the answer is one worker, explain why.
5. **Delegate the code.** Hand it to a subagent on the `feature` role (default `fast`, tuned per the policy in [../SKILL.md](../SKILL.md)) with a precise scope:
   - file paths;
   - the data shape, named, together with the structure that holds it, picked under `principle-model-the-domain` before any logic is written (for example, one state machine in place of several loose boolean flags, a lookup table or registry in place of chains of conditionals, a typed model in place of code that assumes the same shape in many places);
   - the threat-model tests from step 3;
   - success criteria.

   If the code could reasonably be written more than one way (how errors are handled, where the abstraction sits, how the tests are organized), delegate through the `arena` skill. You must do this even though `principle-laziness-protocol` favors the smallest effort. With several runners, alternatives become visible and the judges check each other's work, and one delegate working alone produces neither. A subagent that is not allowed to spawn subagents meets this rule by writing the diff itself while keeping the author and the reviewer separate. Answering that it is waiting is not acceptable.

   Delegate edits are surgical and follow the comment policy in [../SKILL.md](../SKILL.md). Files generated from an upstream source are re-checked against that source. An improvement to a shared primitive is carried to every consumer, and each consumer is verified. Commit often.
6. **Verify on the matching surface.** Drive it with its control skill. Inconclusive or wrong-surface results are not passes; flag them. Run the threat-model tests and confirm each mitigation holds.
7. **Shape the history.** Rebase into small ordered commits and stack follow-ups. Build, verify, and commit each unit before the next (`principle-sequence-verifiable-units`).
8. **Interrogate contested designs.** If reviewers or the `architect` panel disagreed on the design, run `interrogate` before shipping.
9. **Security-review the diff** with the `security-review` skill. Fix confirmed findings before step 10.
10. **Finish** with [opening-a-pr.md](opening-a-pr.md).

## Ownership

When the pieces of work depend closely on each other, as in a single feature or a single migration, assign one owner. That owner keeps the throughput checkpoint and spawns its own parallel workers once the prerequisites are done. Spawning in parallel from the parent level fits only when each slice produces something usable by itself, such as separate audits, investigations that each cover a different subsystem, or experiments competing on the same question. Whenever one phase ends and the next begins, write the checkpoint again. When an owner must change course, spawn a fresh owner with consolidated scope instead of chaining interrupts.

## Reply

What you built, the choices you made and why, the throughput checkpoint, the trust boundaries touched and what the security review found, and open decisions. Present design alternatives as tables.
