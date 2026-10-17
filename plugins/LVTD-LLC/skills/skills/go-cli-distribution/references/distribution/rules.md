# Go CLI Distribution Rules

Actionable rules for portable, reproducible, and verifiable Go CLI releases.

## Platform Rules

1. **Declare the supported target matrix.**
   - List exact `GOOS/GOARCH` pairs and supported release profiles.
   - Generate candidates with the release toolchain, then remove targets that
     dependencies or product requirements cannot support.
   - **Go 1.26 check:** rerun `go tool dist list` in the pinned toolchain.

2. **Prefer platform filename suffixes for platform implementations.**
   - Put substantial OS-specific behavior in files such as
     `terminal_windows.go`.
   - Keep the same internal interface or function signature across variants.
   - Fail clearly when an unsupported platform is intentionally buildable.

3. **Use run-time branching only for small data differences.**
   - `runtime.GOOS` is suitable for labels or argument values.
   - Do not hide large implementations or unsupported imports inside switches.

4. **Use modern build constraints for orthogonal capabilities.**
   - Put `//go:build expression` before the package clause with a blank line.
   - Name tags for capabilities (`sqlite`, `integration`), not vague
     environments (`special`, `prod2`).
   - Make variants mutually exclusive and collectively complete.
   - **Go 1.26 check:** verify constraint syntax in current `go/build` docs.
   - Treat tags as code-selection capabilities, never runtime access control.

5. **Use portable application directories.**
   - Resolve config and cache roots through current platform-aware APIs.
   - Keep config, cache, data, and temporary files semantically distinct.
   - Test first-run creation, permissions, migration, and cleanup on each target.

## Build Rules

6. **Make every build input explicit.**
   - Pin the Go version, dependencies, target, tags, CGO mode, linker flags, and
     source revision.
   - Build into deterministic target-specific paths.
   - Avoid relying on a developer’s persistent `go env` settings.
   - When using PGO, record mode, profile digest, originating workload, main
     package, and the exact profile used for released bytes.
   - Do not apply one profile to unrelated command binaries by accident.

7. **Do not assume `CGO_ENABLED=0` is a universal static-build switch.**
   - Confirm all dependencies support CGO-disabled builds.
   - Inspect linkage and execute smoke tests in the minimum target environment.
   - With CGO enabled, provision a target C compiler and target libraries.
   - **Go 1.26 check:** verify link and stdlib behavior for the chosen flags.

8. **Derive the matrix instead of hard-coding remembered exclusions.**
   - Start with current toolchain support.
   - Overlay dependency and product constraints.
   - Keep the resulting matrix in version control and CI.

9. **Inject release metadata deliberately.**
   - Prefer VCS/build information available from the Go toolchain when adequate.
   - If using `-ldflags -X`, target a stable variable and test the version output.
   - Do not strip debug data until the debugging trade-off is accepted.

## Verification Rules

Treat every supported capability profile as part of the target matrix. Compile,
test, and artifact-smoke each supported combination, including the default and
intentionally reduced profiles.

10. **Inspect selection, compile, and run.**
   - Use `go list` to inspect `GoFiles`, `CgoFiles`, and ignored files by profile.
   - Run unit tests for every build-tag profile.
   - Execute each released target natively, in CI runners, or in a documented
     emulator; compilation alone is insufficient.

11. **Test the artifact, not only the source checkout.**
    - Exercise `--help`, `--version`, representative commands, exit codes,
      stdout/stderr separation, signals, and configuration discovery.
    - Check archive extraction and executable permissions.
    - Compare and smoke-test selected PGO artifacts on supported targets; route
      performance interpretation to `go-performance-testing`.

12. **Publish integrity metadata beside artifacts.**
    - Generate cryptographic checksums from final, immutable files.
    - Sign artifacts or provenance when the release policy requires it.
    - Verify checksums after upload or registry publication.
    - **Current-tooling check:** confirm supported signing/provenance commands
      against the selected 2026 release platform.

13. **Define the final artifact handoff.**
    - Before tagging, snapshot-test the names, targets, profiles, and contents.
    - Let the protected tagged release job build the final bytes exactly once.
    - Record URL/name, digest, target, profile, and source revision after publication.
    - Package-manager automation must promote these bytes, never rebuild the version.

## Container Rules

14. **Use a multistage build and pin every base image.**
    - Pin the builder toolchain and final image by version and preferably digest.
    - Copy only the executable and its required runtime data.
    - Never use the book’s Go 1.15 or `latest` tags in a current release.

15. **Choose `scratch` only after proving self-containment.**
    - Account for CA roots, timezone data, user lookup, DNS, and writable paths.
    - Use a minimal or distroless runtime if any of those are required.

16. **Run containers with least privilege.**
    - Use a non-root UID, a deliberate working directory, and explicit writable
      mounts.
    - Prefer exec-form `ENTRYPOINT`/`CMD` so the CLI receives signals.
    - Scan the final image and test it with the intended runtime flags.
    - **Current-tooling check:** verify Docker/Podman syntax and base-image
      behavior against current upstream documentation.
    - Declare intended CPU and memory limits and test the final image under
      them; runtime tuning remains owned by `go-performance-testing`.

## Source Distribution Rules

### SQL-backed artifacts

- Embed schema or migration assets when the CLI must initialize storage without
  adjacent source files, but keep versioning and coordination in a migration system.
- Treat CGO-dependent drivers as an artifact and cross-compilation constraint,
  not as categorically wrong.
- Document native libraries, static or dynamic linking, supported targets, and
  database-driver configuration.
- Smoke-test the built artifact creating or upgrading an isolated database.

17. **Publish installable, versioned module source.**
    - Keep command packages under stable module paths.
    - Tag releases semantically and document the supported Go version.
    - Tell users to install a fixed version:

      ```sh
      go install example.com/acme/tool/cmd/tool@v1.2.3
      ```

    - **Historical warning:** do not recommend the book’s `go get` executable
      installation flow; verify current `go install` behavior with Go 1.26.

18. **Ship the build contract with the source.**
    - Document tags, CGO/native prerequisites, generated files, and release
      commands.
    - Ensure a clean checkout can build without local `replace` directives.

## Exceptions

- A single-platform internal tool may use one target, but should still declare
  it and test the produced artifact.
- A CGO-backed CLI may intentionally ship dynamically linked binaries or a
  container; document required libraries rather than claiming portability.
- Interactive CLIs may require a TTY. Provide noninteractive smoke checks and
  document terminal requirements.

## Source Traceability

Derived and paraphrased from Chapter 11 of *Powerful Command-Line Applications
in Go*:

- OS-specific data and files — normalized lines 24364–24644
- Conditional builds and `go list` verification — lines 24972–25212
- Cross-compilation and CGO — lines 25213–25389
- Container builds — lines 25390–25638
- Source distribution — lines 25639–25662

The Go 1.26, integrity, reproducibility, and current-container requirements are
modernization guidance and must be verified against current official sources.
