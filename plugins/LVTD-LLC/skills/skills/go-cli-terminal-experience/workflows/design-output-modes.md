# Design Output Modes Workflow

Define stable behavior for terminals, pipes, agents, and CI.

## Steps

### 1. Inventory Callers and Outputs

- [ ] List people, scripts, agents, CI, and downstream pipe consumers.
- [ ] Identify stable fields, prose, diagnostics, and progress.

### 2. Define Modes

- [ ] Specify human, plain, and structured stdout.
- [ ] Specify stderr and prompting behavior for every mode.
- [ ] Define explicit flags and precedence.

### 3. Map Capabilities

- [ ] Detect stdin, stdout, and stderr independently.
- [ ] Define fallback behavior for unknown or limited terminals.
- [ ] Honor color and accessibility controls.

### 4. Verify

- [ ] Test each explicit mode and auto-selection.
- [ ] Test redirection, a short-reading pipe, CI, and cancellation.
- [ ] Assert structured output parses and plain output contains no ANSI escapes.

## Exit Criteria

- [ ] Every mode has a documented stream and interaction contract.
- [ ] Automation never depends on a terminal or prompt.
