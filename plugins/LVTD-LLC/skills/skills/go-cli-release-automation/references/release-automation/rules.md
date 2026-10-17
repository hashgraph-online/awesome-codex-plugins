# Release Automation Rules

## Source and Build

- Release only an approved, clean, reachable commit.
- Make the tag and embedded version agree.
- Run tests, race checks, static checks, and every supported build profile.
- Generate checksums and provenance from the exact published bytes.
- Keep artifact names deterministic across releases.
- Give each capability profile a unique build ID, binary/archive name, and
  publication policy. Prevent default/debug collisions.
- When PGO is selected, preserve its mode, main package, workload provenance,
  and profile digest beside toolchain, source revision, and build flags.
- Release automation transports the approved PGO input unchanged; selection
  and performance proof belong to `go-performance-testing`.

## CI Security

- Set explicit minimal job permissions; grant release writes only to the publish job.
- Do not expose secrets to pull-request code or arbitrary workflow inputs.
- Pin third-party actions to reviewed versions or immutable commits.
- Use protected environments for high-value publishing credentials.
- Prefer short-lived identity federation or narrowly scoped tokens.

## Package Managers

- Reference immutable release URLs and exact checksums.
- Update package metadata only after the release is reachable.
- Use current GoReleaser package configuration; verify deprecations such as
  Homebrew formula versus cask behavior before copying examples.
- Install from the package manager in a clean smoke environment.
- Use a separate narrowly scoped credential or trusted workflow for a tap in
  another repository; the source repository's `GITHUB_TOKEN` is repository-scoped.

## Recovery

- Never replace bytes behind an existing checksum and version.
- Capture durable IDs, URLs, checksums, and successful steps.
- Make retryable steps idempotent.
- Revoke or rotate credentials after suspected exposure.
