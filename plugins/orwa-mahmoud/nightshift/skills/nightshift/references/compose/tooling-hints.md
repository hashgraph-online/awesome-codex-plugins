# Tooling hints

Names, not instructions. When a shift needs a capability the project does not already provide, this
page says which tools are commonly used for it so the model has somewhere to start. It pins no
version, ships no command, and grants no permission.

**A hint is not authority.** The owner's tooling policy decides whether anything may be added at
all. Prefer what the tree already configures; a tool the project chose beats a tool named here. If
the policy forbids additions, or the capability cannot be satisfied from the tree, the shift reports
that capability `unavailable` and continues — never "passed", never a silent install.

When something is added, the seatbelt in [`provisioning-engine.md`](provisioning-engine.md) captures
the write surface first so the change can be undone.

## By ecosystem

| Capability | JavaScript / TypeScript | Python | Go | Rust |
| --- | --- | --- | --- | --- |
| Lint | ESLint, Biome, oxlint | Ruff, Flake8, Pylint | `go vet`, golangci-lint | Clippy |
| Types | `tsc` | mypy, Pyright | `go build` | `cargo check` |
| Tests | Vitest, Jest, node:test | pytest, unittest | `go test` | `cargo test` |
| Coverage | the test runner's own reporter, c8 | Coverage.py, `pytest-cov` | `go test -cover` | cargo-llvm-cov |
| Dependency advisories | the package manager's audit | pip-audit | govulncheck | cargo-audit |
| Outdated dependencies | the package manager's outdated report | the resolver's outdated report | `go list -m -u all` | cargo-outdated |
| Dead code | Knip, ts-prune | Vulture | `go vet`, staticcheck | `cargo check` warnings |

Other stacks follow the same shape: the language's own toolchain first, then whatever the build
system already invokes. A `Makefile`, `justfile`, `Taskfile`, or CI workflow usually names the real
commands — read it before proposing anything.

## By subject

- **Accessibility** — axe-core and its framework bindings, Pa11y, Lighthouse. Automation finds
  objective violations only; keyboard, focus, and journey surfaces stay with a human, and no tool
  here certifies WCAG compliance.
- **Localization** — the catalog format's own validator (i18next, FormatJS, gettext, Fluent). Key
  parity and placeholder shape are checkable; translation quality is not.
- **API contracts** — the schema's own tooling: OpenAPI diff and validators, GraphQL schema checks,
  `protoc` and Buf, consumer-contract test runners.
- **Structured data and docs** — link checkers such as Lychee, markdown linters, the site
  generator's own build. A generated site whose source lives elsewhere is out of scope.
- **Performance** — the repository's existing benchmark harness first. Lighthouse, k6, and language
  benchmark runners only where the owner already tracks a baseline; a single run is never evidence.
- **Shell and plugin repositories** — bats for tests, ShellCheck for lint, the host's own plugin
  validator.

## What this page never becomes

No version pins, no install commands, no per-tool configuration, no ranking of vendors. A catalog of
recipes is a marketplace to maintain, and a stale pin is worse than no hint at all. If a shift needs
a tool badly enough to name a version, that decision belongs to the owner.
