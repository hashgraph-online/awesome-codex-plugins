# Security policy

## Supported versions

The latest published PMC release is supported with security fixes.

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in a public issue. Use GitHub's private vulnerability reporting for this repository, or contact the maintainer through the support details at https://duncanmain.github.io/project-memory-core/support.html.

Include the affected version, a concise reproduction, the potential impact, and any suggested mitigation. Reports will be acknowledged as soon as practical and validated before public disclosure.

## Security boundaries

PMC has no developer backend or telemetry service. It operates on local paths the user places in scope through Codex's normal filesystem permissions. Durable notes must exclude credentials, tokens, private keys, authentication cookies, and unnecessary sensitive data.
