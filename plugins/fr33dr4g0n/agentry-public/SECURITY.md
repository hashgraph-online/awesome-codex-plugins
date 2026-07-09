# Security Policy

Agentry's public discovery adapters are intentionally thin. They point agents
to the live Agentry documentation and do not proxy API traffic, store secrets,
or add a second install flow.

## Reporting A Vulnerability

Please report suspected vulnerabilities privately by opening a GitHub security
advisory on the repository:

https://github.com/fr33dr4g0n/agentry-public/security/advisories/new

Do not include secrets, API keys, DSNs, access tokens, or private customer data
in public issues, pull requests, screenshots, or logs.

## Supported Surface

The supported public discovery surface is the latest `main` branch of this
repository, the published npm package `@agentrysh/mcp`, and the live docs at
https://agentry.sh/ and https://api.agentry.sh/.
