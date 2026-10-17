# Design a Command Interface Workflow

Define a predictable, scriptable contract before implementing a Go command.

## When to Use

- Creating a new command or subcommand.
- Changing flags, operands, streams, output, or exit behavior.
- Repairing a command whose interface is hard to test or automate.

## Prerequisites

- The user goal and supported execution environments.
- Representative interactive and automated invocations.

**Reference:** `../references/command-interface/knowledge.md`

## Workflow Steps

### Step 1: State the Command Contract

**Goal:** Describe the command from the caller's perspective.

- [ ] Write the one-line purpose and invocation syntax.
- [ ] List success results and expected failure classes.
- [ ] Identify human, script, and agent consumers.
- [ ] Decide whether output compatibility is a public promise.
- [ ] Choose standard `flag`, Cobra/pflag, or another parser and document its grammar.
- [ ] Decide whether flags may follow operands and how `--` behaves.

**Ask:** "What must a caller know without reading the source?"

**Reference:** `../references/command-interface/rules.md`

### Step 2: Define Inputs and Precedence

**Goal:** Make every input source unambiguous.

- [ ] Classify values as flags, operands, stdin, environment, or config.
- [ ] Define precedence and distinguish unset from explicit empty values.
- [ ] Reject conflicts, missing operands, and unexpected trailing arguments.
- [ ] Ensure stdin is read only through a documented mode.

**Reference:** `../references/command-interface/examples.md`

### Step 3: Define Streams, Errors, and Exit Codes

**Goal:** Keep the command composable and diagnosable.

- [ ] Route successful data and requested help to stdout.
- [ ] Route diagnostics and invalid-usage help to stderr.
- [ ] Choose stable exit-code classes at the process boundary.
- [ ] Return errors from command logic so cleanup still runs.
- [ ] Specify usage behavior separately from operational failures.
- [ ] Define human, plain, and structured output and interaction behavior.
- [ ] Define explicit flags, `NO_COLOR`, and per-stream terminal precedence.
- [ ] Define cancellation and downstream broken-pipe behavior.

**Reference:** `../references/command-interface/rules.md`

### Step 4: Design the Testable Boundary

**Goal:** Keep process-global state out of reusable logic.

- [ ] Use a dedicated `flag.FlagSet` or framework command constructor.
- [ ] Inject readers, writers, configuration, and effectful dependencies.
- [ ] Keep `main` responsible only for wiring and final exit behavior.
- [ ] Separate stable data rendering from human presentation.

**Reference:** `../references/command-interface/examples.md`

### Step 5: Verify Portability and Usability

**Goal:** Prove that the documented interface works in supported environments.

- [ ] Run success, invalid-usage, and operational-failure cases.
- [ ] Verify exact stdout, stderr, and exit status where compatibility matters.
- [ ] Check paths, terminals, executable names, and signals per target OS.
- [ ] Review the completed command against the checklist.
- [ ] Test noninteractive execution, redirection, structured parsing, and interrupt.
- [ ] Assert plain and structured output contain no ANSI control sequences.

**Reference:** `../references/command-interface/checklist.md`

## Quick Checklist

```text
[ ] Purpose and syntax are explicit
[ ] Inputs and precedence are unambiguous
[ ] stdout, stderr, errors, and exit codes are deliberate
[ ] Command logic is isolated from process globals
[ ] Supported targets are smoke-tested
```

## Common Mistakes

| Mistake | Consequence | Do Instead |
|---|---|---|
| Parsing global flags in reusable code | Repeated execution and tests interfere | Construct an isolated parser |
| Printing everything to stdout | Pipelines receive diagnostics as data | Separate result and diagnostic streams |
| Calling `os.Exit` in helpers | Cleanup and tests are bypassed | Return an error or exit code |

## Exit Criteria

- [ ] Help and examples match actual behavior.
- [ ] Invalid and operational failures are distinguishable.
- [ ] The command is testable without replacing process-global state.
- [ ] Artifact-level smoke tests pass on supported targets.
