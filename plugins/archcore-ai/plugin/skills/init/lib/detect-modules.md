# Module Detection

Language-agnostic source-file enumeration. Used for `module_count`, hotspot ranking, and test-LOC companion lookup.

## What it detects

A module is a source file that carries the project's own logic — as opposed to config, data, markup, docs, generated, or vendored files. The "source language" is whatever the repo is actually written in (a niche, DSL, or in-house language counts just as much as a popular one), not only the extensions listed below. The aim is to count the files a human author would call "the code" — and attribute each one's companion test LOC — for ANY stack: web, ML, embedded, games, data/IaC, mobile.

## How to find it (any codebase)

1. Establish the dominant code-bearing extension(s) from EVIDENCE: read the manifest/build system (language field, source globs, compiler/toolchain config) and run a file census of the tree after excluding vendored/generated/build trees. The extension(s) carrying the most non-excluded files that the build actually compiles or runs are the source language(s) — even if they are absent from the table below.
2. Build the exclusion set BY ROLE, not by a fixed name list: drop dependency/vendor trees, build/output trees, and generated files (generated-by headers, codegen/protobuf suffixes, minified bundles). If `git` is available, also exclude anything `git check-ignore -q <file>` matches, to catch build artifacts left in the working tree.
3. Count each source-extension file whose LOC (via `wc -l < <file>`; do not subtract blank or comment lines) clears the threshold. Classify tests BY ROLE — a sibling or path whose name embeds `test`/`spec`, a conventional test root — not by a fixed basename, and exclude them from `module_count`.
4. For each counted module, attribute companion test LOC by PROXIMITY/path (same directory, or the mirrored test root), never basename alone — so test LOC is not mis-credited across same-named modules in different domains. Sum LOC of matches; 0 if none.
5. Guard false positives: do NOT drop real product code because a path segment is literally named `spec`/`build`/`test`, because it is an A/B-test module, or because it lives under a dotted directory that is nonetheless source. Return `module_count = 0` only when the source root genuinely holds no code.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Instruction-modules exception (prompt/markdown tooling)

Markdown is markup, NOT a module — **except** when the repo's *product itself is
instruction/prompt content*: an agent / LLM plugin or markdown-tooling repo whose
deliverable is skills, commands, agents, or prompts written in Markdown. The signal
is narrow and must be POSITIVE on all three: (a) a plugin/agent manifest or a
conventional layout (`**/skills/*/SKILL.md`, `**/commands/*.md`, `**/agents/*.md`,
a `marketplace.json`/`plugin.json`); (b) those instruction files carry real,
load-bearing content (frontmatter + substantial body, not stubs); AND (c) there is
**little or no traditional source** that would otherwise dominate the count.

When all three hold, treat each substantial instruction file as a source module
(its body LOC is its size; its companion "tests" are usually absent, so such repos
lean on the hotspot fallback tier). Outside this case — a normal repo with a `docs/`
tree, a README-heavy library, a code project that merely contains some Markdown —
Markdown stays markup and is excluded, so ordinary `module_count` is unaffected.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

Common source-file extensions (JSON/YAML/TOML/Markdown are data/markup, not modules):

| Language | Extensions |
|---|---|
| TS / JS | `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` |
| Python | `.py` |
| Go / Rust | `.go` / `.rs` |
| Java / Kotlin | `.java` / `.kt`, `.kts` |
| C# / Swift / Scala | `.cs` / `.swift` / `.scala` |
| Ruby / PHP / Elixir | `.rb` / `.php` / `.ex`, `.exs` |

Common test-role patterns (match by role, not these literal names):

| Language | Test patterns |
|---|---|
| TS / JS | `*.test.*`, `*.spec.*`, `**/__tests__/**` |
| Python | `test_*.py`, `*_test.py`, `**/tests/**` |
| Go | `*_test.go` |
| Java / Kotlin | `*Test.*`, `*Tests.*`, `*Spec.kt`, `**/src/test/**` |
| Ruby / PHP / C# | `*_spec.rb`, `*_test.rb`, `*Test.php`, `*Tests.cs`, `**/spec/**`, `**/tests/**` |

(Rust unit tests live in `#[cfg(test)]` blocks — not detectable without parsing; accept the undercount.)

Always-exclude trees and generated suffixes:

- Vendor/deps: `node_modules/`, `vendor/`, `.venv/`, `venv/`, `.pnpm/`
- Build/output: `dist/`, `build/`, `out/`, `target/`, `.next/`, `.nuxt/`, `.svelte-kit/`, `coverage/`
- Generated: `generated/`, `__generated__/`, `*.pb.{go,ts,js}`, `*.generated.*`, `*.g.{ts,go,dart}`, `*.min.{js,css}`
- Any dotted path segment except the repo root itself (`.git/`, `.cache/`, `.turbo/`)

Companion-test proximity examples (attribute by path, not basename alone):

| Source | Companion candidates |
|---|---|
| `src/foo.ts` | `src/foo.test.ts`, `src/__tests__/foo.test.ts`, `tests/foo.test.ts` |
| `src/foo.py` | `tests/test_foo.py`, `tests/foo_test.py` |
| `foo.go` | `foo_test.go` (same package dir) |
| `src/Foo.java` / `.kt` | `src/test/**/FooTest.java`, `src/test/**/FooSpec.kt` |
| `src/foo.rb` | `spec/foo_spec.rb`, `test/foo_test.rb` |
