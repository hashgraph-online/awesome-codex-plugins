# Go CLI Distribution Patterns

Reusable structures for multi-platform implementation and releases.

## Pattern: Stable Contract, Platform Files

### Intent

Expose one package contract while compiling a different implementation for each
supported operating system.

### Structure

```text
notify/
  notify.go
  sender_linux.go
  sender_darwin.go
  sender_windows.go
  sender_unsupported.go
```

Each selected file defines the same unexported type or function. Use filename
suffixes for OS/architecture selection and `//go:build` only when the condition
is more expressive.

### Verification

```sh
GOOS=linux go list -f '{{.GoFiles}}' ./notify
GOOS=windows go list -f '{{.GoFiles}}' ./notify
```

Compile and run tests for every supported implementation. Add compile-failure
or explicit-error behavior for unsupported targets.

**Go 1.26 check:** validate supported suffixes and build-constraint syntax using
the current `go/build` documentation.

## Pattern: Capability Pair

### Intent

Offer a feature in one profile and a compatible no-op or alternative in another.

### Structure

```text
feature_enabled.go   //go:build feature
feature_disabled.go  //go:build !feature
```

The pair must export the same internal behavior to callers. Prefer positive,
domain-specific tags and keep the number of independent tags small; combinations
grow exponentially.

### Verification

- Inspect selected files with `go list`.
- Test both sides of each pair.
- Test supported combinations, especially mutually interacting tags.
- Reject impossible or unsupported combinations in CI.

## Pattern: Curated Build Matrix

### Intent

Produce only the artifacts the project commits to supporting.

### Structure

```yaml
include:
  - { goos: linux,   goarch: amd64, cgo: "0" }
  - { goos: linux,   goarch: arm64, cgo: "0" }
  - { goos: darwin,  goarch: arm64, cgo: "0" }
  - { goos: windows, goarch: amd64, cgo: "0" }
```

For each row:

1. Build from the same clean revision and pinned toolchain.
2. Apply explicit tags, CGO mode, metadata, and output naming.
3. Package the artifact in a platform-appropriate archive.
4. Execute target-aware smoke tests.
5. Generate checksums after packaging.

**Go 1.26 check:** generate candidates with `go tool dist list`, then filter by
dependency and product support. Do not copy the book’s 2021 exclusions.

## Pattern: Native Boundary Lane

### Intent

Isolate targets that require CGO or native libraries instead of weakening the
pure-Go release path.

### Structure

```text
release-pure:
  CGO_ENABLED=0
  broad curated matrix

release-native:
  CGO_ENABLED=1
  target C toolchain and libraries
  narrower matrix
  native runtime tests
```

Document whether artifacts are static or dynamically linked and which target
libraries are required. Containerize only when that improves the user’s actual
deployment model.

**Go 1.26 check:** verify the dependency’s current cross-build instructions and
the target compiler/sysroot; the book’s SQLite/MinGW command is historical.

## Pattern: Hermetic Multistage Container

### Intent

Build and package the CLI in one declared pipeline while keeping build tools out
of the runtime image.

### Structure

```text
Pinned builder image
  -> download locked modules
  -> copy source
  -> build explicit Linux target
  -> smoke/inspect binary
Pinned minimal runtime image
  -> copy binary and required data only
  -> set non-root identity
  -> exec-form entrypoint
```

Use `scratch` only for a proven self-contained runtime. Otherwise add precisely
the CA roots, timezone data, user records, or native libraries the CLI needs.

**Current-tooling check:** verify image digests, BuildKit/Podman features,
multi-architecture flags, and current hardening guidance before implementation.

## Pattern: Dual Distribution

### Intent

Serve users who want immediate binaries and users who prefer toolchain-native
source installation.

### Structure

- Versioned archives per supported target
- Checksums and optional signatures/provenance
- Container image only when the CLI has a credible container use case
- Versioned module source install:
  `go install module/path/cmd/tool@vX.Y.Z`
- Build prerequisites and tags documented at the release tag

**Historical warning:** do not use `go get` as the executable installation
instruction. Verify current Go 1.26 source-install behavior.

## Pattern Selection Guide

| Situation | Pattern |
|---|---|
| OS APIs or commands differ | Stable Contract, Platform Files |
| Optional storage or integration | Capability Pair |
| Multiple binary targets | Curated Build Matrix |
| SQLite or another C dependency | Native Boundary Lane |
| Container is a real deployment target | Hermetic Multistage Container |
| Public CLI with varied consumers | Dual Distribution |

## Source Traceability

Derived and paraphrased from Chapter 11 of *Powerful Command-Line Applications
in Go*:

- OS-specific files — normalized lines 24442–24644
- Conditional build profiles and `go list` — lines 24972–25212
- Cross-compilation and native dependencies — lines 25213–25389
- Container packaging — lines 25390–25638
- Binary and source choices — lines 25639–25662

The matrix, integrity, hardening, and Go 1.26 notes are modern synthesis and
require current official-source verification.
