# Cobra Applications Rules

Actionable rules for command trees, dependencies, configuration, errors, and
tests.

## Command Tree

1. **Construct commands in functions.** Return a fresh root for each execution
   and test; avoid mutable package-global command values.
2. **Keep the root inert by default.** A bare command should show help unless
   the product has one obvious default operation.
3. **Group by user intent.** Parent commands name resources or workflows;
   children name operations.
4. **Use precise invocation contracts.** `Use`, descriptions, argument
   validation, examples, and aliases must agree.
5. **Scope flags narrowly.** Use a local flag for one command and a persistent
   flag only when every relevant descendant shares its meaning.
6. **Avoid shorthand collisions.** Reserve short flags for frequent,
   unambiguous options across the entire inherited scope.

## Dependencies and Business Logic

7. **Keep Cobra at the edge.** Handlers translate CLI values into typed
   application calls; domain packages must not import Cobra or Viper.
8. **Inject effects.** Pass services, filesystem abstractions, clocks, and
   streams through constructors or a dependency struct.
9. **Pass context.** Long-running operations must accept the command context
   and stop on cancellation.
10. **Return values and errors.** Do not call `os.Exit`, `log.Fatal`, or panic
    below the process entry point.
11. **Separate rendering.** Make human and machine output explicit renderers
    rather than interleaving formatting with business operations.

## Flags and Configuration

12. **Define precedence once.** Document and test defaults, file, environment,
    and flag ordering.
13. **Resolve into a typed config.** Commands should pass validated values to
    the application rather than exposing a configuration registry.
14. **Distinguish unset from explicit zero.** Use changed-state checks or
    nullable representations when `0`, `false`, or empty string is meaningful.
15. **Normalize environment keys.** Give the tool a stable prefix and define
    dash-to-underscore mapping.
16. **Validate semantic ranges.** Parser success does not prove that a port,
    timeout, path, or concurrency value is valid.
17. **Do not log secrets.** Mark sensitive inputs, avoid defaults that expose
    them in help, and prefer secure sources over command-line arguments.
18. **Treat configuration sources as inputs, not shared state.**
    - Put file, buffered, and remote sources behind an explicit loader.
    - Keep mutable user or application records in a dedicated store.
19. **Reload by validating then swapping.**
    - Parse and validate a complete candidate before publishing it atomically.
    - Retain last-known-good state when reload fails.
    - Own watcher shutdown and dependent-client replacement explicitly.
    - Capture one immutable settings/client snapshot at command start; do not
      mix base URLs, credentials, cursors, or retry policies within one operation.
    - Retire replaced clients only after in-flight users release the old snapshot.

## Errors and Output

20. **Use error-returning handlers.** Return failures with operation context.
21. **Choose exit codes centrally.** Map typed errors to stable exit codes at
    the entry point.
22. **Route streams consistently.** Results go to stdout; diagnostics and
    progress go to stderr.
23. **Silence usage selectively.** Show it for syntax problems, not for network,
    filesystem, or application failures.
24. **Check write errors.** Rendering can fail when output is piped.

## Completion and Documentation

25. **Generate from the real tree.** Completion and docs must use the same
    constructor and metadata as runtime commands.
26. **Support declared shells deliberately.** Do not label a Bash-only command
    as generic completion.
27. **Keep completion safe.** No mutations, prompts, or expensive unbounded
    calls in completion callbacks.
28. **Make generated docs reproducible.** Pin dependency versions and review
    generated diffs.

## Testing

29. **Build a fresh root per test.**
30. **Capture command streams.** Do not replace process-global stdout or stderr.
31. **Test both seams.** Unit-test application actions and integration-test
    parsing, validation, flag inheritance, config precedence, errors, and help.
32. **Use isolated temporary state.** Prefer test-owned temporary directories
    and automatic cleanup.
33. **Assert behavior, not framework internals.** Test output, calls, state,
    errors, and exit mapping.
34. **Cover repeated execution.** A command tree should behave consistently
    when invoked more than once in the same process.
35. **Do not import standard `flag` assumptions.** Verify pflag interspersed
    parsing, `--`, repeated values, and positional validators.
36. **Keep custom values transactional.** Rejected input must not leave partial
    mutation, and defaults must render correctly.
37. **Test help and diagnostics deliberately.** Assert the selected Cobra
    output methods and usage policy against the pinned version.

## Historical API Verification

The source demonstrates these version-sensitive APIs: `cobra.Command`,
`AddCommand`, `RunE`, `MinimumNArgs`, `SilenceUsage`, `Flags`,
`PersistentFlags`, `SetVersionTemplate`, `GenBashCompletion`,
`cobra/doc.GenMarkdownTree`, plus Viper `BindPFlag`, `AutomaticEnv`,
`SetEnvPrefix`, `SetEnvKeyReplacer`, `SetConfigFile`, `AddConfigPath`,
`SetConfigName`, `ReadInConfig`, and `GetString`.

**Upstream verification required:** confirm every listed API, the Cobra
generator workflow, initialization hooks, shell-completion functions,
documentation package, and Viper precedence semantics against pinned current
versions before implementation.

## Source Traceability

- Chapter 7, “Navigating Your New Cobra Application” through “Adding the First
  Subcommand to Your Application,” normalized lines 12027-12360.
- “Creating the Subcommands to Manage Hosts” and “Testing the Manage Hosts
  Subcommands,” normalized lines 12804-13698.
- “Adding the Port Scanning Functionality,” normalized lines 13699-14721.
- “Using Viper for Configuration Management,” normalized lines 14722-14948.
- “Generating Command Completion and Documentation,” normalized lines
  14949-15235.
