# Go CLI Command Interface Knowledge

Core concepts for designing small, composable Go command-line interfaces.

## Command Boundary

A command has two layers:

- The process boundary parses arguments, reads environment variables, connects
  standard streams, selects an exit status, and invokes application code.
- The application layer performs the work through ordinary functions and
  package APIs.

Keep `main` small. Put reusable business behavior in a non-`main` package and
place executable entry points under `cmd/<name>/`. This lets tests and other
programs call the behavior without simulating a whole process.

## Standard Streams

| Stream | Contract |
|---|---|
| stdin | Data supplied by a user, pipe, redirected file, or another process |
| stdout | Successful command results that callers may pipe or parse |
| stderr | Diagnostics, warnings, usage errors, and progress |

Accept `io.Reader` and `io.Writer` values at internal boundaries instead of
opening `os.Stdin`, `os.Stdout`, or `os.Stderr` throughout the code. Files,
buffers, network bodies, and process streams can then use the same logic.

## Arguments, Options, and Flags

- `os.Args[0]` identifies the executable; later elements are user arguments.
- Positional arguments carry command operands such as names or paths.
- Flags alter behavior or supply named values.
- Go's `flag` package parses typed values and generates basic help.
- `flag.Args()` returns positional arguments left after flag parsing.
- A `flag.FlagSet` gives a command its own parser and output destination.

Direct `os.Args` inspection is adequate only for tiny, stable interfaces.
Typed parsing scales better and rejects malformed values consistently.

## Input Precedence

When a value can come from multiple sources, the command needs a documented
precedence. A useful default is:

1. Explicit flag or positional argument
2. Environment variable
3. Configuration file
4. Built-in default

For payload data, an explicitly provided argument commonly wins over stdin.
Do not read stdin as an accidental fallback if that could block an interactive
terminal; make the stdin mode explicit or detect the intended mode.

## Environment Variables

Environment variables are useful for per-environment defaults and values users
do not want to repeat. Treat them as configuration, not as hidden commands.

- Use stable, application-prefixed names such as `ACME_CACHE_DIR`.
- Distinguish unset from explicitly empty with `os.LookupEnv` when it matters.
- Resolve environment values once near the process boundary.
- Pass the resulting configuration into application code.

## Standard Flag Grammar

A dedicated `flag.FlagSet` with `flag.ContinueOnError` gives reusable code
control over diagnostics and errors. Standard `flag` parsing stops at the first
non-flag operand; flags after that operand remain positional input. `--`
explicitly ends flag parsing. This grammar differs from Cobra/pflag and must be
documented and tested rather than assumed.

Treat conversion, validation of one value, and validation across values as
separate concerns. A custom `flag.Value` must not leave partially mutated state
after rejecting input. Requested help is represented by `flag.ErrHelp` and is a
successful user action even though parsing returns an error sentinel.

## Output and Exit Status

Successful, machine-consumable results belong on stdout. Errors belong on
stderr. A zero exit status means success; nonzero means the command could not
fulfill its contract. Stable exit behavior lets shells and agents respond
without scraping diagnostic prose.

Usage text should explain syntax, operands, defaults, and important input
alternatives. Help is part of the public interface, not an afterthought.

## Cross-Platform Behavior

Go can target another operating system and architecture using `GOOS` and
`GOARCH`. Cross-compilation proves that code builds for a target; it does not
prove runtime behavior there.

Account for:

- Windows executable suffixes and process conventions
- Paths via `path/filepath`, not hard-coded separators
- Line-ending and terminal differences
- Signals and OS-specific features
- C dependencies, which can complicate static builds and cross-compilation

## Source Traceability

Derived and paraphrased from:

- Chapter 1, “Building the Basic Word Counter,” “Adding Command-Line Flags,”
  and “Compiling Your Tool for Different Platforms” (normalized lines 532–963).
- Chapter 2, “Organizing Your Code,” “Creating the Initial To-Do Command-Line
  Tool,” “Handling Multiple Command-Line Options,” “Display Command-Line Tool
  Usage,” “Increasing Flexibility with Environment Variables,” and “Capturing
  Input from STDIN” (normalized lines 994–2699).
- *Go by Example: Programmer's Guide to Idiomatic and Testable Programs*,
  Chapter 4, “Command-line interfaces” (normalized lines 8752–11420).
