# Go CLI Command Interface Checklist

Use when designing or reviewing a Go command's public interface.

## Command Contract

- [ ] The command has one clear purpose and a documented invocation syntax.
- [ ] Actions, flags, operands, and defaults have unambiguous meanings.
- [ ] Conflicting actions and unexpected operands are rejected.
- [ ] The behavior for empty input is explicit.
- [ ] Machine callers can rely on stable output and exit behavior.

## Code Boundary

- [ ] `main` only wires process resources, invokes a runner, and exits.
- [ ] Business logic lives outside `package main` when reuse or complexity
  justifies it.
- [ ] Command logic receives args, streams, and configuration as dependencies.
- [ ] Helpers return errors instead of calling `os.Exit`.
- [ ] Deferred cleanup is able to run.

## Arguments and Flags

- [ ] Typed flags are defined before parsing.
- [ ] Parsing errors are checked.
- [ ] Remaining positional arguments are validated after parsing.
- [ ] A dedicated `flag.FlagSet` is used for reusable or testable parsing.
- [ ] Help text states accepted values and meaningful defaults.
- [ ] Repeated, mutually exclusive, and malformed options are tested.

## Configuration

- [ ] Precedence among flags, arguments, environment, files, and defaults is
  documented and implemented once.
- [ ] Environment variables use a stable application prefix.
- [ ] `os.LookupEnv` is used if empty differs from unset.
- [ ] Sensitive configuration is not exposed in output or help.
- [ ] Environment-derived paths and values are validated.

## Standard Streams

- [ ] stdin is accepted through `io.Reader`.
- [ ] stdout and stderr are separate injected `io.Writer` values.
- [ ] stdout contains successful results only.
- [ ] Requested help goes to stdout; invalid-usage help and diagnostics go to stderr.
- [ ] stdin fallback cannot unexpectedly block an interactive invocation.
- [ ] Read and write errors are checked.
- [ ] Human, plain, and structured modes have documented stream contracts.
- [ ] stdin, stdout, and stderr terminal capabilities are considered independently.
- [ ] Plain and structured output contain no ANSI escapes or progress frames.
- [ ] `NO_COLOR` and explicit color policy have defined precedence.

## Errors and Exit Codes

- [ ] Success returns zero.
- [ ] Invalid usage and operational failure return deliberate nonzero statuses.
- [ ] Error messages say what failed and preserve the underlying cause.
- [ ] Expected user errors do not include noisy stack traces by default.
- [ ] Tests assert stderr and exit behavior separately from stdout.
- [ ] Cancellation and short-reading pipe behavior are intentional and tested.

## Interaction

- [ ] Noninteractive mode never prompts or waits on stdin unexpectedly.
- [ ] Prompt defaults and destructive confirmation behavior are explicit.
- [ ] Sensitive credentials cannot leak through arguments, history, logs, or diagnostics.
- [ ] Progress and terminal state are cleaned up on every return path.

## Parser Grammar

- [ ] The chosen parser and its operand/flag ordering are documented.
- [ ] `--`, repeated flags, missing values, and extra operands are tested.
- [ ] Help exits successfully and is distinct from invalid usage.
- [ ] Custom values reject malformed input without partial mutation.
- [ ] Conversion, single-value validation, and cross-field validation are separate.
- [ ] Parser and process layers do not print duplicate diagnostics.

## Portability

- [ ] Paths use `filepath` and platform-aware directories.
- [ ] Executable names account for Windows where relevant.
- [ ] Supported `GOOS`/`GOARCH` targets compile in CI.
- [ ] Target systems receive smoke tests, not build checks alone.
- [ ] cgo/native dependencies and static-link assumptions are verified.
- [ ] Line endings, signals, terminals, and permissions have defined behavior.

## Red Flags

Stop and reconsider the design if:

- Parsing, environment access, domain work, printing, and exiting all occur in
  one large `main` function.
- The command silently selects one of several conflicting actions.
- Logs or progress corrupt pipeable stdout.
- No-argument execution waits on stdin without documenting that behavior.
- Cross-compilation is treated as proof that the target binary works.

## Source Traceability

Derived and paraphrased from:

- Chapter 1, “Building the Basic Word Counter,” “Adding Command-Line Flags,”
  and “Compiling Your Tool for Different Platforms” (normalized lines 548–963).
- Chapter 2, “Organizing Your Code,” “Creating the Initial To-Do Command-Line
  Tool,” “Handling Multiple Command-Line Options,” “Display Command-Line Tool
  Usage,” “Increasing Flexibility with Environment Variables,” and “Capturing
  Input from STDIN” (normalized lines 1012–2699).
