# Release Automation Examples

## Minimal GitHub Actions Shape

```yaml
on:
  push:
    tags:
      - "v*"

permissions:
  contents: read

jobs:
  release:
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@<reviewed-full-commit-sha>
        with:
          fetch-depth: 0
      - uses: actions/setup-go@<reviewed-full-commit-sha>
      - uses: goreleaser/goreleaser-action@<reviewed-full-commit-sha>
        with:
          distribution: goreleaser
          version: '~> v2'
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Replace placeholders only after reviewing current action releases and security.
Do not grant write permissions to the test job. Add `id-token: write` only when
a reviewed signing or attestation step actually uses OIDC. A separate tap
repository needs its own narrowly scoped credential or trusted automation there.

## Build Information

```yaml
builds:
  - id: default
    binary: tool
    ldflags:
      - -s -w
      - -X example.com/project/internal/version.Version={{.Version}}
  - id: debug-internal
    binary: tool-debug
    tags: [debug]
```

Test that `tool version` reports the tag and that each archive contains the
expected files. Give every profile unique build/archive IDs and names. Declare
whether it is public; Homebrew should select only the production/default artifact.

## Unsafe Pattern

Publishing archives, then rebuilding binaries for Homebrew, creates different
checksums for the same version. Hand downstream systems the original release
URL and checksum instead.
