# Go CLI Distribution Examples

Compact original examples for platform selection, release builds, containers,
and source installation.

## Platform Implementations

Keep the common contract in a neutral file:

```go
// package notify
type Sender interface {
	Send(title, body string) error
}

func Default() Sender { return platformSender{} }
```

Implement it in target-specific files:

```go
// sender_unix.go
//go:build linux || darwin

package notify

type platformSender struct{}

func (platformSender) Send(title, body string) error {
	return runNotifier(title, body)
}
```

```go
// sender_windows.go
//go:build windows

package notify

type platformSender struct{}

func (platformSender) Send(title, body string) error {
	return runWindowsToast(title, body)
}
```

**Why it works:** only the target implementation and imports enter the build.
The callers depend on one stable contract.

**Go 1.26 check:** verify `//go:build` expressions and filename constraints
against the current `go/build` documentation.

## Capability Variant With a Stub

```go
// telemetry_enabled.go
//go:build telemetry

package app

func emit(event string) { exporter.Send(event) }
```

```go
// telemetry_disabled.go
//go:build !telemetry

package app

func emit(string) {}
```

Avoid overlapping expressions that select both definitions or gaps that select
neither. Test both profiles:

```sh
go test ./...
go test -tags=telemetry ./...
go list -tags=telemetry -f '{{.ImportPath}} {{.GoFiles}}' ./...
```

## Explicit Release Matrix

```sh
#!/bin/sh
set -eu

version="${VERSION:?set VERSION}"
for target in linux/amd64 linux/arm64 darwin/arm64 windows/amd64; do
  os=${target%/*}
  arch=${target#*/}
  suffix=
  [ "$os" = windows ] && suffix=.exe
  out="dist/tool_${version}_${os}_${arch}${suffix}"
  CGO_ENABLED=0 GOOS="$os" GOARCH="$arch" \
    go build -trimpath -o "$out" ./cmd/tool
done
```

This is intentionally a small matrix, not the Cartesian product of remembered
platforms. CI should run tests and artifact smoke checks around it.

**Go 1.26 check:** confirm targets with the pinned toolchain and verify that
`-trimpath`, CGO mode, and the module’s dependencies fit the release contract.

## Inspect Artifact Metadata

```sh
go version -m dist/tool_v1.2.3_linux_amd64
file dist/tool_v1.2.3_linux_amd64
sha256sum dist/tool_v1.2.3_linux_amd64
```

On macOS, use `shasum -a 256` if `sha256sum` is unavailable. Do not infer
runtime compatibility from these inspections; execute a smoke test on the
target as well.

## Minimal Multistage Container

```dockerfile
# Verify and pin current image versions and immutable digests before release.
FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -o /out/tool ./cmd/tool

FROM scratch
COPY --from=build /out/tool /tool
USER 65532:65532
ENTRYPOINT ["/tool"]
```

Use `scratch` only if the binary needs no certificates, timezone data, passwd
records, shell, or shared libraries. Otherwise choose and pin a runtime image
that supplies the required data.

**Current-tooling check:** verify the Go 1.26 image tag/digest, builder platform,
container syntax, and multi-architecture behavior in current Docker or Podman.

## Source Installation

```sh
go install example.com/acme/tool/cmd/tool@v1.2.3
```

Pin a version in documentation and automation. A command using `@latest` is
convenient for people but not reproducible.

**Historical warning:** Chapter 11’s `go get` installation workflow is obsolete;
verify the current `go install` contract in Go 1.26 documentation.

## Bad: Hidden Release Inputs

```sh
go build ./cmd/tool
docker build -t acme/tool:latest .
```

Problems:

- Target, CGO mode, tags, and output identity depend on local state.
- Mutable base and output tags obscure the inputs.
- No artifact checksum or target smoke test is produced.

## Better: Declared Inputs and Verification

```sh
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
  go build -trimpath -o dist/tool-linux-amd64 ./cmd/tool
./dist/tool-linux-amd64 --version
shasum -a 256 dist/tool-linux-amd64 > dist/checksums.txt
```

Run that smoke test only on a compatible host; use a target runner or emulator
for other platforms.

## Source Traceability

Derived and paraphrased from Chapter 11 of *Powerful Command-Line Applications
in Go*:

- OS-specific implementation files — normalized lines 24442–24644
- Conditional variants and file inspection — lines 24972–25212
- Cross-build matrix and CGO boundary — lines 25213–25389
- Multistage and minimal containers — lines 25390–25638
- Source installation — lines 25639–25662

All examples are newly written. Commands and image references marked as
verification points must be checked against Go 1.26 and current upstream tools.
