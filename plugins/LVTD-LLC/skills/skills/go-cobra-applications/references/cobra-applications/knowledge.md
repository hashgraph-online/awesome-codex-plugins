# Cobra Applications Knowledge

Core concepts for structuring testable Go command-line applications with Cobra.

## Command Model

`cobra.Command` represents one command node. A root command and its descendants
form a tree:

```text
tool
├── account
│   ├── add
│   └── list
├── completion
└── version
```

Each node describes its invocation (`Use`), concise purpose (`Short`), optional
detail (`Long`), argument contract (`Args`), flags, and execution callback.
Parent nodes often group related operations and intentionally have no action.

Help, usage, suggestions, completion, and generated documentation derive from
this metadata. Treat command metadata as a user-facing contract, not filler.

## Root and Subcommands

- Keep `main` limited to constructing and executing the application.
- Make the root a grouping command unless invoking the bare binary has a clear
  operation.
- Attach each child to the intended parent; tree position determines its
  invocation path and inherited flags.
- Put flags on the narrowest command that needs them.
- Use persistent flags only for values genuinely shared by a whole subtree.
- Validate positional arguments before performing work.
- Prefer clear names over aliases; aliases are compatibility conveniences.

## Command Boundary

Cobra should adapt CLI input to application calls:

1. Parse and validate arguments and flags.
2. Resolve configuration.
3. Call application or domain logic.
4. Render the result.
5. Return an error to the top-level exit policy.

Business logic should not depend on `*cobra.Command`, package-global flags, or
process streams. Give it ordinary Go parameters, interfaces, and `context.Context`.
This keeps the core reusable and lets tests bypass parser internals.

## Error and Output Boundaries

Use error-returning handlers for fallible work. A command should return
context-rich errors; only the process entry point should choose an exit code.

Inject or obtain output from the command rather than writing directly to
`os.Stdout`. Keep normal output on stdout and diagnostics on stderr. Suppress
usage for runtime failures when repeating syntax would obscure the real error,
but preserve usage for parsing or argument errors.

## Configuration

Configuration can come from defaults, files, environment variables, and flags.
Define and test precedence explicitly. A practical order is:

```text
explicit flag > environment > config file > built-in default
```

Normalize key naming deliberately, such as mapping `cache-dir` to
`TOOL_CACHE_DIR`. Avoid reading configuration through package-global state in
business logic; resolve it once into a typed configuration value.

Viper can bind keys to flags and read environment variables and files, but it
adds global state and subtle precedence behavior. Use it only when the
configuration surface warrants the dependency.

## Completion and Documentation

Completion should cover every supported shell and should be generated from the
same command tree users execute. Dynamic completion must be fast, side-effect
free, and safe when invoked repeatedly.

Generated documentation reflects command metadata. Generate it in a repeatable
build or release workflow, review diffs, and avoid embedding unstable timestamps
when deterministic output matters.

## Testing Seams

Two complementary seams are useful:

- Test application functions directly with fake dependencies and buffers.
- Test a newly constructed root command with arguments and captured streams.

Construct a fresh tree per test. Global command variables, global Viper state,
and direct process exits cause test leakage and make parallel tests unsafe.

## Parser Boundary

Standard `flag.FlagSet` grammar does not describe Cobra/pflag behavior.
Interspersed flags, `--`, positional validators, custom values, help, and error
output must be verified against the pinned Cobra and pflag versions. Keep
framework parsing diagnostics separate from application error presentation.

## Historical and Version-Sensitive Material

The source uses Cobra v1.1.3-era generator commands, generated `init` functions,
package-global command variables, `RunE`, `SilenceUsage`, `MinimumNArgs`,
`PersistentFlags`, `Flags`, `AddCommand`, `GenBashCompletion`, and
`cobra/doc.GenMarkdownTree`. It uses Viper's `AutomaticEnv`,
`SetEnvKeyReplacer`, `SetEnvPrefix`, `BindPFlag`, `SetConfigFile`,
`AddConfigPath`, `SetConfigName`, and `ReadInConfig`.

**Upstream verification required:** verify every Cobra and Viper identifier,
generator/install command, initialization pattern, precedence behavior, and
completion/documentation API above against the versions pinned by the target
module. Do not copy the book's installation commands or generated layout.

## Source Traceability

- *Powerful Command-Line Applications in Go*, Chapter 7, “Using the Cobra CLI
  Framework” and “Starting Your Cobra Application,” normalized lines
  11848-12026.
- “Navigating Your New Cobra Application” and “Adding the First Subcommand to
  Your Application,” normalized lines 12027-12360.
- “Starting the Scan Package,” “Creating the Subcommands to Manage Hosts,” and
  “Testing the Manage Hosts Subcommands,” normalized lines 12361-13698.
- “Adding the Port Scanning Functionality,” normalized lines 13699-14721.
- “Using Viper for Configuration Management,” normalized lines 14722-14948.
- “Generating Command Completion and Documentation,” normalized lines
  14949-15235.
