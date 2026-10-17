---
name: go-cli-distribution
description: Prepare reproducible Go CLI artifacts across operating systems and architectures with toolchain-derived target matrices, capability profiles, portable config and cache discovery, CGO decisions, version metadata, artifact handoff, smoke tests, archives, checksums, containers, and versioned source installation. Use when cross-compiling, packaging binaries, defining the distribution contract, or reviewing portability before release automation.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.4.0"
  displayName: Go CLI Distribution
  category: Go
  tags: go,golang,cli,distribution,cross-compilation,release,cgo
---

# Go CLI Distribution

Treat compilation as the start of release verification, not the finish. Declare
the matrix, record every build input, and execute the final artifacts.

## Core Workflow

1. Derive supported `GOOS/GOARCH` targets from the pinned toolchain and dependencies.
2. Verify platform files and modern `//go:build` capability constraints.
3. Pin toolchain, modules, tags, CGO mode, linker flags, and source revision.
4. Build deterministic target-specific artifacts with deliberate version metadata.
5. Execute each artifact and test help, version, commands, streams, status, and signals.
6. Package immutable archives, then generate and verify integrity metadata.
7. Verify container and versioned `go install` paths when those are supported.

## Read Next

| Task | Load |
|---|---|
| Prepare a complete multi-platform release | `guidelines.md`, `workflows/prepare-cross-platform-release.md` |
| Apply build, verification, container, and install rules | `references/distribution/rules.md` |
| Implement constraints or build commands | `references/distribution/examples.md` |
| Use cross-build, CGO, metadata, or container patterns | `references/distribution/patterns.md` |
| Review release readiness | `references/distribution/checklist.md` |
| Understand portability and artifact tradeoffs | `references/distribution/knowledge.md` |

## Guardrails

- Use `//go:build`; do not introduce legacy-only `// +build` constraints.
- Do not assume `CGO_ENABLED=0` proves a self-contained artifact.
- Cross-compilation alone does not establish runtime support.
- Generate checksums only after final packaging and verify them after upload.
- Use platform config and cache directory APIs; do not assume Unix home layouts.
- Treat build tags as capability selection, never authentication or authorization.
- Define and snapshot-test the artifact contract before release. The protected
  tagged release job builds final bytes once; downstream channels must not rebuild them.
- Recommend `go install module/cmd/tool@version`, not `go get`, for executable installation.

## Source Notes

Guidance is transformed and paraphrased from Ricardo Gerardi,
*Powerful Command-Line Applications in Go* (Pragmatic Bookshelf, 2021),
especially Chapter 11. Examples are original adaptations.

Book: https://pragprog.com/titles/rggo/powerful-command-line-applications-in-go/

The source's Go 1.15-era build and install details are historical. Verify
current behavior against https://go.dev/doc/go-get-install-deprecation and the
current Go build documentation.

Portable directory, profile-matrix, and artifact-handoff guidance also
incorporates transformed material from Marian Montagnino, *Building Modern CLI
Applications in Go* (Packt, 2023), especially Chapters 7 and 12-14.

Embedded-schema and SQL-driver packaging guidance also incorporates transformed
material from Inanc Gumus, *Go by Example: Programmer's Guide to Idiomatic and
Testable Programs* (Manning, 2025), Chapter 10.
