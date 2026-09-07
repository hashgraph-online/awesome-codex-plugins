# Terminal Experience Rules

## Selection

- Define precedence: explicit flag, environment policy, detected capability, default.
- Resolve incompatible explicit options before constructing renderers: reject
  color or prompting with structured output, reject forced prompts with
  `--no-input`, and return an actionable missing-value error in noninteractive mode.
- Treat `NO_COLOR` as disabling color unless an explicit user flag intentionally wins.
- Provide a noninteractive flag when an operation can otherwise prompt.
- Fail with an actionable error when required input is absent; never hang.

## Streams

- Keep result data on stdout and diagnostics or progress on stderr.
- Never write progress to stdout when stdout is pipeable.
- Test stdin, stdout, and stderr terminal status separately.
- Suppress terminal control sequences when the destination is not a compatible terminal.

## Interaction

- State prompt defaults and make destructive confirmation opt-in.
- Read secrets from a terminal, protected file descriptor, or environment only
  when the exposure tradeoff is documented; prefer hidden terminal entry.
- Restore terminal state on success, error, panic boundary, and cancellation.
- Stop tickers, goroutines, and render loops before returning.
- Give input, rendering, and background work one shared cancellation tree.
- Stop production, then drain or discard by contract, join goroutines, and only
  then restore terminal state.
- Bound or coalesce progress events so a slow terminal cannot grow memory without limit.

## Structured Output

- Version or otherwise stabilize schemas consumed by agents and scripts.
- Emit exactly one documented stream shape: object, array, or JSON Lines.
- By default, keep structured success on stdout and emit a documented
  machine-readable error envelope on stderr with stdout empty. If a command
  intentionally uses one stdout result/error envelope, document and test that
  different contract explicitly.
- Do not mix banners, warnings, spinners, or help text into structured stdout.

## Verification

- Test explicit modes, auto mode, redirection, pipes, CI, and interrupt.
- Assert absence of ANSI escapes in plain and structured output.
- Assert no read from stdin in noninteractive mode.
- Exercise narrow terminal widths and color-disabled environments.
- Test incompatible option combinations as usage errors.
