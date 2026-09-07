# Security Policy

Unified AI System accepts coordinated, private vulnerability reports. Do not
open a public issue for a suspected security problem.

## Supported Versions

| Version | Security fixes |
| --- | --- |
| `0.5.x` | Supported |
| `0.4.x` | Critical fixes only |
| `0.3.x` and earlier | Not supported |

Reports about `master` are welcome, but released versions are the supported
distribution boundary.

## Report A Vulnerability

Use GitHub's private
[Report a vulnerability](https://github.com/happy520ai/unified-ai-system/security/advisories/new)
form. Include:

- the affected component and version;
- reproduction steps or a minimal proof of concept;
- the expected impact and required preconditions;
- any practical mitigation you have identified.

Never include provider keys, access tokens, private endpoints, raw webhooks,
or authorization records. Sanitize logs and examples before submitting them.

## Response Targets

The project aims to acknowledge a report within three business days and share
an initial assessment within seven business days. These are best-effort
targets, not a commercial support SLA. Remediation and disclosure timing will
depend on severity, exploitability, and release risk.

## Research Boundaries

Use the credential-free fake provider and infrastructure you own or are
authorized to test. Do not make unapproved real-provider calls, access other
people's data, degrade shared services, or use social engineering. Stop and
report privately if testing exposes credentials or sensitive data.

## Coordinated Disclosure

Please allow time for validation and a supported fix before public disclosure.
After remediation, the project may publish a GitHub Security Advisory and will
credit reporters who request attribution.
