# Review Code Sample Workflow

Review or design a code sample for developer documentation.

## When To Use

- Reviewing runnable code blocks, API examples, CLI commands, config examples, SDK snippets, or generated reference samples.
- Creating a new sample for a doc.
- Checking sample drift before release.

## Prerequisites

- Sample code or sample requirements.
- Target reader, doc goal, language or API version, and source of truth when available.

**Reference**: from this workflow file, open `../references/core/knowledge.md`.

## Workflow Steps

### Step 1: Classify The Sample

**Goal**: Apply the right quality bar.

- [ ] Identify whether the sample is executable, explanatory, request/response, CLI, config, or generated.
- [ ] State what the reader should learn or accomplish.
- [ ] Identify intended language, version, API, SDK, or platform.

### Step 2: Check Usability

**Goal**: Make the sample copyable and adaptable.

- [ ] Confirm prerequisites and setup are stated.
- [ ] Check placeholders, IDs, secrets, URLs, and filenames.
- [ ] Check that inputs and outputs match.
- [ ] Check that the sample uses realistic values and idiomatic style.

### Step 3: Check Clarity And Scope

**Goal**: Keep the sample focused.

- [ ] Remove unrelated product features or clever language tricks.
- [ ] Split overloaded samples.
- [ ] Add explanation for why the sample matters and what each important part does.
- [ ] Mark intentional simplifications.

### Step 4: Verify Behavior

**Goal**: Avoid publishing stale or false examples.

- [ ] Run the sample, test, command, or API call when feasible.
- [ ] Compare output, errors, and status codes against real behavior.
- [ ] If execution is not feasible, state what remains unverified and who should check it.

### Step 5: Plan Maintenance

**Goal**: Keep the sample accurate after launch.

- [ ] Identify owner and source of truth.
- [ ] Note generated/manual boundary.
- [ ] Recommend tests, snippets extraction, link checks, or release review triggers.

## Exit Criteria

- [ ] The sample has a clear purpose and reader fit.
- [ ] Copy-paste risks and placeholders are controlled.
- [ ] Runtime behavior is verified or explicitly marked as unverified.
