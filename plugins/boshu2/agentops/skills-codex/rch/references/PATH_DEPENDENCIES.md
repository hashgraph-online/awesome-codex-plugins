# Path Dependencies, Workspaces, and Topology

## Contents

- [Mental Model](#mental-model)
- [The `[path_topology]` Section](#the-path_topology-section)
- [Closure Planner](#closure-planner)
- [Common Failure Patterns](#common-failure-patterns)
- [Strategies](#strategies)
- [Diagnostic Commands](#diagnostic-commands)

The single largest class of "RCH worked yesterday, fails today" incidents is **multi-repo workspace topology**: a `Cargo.toml` somewhere has `path = "../../other-repo"`, and either RCH can't decide what to ship or the worker doesn't have the sibling repo at the right place.

This file is the canonical guide. It also covers the `[path_topology]` config section, which lets you **change** the canonical roots away from the hard-coded defaults.

---

## Mental Model

RCH plans a **dependency closure** before shipping anything. Three things have to line up:

1. **Workspace expansion.** RCH walks `cargo metadata` from the entry manifest, follows every local `path = "..."`, and promotes nested path-deps to their enclosing workspace root.
2. **Canonical-root containment.** Every root in the closure must live under `[path_topology] canonical_root` (default `/data/projects`). If any escapes, RCH refuses to ship the closure (`RCH-E016`) and falls open.
3. **Worker-side mirror.** Each closure root must already exist on the chosen worker under the canonical root, with the SSH user able to write to it.

If any of these breaks, you'll see one of:

- `[RCH] local (dependency preflight RCH-E0XX: <remediation>)` — closure planner refused
- `[RCH] local (all workers failed repo convergence checks)` — snake-case tag `all_workers_failed_convergence`; workers couldn't bring repos to needed state
- `RCH-E405 Permission denied during file transfer` — mirror perms broken
- rsync error mentioning a path under the canonical root that doesn't exist on the worker

---

## The `[path_topology]` Section

Defaults:

```toml
[path_topology]
# canonical_root = "/data/projects"   # Where canonical project paths live
# alias_root     = "/dp"              # Optional symlink alias (must point at canonical_root)
```

Override in `~/.config/rch/config.toml` (host-wide) or `.rch/config.toml` (project-local). Env-var overrides:

```bash
export RCH_CANONICAL_PROJECT_ROOT=/srv/projects
export RCH_ALIAS_PROJECT_ROOT=/p
```

Verify:

```bash
rch --json config get path_topology.canonical_root
rch --json config get path_topology.alias_root
rch config show --sources | grep -A2 path_topology
```

After changing, `rch daemon reload` (no restart needed for path topology in v1.0.18+).

### Why operators change it

- macOS workers where `/data` doesn't exist
- Multi-tenant boxes where `/srv/projects/<tenant>` is the right anchor
- Sandbox/test rigs where everything lives under `/tmp/rch-fixtures`
- Worker mirrors that already exist under a different prefix

### Topology error exit codes (visible in worker logs)

When the daemon probes a worker's topology, the probe script can exit with:

| Exit | Marker emitted | Meaning |
|---|---|---|
| 41 | `RCH_TOPOLOGY_ERR_CANONICAL_NOT_DIRECTORY` | Canonical root exists but isn't a directory |
| 42 | `RCH_TOPOLOGY_ERR_ALIAS_NOT_SYMLINK` | Alias root exists but isn't a symlink |
| 43 | `RCH_REMOTE_DEPENDENCIES_OK` not reached | A `RCH_DEP_MISSING:<path>` was emitted (sibling repo missing) |
| 0 + `RCH_TOPOLOGY_OK` | — | Healthy |

Reproduce on the worker:

```bash
ssh ubuntu@<host> 'ls -ld /data/projects && [ -L /dp ] && readlink /dp'
```

---

## Closure Planner

The planner (`rch_common::dependency_closure_planner`) runs before transfer and emits:

```
DependencyClosurePlan {
  state: Ready | FailOpen,
  entry_manifest_path,
  workspace_root,
  sync_actions: [DependencySyncAction { package_root, manifest_path, package_name, risk, metadata }],
  issues: [DependencyPlanIssue { code, message, risk, diagnostics }],
}
```

Inspect with:

```bash
rch diagnose --dry-run "cargo build --release"   # human form
rch --json diagnose --dry-run "cargo build --release" | jq '.data.dependency_closure'
```

Risk classes:

- `Low` — workspace member, in canonical root
- `Medium` — transitive path dep, in canonical root
- `High` — risky symlink hop, accepted but flagged
- `Critical` — outside canonical root or cyclic — closure becomes `FailOpen`

### Recent fixes you should know about

- **v1.0.17 (29d0d63):** Path-deps that live inside an enclosing workspace are now promoted to the workspace root for transfer. Before, you'd see redundant transfers per crate.
- **v1.0.16 (cb80c59):** Nested path dependencies promote to the enclosing Cargo workspace root.
- **v1.0.16 (61e95d1):** Dev-only path dependencies (`[dev-dependencies]`) are excluded from the runtime closure. If you depend on one for production code, declare it in `[dependencies]`.
- **v1.0.16 (877c800):** Symlink targets are accepted as valid dependency-scope candidates.
- **v1.0.16 (61e95d1):** Fail-open fallback is **narrowed to policy violations only**. A generic `cargo metadata` error no longer causes silent local fallback — it now surfaces as `RCH-E017`/`E019` and you'll see the reason explicitly.
- **v1.0.18 (24580cd):** `rch diagnose` and `rch exec` now use the configured `[path_topology]` instead of the compiled-in defaults. If you were on v1.0.17 or earlier and set custom roots, upgrade.

---

## Common Failure Patterns

### "input resolves outside canonical root"

A path entered `rch exec` (cwd, target dir, or path-dep) that isn't under the canonical root.

```bash
pwd                                   # Where am I?
rch --json config get path_topology   # What's canonical?
rch diagnose --dry-run "cargo check"  # Show normalization decisions
```

Fix: move the workspace under the canonical root, or extend `canonical_root` to a parent that contains it.

### `RCH-E014 Path dependency declared but target dir not found`

A `Cargo.toml` references `path = "../sibling"` but `../sibling` doesn't exist on the host *or* the worker.

```bash
# Show all path-deps in the entry manifest
cargo metadata --no-deps --format-version 1 | jq -r '.packages[].dependencies[] | select(.source==null) | "\(.name) -> \(.path)"'
```

Fix on the host: clone the sibling under the canonical root. Fix on the worker: same — make sure each sibling repo is checked out at the matching canonical path. Or, if the dep is only used for dev, move it to `[dev-dependencies]` so the runtime closure excludes it.

### `RCH-E016 Path dependency violates canonical-root topology`

The path-dep target *exists*, but it resolves *outside* the canonical root (often via a symlink chain).

```bash
realpath ../sibling
```

Fix: re-anchor the sibling under the canonical root, or update `canonical_root` to a common ancestor.

### `all workers failed repo convergence checks` (tag: `all_workers_failed_convergence`)

Daemon picked candidate workers but none could converge their copy of the closure repos to the required state. Check that each worker has every closure root present and writable:

```bash
ssh ubuntu@<host> "for r in /data/projects/{repo_a,repo_b,sibling}; do test -w \$r && echo OK \$r || echo FAIL \$r; done"
```

If a sibling is missing on the worker:

```bash
ssh ubuntu@<host> "git clone --depth 1 git@github.com:org/sibling.git /data/projects/sibling"
ssh ubuntu@<host> "sudo chown -R ubuntu:ubuntu /data/projects/sibling && sudo chmod 775 /data/projects/sibling"
rch workers probe <id>
```

### `Permission denied` during rsync to `/data/projects/<repo>`

The mirror was created (or modified) as `root` and the SSH user can't write to it. Recovery:

```bash
ssh ubuntu@<host> 'sudo chown -R ubuntu:ubuntu /data/projects/<repo> && sudo chmod 775 /data/projects/<repo>'
```

If you see this often, audit who's pushing changes — usually it's a `sudo git pull` somewhere.

### Symlink target not detected (pre-v1.0.16)

If you're on rch ≤ v1.0.15 and your sibling is a symlink, you'll see scope-validation failures. Upgrade the rch CLI: `rch update` (or `rch update --fleet` to also update worker binaries).

---

## Strategies

- **Co-locate.** Put every interlinked repo under the same canonical root. This is the fastest setup.
- **Workspace-first.** Prefer a top-level `[workspace]` Cargo manifest with `members = ["repo_a", "repo_b"]` over standalone crates with reciprocal `path =` deps. Workspaces are first-class.
- **Excludes.** If a sibling is huge and you only need the build artifacts of a published crate version, move it from path-dep to a normal version-pinned dep.
- **Tags.** When some workers don't have a sibling and you don't want to mirror it everywhere, tag the projects' workers (`tags = ["my-app"]`) and require that tag in the project's `.rch/config.toml`.

---

## Diagnostic Commands

```bash
rch diagnose --dry-run "cargo test --workspace"           # full pipeline preview
rch --json diagnose --dry-run "cargo test --workspace" | jq '.data.dependency_closure'
RCH_LOG_LEVEL=debug rch exec -- cargo check               # see closure decisions live
rch --json workers probe --all | jq '.data[] | {id, status, last_error}'
```

For deep debugging of the closure planner output, the `dependency_closure_plan` field is JSON-serializable (`rch_common::dependency_closure_planner::DependencyClosurePlan`).
