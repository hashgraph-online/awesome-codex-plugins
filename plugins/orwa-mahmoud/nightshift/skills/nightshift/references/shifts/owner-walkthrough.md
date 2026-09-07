# Owner walkthrough — open-ended — pursue one owner-supplied objective until quitting time

A custom hours-cycle for a goal the owner names. Nightshift keeps the objective verbatim, derives
the next concrete unit from the work target, and implements, verifies, and reassesses until the
objective is verifiably satisfied or the clock ends the shift.

**Selection:** Guided only. Never select this entry in Automatic mode: its objective must come
directly from the owner, not from work-target discovery. Do not combine it with another open-ended
entry; this walkthrough owns the shift's single continuation record.

**Owner instructions:** Required. The guided scope answer is the objective, not optional tailoring.
If it is empty, do not compose, cut, or arm the shift.

Supported in a persistent project workspace whose objective can be advanced through local, reviewable
engineering work. Publishing, deployment, spending, production-data mutation, secrets, and legal or
licensing decisions remain outside the coding-work authorization.

```text
- [ ] **Owner walkthrough — pursue the owner's objective until quitting time.**
  - Ending: open-ended — hours and a deadline are required; verified objective satisfaction may
    finish it earlier.
  - Objective: the Owner instructions attached by Hunt are authoritative and must remain verbatim.
    Never replace them with an easier, narrower, or merely adjacent goal.
  - Isolate first: in repository mode, work on a dedicated nightshift branch, never the default
    branch. In artifact mode do not `git init` the folder; write receipts under `$NS/receipts/` instead of commits. Never merge,
    push, open a PR, deploy, publish, or mutate an external service unless the owner explicitly
    authorized that exact action.
  - Establish the continuation record before implementation: use the single `Status: building`
    entry in opportunity-map.md. Preserve the owner objective in Scope, derive observable
    Acceptance from it and the work target, and record Current phase, Completed, Decisions,
    Rejected, Next, and Verify remaining. If a building entry already exists for this objective,
    resume its exact Next action before exploring again. Never open a second building entry.
  - Each cycle: inspect current work-target evidence and the continuation record, choose the
    strongest coherent unit that advances the objective and fits the remaining time, implement it
    end-to-end, run the item gate, commit separately or write an artifact receipt, then refresh the continuation record and
    reassess. Prefer completing one reviewable path over starting several partial ones.
  - Verification comes from the objective, work-target tests and tooling, and the configured
    item gate. Never weaken a test, suppress a finding, or redefine acceptance merely to claim
    progress. The item gate must be green at every commit or artifact receipt.
  - Keep the continuation record current at meaningful boundaries: after design, a coherent
    implementation step, a stable decision, a commit or artifact receipt, or a verification-state change. Record the
    exact next action and remaining verification so compaction or revival can continue without
    reconstructing the conversation. Do not rewrite it after every command.
  - Park genuine owner decisions with the strongest sensible reversible default and continue.
    Stop for the owner only when the action falls outside the authorized coding-work boundary.
  - Large work is allowed; an incoherent stopping point is not. Do not begin a unit that cannot be
    left reviewable within the remaining time.
  - The objective can be finished before the whistle. When its recorded Acceptance is verified and
    the item gate is green, record the evidence in the continuation record, write the handoff, tick
    the item, and clock out early. Never manufacture busywork or expand into unrelated work to fill
    the remaining hours.
  - Open-ended: quitting time is the normal ending. At the whistle, finish the coherent unit in
    hand, leave the branch green or the outputs reviewable, update the continuation record, and write a morning handoff with
    delivered commits or receipts, decisions, remaining work, exact Next, and Verify remaining. The owner's
    stop-work order remains available and leaves unfinished work open.
  - Verify: the item gate is green at every commit or artifact receipt; each delivered unit advances the verbatim
    owner objective; opportunity-map.md and the morning handoff identify the exact current state.
```
