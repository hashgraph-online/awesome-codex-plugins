# Go CLI Distribution Checklist

Use this checklist when implementing platform variants or reviewing a release.

## Support Contract

- [ ] Supported `GOOS/GOARCH` pairs are explicit.
- [ ] The matrix was regenerated with the pinned Go 1.26 toolchain.
- [ ] Dependency, CGO, terminal, filesystem, and external-command constraints
      have been applied to the toolchain’s raw target list.
- [ ] Unsupported targets fail clearly or are excluded intentionally.
- [ ] Release profiles and their build tags are documented.
- [ ] Config, cache, data, and temporary paths use platform-aware locations.

## Platform Implementation

- [ ] Small data differences use a simple run-time decision.
- [ ] Substantial OS-specific code lives in suffix-selected files.
- [ ] Platform variants implement the same package contract.
- [ ] Build expressions are mutually exclusive and collectively complete.
- [ ] New constraints use `//go:build`, not only legacy `// +build`.
- [ ] Go 1.26 build-constraint and filename rules were checked in current docs.
- [ ] External OS tools and native prerequisites are detected with useful errors.

## Build Inputs

- [ ] Go toolchain version is pinned.
- [ ] `go.mod` and `go.sum` are clean and committed.
- [ ] The source revision is identified and the build starts from a clean tree.
- [ ] `GOOS`, `GOARCH`, `CGO_ENABLED`, tags, and linker flags are explicit.
- [ ] Output names include version, OS, architecture, and `.exe` where needed.
- [ ] Version/build metadata has an automated test.
- [ ] Mutable builder inputs such as `latest` are absent.
- [ ] `-trimpath` and any stripping flags have deliberate, verified semantics.
- [ ] Current Go 1.26 flag behavior was verified before adopting book-era commands.

## Build Selection

- [ ] `go list -f '{{.GoFiles}} {{.CgoFiles}}'` matches each release profile.
- [ ] Default, optional-feature, and minimal/container profiles compile.
- [ ] Unit tests run for every supported tag profile.
- [ ] Every supported target/profile combination has an artifact smoke plan.
- [ ] No build tag is treated as authentication or authorization.
- [ ] No profile selects duplicate definitions or omits required definitions.
- [ ] Local-only `replace` directives are absent from released module source.

## CGO and Linkage

- [ ] Every dependency supports the chosen CGO mode.
- [ ] CGO-enabled cross-builds use a target compiler, sysroot, and native libs.
- [ ] `file`, platform-native tools, or equivalent inspection confirms format
      and linkage.
- [ ] “Static” artifacts have been run in the minimum supported environment.
- [ ] CA roots, DNS, user lookup, timezone data, and plugins were tested.
- [ ] Any MinGW/SQLite or other native recipe was refreshed from current
      dependency and Go 1.26 documentation.

## Artifact Testing

- [ ] Every target artifact was executed natively or with a documented emulator.
- [ ] `--help` and `--version` work.
- [ ] Representative success and failure paths return stable exit codes.
- [ ] stdout and stderr remain suitable for scripts.
- [ ] Interrupt and termination signals produce expected cleanup.
- [ ] Interactive commands were tested with a TTY.
- [ ] Archives extract with correct filenames and executable permissions.

## Integrity and Reproducibility

- [ ] Final archives have cryptographic checksums.
- [ ] Checksums were verified after upload.
- [ ] Signing or provenance meets the release policy.
- [ ] Artifact names and metadata map back to the source revision.
- [ ] Snapshot output proves the intended target/profile artifact contract.
- [ ] The tagged release job is the single owner that builds final bytes.
- [ ] Downstream channels consume its recorded digests rather than rebuilding.
- [ ] Re-running the release from the same inputs was compared for equivalence.
- [ ] Current signing/provenance commands were verified against the 2026 release
      platform rather than inferred from the book.

## Containers

- [ ] A container is appropriate for the CLI’s actual usage.
- [ ] Builder and runtime images are current and pinned by digest.
- [ ] The final image contains only the binary and required runtime data.
- [ ] `scratch` is used only after proving self-containment.
- [ ] The process runs as a non-root UID.
- [ ] Entrypoint is exec-form and receives signals.
- [ ] Writable paths, read-only filesystem use, and mounts are explicit.
- [ ] Image architecture matches its manifest.
- [ ] The final image was scanned and smoke-tested with the intended runtime.
- [ ] Docker/Podman and multi-architecture commands were checked against current
      upstream documentation.

## Source Distribution

- [ ] Repository and module paths are stable and publicly resolvable.
- [ ] Release has a semantic version tag.
- [ ] Supported Go version and build prerequisites are documented.
- [ ] Installation uses a pinned command such as
      `go install module/path/cmd/tool@vX.Y.Z`.
- [ ] Documentation does not use the obsolete `go get` executable-install flow.
- [ ] Current `go install` behavior was checked against Go 1.26 documentation.
- [ ] License, notices, and contribution instructions are included.

## Stop-Ship Red Flags

- A claimed target was compiled but never run.
- Build tags select conflicting or incomplete implementations.
- A CGO-disabled build silently drops required behavior.
- A container relies on `latest`, runs as root without justification, or lacks
  runtime certificates/data that the CLI needs.
- Release files have no checksums or cannot be traced to a source revision.
- Documentation recommends a historical command without a current verification.

## Source Traceability

Derived and paraphrased from Chapter 11 of *Powerful Command-Line Applications
in Go*:

- OS-specific selection and testing — normalized lines 24364–24971
- Conditional profiles and selection inspection — lines 24972–25212
- Cross-compilation and CGO — lines 25213–25389
- Container compilation and packaging — lines 25390–25638
- Source distribution — lines 25639–25662

The integrity, provenance, hardening, and explicit Go 1.26 verification gates are
modern additions and require current official-source confirmation.
