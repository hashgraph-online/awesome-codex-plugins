# Go CLI Command Interface Rules

Actionable rules for implementing predictable, composable Go commands.

## Boundaries and Organization

1. **Keep `main` mechanical.**
   - Resolve process inputs, call a testable runner, print diagnostics, and exit.
   - Keep domain state and behavior in importable packages.

2. **Inject process resources.**
   - Pass `io.Reader` and `io.Writer` values to command logic.
   - Pass parsed configuration rather than reading global environment state deep
     inside the application.

3. **Use one executable directory per command.**
   - Prefer `cmd/<command>/main.go` when the module contains reusable packages
     or multiple binaries.
   - Do not create package structure solely to mimic a template for a tiny,
     single-file utility.

## Inputs and Precedence

4. **Parse typed flags before reading remaining arguments.**
   - Define all flags, call `Parse`, check its error, then inspect `Args`.
   - Prefer a dedicated `flag.FlagSet` over package globals in testable code.

5. **Give each action an unambiguous interface.**
   - Reject conflicting action flags instead of silently choosing the first
     matching branch.
   - Reject missing operands and unexpected trailing arguments.

6. **Document precedence explicitly.**
   - Use explicit CLI input over environment defaults.
   - Use environment values over built-in defaults.
   - If positional data and stdin are both accepted, state which wins.

7. **Do not unexpectedly block on stdin.**
   - Read stdin only for a documented mode or an intentional pipeline contract.
   - Validate empty input after trimming according to the command's semantics.
   - Always check scanner or decoder errors.

8. **Use environment variables for defaults, not secret side effects.**
   - Prefix names with the application name.
   - Use `os.LookupEnv` when empty and unset have different meanings.
   - Never echo secret values in help or diagnostics.

## Output, Errors, and Help

9. **Keep stdout clean.**
   - Write successful results to stdout.
   - Write requested help to stdout so `--help` is a successful operation.
   - Write errors, warnings, usage caused by invalid syntax, and progress to stderr.
   - Avoid combining streams in tests when their separation is part of the
     public contract.

10. **Return errors; call `os.Exit` only at the outermost boundary.**
    - A runner should return an error or exit code so deferred cleanup and tests
      work normally.
    - Map invalid usage and operational failure to deliberate nonzero codes.

11. **Make help complete and stable.**
    - Include a one-line purpose, syntax, operands, input alternatives, defaults,
      and examples where ambiguity remains.
    - Route parser help through the parser's configured output.

12. **Treat output format as an API.**
    - Test exact formatting when scripts or agents depend on it.
    - Keep human display formatting separate from persistent serialization.

## Portability

13. **Use platform-aware APIs.**
    - Construct filesystem paths with `filepath`.
    - Do not assume executable suffixes, separators, signals, or terminal
      capabilities are identical across operating systems.

14. **Build and test each supported target.**
    - Set both `GOOS` and `GOARCH` for release builds.
    - Run smoke tests on the target OS; cross-compilation alone is insufficient.
    - Verify static-link assumptions when cgo or native dependencies are present.

## Naming and Interaction Modes

15. **Follow established command vocabulary.**
    - Prefer lowercase command and long-flag names and conventional flags such
      as `--help`, `--version`, `--quiet`, and `--output`.
    - Add aliases only for compatibility or proven common usage.

16. **Make output and interaction modes explicit.**
    - Define human, plain, and structured output separately.
    - Let explicit flags override environment and TTY-derived defaults.
    - Detect stdin, stdout, and stderr capabilities independently.
    - Honor `NO_COLOR` and never rely on color alone.

17. **Keep automation noninteractive and bounded.**
    - Never prompt or animate in structured or declared noninteractive mode.
    - Send progress to stderr only in compatible human mode.
    - Keep secrets out of argv, logs, errors, and diagnostic bundles.
    - Propagate context cancellation through effects.
    - Treat a normal downstream broken pipe as pipeline completion, not a crash.

## Parser Contract

18. **Choose and document the parsing grammar.**
    - State whether flags may appear after operands.
    - Test `--`, repeated flags, missing values, and extra operands.
    - Do not copy standard `flag` behavior into Cobra/pflag guidance.

19. **Separate conversion and validation.**
    - Parse text into typed values without partial mutation on failure.
    - Validate individual values, then conflicts and cross-field invariants.
    - Parse documented decimal values with decimal semantics rather than
      surprising base inference.

20. **Treat help as success.**
    - Detect `flag.ErrHelp` separately from invalid usage.
    - Avoid printing the same parser diagnostic at multiple layers.
    - Keep usage policy at the command boundary.

## Quick Reference

| Concern | Do | Don't |
|---|---|---|
| Parsing | Use a checked `FlagSet` | Mutate global flags in reusable logic |
| Input | Define precedence | Guess between args, env, and stdin |
| Output | stdout results/help, stderr diagnostics | Mix logs with pipeable data |
| Errors | Return to the boundary | Exit inside helpers |
| Portability | Target-build and smoke-test | Assume a build proves runtime behavior |

## Source Traceability

Derived and paraphrased from:

- Chapter 1, “Building the Basic Word Counter,” “Adding Command-Line Flags,”
  and “Compiling Your Tool for Different Platforms” (normalized lines 548–937).
- Chapter 2, “Organizing Your Code,” “Creating the Initial To-Do Command-Line
  Tool,” “Handling Multiple Command-Line Options,” “Display Command-Line Tool
  Usage,” “Increasing Flexibility with Environment Variables,” and “Capturing
  Input from STDIN” (normalized lines 1012–2699).
- *Go by Example: Programmer's Guide to Idiomatic and Testable Programs*,
  Chapter 4, normalized lines 8752–11420.
