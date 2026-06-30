# Domain Detection

Enumerates bounded contexts / domain slices of the repo. Used in `large` mode for the top-level map and domain-selection dialog, and in `medium` mode to inform entry-point grouping.

## What it detects

A DOMAIN is a bounded context — a cohesive slice of the codebase with its own responsibility that could own its own docs. Domains are declared by the project's own structure, in whatever form that structure takes: a workspace member, a service, a crate, a feature folder, a deployable, a bounded subsystem. The concept is language- and stack-neutral; detect the unit of cohesion the repo itself asserts, not a fixed set of folder names.

## How to find it (any codebase)

Reason from the evidence the repo declares about its own structure. Manifest-declared structure outranks directory names.

1. **Workspace/multi-module manifest first.** Look for any manifest of any ecosystem that DECLARES member directories (a workspace, module list, or project list). Treat each declared member directory as a candidate domain regardless of its parent folder's name (`crates/`, `libs/`, `services-*`).
2. **Cohesive subdirectories next.** When no such manifest exists, treat any immediate subdirectory of the conventional root (per `detect-scale.md`) holding ≥ 2 content-source files (by the `detect-modules.md` method, any language; LOC > 50, excluding tests) as a candidate domain. Record `(name, relative_path, file_count, total_loc)`.
3. **Reject thin candidates.** A candidate with a single file, only config, or only a manifest is not a domain.
4. **False-positive guard.** Treat a top-level `apps/`/`packages/`/`services/`-style directory as a monorepo root that BYPASSES the utility-exclusion list ONLY when a workspace manifest confirms it holds workspaces; otherwise it may be one app's service/layer folder — apply the utility-exclusion list (per `detect-scale.md`) as normal, and do not mint false bounded contexts.
5. **Single-domain fallback.** Only when neither declared members nor cohesive subdirs yield ≥ 2 candidates, the repo is effectively single-domain.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

Workspace / multi-module manifests that declare member directories:

| Ecosystem | Manifest signal |
|---|---|
| JS/TS | `pnpm-workspace.yaml`, `package.json#workspaces`, `nx.json`, `lerna.json`, `turbo.json` |
| Rust | `Cargo.toml` → `[workspace].members` |
| Go | `go.work` |
| JVM | Maven `<modules>`, Gradle `settings.gradle` `include(...)` |
| .NET | `*.sln` project list |

Each DECLARED member is first-class — its name need not match a "domain-like" word. Common monorepo root folder names (`apps/`, `packages/`, `services/`, `crates/`, `libs/`, `modules/`) are hints, not proof: confirm with a manifest before bypassing the utility-exclusion list.

## Auto-summary per domain (one-liner for top-level map)

For each detected domain, derive a one-line description in this priority order:

1. **Domain README**: if `<domain-path>/README.md` exists, read the first heading and its immediately following paragraph. Extract ≤ 120 chars, single line, no markdown.
2. **Domain manifest signals**: if the domain has its own manifest (`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / equivalent), extract its top 3 direct dependencies. Format: `"Uses <a>, <b>, <c>."`.
3. **Shape fallback**: `"<file_count> modules (<top_language>)."` — language inferred from the dominant extension.

## Ranking (for domain-selection dialog in large mode)

Rank domains by:

```
rank_score = total_loc + 50 * file_count + 0.5 * recent_commit_weight
```

Where `recent_commit_weight` is the count of commits touching files under the domain's path in the last 90 days:

```
git log --since=90.days --name-only --pretty=format: -- <domain_path>/ \
  | grep -c -v '^$'
```

If `git` is unavailable (shallow clone, git missing) or the repo has no commit history, drop the git term and rank by `total_loc + 50 * file_count`.

## Presentation

Show the top 5 ranked domains to the user. The rest are listed in the closing message under:

> Also detected: <domain-a>, <domain-b>, … — run `/archcore:init --domain=<name>` later to drill into these.

## Domain tags

When the user selects domains in the dialog, tag the top-level map `doc` with `domain:<slug>` for each selected domain. Slug rules:

- Lowercase, alphanumeric + hyphens.
- Slashes → hyphens (`apps/billing-api` → `apps-billing-api`).
- Dots → hyphens.
- Prefix with `domain:` literal (e.g. `domain:billing`, `domain:apps-billing-api`).

These tags enable `/archcore:context` to scope queries to a specific domain.

## Output (top-level map doc, large mode)

`SKILL.md` Phase E fires the `create_document`; this catalog supplies the domain table + auto-summaries.

| Field | Value |
|---|---|
| `type` | `doc` |
| `directory` | `architecture` |
| `filename` | `top-level-map` |
| `title` | `Top-level domain map` |
| `status` | `accepted` |
| `tags` | `['top-level-map', 'architecture']` + `domain:<slug>` per selected domain |
