# Security Policy

## Reporting Vulnerabilities

Report security issues privately by opening a GitHub security advisory for this repository or emailing the maintainer address listed on the package profile.

Please include:

- AgentPack version and install method
- affected command or integration
- minimal reproduction steps
- whether private source, secrets, or generated packs were exposed

Do not publish exploit details before a fix or mitigation is available.

## Scope

Security-relevant areas include:

- local source scanning, ranking, packing, and redaction
- generated `.agentpack/` artifacts
- MCP server access to local repo context
- installer-written agent rules, hooks, and config files
- package release workflows and published artifacts

## Privacy Baseline

AgentPack does not upload source code for scan, summarize, rank, route, pack, stats, or benchmark. These commands operate locally and write local artifacts under `.agentpack/`.

See [`docs/privacy.md`](docs/privacy.md), [`docs/threat-model.md`](docs/threat-model.md), and [`docs/data-flow.md`](docs/data-flow.md) for the detailed model.

## Release Trust

- License: MIT
- Python package: `agentpack-cli`
- npm wrapper: `@vishal2612200/agentpack`
- PyPI publish workflow uses GitHub OIDC / Trusted Publishing
- npm publish workflow requests provenance with `npm publish --provenance`

Users should still inspect generated context before sharing it outside their machine.
