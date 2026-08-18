# Prepare a Cross-Platform Release Workflow

Build, package, and verify versioned Go CLI artifacts for a declared target matrix.

## When to Use

- Preparing a public or internal multi-platform CLI release.
- Adding platform-specific files, build tags, CGO, or containers.
- Repairing release instructions or artifacts that are not reproducible.

## Prerequisites

- A pinned Go toolchain and clean source revision.
- Declared supported `GOOS/GOARCH` targets and release profiles.
- Native runners or documented emulators for artifact smoke tests.

**Reference:** `../references/distribution/knowledge.md`

## Workflow Steps

### Step 1: Derive the Target Matrix

**Goal:** Build only targets the product and its dependencies support.

- [ ] Start from `go tool dist list` in the pinned toolchain.
- [ ] Overlay dependency, CGO, OS-feature, and product constraints.
- [ ] Record exact targets and build profiles in version control.
- [ ] Define how every released target will be executed for verification.
- [ ] Include supported capability/build-tag profiles in the matrix.
- [ ] Reject any design that uses a tag as runtime access control.

**Reference:** `../references/distribution/rules.md`

### Step 2: Verify Source Selection

**Goal:** Make platform and capability variants explicit and complete.

- [ ] Prefer `_GOOS.go` or `_GOARCH.go` files for substantial platform code.
- [ ] Use modern `//go:build` expressions for orthogonal capabilities.
- [ ] Ensure variants are mutually exclusive and collectively complete.
- [ ] Inspect selected and ignored files with `go list`.

**Reference:** `../references/distribution/examples.md`

### Step 3: Make Build Inputs Reproducible

**Goal:** Ensure a clean environment can reproduce each artifact.

- [ ] Pin toolchain, dependencies, targets, tags, CGO mode, flags, and revision.
- [ ] Build into deterministic target-specific paths.
- [ ] Inject version metadata deliberately and test `--version`.
- [ ] For CGO, provision the target compiler and libraries or document dynamic requirements.

**Reference:** `../references/distribution/patterns.md`

### Step 4: Test the Final Artifacts

**Goal:** Prove runtime behavior rather than compilation alone.

- [ ] Run unit tests for every build-tag profile.
- [ ] Execute each target natively or in the declared emulator.
- [ ] Smoke-test help, version, representative commands, streams, exit codes, and signals.
- [ ] Inspect linkage and minimum-environment requirements.
- [ ] Verify platform config, cache, data, and temporary directory behavior.

**Reference:** `../references/distribution/checklist.md`

### Step 5: Package and Protect Artifacts

**Goal:** Produce immutable, installable release files.

- [ ] Create consistently named archives with executable permissions intact.
- [ ] Generate and verify checksums for the local snapshot.
- [ ] Confirm the tagged release job will build final bytes exactly once, then
      generate signing/provenance and post-publication checksum verification.
- [ ] Define the handoff manifest: artifact name, target, profile, digest, and revision.

**Reference:** `../references/distribution/rules.md`

### Step 6: Verify Containers and Source Installation

**Goal:** Keep alternate distribution paths aligned with the binary release.

**If shipping a container:**

- [ ] Use pinned multistage images, exec-form entrypoint, and a non-root user.
- [ ] Prove CA, timezone, DNS, user, and writable-path requirements.

**If shipping module source:**

- [ ] Tag a semantic version and document the supported Go version.
- [ ] Test `go install module/cmd/tool@version` from outside the checkout.
- [ ] Document build tags, CGO prerequisites, and generated inputs.

**Reference:** `../references/distribution/patterns.md`

## Quick Checklist

```text
[ ] Supported targets and profiles are declared
[ ] Build constraints select the intended source
[ ] Every build input is pinned or recorded
[ ] Final artifacts run on every supported target
[ ] Archives, checksums, metadata, containers, and install docs are verified
```

## Common Mistakes

| Mistake | Consequence | Do Instead |
|---|---|---|
| Treating cross-compilation as runtime proof | Broken artifacts are published | Execute every released target |
| Assuming `CGO_ENABLED=0` means static | Runtime dependencies are missed | Inspect linkage and minimum environment |
| Recommending `go get` for installation | Current module workflows are misrepresented | Use versioned `go install` |

## Exit Criteria

- [ ] A clean revision reproduces the artifact set.
- [ ] Every artifact passes target-level smoke tests.
- [ ] Integrity metadata matches immutable published files.
- [ ] Binary, container, and source-install documentation match the release.
