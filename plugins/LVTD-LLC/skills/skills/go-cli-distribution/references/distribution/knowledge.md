# Go CLI Distribution Knowledge

Core concepts for selecting platform code, building portable binaries, packaging
containers, and publishing Go command-line tools.

## Distribution Starts With a Support Contract

A Go executable targets one operating-system and architecture pair. Define the
supported `GOOS/GOARCH` matrix before designing build jobs or release assets.
The toolchain can report its current target set:

```sh
go tool dist list
```

This is a capability list, not a promise that every dependency, feature, or test
works on every listed target. Native libraries, external commands, terminals,
filesystems, and OS APIs can narrow the real support matrix.

**Go 1.26 verification point:** regenerate the target list with the exact release
toolchain; do not preserve a target matrix copied from the 2021 book.

## Build-Time and Run-Time Selection

Use `runtime.GOOS` when only small data values differ at run time. Use separate
files when implementations, imports, system calls, or external programs differ.

Go selects platform files by filename suffix:

- `feature_linux.go`
- `feature_darwin.go`
- `feature_windows.go`
- `feature_linux_arm64.go`

Each selected file can implement the same package-level contract. This keeps
unsupported imports out of other builds and avoids large platform switches.

Build constraints select variants for capabilities or release profiles that
filenames cannot express, such as `integration`, `sqlite`, or `minimal`.

```go
//go:build sqlite && !minimal

package store
```

**Historical note:** Chapter 11 uses legacy `// +build` lines. New work should
use `//go:build`; verify exact syntax and compatibility requirements against the
Go 1.26 `go/build` documentation.

## Verify the Selected Build

Build tags create multiple programs from one source tree. Inspect the source
files selected for every important profile:

```sh
go list -tags=minimal -f '{{.ImportPath}} {{.GoFiles}} {{.CgoFiles}}' ./...
```

Then compile and test that profile. `go list` proves selection, not behavior.
Tests run on the host platform unless a target runner or emulator executes the
artifact.

## Cross-Compilation

`GOOS` and `GOARCH` control the target:

```sh
CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -o dist/tool-linux-arm64 ./cmd/tool
```

Pure-Go dependencies usually cross-compile directly. CGO changes the problem:
the build needs a C toolchain and native dependencies for the target platform.
The resulting binary may still require target shared libraries.

`CGO_ENABLED=0` disables CGO; it does not universally guarantee that every
binary is fully static or that behavior is identical. DNS, user lookup,
certificates, plugins, and native-backed libraries deserve explicit checks.

**Go 1.26 verification point:** test the actual link mode and runtime behavior
for each artifact. Treat the book’s MinGW/SQLite recipe as a historical example,
not a current universal command.

## Reproducible Release Inputs

Repeatable builds require more than a script:

- Pin the Go toolchain and module inputs.
- Build from a clean, identified commit.
- Keep target, tags, CGO mode, and linker flags explicit.
- Normalize version metadata and output names.
- Avoid mutable container tags such as `latest` as build inputs.
- Record checksums and provenance for published artifacts.

Reproducible means the same declared inputs produce equivalent output.
Integrity means consumers can verify the artifact they downloaded. Both should
be designed into the release process.

## Container Distribution

A multistage container build compiles in a builder image and copies only runtime
material into a smaller final image. A `scratch` image can hold a truly
self-contained binary, but it contains no shell, CA certificates, timezone
database, passwd data, or diagnostic utilities.

Choose the final image from runtime needs:

| Runtime need | Likely final image |
|---|---|
| Self-contained computation only | `scratch` |
| Certificates or basic OS data | Minimal/distroless image with required data |
| Shell or package-managed runtime dependencies | Small distribution image |

Run as a non-root user where the base supports it, use an exec-form entrypoint,
and test signals, terminal behavior, writable paths, and read-only operation.

**Current-tooling verification point:** the book’s Go 1.15 images,
`alpine:latest`, Docker/Podman commands, and size/security claims are historical.
Pin current images by immutable digest and verify current runtime behavior and
security guidance before release.

## Binary and Source Distribution

Binary releases minimize consumer setup but require one artifact per supported
target. Source releases maximize flexibility but shift toolchain, dependency,
and build-profile choices to the consumer.

For a Go command package, publish versioned module source and document:

```sh
go install example.com/acme/tool/cmd/tool@v1.2.3
```

**Historical note:** the book describes `go get` building and installing
executables. That workflow is obsolete. Verify the `go install ...@version`
contract against Go 1.26 documentation and publish semantic version tags.

## Source Traceability

Derived and paraphrased from *Powerful Command-Line Applications in Go*,
Chapter 11, “Distributing Your Tool”:

- “Including OS-Specific Data” — normalized lines 24364–24441
- “Including OS-Specific Files in the Build” — lines 24442–24644
- “Conditionally Building Your Application” — lines 24972–25212
- “Cross-Compiling Your Application” — lines 25213–25389
- “Compiling Your Go Application for Containers” — lines 25390–25638
- “Distributing Your Application as Source Code” — lines 25639–25662

Modernization notes are original synthesis and require verification against Go
1.26 and current upstream release/container documentation.
