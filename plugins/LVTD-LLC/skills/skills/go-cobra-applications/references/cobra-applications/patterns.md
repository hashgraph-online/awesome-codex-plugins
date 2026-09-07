# Cobra Applications Patterns

Reusable structures for maintainable Cobra applications.

## Pattern: Command Constructor Tree

### Intent

Create an isolated command graph with explicit dependencies.

### Structure

```text
main
└── NewRoot(dependencies)
    ├── newConfigCommand(dependencies)
    └── newJobCommand(dependencies)
        ├── newJobRunCommand(dependencies)
        └── newJobListCommand(dependencies)
```

Each constructor owns its node's metadata, local flags, validation, and child
attachment. The root constructor composes the graph.

### Benefits

- Fresh state for every test and invocation
- Visible dependency flow
- No generator-imposed global initialization order
- Easy reuse for completion and documentation generation

## Pattern: Parse, Invoke, Render

### Intent

Keep framework code thin while preserving a testable business core.

```text
Cobra args/flags
      ↓ parse + validate
typed request → application service → typed result
      ↓ render
stdout / stderr
```

The command callback handles translation only. Application services own policy
and effects; renderers own presentation.

### Use When

- A command performs I/O or nontrivial validation.
- The same operation may be called by another interface.
- Human and JSON output must share behavior.

## Pattern: Dependency Bundle

### Intent

Pass cohesive external capabilities without package globals.

```go
type Dependencies struct {
	Store  Store
	Clock  Clock
	Stdout io.Writer
	Stderr io.Writer
}
```

Keep the bundle concrete and small. Define interfaces at the consuming package,
not around every function preemptively.

## Pattern: Typed Configuration Snapshot

### Intent

Resolve multiple configuration sources once, validate them, then pass an
immutable value to commands and services.

```text
defaults → file → environment → explicit flags → validate → Options
```

### Considerations

- Record whether a flag was explicitly set.
- Avoid global Viper reads inside handlers or domain packages.
- Keep secret-bearing values out of diagnostics and generated docs.
- Test precedence collisions, missing files, malformed values, and zero values.

## Pattern: Validate-Then-Swap Configuration

Load bytes from a local, buffered, or remote source into a new typed value.
Apply precedence, validate the whole candidate, then publish it through an
atomic pointer or locked owner. On failure, retain last-known-good state. The
owner starts and stops watchers and rebuilds dependent resources explicitly.

Use this only when live reload has concrete value; prefer immutable startup
configuration for most short-lived CLIs.

## Pattern: Root-Level Error Policy

### Intent

Make commands return meaningful errors while centralizing presentation and exit
codes.

```text
handler returns wrapped or typed error
        ↓
root runner classifies error
        ↓
stderr message + stable exit code
```

Use argument errors to trigger usage when helpful. Runtime failures should not
usually print a full usage page.

## Pattern: Dual-Layer Testing

### Intent

Test behavior without coupling every test to Cobra.

1. **Application tests:** Call services/actions with fake dependencies and
   assert typed results, state, and errors.
2. **Command tests:** Execute a fresh tree with argument slices and buffers;
   assert parsing, inheritance, output routing, and returned errors.

Add an end-to-end binary test only for process behavior that an in-process
command test cannot cover, such as OS exit status or signals.

## Pattern: Generated Surface From One Tree

### Intent

Prevent drift among runtime help, completion, and documentation.

Use the production command constructor to generate every derivative artifact.
Pin dependency versions, generate in a clean environment, and review output
diffs. Keep dynamic completion side-effect free.

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| Tests leak flags or config | Command Constructor Tree |
| Handler mixes parsing and domain work | Parse, Invoke, Render |
| Commands reach into globals | Dependency Bundle |
| Config precedence is unclear | Typed Configuration Snapshot |
| Errors print twice or show noisy usage | Root-Level Error Policy |
| Tests either mock Cobra or skip parsing | Dual-Layer Testing |
| Help, docs, and completion disagree | Generated Surface From One Tree |

## Historical API Verification

The book's patterns use `cobra.Command`, `AddCommand`, `RunE`, `Args`,
`Flags`, `PersistentFlags`, `SilenceUsage`, completion generators, and
`cobra/doc`, plus Viper flag binding and environment/config readers.

**Upstream verification required:** verify each named Cobra and Viper API,
generator workflow, global initialization behavior, precedence rule, completion
generator, and documentation generator against pinned dependencies. Prefer
constructor-based composition even if current generators still emit globals.

## Source Traceability

- Chapter 7, “Navigating Your New Cobra Application” through “Starting the Scan
  Package,” normalized lines 12027-12803.
- “Creating the Subcommands to Manage Hosts” and “Testing the Manage Hosts
  Subcommands,” normalized lines 12804-13698.
- “Adding the Port Scanning Functionality,” normalized lines 13699-14721.
- “Using Viper for Configuration Management,” normalized lines 14722-14948.
- “Generating Command Completion and Documentation,” normalized lines
  14949-15235.
