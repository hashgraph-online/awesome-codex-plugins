# Security Policy

## Supported versions

Security reports are evaluated against the current `main` branch and the latest published release. Older versions may not receive fixes.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Email `info@suedeai.ai` with:

- the affected version or commit;
- a concise impact description;
- reproducible steps or a minimal proof of concept; and
- any suggested mitigation.

Do not include live credentials, personal data, or third-party secrets. Use synthetic test data and redact sensitive values from logs and screenshots.

This project does not promise a response time, remediation timeline, bounty, or embargo period. Please keep the report private while it is being evaluated unless disclosure is required by law or a disclosure plan is agreed in writing.

## Scope

Security reports may cover plugin manifests and installation paths, bundled executable helpers, and the local read-only MCP servers. For usage questions or non-security defects, use the repository's normal issue tracker.

## Reviewed scanner exceptions

`.plugin-scanner.toml` contains exact-path exceptions for findings that were manually reviewed in the current source tree. It deliberately uses no wildcard paths, so new files remain visible. Scanner findings on an excepted path are hidden and that path must be manually re-reviewed after any change.

- `skills/suede-agent-teams/scripts/contribution-ledger.mjs` performs local ledger reads and atomic writes behind path, lock, authorization, and content-hash checks. It has no network or credential-store sink.
- `skills/suede-graph-flo-xr/workflows/helpers/apply-patch.cjs` validates its worktree and private temporary roots. `diff-digest.cjs` canonicalizes its worktree and each existing reported file, rejects paths that resolve outside the worktree, and rejects symlinks and non-regular files. Both invoke Git with explicit argument arrays and no shell interpolation.
- The four listed WAV files under `skills/suede-release-linter/scripts/fixtures/sample-clean-project/` are identical 16,044-byte PCM test fixtures (SHA-256 `56d4af65701c26df20bd4021eda95b6e830348ce3a746086079fe89285548dc9`). The exact skill-directory exception accounts only for the scanner's aggregate analyzability finding; each binary path is also listed explicitly.

These exceptions are not a security certification. Changes to an excepted path require renewed review, and reports about those paths remain in scope.

## Scanner version pin

The HOL Plugin Scanner workflow installs `plugin-scanner` by exact version and SHA256, but that wheel leaves its `cisco-ai-skill-scanner` dependency as an open `~=2.0.12` range. `.github/hol-scanner-constraints.txt` pins that dependency to `2.0.13`, the release the current tree was reviewed against, so a new scanner release cannot change the verdict on an unchanged tree. Cisco `2.0.14` (2026-09-01) added a `UNICODE_OBFUSCATED_INSTRUCTION` rule that treats three or more non-ASCII characters in a Markdown file as obfuscation; it reported HIGH findings on em dashes, arrows and multiplication signs in four prose files that contain no homoglyphs. Moving the pin forward is a deliberate change: re-run the scan against the new release, then review each new finding on its own terms before editing the constraint.
