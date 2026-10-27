# Security Policy

Agent skills are instructions and code that AI agents execute with your
permissions. We treat every file in `skills/` as security-sensitive.

## Reporting a vulnerability

**Do not open a public issue.** Report privately via GitHub's
[private vulnerability reporting](https://github.com/KalarisLabs/research-agent-skills/security/advisories/new).

Include the affected skill or file, a description of the impact, and reproduction steps.
We aim to acknowledge reports within **2 business days**, give an initial assessment within
**5 business days**, and ship a fix or mitigation for high/critical issues within **14 days**.
We credit reporters in the advisory unless you prefer otherwise.

In scope:
- Prompt injection or hidden instructions in any skill file (SKILL.md, references, assets, scripts, tests)
- Malicious or dangerous code in skill scripts (exfiltration, credential access, remote code execution)
- Supply-chain issues in the CLI, installers, release artifacts or CI workflows
- Checksum/signature bypasses in `install.sh`, `install.ps1` or the npm CLI

## Secure design and common errors

The design follows Saltzer and Schroeder's principles, and the code and CI address the common error classes
in the OWASP Top 10 that apply to an installer and a body of agent instructions.

| Principle or error class | How the project applies it |
|---|---|
| Least privilege | Workflows declare `permissions: {}` and grant each job only what it needs |
| Fail-safe defaults | The installers verify SHA-256 before extracting and stop on a mismatch; unknown paths in an archive are skipped, not installed |
| Complete mediation | Script network access is limited to `security/allowed-domains.txt`, enforced in CI |
| Economy of mechanism | Scripts are standard-library first; the installer has no runtime dependencies |
| Path traversal and archive attacks (zip slip) | `cli/src/tar.ts` rejects absolute paths, `..`, links and oversized entries; covered by unit tests and property-based fuzz tests |
| Injection (shell, prompt) | No `eval`/`exec` of fetched data; prompt-injection and hidden-Unicode lint over every file under `skills/` |
| Vulnerable and outdated components | Dependabot, dependency review and lockfiles |
| Software and data integrity failures | Actions pinned by SHA, SLSA build provenance, Sigstore signatures on checksums |
| Security logging | CI findings are recorded as code-scanning alerts; pinned baselines require review to change |

## Supported versions

Security fixes land on `main` and in the latest release. Pin versions (`--version` / `RAS_VERSION`)
and update when advisories are published.

## How we protect users

| Layer | Control |
|---|---|
| Every pull request | Agent Skills spec validation; repository policy (file types, sizes, links, paths); prompt-injection and payload lint over **all** files including tests; Cisco AI Defense skill-scanner (static, YARA, behavioral dataflow); CodeQL; Semgrep; Bandit; ShellCheck; secret scanning (TruffleHog); dependency review |
| Optional vendor scans | With `VENDOR_SCANS_ENABLED=true` and the corresponding secrets, Snyk Agent Scan checks every skill folder and Socket checks dependency manifests against the organization's security and license policy. The release workflow always repeats local validation, prompt-injection lint, Cisco AI Defense scanning and tests. |
| Network egress in scripts | Domains contacted by skill scripts must be listed in `security/allowed-domains.txt` (CODEOWNERS review required) |
| Accepted findings | Reviewed false positives are pinned by fingerprint in `security/lint-baseline.json` and `security/skill-scanner-baseline.json`; any new finding fails CI |
| Workflows | Actions pinned by commit SHA, least-privilege `permissions`, no `pull_request_target` checkouts, zizmor + actionlint, harden-runner, OpenSSF Scorecard |
| Releases | Tarball + `SHA256SUMS` with GitHub build-provenance attestations (SLSA) and a Sigstore signature; npm package published with provenance |
| Installers | Verify SHA-256 before extracting; tar extraction rejects links, absolute paths and `..`; the CLI records per-file hashes and `doctor` detects tampering |

## Verifying a release

The installers check the archive against the SHA-256 checksums published in the same release. That detects corrupted or
altered downloads but does not authenticate the release. To authenticate it, run the commands below.

```bash
gh attestation verify research-agent-skills-1.0.0.tar.gz --repo KalarisLabs/research-agent-skills
cosign verify-blob SHA256SUMS --bundle SHA256SUMS.sigstore.json \
  --certificate-identity-regexp 'https://github.com/KalarisLabs/research-agent-skills/.github/workflows/release.yml@.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
sha256sum -c SHA256SUMS
npm audit signatures   # for the research-agent-skills npm package
```

## Guidance for users

- Install only the skills you need. Each installed skill's description is loaded into your
  agent's context, and fewer skills means a smaller attack surface.
- Skills with `scripts/` run code on your machine when the agent chooses to. Review scripts for
  skills you install, and run agents with sandboxing and permission prompts enabled.
- Skills that call external APIs need your API keys in environment variables. Scope keys narrowly.
