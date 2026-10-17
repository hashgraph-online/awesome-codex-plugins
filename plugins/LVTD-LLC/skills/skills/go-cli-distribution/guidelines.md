# Go CLI Distribution Guidelines

Use this file to route build, cross-platform, and release work to focused references.

## Workflows

| Task | Workflow |
|---|---|
| Prepare and verify a cross-platform CLI release | `workflows/prepare-cross-platform-release.md` |

## By Task

| Task | Load |
|---|---|
| Plan a release matrix | `references/distribution/knowledge.md`, `references/distribution/rules.md` |
| Implement OS-specific or constrained code | `references/distribution/patterns.md`, `references/distribution/examples.md` |
| Build and package artifacts | `references/distribution/rules.md`, `references/distribution/examples.md` |
| Review release readiness | `references/distribution/checklist.md` |

## By Code Element

| Element | Primary | Secondary |
|---|---|---|
| `//go:build` and filename constraints | `references/distribution/rules.md` | `references/distribution/examples.md` |
| `GOOS`, `GOARCH`, and CGO | `references/distribution/knowledge.md` | `references/distribution/patterns.md` |
| version metadata and reproducible build flags | `references/distribution/patterns.md` | `references/distribution/checklist.md` |
| archives, checksums, containers, and install instructions | `references/distribution/rules.md` | `references/distribution/checklist.md` |

## By Problem or Symptom

| Symptom | Load |
|---|---|
| Cross-compiled artifact builds but will not run | `references/distribution/knowledge.md`, `references/distribution/checklist.md` |
| Platform-specific files are selected incorrectly | `references/distribution/rules.md`, `references/distribution/examples.md` |
| CGO breaks the release matrix | `references/distribution/patterns.md`, `references/distribution/checklist.md` |
| Documentation still recommends `go get` for installation | `references/distribution/rules.md` |

## Decision Tree

```text
What are you shipping?
├─ One native binary → rules.md + checklist.md
├─ Multi-platform artifacts
│  ├─ Pure Go → examples.md + checklist.md
│  └─ CGO involved → knowledge.md + patterns.md
├─ Platform-specific source → rules.md + examples.md
└─ Publishing, CI credentials, Homebrew, or recovery → $go-cli-release-automation
```

## File Index

| File | Purpose |
|---|---|
| `references/distribution/knowledge.md` | Portability, target matrices, CGO, artifacts, and release concepts |
| `references/distribution/rules.md` | Current Go build, install, and packaging rules |
| `references/distribution/examples.md` | Original build-constraint and release examples |
| `references/distribution/patterns.md` | Repeatable cross-build, metadata, container, and verification patterns |
| `references/distribution/checklist.md` | Release-readiness and artifact verification checklist |

## Common Combinations

| Scenario | Files |
|---|---|
| Cross-platform release | `rules.md` + `patterns.md` + `checklist.md` |
| Add platform-specific code | `rules.md` + `examples.md` |
| Diagnose target failure | `knowledge.md` + `checklist.md` |
