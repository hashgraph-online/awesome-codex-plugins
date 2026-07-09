# Release Notes Generation

Release notes are **not the changelog**. `CHANGELOG.md` is comprehensive and
developer-facing. `docs/releases/YYYY-MM-DD-v<version>-notes.md` is the public
GitHub Release body: scannable, product-area-first, and curated for users who
want to know whether a release touches the part of AgentOps they care about.

## Scope rule (read this first)

**The notes cover the git range since the previous release — `git log <prev-tag>..HEAD` — not the single `## [version]` CHANGELOG stanza.** This is the rule that prevents under-scoped notes. For a major, the previous release is the last minor/patch, so the range *is the entire major* (every product area the major touched). Derive scope from `git diff --name-only <prev-tag>..HEAD`, never from one changelog entry.

Don't hand-mine from scratch — run `scripts/scaffold-release-notes.sh v<version> --since <prev-tag>` to emit a tier-correct draft (one `### ` per touched area, seeded with that area's commit subjects), then curate. `scripts/validate-release-notes.sh v<version> --since <prev-tag>` enforces both the shape and **coverage** (every area the range touched must appear), and runs as a hard gate in `release.yml`.

## Release tiers

The version determines the tier and the shape:

| Tier | Version | Scope (git range) | `## Breaking Changes` |
|---|---|---|---|
| **major** | `X.0.0` | last release → HEAD (the whole major) | **required** |
| **minor** | `X.Y.0` | last minor/patch → HEAD | only if actually breaking |
| **hotfix** | `X.Y.Z` (Z>0) | last patch → HEAD (narrow) | only if actually breaking |

All tiers use the same required section skeleton below; only `## Breaking Changes` (required for majors) and the breadth of `## Product Areas` differ. A hotfix typically has one or two areas; a major has many.

## Audience

Write for people scrolling a GitHub release page, not for contributors reading
commit history. They need fast answers:

- Did install or upgrade behavior change?
- Did the CLI command I use change?
- Did daemon, hooks, skills, Codex, eval, or security behavior change?
- Is there anything I must do after upgrading?

## Required Structure

Use this shape for every curated release-note file:

```markdown
## Highlights

<2-4 sentences: the release theme, why it matters, and the one or two biggest
user/operator outcomes. Explain internal names the first time they appear.>

## Upgrade Notes

- <Required operator action, migration note, deprecation, or "No manual action
  required" when that is genuinely useful. Omit only when the release has no
  upgrade implications.>
- <Major releases: link the migration guide here, e.g. `See docs/MIGRATION-X.0.md`.>

## Breaking Changes

<!-- MAJOR releases (X.0.0) ONLY — required for them, omit entirely otherwise. -->

- <Each breaking change as one bullet: what changed, what to use instead, and a
  migration pointer. Surfacing breaking changes at the top is the whole point of
  a major; do not bury them under a product-area `Removed:` bullet.>

## At a Glance

| Product Area | Added | Changed | Refactored | Fixed | Deprecated/Removed |
|---|---:|---:|---:|---:|---:|
| <Touched area> | N | N | N | N | N |

## Product Areas

### <Touched Product Area>

- Added: <user/operator impact>
- Changed: <user/operator impact>
- Refactored: <why this refactor matters for users, operators, or contributors>
- Fixed: <bug or reliability issue fixed>
- Deprecated: <what changed and what to use instead>
- Removed: <what was removed and why>
- Security: <security, privacy, or supply-chain impact>
- Docs: <new docs users should know about>

## Known Issues

- <Known release risk, limitation, or "No release-blocking known issues.">

[Full changelog](../CHANGELOG.md)
```

## Major Releases (X.0.0)

A major release adds one section to the shape above and tightens one rule:

- **`## Breaking Changes` is required** (placed after `## Upgrade Notes`, before
  `## At a Glance`). Every removed/renamed/behavior-breaking change gets a bullet
  with its replacement and a migration pointer. This is in addition to — not a
  replacement for — the per-area `Removed:` / `Deprecated:` bullets in
  `## Product Areas`.
- **`## Upgrade Notes` must link the migration guide** (`docs/MIGRATION-X.0.md`).
- Highlights may run to the upper end of the 2-4 sentence range to frame the
  release theme.

Minor and patch releases omit `## Breaking Changes` entirely.

## Product-Area Taxonomy

Only show areas touched by the release. Keep this canonical order:

1. Install, Upgrade, and Distribution
2. CLI and Operator Commands
3. Daemon, Scheduling, and Factory
4. Skills and Workflows
5. Codex and Runtime Integrations
6. Hooks and Lifecycle
7. Knowledge Flywheel, Search, and Memory
8. Eval, Validation, and Release Gates
9. Docs and Onboarding
10. Security, Privacy, and Supply Chain
11. Contributor/Internal Refactors

Do not include empty sections. Small patch releases may have only one or two
product areas.

## Action Labels

Use stable action labels inside each product-area section:

| Label | Use when |
|---|---|
| `Added:` | A new user/operator capability exists. |
| `Changed:` | Existing behavior or defaults changed. |
| `Refactored:` | Internals changed in a way that affects reliability, maintainability, performance, migration path, or contributor workflow. |
| `Fixed:` | A bug, drift, flake, or regression was corrected. |
| `Deprecated:` | A supported path remains available but is no longer preferred. Include the replacement. |
| `Removed:` | A supported path or artifact is gone. Include the reason and replacement when one exists. |
| `Security:` | Security, privacy, provenance, or supply-chain posture changed. |
| `Docs:` | New or substantially changed docs help users operate a touched area. |

