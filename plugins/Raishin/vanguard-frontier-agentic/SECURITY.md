# Security Policy

## Supported Versions

The table below shows which versions of `@raishin/vanguard-frontier-agentic`
(current published version: **2.10.1**) receive security fixes.

| Version range | Supported          |
| ------------- | ------------------ |
| 2.10.x        | Yes — current minor |
| 2.9.x         | Yes — previous minor |
| < 2.9.0      | No                 |

Fixes are back-ported to the previous minor only when the vulnerability is
rated high or critical. Older versions receive no patches; upgrade to a
supported range.

---

## Reporting a Vulnerability

**Primary channel — GitHub Security Advisories (preferred)**

Use the private reporting form so the disclosure stays confidential:

> https://github.com/Raishin/vanguard-frontier-agentic/security/advisories/new

Do not open a public GitHub issue, start a GitHub Discussion, or use any chat
platform to report a suspected vulnerability. Those channels are public and
expose other users before a fix is available.

---

## What to Include in Your Report

A complete report helps us triage quickly. Include:

1. **Reproduction steps** — a minimal, numbered sequence that reproduces the
   issue reliably.
2. **Affected component path** — the file or directory inside this repository
   (for example `skills/aws/aws-iam-least-privilege-review/skill.md` or
   `schemas/skill.schema.json`).
3. **Impact assessment** — what an attacker could achieve by exploiting the
   issue, and under what conditions.
4. **Suggested fix** — optional, but appreciated if you have one.
5. **Your contact information** — so we can reach you during the coordinated
   disclosure window. We will not share it without your permission.

If you are reporting a vulnerability in a dependency of this package, please
also note the dependency name and version so we can file an upstream report.

---

## What NOT to Do

- Do **not** open a public GitHub issue to report a security vulnerability.
- Do **not** post vulnerability details in GitHub Discussions, Slack, Discord,
  or any other public forum.
- Do **not** send vulnerability reports as direct messages to individual
  maintainers on social media or other platforms.
- Do **not** exploit the vulnerability beyond the minimum proof-of-concept
  needed to demonstrate the issue. Accessing, modifying, or exfiltrating data
  beyond what is required to confirm the vulnerability is out of scope for this
  policy.
- Do **not** publish or share exploit details, proof-of-concept code, or
  reproduction steps publicly until coordinated disclosure is complete.

---

## Response SLA

| Milestone                             | Target                              |
| ------------------------------------- | ----------------------------------- |
| Acknowledgement of receipt            | Within 5 business days              |
| Triage (severity assessment, scope)   | Within 10 business days of receipt  |
| Coordinated disclosure window         | 90 days from initial acknowledgement, unless mutually extended in writing |

If you have not received an acknowledgement within 5 business days, send a
follow-up through the same private reporting channel.

We will keep you informed of progress throughout the window. Extensions to the
90-day window require mutual agreement and are granted when a fix is actively
in progress and a realistic release date is established.

---

## Scope

### In scope

The following assets are in scope for this policy:

- Source code and scripts in this repository (`scripts/`, `tests/`)
- Skill workflow files (`skills/**`)
- Agent definition files (`agents/**`)
- Rule files (`rules/**`)
- Schema files (`schemas/**`)
- Catalog metadata (`catalog/**`)
- MCP reference files (`mcp/**`)
- Package configuration and CI/CD definitions (`.github/`, `package.json`)

### Out of scope

- **Third-party dependencies** — if you find a vulnerability in a package this
  repository depends on, report it to that package's maintainers directly. We
  will file an upstream report if you notify us.
- **AI harnesses and platforms** — Claude Code, Codex, GitHub Copilot, Cursor,
  Gemini CLI, Kiro, and other harnesses that consume assets from this
  repository are independent products. Vulnerabilities in those platforms
  should be reported to their respective vendors.
- **Cloud provider services** — AWS, Azure, OCI, GCP, and other cloud services
  referenced in skills and agents are not in scope here. Report those to the
  relevant provider.
- **User-managed infrastructure** — environments where end users have deployed
  these assets are outside this repository's control.

---

## Safe Harbor

We support responsible security research. If you discover and report a
vulnerability in good faith and in accordance with this policy, we will:

- not pursue or support legal action against you related to your research,
- not refer your report to law enforcement, and
- work with you on a mutually agreeable disclosure timeline.

Good faith means: you limit testing to what is necessary to confirm the
vulnerability, you do not access or modify data that does not belong to you,
and you report the issue to us before disclosing it publicly.

This safe harbor applies to activity that complies with this policy. It does
not extend to conduct that is harmful, unlawful on independent grounds, or
outside the scope defined above.

---

## Release Artifact Verification

Each tagged release publishes the following supply-chain evidence:

1. **npm provenance** — `npm publish` is run with `--provenance` and emits a
   Sigstore bundle recorded on the public Rekor transparency log. Verify with:

   ```sh
   npm audit signatures
   # or, for a single version:
   npm view @raishin/vanguard-frontier-agentic@<version> --json \
     | jq -r '.dist.attestations'
   ```

2. **GitHub artifact attestations (SLSA Build L3 provenance)** — the release
   workflow attests both the published npm tarball and the SPDX SBOM using
   `actions/attest-build-provenance`. Verify with the GitHub CLI:

   ```sh
   # Download the tarball from the GitHub Release assets, then:
   gh attestation verify ./raishin-vanguard-frontier-agentic-<version>.tgz \
     --repo Raishin/vanguard-frontier-agentic

   gh attestation verify ./sbom.spdx.json \
     --repo Raishin/vanguard-frontier-agentic
   ```

3. **SPDX SBOM** — `sbom.spdx.json` is attached to every GitHub Release as a
   downloadable asset, generated by `anchore/sbom-action` from the repository
   source tree at release time.

Downstream consumers in regulated environments should pin to a specific
version, capture the SBOM and attestation bundle, and store both alongside
their internal SBOM evidence for SLSA / NIST SSDF / EU CRA audit trails.

---

## Acknowledgements

We recognise researchers who report valid vulnerabilities and help improve the
security of this repository. With your permission, we will credit you by name
or handle in the release notes and changelog for the fix.

If you prefer to remain anonymous, say so in your report and we will honor
that request.
