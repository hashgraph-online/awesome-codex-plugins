# Design Runnable Lab Workflow

Use this workflow to turn a technical book section into a lab readers can complete.

## When To Use

- A chapter has technical instructions but weak checkpoints.
- A self-hosting or DevOps section needs a hands-on exercise.
- A tutorial feels like commands without reader understanding.
- Beta readers are failing to complete a technical chapter.

## Prerequisites

- Draft section, outline, or intended lab topic.
- Target reader and book promise.
- Known or assumed reader environment.

**Reference**: `references/core/rules.md`

---

## Workflow Steps

### Step 1: Define The Outcome

**Goal**: Make success observable.

- [ ] State what the reader will build, debug, decide, or explain.
- [ ] Define how success will be verified.
- [ ] Remove secondary goals that do not serve the outcome.

---

### Step 2: Define Starting State

**Goal**: Prevent hidden assumptions.

- [ ] List required prior knowledge.
- [ ] List required tools, versions, accounts, hardware, network access, and permissions.
- [ ] Mark assumptions that should become prerequisites, notes, or companion resources.

---

### Step 3: Break Into Checkpoints

**Goal**: Create frequent progress and early failure detection.

- [ ] Divide the lab into 3-7 meaningful stages.
- [ ] Add a purpose for each stage.
- [ ] Add expected output or state after each stage.
- [ ] Add verification before the next stage.

---

### Step 4: Add Failure Paths

**Goal**: Help readers recover from likely problems.

- [ ] Identify likely environment differences.
- [ ] Add symptom-to-cause troubleshooting.
- [ ] Add cleanup or rollback for risky changes.
- [ ] Add security, data, cost, and public-exposure warnings before the relevant step.

---

### Step 5: End With Transfer

**Goal**: Make the lab useful beyond copying commands.

- [ ] Summarize what now exists.
- [ ] Explain the core model the reader should retain.
- [ ] Suggest one safe variation.
- [ ] List maintenance or monitoring tasks if relevant.

## Exit Criteria

Task is complete when:

- [ ] The lab has a clear outcome and starting state.
- [ ] Every major stage has verification.
- [ ] Common failures have useful next checks.
- [ ] The reader can explain and adapt what they did.
