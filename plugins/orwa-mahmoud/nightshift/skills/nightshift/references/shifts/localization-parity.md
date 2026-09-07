# Localization parity — finite — objective key drift in an existing localization system

Missing, unused, or structurally inconsistent localization keys reported by tooling or proved by
comparison inside a localization system the repository already uses. Language judgment remains
with a human.

Supported only when the project already has locale catalogs plus an established checker, generator,
type system, or canonical source locale. If localization is absent or no source of truth can be
identified, this shift is unsupported and must not start.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Localization parity — repair objective key drift without inventing translations.**
  - Never select this entry when work mode is artifact.
  - Discovery: detect the repository's locale catalogs, canonical source locale, and configured
    localization check, generator, or typed-key command. Use those established sources to find
    missing, unused, duplicate, or structurally inconsistent keys. Dedupe against snag-log.md
    (ALL seen — fixed and rejected).
  - Fix objective structure one cluster at a time: restore a key from an existing canonical value,
    align placeholders and plural forms that tooling defines, or remove an unused key only after
    project tooling and a repository-wide reference check agree. Run the item gate, commit.
  - Park every missing translation that requires language judgment in drafting-table.md with the
    locale, source text, key, and decision needed. Do not copy machine output into the catalog.
  - Never invent or machine-generate translations, rewrite product copy, or choose regional tone.
  - Never introduce localization to a project that lacks it or add new localization tooling
    without owner approval.
  - Never delete a key based on text search alone; dynamic lookup and external consumers must be
    ruled out by the project's established tooling.
  - Ends when existing localization checks report no actionable structural drift, and every
    language-dependent gap is staged with its key and source text.
  - Verify: the item gate is green at every commit; rerun the existing localization checker or
    generator and its relevant application tests after each cluster.
```
