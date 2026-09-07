---
name: go-cli-release-automation
description: Design, implement, and review secure Go CLI release automation with versioned tags, GoReleaser, GitHub Actions, checksums, signing, provenance, changelogs, Homebrew distribution, least-privilege credentials, verification, and recovery. Use when publishing CLI artifacts, configuring release CI, adding package-manager delivery, or diagnosing a partial or failed release.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.2.0"
  displayName: Go CLI Release Automation
  category: Go
  tags: go,golang,cli,release,ci,goreleaser,homebrew
---

# Go CLI Release Automation

Treat release automation as a state transition with verifiable inputs, immutable
artifacts, least privilege, and an explicit recovery path.

## Core Workflow

1. Define version, supported targets, artifact names, and release authority.
2. Validate release configuration without publishing.
3. Build final artifacts exactly once from a clean tagged commit and generate checksums.
4. Publish through pinned, least-privilege CI with protected environments.
5. Update package-manager metadata from the published artifacts.
6. Install and smoke-test representative artifacts.
7. Record partial state and recover without silently replacing released bytes.

## Read Next

| Task | Load |
|---|---|
| Design and validate the pipeline | `guidelines.md`, `workflows/validate-release-config.md` |
| Publish a tagged release | `workflows/publish-tagged-release.md` |
| Publish Homebrew metadata | `workflows/publish-homebrew-package.md` |
| Recover a failed release | `workflows/recover-failed-release.md` |
| Review security and reproducibility | `references/release-automation/rules.md` |
| Review examples | `references/release-automation/examples.md` |

## Guardrails

- Never release from an unreviewed or dirty source state.
- Do not grant write tokens to pull-request jobs or untrusted code.
- Pin CI actions and use current, supported GoReleaser configuration.
- Do not treat build tags as authorization controls.
- Do not overwrite published artifacts under the same version.
- Do not accept locally rebuilt bytes as recovery evidence.

## Source Notes

Guidance is transformed and paraphrased from Marian Montagnino,
*Building Modern CLI Applications in Go* (Packt, 2023), Chapters 7 and 12-14,
and Ricardo Gerardi, *Powerful Command-Line Applications in Go* (2021).

Verify current configuration against https://goreleaser.com/,
https://docs.github.com/en/actions/reference/security/secure-use, and the
target package manager. Current GoReleaser deprecations must be checked before use.
