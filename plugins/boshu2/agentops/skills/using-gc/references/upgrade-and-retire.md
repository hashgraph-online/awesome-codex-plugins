# Setup, upgrade and retirement

Operator actions taken outside any run. Install the `gascity` pack itself with
the skill's `gc` binding and pins, not the command a registry prints.

## Registries

The built-in `main` registry catalogs official packs; the community registry is
optional configuration.

```sh
gc pack registry refresh
gc pack registry search --all
gc pack registry show main:<pack>
gc pack registry add community https://registry.gascity.com/registry.toml
gc pack registry search --registry community --all
```

`search` reads the local registry cache, so refresh first. `show` reports
release provenance and an import command whose binding is the pack name
(`--name <pack>`); the binding qualifies that pack's agent and skill names.
`gc import add` declares a source and version, and `gc import install` resolves
it into `packs.lock`. Prefer an exact accepted release for reproducible cities.

## Upgrade an existing city to 1.5.x

First upgrade bd to the release the new gc pins (bd v1.3.2 for gc v1.5.1).
Then restart the supervisor on the new binary before repairing any city:

```sh
gc supervisor stop --wait   # stops every city this supervisor hosts
gc start
gc doctor --fix             # once per city
```

Then confirm:

- `gc version` reports a 1.5.x release (v1.5.1 was current on 2026-10-25) or
  the intended `edge` build, from the intended path, and `bd version` reports
  the bd that release pins;
- `gc doctor` has no blocking failures;
- each graph-owning rig has an unsuspended `core.control-dispatcher`;
- imports and `packs.lock` resolve;
- `ao gc check` accepts the contained maintainer runtime and AgentOps skill
  links;
- on macOS, the supervisor LaunchAgent resolves to the same executable as the
  selected `gc` binary.

A stale registered city may block every start. Repair that city with
`gc doctor --fix`, or explicitly unregister it if it is intentionally retired.

## Retire a city

Retire an old HQ or canary by exact registered name or path, without stopping
the machine-wide supervisor its replacement needs:

```sh
gc cities --json
gc stop /path/to/old-city --timeout 45s
gc unregister /path/to/old-city
gc cities --json
```

On Gas City 1.5.x, `gc stop` of a supervisor-registered city also unregisters
it, so drop the separate `gc unregister` line there; keep it only on builds
whose `gc stop --help` does not say so. `unregister` fails rather than silently
accepting an unknown target. If `gc stop` exits 1 with `stop not confirmed`, its
registration is restored; resolve the named error and stop again. Preserve the
city directory until its Beads state is backed up or confirmed disposable.
Create the replacement from the upstream Gas City template, install its pinned
imports, and verify it with `gc cities --json`, `gc --city <new-city> status`,
and `gc --city <new-city> doctor --json`.
