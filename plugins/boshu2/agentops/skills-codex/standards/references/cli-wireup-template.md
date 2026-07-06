# CLI Wireup Template (Go + cobra + Hexagonal Adapter)

The reproducible cycle-shape for exposing a production adapter as an `ao`
subcommand. Empirically derived across `/evolve` cycles 144-146 (three
`ao` subcommands shipped in ~10 minutes each, ~250-335 LOC including
tests + docs). Captured durably here so any future port-to-subcommand
slice is mechanical.

Mirror of `docs/learnings/2026-05-13-cli-wiring-cycle-shape.md` (canonical
source). Copied per CI's no-symlinks rule so `/standards`-consuming agents
discover it via the skill-link path.

## The 3 Reference Cycles (Empirical Baseline)

| Cycle | Subcommand | Adapter | Time | LOC | Tests |
|---|---|---|---|---|---|
| 144 | `ao loop history` | `productionLoopReader` | ~10 min | 335 | 6 |
| 145 | `ao ci latest/recent` | `productionCIStatus` | ~8 min | 258 | 4 |
| 146 | `ao corpus inject` | `productionCorpusReader` | ~8 min | 252 | 5 |

**8-10 minutes wall-clock**, ~250-335 LOC. Adapter-side complexity
dominates the variation — Loop took longer because it needed JSON
slicing logic; CI was simplest because the adapter already had a clean
stub-injectable shape.

## The Template

```go
// cli/cmd/ao/<noun>.go
var <noun>Cmd = &cobra.Command{
    Use:   "<noun>",
    Short: "BC<n> <surface> operations",
}

var <noun><Verb>Cmd = &cobra.Command{
    Use:   "<verb> [flags]",
    Short: "Short imperative description",
    Long:  `Long description with Examples block.`,
    RunE:  run<Noun><Verb>,
}

type <noun><Verb>Options struct {
    // flag-derived fields
    writer io.Writer
    // injectFn lets tests substitute the port without real I/O
    injectFn func(ctx context.Context, opts <noun><Verb>Options) ([]ports.X, error)
}

func init() {
    <noun>Cmd.GroupID = "core"
    rootCmd.AddCommand(<noun>Cmd)
    // flag registrations
    <noun>Cmd.AddCommand(<noun><Verb>Cmd)
}

func run<Noun><Verb>(cmd *cobra.Command, _ []string) error {
    // pull flag values, build options, delegate
    return <noun><Verb>Run(cmd.Context(), opts)
}

func <noun><Verb>Run(ctx context.Context, opts <noun><Verb>Options) error {
    if opts.writer == nil { opts.writer = os.Stdout }
    fn := opts.injectFn
    if fn == nil { fn = <noun><Verb>ViaPort }
    items, err := fn(ctx, opts)
    if err != nil { return fmt.Errorf("<noun> <verb>: %w", err) }
    enc := json.NewEncoder(opts.writer)
    for _, item := range items {
        if err := enc.Encode(item); err != nil {
            return fmt.Errorf("<noun> <verb> encode: %w", err)
        }
    }
    return nil
}

func <noun><Verb>ViaPort(ctx context.Context, opts <noun><Verb>Options) ([]ports.X, error) {
    adapter := newProduction<X>(/* construction args */)
    return adapter.<Method>(ctx, /* args */)
}
```

```go
// cli/cmd/ao/<noun>_test.go
// 4-6 tests covering:
//   - stub returns N items → N lines emitted
//   - stub returns empty → 0 bytes emitted
//   - stub error → wrapped error
//   - live root (filesystem fixture) → walks correctly
//   - flag combinations (limit, range, etc.) honored
```

After the `.go` + `_test.go` files: `scripts/generate-cli-reference.sh`
regenerates `cli/docs/COMMANDS.md`. **Don't forget `generate-registry.sh`
too** — the `cli-command-dual-generator` learning documents the failure
mode where one is regenerated and the other isn't.

## Why This Shape Works

1. **Parent noun + verb subcommands.** `ao loop history` reads better
   than the flat `loop-history` spelling. The parent groups future subcommands
   (`ao loop write`, `ao loop tail`) under one verb-space. cobra
   handles this natively.

2. **Injectable function field on Options.** Production runs use the
   default port wrapper; tests substitute a stub. This is the same
   pattern cycle 117's `productionCIStatus.runGH` proved — refined here
   from a struct field to an option-bag function. Faster than
   fake-file-tree harnesses and platform-neutral.

3. **Line-delimited JSON output.** One record per line means the
   output composes with `jq -c`, `head`, `grep`, `awk`. Operators
   don't need to remember the schema; they pipe and `jq '.field'`.

4. **Error wrapping with the command name.** `"<noun> <verb>:
   underlying error"` makes debugging easy when the cobra layer
   surfaces an error to stderr.

5. **Validate by live smoke after build.** Each cycle ran `make build`
   then `./bin/ao <noun> <verb> <args>` against real data. Proves
   end-to-end semantic correctness, not just compilation.

## Anti-Patterns (Observed Across The 3 Cycles)

- **Name collisions in `cli/cmd/ao`.** Cycle 144's first helper was
  named `loadCycleHistory` — collided with an existing function in
  `metrics_health.go`. `go vet` caught it; renamed to
  `loadCycleHistoryViaPort`. **Always `grep` before naming helpers
  in `cli/cmd/ao`** (the package is ~150 files).

- **Shadowing Go builtins.** Cycle 117 used `cap := limit`; same rule
  applies to CLI helpers.

- **Dead imports of `internal/ports` in test files.** Cycle 144's
  first test file had a dead import; `go vet` caught it.

- **Forgetting the registry regen.** `scripts/generate-cli-reference.sh`
  is the obvious regen; `scripts/generate-registry.sh` is the
  not-obvious one. Both are required when adding a `cobra.Command`. See
  the `cli-command-dual-generator` learning for the failure mode.

## Pre-Flight Checklist

Before writing the `.go` file:

```bash
# 1. Pick noun + verb. Verify no collision in cli/cmd/ao:
grep -rn "Cmd = &cobra.Command" cli/cmd/ao/ | grep -i "<noun>"

# 2. Verify helper names don't collide:
grep -rn "func <helperName>\b" cli/cmd/ao/

# 3. Confirm the port + production adapter exist:
ls cli/internal/ports/<surface>.go cli/internal/adapters/*<X>*.go
```

After committing:

```bash
# Regenerate BOTH:
scripts/generate-cli-reference.sh
scripts/generate-registry.sh

# Smoke test:
cd cli && make build && ./bin/ao <noun> <verb> <args>
```

## Worked Reference Implementations

The 3 reference implementations on `main`:

- `cli/cmd/ao/loop.go` + `loop_test.go` — `ao loop history`
- `cli/cmd/ao/ci.go` + `ci_test.go` — `ao ci latest/recent`
- `cli/cmd/ao/corpus_inject.go` + `corpus_inject_test.go` — `ao corpus inject`

Read those 3 pairs before writing a new wireup; they're shorter than
this template.

## See Also

- `docs/learnings/2026-05-13-cli-wiring-cycle-shape.md` — canonical
  source (this file is the skill-side mirror)
- `docs/learnings/2026-05-13-bc-ports-wire-up-arc.md` — the broader
  14-port wire-up arc (cycle 122); historical/architecture, not
  a reusable template
- `docs/learnings/2026-05-13-bc-ports-narrowness-postmortem.md` — the
  narrowness debate that preceded the wire-up
- `references/go.md` — Go conventions this template assumes
