# Rule File Splitting

**Purpose**: Keep a governing `AGENTS.md` lean by moving same-scope detail into an adjacent `rules/` directory without hiding instructions that must always load.

## 1. When to Split

Use this rule when an existing or drafted `AGENTS.md` is becoming hard to scan, consumes too much of the combined instruction budget, or contains detailed procedures that apply only to some tasks.

Apply these decisions in order:

1. Delete generic, discoverable, stale, duplicated, or non-load-bearing text.
2. Move genuine subtree differences to the closest justified nested `AGENTS.md`.
3. Keep always-needed scope, authority, commands, safety gates, and stop conditions in the governing `AGENTS.md`.
4. Move only same-scope, conditionally needed detail to `rules/*.md` beside that `AGENTS.md`.

A `rules/` split is progressive disclosure, not a way to preserve everything that failed the admission test.

## 2. Placement and Shape

For a root instruction file:

```text
repository/
├── AGENTS.md
├── AGENTS.ko.md
└── rules/
    ├── architecture.md
    ├── architecture.ko.md
    ├── testing.md
    └── testing.ko.md
```

For a nested instruction file, place its support rules beside it in that subtree only when the rules govern the same subtree. Reuse an existing adjacent `rules/` directory only when it already holds instruction documentation and the new names cannot collide. Do not mix agent-policy Markdown into a directory used for product code, generated files, or another established purpose; use the repository's existing instruction-doc location instead and link it directly.

Use descriptive kebab-case names based on the decision surface, such as `architecture-boundaries.md`, `testing.md`, or `release-safety.md`. Do not create catch-all files such as `misc.md`.

## 3. Loading Contract

Arbitrary `rules/*.md` files are not assumed to be runtime-discovered or automatically imported. The governing `AGENTS.md` must link every support file directly and state exactly when to read it.

Good:

```markdown
## Conditional rules

- Read `rules/testing.md` before changing test infrastructure or test commands.
- Read `rules/architecture-boundaries.md` before moving code across package boundaries.
```

Each entry is one Markdown link to the support file plus the condition that triggers reading it. The paths above are example paths inside a target repository, so they appear here as code spans instead of links that would not resolve from this package.

Do not use vague cues such as “see `rules/`.” Do not use runtime-specific import syntax in shared `AGENTS.md` unless the target runtime and syntax were explicitly verified. A plain Markdown link plus a read condition is the portable default.

Because linked files are conditional context, never move essential scope, authority, safety, required commands, or completion gates out of `AGENTS.md`. The core must remain safe and actionable when no support rule has been opened yet.

## 4. Canonical Ownership

Each rule has one canonical home:

| Content | Home |
|---|---|
| Always-needed repository contract | Governing `AGENTS.md` |
| Subtree-specific delta | Closest justified nested `AGENTS.md` |
| Same-scope detailed policy or procedure used only for matching tasks | Adjacent `rules/*.md` |
| Detailed architecture or API knowledge already maintained elsewhere | Existing project documentation, linked directly |
| Deterministic enforcement | Hook, CI, lint rule, schema, or executable configuration |

Do not summarize a support rule back into the core beyond the minimum routing cue. Do not create support files that merely repeat root or nested instructions.

## 5. Language Pairing

Write agent-loaded rule files in the same language as the governing `AGENTS.md`. When the root `AGENTS.md` uses this skill's default English-plus-Korean-mirror contract, pair each created or materially changed `rules/name.md` with `rules/name.ko.md`. Links in `AGENTS.md` point to the English files; links in `AGENTS.ko.md` point to the Korean mirrors.

A nested rule mirror follows the same policy selected for its governing nested `AGENTS.md`. Preserve commands, paths, identifiers, and modal strength across translations.

## 6. Validation Gate

- [ ] Deletion and nested placement were considered before creating support rules.
- [ ] The `rules/` directory is adjacent to the governing `AGENTS.md` or an existing documented instruction location is used instead.
- [ ] Every support file has one responsibility, a direct link, and an explicit read condition.
- [ ] No essential always-loaded contract moved out of `AGENTS.md`.
- [ ] No support rule duplicates root, nested, or existing project documentation.
- [ ] Existing non-documentation `rules/` content was not overwritten or mixed with agent policy.
- [ ] English/Korean links resolve to semantically aligned files when mirrors are required.
- [ ] Root plus applicable nested instruction files still leave headroom under the configured runtime budget.

## Sources

> Links checked 2026-09-21. No external source was used in this file.

| Claim | Source |
|---|---|
| The split, placement, loading, ownership, and language rules in this file | the repository skill-authoring standard under `instructions/skill/` and this package's `SKILL.md`; no vendor or web source is cited |
