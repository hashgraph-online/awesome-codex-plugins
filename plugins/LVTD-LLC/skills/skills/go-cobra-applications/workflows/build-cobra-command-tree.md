# Build a Cobra Command Tree Workflow

Create a fresh, testable Cobra tree with typed application boundaries and predictable configuration.

## When to Use

- Starting a Cobra CLI or adding a command family.
- Refactoring package-global Cobra commands.
- Adding Viper-backed flags, environment, or configuration files.

## Prerequisites

- A user-oriented command hierarchy and invocation examples.
- Pinned current Cobra and Viper versions.
- Application services that do not depend on Cobra or Viper.

**Reference:** `../references/cobra-applications/knowledge.md`

## Workflow Steps

### Step 1: Model User Intent

**Goal:** Make the command hierarchy explain the product.

- [ ] Group parent commands by resource or workflow and children by operation.
- [ ] Define `Use`, descriptions, argument validation, examples, and aliases together.
- [ ] Keep a bare root inert unless one default action is unmistakable.
- [ ] Scope local and persistent flags narrowly and avoid shorthand collisions.
- [ ] Decide whether typo suggestions help humans without destabilizing automation.

**Reference:** `../references/cobra-applications/rules.md`

### Step 2: Construct a Fresh Tree

**Goal:** Make repeated execution and tests independent.

- [ ] Build the root and every subcommand in constructor functions.
- [ ] Inject services, streams, filesystem access, and clocks.
- [ ] Avoid mutable package-global command values and initialization side effects.
- [ ] Pass `cmd.Context()` into long-running application work.

**Reference:** `../references/cobra-applications/examples.md`

### Step 3: Keep Framework Code at the Edge

**Goal:** Prevent Cobra and Viper from becoming domain dependencies.

- [ ] Use `RunE` handlers to translate CLI values into typed application calls.
- [ ] Return errors instead of exiting, panicking, or logging fatally.
- [ ] Separate human and machine renderers.
- [ ] Map typed errors to exit codes only at the process boundary.

**Reference:** `../references/cobra-applications/patterns.md`

### Step 4: Resolve Typed Configuration

**Goal:** Make defaults, files, environment, and flags predictable.

- [ ] Document and test one precedence order.
- [ ] Normalize the environment prefix and key mapping.
- [ ] Distinguish unset from explicit zero values.
- [ ] Validate semantic ranges and secret handling.
- [ ] Pass a typed validated configuration inward.
- [ ] Put local, buffered, and remote sources behind one loader boundary.
- [ ] Keep mutable application state outside configuration.
- [ ] If reloading, validate then atomically swap while retaining last-known-good
      state and owning watcher/client cleanup.

**Reference:** `../references/cobra-applications/rules.md`

### Step 5: Test the Real Tree

**Goal:** Verify user-visible behavior without sharing state.

- [ ] Construct a fresh root for every test.
- [ ] Set arguments and capture command-owned output streams.
- [ ] Test parsing, inherited flags, validation, precedence, help, and errors.
- [ ] Execute the same constructor repeatedly to catch retained state.

**Reference:** `../references/cobra-applications/checklist.md`

### Step 6: Generate Completion and Documentation

**Goal:** Derive auxiliary artifacts from the runtime tree.

- [ ] Confirm current APIs against pinned upstream versions.
- [ ] Generate declared shell completions safely.
- [ ] Generate docs reproducibly from the same constructor.
- [ ] Review generated diffs and smoke-test supported shells.

**Reference:** `../references/cobra-applications/knowledge.md`

## Quick Checklist

```text
[ ] Hierarchy and invocation contracts match user intent
[ ] Every execution receives a fresh command tree
[ ] Business logic is independent of Cobra and Viper
[ ] Configuration resolves into a typed validated value
[ ] Parsing, help, errors, repetition, completion, and docs are verified
```

## Common Mistakes

| Mistake | Consequence | Do Instead |
|---|---|---|
| Global command values and `init` wiring | State leaks across tests | Use explicit constructors |
| Reading Viper throughout domain code | Precedence becomes invisible | Resolve one typed config at the edge |
| Showing usage for operational errors | Users receive irrelevant help | Silence usage selectively |

## Exit Criteria

- [ ] Command construction is deterministic and repeatable.
- [ ] Flags, configuration, errors, streams, and context follow one contract.
- [ ] Application packages do not import Cobra or Viper.
- [ ] Tests, completion, and generated documentation pass review.
