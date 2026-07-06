# Standing up a correct Gas City (native + membrane)

> Codifies the proven recipe from the live reference city (`~/dev/gc-city`,
> RUNBOOK.md) and the adoption slate. Order matters — the failure modes this
> sequence prevents are silent (perf cliffs, print-sinks, port collisions).
> When `scripts/install-gc-city.sh` lands (bead age-gc-adoption-u0he.1) it
> automates this file; until then this IS the bootstrap contract.

## 0. Isolation invariants (before anything)

- **Own city dir** (its own git repo), **dedicated `GC_HOME`** at
  `<city>/.gc-home` — the legacy `~/.gc` is NEVER touched or migrated.
  Fresh-under-dedicated-GC_HOME beats migrating a stale one, always.
- **Dedicated tmux socket** (`-L <city-name>`) so the city coexists cleanly
  with NTM and other cities.
- **Explicit supervisor port**: isolated GC_HOMEs do NOT auto-pick a port
  (unless `GC_ISOLATED=1`). If another city holds the default 8372, set the
  port in `<GC_HOME>/supervisor.toml` — this file is load-bearing.
- An `env.sh` at the city root is the operator entrypoint: exports `GC_HOME`,
  puts the city's PATH shims first, defines the `gc` wrapper. Every operator
  command starts with `source <city>/env.sh`.

## 1. Version contract (the silent cliff)

| Component | Contract |
|---|---|
| `bd` | Must EXACTLY match the beads library gc links (`go.mod` of your gc build pins `steveyegge/beads vX.Y.Z` — match it; e.g. gc edge 8b17c64 pins v1.1.0) |
| `dolt` | ≥ the managed floor gc's dolt pack pins (2.1.x line; newer patch fine) |
| `gc` | Build from the fork with `make build` (CGO/icu4c: needs `brew --prefix icu4c`), NOT bare `go build`. Install so ONE binary wins on PATH — stale duplicate gc binaries in `~/go/bin` have shadowed the real one before. |

**THE gate that matters:**

```bash
cd <city> && bd context --json | jq .dolt_mode     # MUST print "server"
gc status --json | jq .beads
# MUST show {"beads_store":"NativeDoltStore","native_store_eligible":true}
```

Anything else means gc fell back to per-op `bd` subprocess calls — a
documented perf cliff — or worse, the file backend. **`GC_BEADS=file` is a
troubleshooting escape hatch, not a real backend**: the control dispatcher and
core-pack orders shell out to `bd` and die on it (proven: the file-backend MVP
needed a hand-rolled control pump; every one of those brittlenesses vanished
on native).

## 2. Init and pinned packs

```bash
gc init <city> --no-start     # writes pack.toml with pinned core+bd imports + packs.lock
```

`gc init` writes sha-pinned `core` + `bd` imports (bd pulls `dolt`
transitively) served offline from the binary's embedded cache. Don't fight or
hand-edit the pins. Add remote packs with durable tree-URLs + version pins
(`gc import add <url> --name <n> --version <pin>` then `gc import install`).
The `agentops-membrane` pack may be imported by **absolute local path** (no
lock — read-in-place) when iterating on the pack or when network git is
wedged on the host (see §6); pin it by sha once published.

Dolt lifecycle is **gc-managed** (start/stop/SIGTERM grace/auto-GC): never run
your own `dolt sql-server` against `<city>/.beads/dolt`. The live port is
recorded in `.beads/dolt-server.port`; the generated
`.gc/runtime/packs/dolt/dolt-config.yaml` is not hand-editable (override via
`GC_DOLT_PORT`).

## 3. Providers — three families, LAW 0 structural

```toml
[workspace]
provider = "codex"                    # workspace default: NOT claude (title-gen sink)

[providers.claude]
base = "builtin:claude"
print_args = []                       # LAW 0: builtin default is ["-p"] — kill it

[providers.codex]
base = "builtin:codex"

[providers.antigravity]               # the Gemini family — via agy
base = "builtin:antigravity"
print_args = []                       # kills its builtin ["--print"] one-shot sink
```

- The builtin `gemini` provider shells the bare `gemini` CLI — on hosts where
  the sanctioned path is `agy`, use the builtin **`antigravity`** provider
  (its Command IS `agy`). Shell aliases don't reach child processes.
- `print_args = []` works because an empty NON-nil array overrides the builtin
  default (BurntSushi toml decodes it non-nil). The `law0-print-args` doctor
  check (exit-2 BLOCKING) asserts this holds for every claude/antigravity
  provider — a template refresh that silently restores `["-p"]` fails doctor.

## 4. Membrane wiring (the close door)

Import the pack, then make the reviewer lanes **always-on named sessions** so
`gc session submit` delivery is deterministic:

```toml
[imports.agentops-membrane]
source = "<pinned tree-url or local path>"

[[named_session]]
template = "agentops-membrane.verifier"        # LANE1: codex/gpt
mode = "always"
[[named_session]]
template = "agentops-membrane.agy-verifier"    # LANE2: antigravity/gemini
mode = "always"
```

**Known gap (A):** `gc import` does NOT materialize the pack's gate scripts
into the city — the check step resolves `membrane/close-gate.sh` against the
city root. Copy the pack's `membrane/` scripts to `<city>/membrane/` until the
install script automates it, or the dispatcher will quarantine every workflow
at the check step.

**Pre-trust the provider modals now** (they otherwise wedge the first
verifier lane):

```bash
export CODEX_HOME="<city>/.gc/codex-home"      # wire into codex provider env
mkdir -p "$CODEX_HOME" && printf '{}\n' > "$CODEX_HOME/hooks.json"
# agy: run the provider once interactively and accept its trust prompt
```

## 5. Boot and gate on green

```bash
source <city>/env.sh
gc start          # registers city, boots managed dolt, controller, named sessions
gc status         # controller PID, agents, named sessions, store health
gc doctor         # the standup gate — do not proceed on red
```

**Canonical green:** `law0-print-args` ok; `membrane-health` ok (door present
+ executable, trinity present, **≥2 provider families** — a 1-family city can
never CONFIRM and is flagged early); `dolt-server` reachable; `beads-store`
accessible; `controller` running. **Known-benign warnings:** `jsonl-archive`
(local-only mode), `formula-requirements` (optional deps), provider-catalog
advisory, `codex-hooks-drift` (upstream churn).

The supervisor runs under launchd/systemd and restarts itself;
`gc service restart` restarts it deliberately. After a gc binary rebuild,
`gc start` auto-restarts on drift (`auto_restart_on_drift`, default true).

## 6. Host quirks worth pre-empting

- **Network-git hang (~151 s to github.com,** rtk/homebrew-git signature): if
  pack clones hang, install the git shim — `$GC_HOME/bin/git -> /usr/bin/git`,
  first on PATH via `env.sh`. `gc import install` works through it.
- **Rigs:** for real work on an external repo, register it —
  `gc rig add <path>` — rather than growing quest dirs in the city root. Each
  rig gets its own bead namespace + agent scope (this is gc's documented
  canonical shape; the city-internal quests pattern is for factory
  self-validation).
