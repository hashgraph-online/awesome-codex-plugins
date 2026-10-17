# Cobra Applications Checklist

Use when implementing or reviewing a Cobra command-line application.

## Parser Contract

- [ ] Interspersed flags and `--` behavior match the pinned pflag version.
- [ ] Positional argument cardinality and validation are explicit.
- [ ] Custom value defaults, repetition, and failed mutation are tested.
- [ ] Help, usage, diagnostics, and returned errors use the intended streams.

## Command Structure

- [ ] A function constructs a fresh root command.
- [ ] `main` only wires dependencies, executes, reports, and exits.
- [ ] The tree mirrors user tasks and has no unnecessary nesting.
- [ ] Grouping commands do not perform surprising default actions.
- [ ] Every command has accurate usage, short help, and argument validation.
- [ ] Aliases are intentional, documented, and collision-free.
- [ ] Local flags stay local.
- [ ] Persistent flags are relevant to every inheriting descendant.
- [ ] Shorthand flags do not collide within inherited scopes.
- [ ] Typo-suggestion behavior is intentional and tested.

## Application Boundary

- [ ] Domain and application packages do not import Cobra or Viper.
- [ ] Handlers only parse, validate, invoke, and render.
- [ ] Effects are injected through narrow dependencies.
- [ ] Long-running work receives the command context.
- [ ] Human and structured output use explicit renderers.
- [ ] No library code calls `os.Exit`, `log.Fatal`, or panic for normal errors.

## Flags and Configuration

- [ ] Precedence among defaults, file, environment, and flags is documented.
- [ ] Precedence collisions have tests.
- [ ] Explicit zero values are distinguishable from unset values where needed.
- [ ] Environment variables use a stable application prefix.
- [ ] Key normalization is documented.
- [ ] Resolved configuration is typed and validated before business logic runs.
- [ ] Numeric ranges, paths, enumerations, and cross-field constraints are
      validated.
- [ ] Secrets are not exposed in arguments, help, logs, errors, or generated
      docs.
- [ ] Missing optional config and malformed config have distinct behavior.
- [ ] Local, buffered, or remote sources enter through a loader boundary.
- [ ] Configuration is not used as mutable application storage.
- [ ] Reload validates before atomic swap and retains last-known-good state.
- [ ] Watchers and replaced clients have explicit cleanup.
- [ ] Each operation captures one immutable settings/client snapshot.
- [ ] Replaced clients retire only after in-flight operations finish.

## Errors and Streams

- [ ] Fallible handlers return errors.
- [ ] Errors include useful operation context without duplicating messages.
- [ ] Typed or sentinel errors map to stable exit codes centrally.
- [ ] Normal results go to stdout.
- [ ] Diagnostics and progress go to stderr.
- [ ] Write failures are returned.
- [ ] Usage appears for syntax errors but not routine runtime failures.
- [ ] Cancellation reaches active work and cleanup.

## Testing

- [ ] Every test constructs a new command tree.
- [ ] Tests set arguments directly and capture command-owned streams.
- [ ] Tests do not replace process-global stdout, stderr, env, or working
      directory without isolated cleanup.
- [ ] Application logic has direct unit tests.
- [ ] Command tests cover valid and invalid arguments.
- [ ] Tests cover local and inherited flags.
- [ ] Tests cover repeated execution in one process.
- [ ] Help and error-output routing are asserted.
- [ ] Temporary state uses test-owned directories.
- [ ] At least one integration test covers a representative command sequence.
- [ ] OS exit codes are tested at the process boundary when part of the contract.
- [ ] Reload tests cover valid update, invalid retention, cancellation, and cleanup.
- [ ] An in-flight reload race test proves an operation cannot mix snapshots.

## Completion and Documentation

- [ ] Supported shells are named explicitly.
- [ ] Completion generation uses the production tree.
- [ ] Dynamic completion is fast, bounded, noninteractive, and side-effect free.
- [ ] Completion failure does not corrupt normal output.
- [ ] Documentation generation uses the production tree.
- [ ] Generated artifacts are reproducible and reviewed.
- [ ] Help examples are executable and current.
- [ ] Generated output does not contain accidental timestamps or local paths.

## Version Gate

- [ ] The module pins Cobra and, if used, Viper versions.
- [ ] Current official Cobra installation and generator guidance was checked.
- [ ] `cobra.Command` fields and execution methods were checked upstream.
- [ ] Argument validators, flag APIs, output APIs, and context APIs were checked.
- [ ] Completion APIs for every supported shell were checked.
- [ ] `cobra/doc` generators and output behavior were checked.
- [ ] Viper binding, environment, file-reading, and precedence behavior were
      checked.
- [ ] Historical `ioutil` and home-directory helpers were replaced with current
      standard-library equivalents where appropriate.

## Red Flags

Stop and redesign when:

- Commands, flags, or Viper state are mutable package globals.
- Business logic accepts `*cobra.Command`.
- A child command reads flags by reaching into unrelated global state.
- Runtime failures print the error twice or always dump usage.
- Tests depend on execution order or leak flags between cases.
- Completion performs mutations, prompts, or unbounded network calls.
- Generated documentation is treated as authoritative without validating the
  command metadata.

## Historical API Verification

The source demonstrates `cobra.Command`, `AddCommand`, `RunE`,
`MinimumNArgs`, `SilenceUsage`, `Flags`, `PersistentFlags`,
`SetVersionTemplate`, `GenBashCompletion`, `cobra/doc.GenMarkdownTree`, and
Viper configuration/binding APIs.

**Upstream verification required:** verify every listed Cobra/Viper API and any
replacement selected during implementation against the target module's pinned
versions.

## Source Traceability

- Chapter 7, “Navigating Your New Cobra Application” and “Adding the First
  Subcommand to Your Application,” normalized lines 12027-12360.
- “Creating the Subcommands to Manage Hosts” and “Testing the Manage Hosts
  Subcommands,” normalized lines 12804-13698.
- “Adding the Port Scanning Functionality,” normalized lines 13699-14721.
- “Using Viper for Configuration Management,” normalized lines 14722-14948.
- “Generating Command Completion and Documentation,” normalized lines
  14949-15235.
- “Exercises” and “Wrapping Up,” normalized lines 15236-15263.
