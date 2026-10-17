# Terminal Experience Knowledge

## Mode Is a Contract

- **Human mode** may use color, prompts, progress, and layout.
- **Plain mode** emits readable, stable text without terminal control sequences.
- **Structured mode** emits a documented machine-readable schema and never prompts.

Mode selection is policy. TTY detection supplies evidence but must not silently
override an explicit `--output`, `--no-input`, `--color`, or equivalent flag.

## Streams Have Independent Capabilities

stdin may be a pipe while stderr is a terminal; stdout may be redirected while
stdin is interactive. Detect each file descriptor separately with
`term.IsTerminal(int(file.Fd()))` when it is an `*os.File`. For injected buffers
or remote streams, accept explicit capability information instead of guessing.

## Output Layers

1. Domain result: typed values and failures.
2. Renderer: human, plain, or structured representation.
3. Terminal enhancer: optional color, progress, cursor movement, or alternate screen.
4. Process boundary: cancellation, signals, exit status, and closed pipes.

This separation lets tests assert stable results without parsing animation frames.

## Cancellation and Closed Consumers

Use a context shared by prompts, network calls, subprocesses, and render loops.
`signal.NotifyContext` can map interrupt signals to cancellation at the process
edge. If stdout's consumer closes early, such as `command | head`, recognize
only the platform-equivalent `EPIPE`, cancel upstream work, stop rendering, and
avoid a noisy diagnostic. Document whether this benign truncation returns zero
or a signal-compatible status because shell `pipefail` behavior differs. Treat
all other I/O failures normally.

## Accessibility

Color must not be the only carrier of meaning. Provide textual status, allow
color to be disabled, avoid uncontrolled motion, and keep a plain alternative
for screen readers, limited terminals, logs, and agents.