Prefer one sentence per bullet. Keep file paths, issue IDs, and commit hashes in
the changelog unless they are the only clear way to name a public artifact.

## Coverage Workflow

Before writing prose, inventory the release range:

```bash
git diff --name-only <previous-tag>..HEAD
git log --oneline --no-merges <previous-tag>..HEAD
git diff --stat <previous-tag>..HEAD
```

Map touched paths to product areas:

| Paths / signals | Product area |
|---|---|
| `scripts/install*`, `.goreleaser.yml`, `.github/workflows/release.yml`, installer docs, Homebrew notes | Install, Upgrade, and Distribution |
| `cli/cmd/ao/**`, `cli/docs/COMMANDS.md`, command tests | CLI and Operator Commands |
| `cli/internal/daemon/**`, `cli/internal/schedule/**`, `cli/internal/agentworker/**`, `cli/internal/gascity/**`, daemon docs/contracts | Daemon, Scheduling, and Factory |
| `skills/**`, `skills-codex/**`, `skills-codex-overrides/**` | Skills and Workflows |
| `.codex-plugin/**`, `scripts/install-codex*`, `scripts/validate-codex*`, Codex docs/tests | Codex and Runtime Integrations |
| `hooks/**`, `cli/embedded/hooks/**`, `lib/hook-helpers.sh`, hook tests | Hooks and Lifecycle |
| `.agents` policy, `cli/internal/{knowledge,harvest,pool,lifecycle,search}/**`, Dream/flywheel docs | Knowledge Flywheel, Search, and Memory |
| `cli/internal/eval/**`, `evals/**`, `tests/canaries/**`, validation/release scripts, CI workflows | Eval, Validation, and Release Gates |
| `README.md`, `docs/**`, `PRODUCT.md`, onboarding/runbook docs | Docs and Onboarding |
| security scripts, SBOM/provenance, scanner config, secret/path/auth hardening | Security, Privacy, and Supply Chain |
| broad test splits, package extractions, generated artifact sync, internal-only cleanup | Contributor/Internal Refactors |

Every product area touched by meaningful code, scripts, workflows, skill
behavior, install paths, security posture, or operator docs must appear in the
release notes, or be explicitly folded into a broader touched area. Trivial
typos and generated-only churn may be omitted.

## Quality Bar

- The release theme is obvious from `## Highlights`.
- `## Upgrade Notes` names required action or intentionally says there is none
  when the release could look scary.
- Touched areas are visible by scrolling section headings.
- Major refactors are not hidden under generic `Changed` bullets.
- Internal names are explained or omitted.
- The notes do not copy-paste the changelog.
- The full changelog link remains available for archaeology.

## Condensing Rules

- Collapse related commits into one product-area bullet.
- Use `Refactored:` for architecture work that affects reliability, migration,
  contributor workflow, or future product capacity.
- Use `Contributor/Internal Refactors` for internal-only work that still matters
  to contributors.
- Keep counts in `At a Glance` approximate but honest; they are scan aids, not
  audit evidence.
- Omit sections with no real release impact.

## Example

```markdown
## Highlights

AgentOps v2.40.0 makes daemon-backed Dream runs easier to operate and safer to
debug. The release also tightens Codex plugin validation and fixes two release
gate flakes that could block otherwise good tags.

## Upgrade Notes

- No manual migration is required.
- Codex users should refresh the native plugin and restart Codex.

## At a Glance

| Product Area | Added | Changed | Refactored | Fixed | Deprecated/Removed |
|---|---:|---:|---:|---:|---:|
| Daemon, Scheduling, and Factory | 2 | 1 | 1 | 3 | 0 |
| Codex and Runtime Integrations | 0 | 1 | 0 | 2 | 0 |
| Eval, Validation, and Release Gates | 1 | 1 | 0 | 2 | 0 |

## Product Areas

### Daemon, Scheduling, and Factory

- Added: daemon Dream runs now write terminal summaries operators can surface
  without reading raw runtime files.
- Refactored: queue projection rebuilds now share the same replay path used by
  status checks, reducing drift between CLI and daemon views.
- Fixed: daemon runs no longer claim success from stale projections after a
  worker timeout.

### Codex and Runtime Integrations

- Changed: the Codex native plugin installer now validates hook layout before
  updating the plugin cache.
- Fixed: Codex runtime section checks now catch missing prompt metadata before
  release.

### Eval, Validation, and Release Gates

- Added: release notes coverage checks now warn when touched product areas are
  missing from curated notes.
- Fixed: the local release gate no longer fails when advisory eval baselines are
  absent in a fresh clone.

## Known Issues

- No release-blocking known issues.

[Full changelog](../CHANGELOG.md)
```

## File And CI Contract

Always write curated notes to:

```bash
docs/releases/YYYY-MM-DD-v<version>-notes.md
```

This file must be committed before tagging. The CI release pipeline reads it
from the tagged tree through `scripts/extract-release-notes.sh`, prepends the
install/checksum/provenance header, and appends the full changelog details.

**Enforced, not optional.** `scripts/validate-release-notes.sh <version>` checks
that the curated file exists and conforms to this standard (required sections,
canonical product-area taxonomy, action labels, and `## Breaking Changes` for
majors). It runs as a hard gate in the `publish` job of
`.github/workflows/release.yml` **before** notes are extracted, and
`extract-release-notes.sh` itself now **fails** rather than falling back to the
raw CHANGELOG when the curated file is missing. A release cannot publish with a
missing or non-conforming notes file. (Root cause: 3.0.0/3.0.1 shipped raw
CHANGELOG dumps because the generator used to fall back silently.)
