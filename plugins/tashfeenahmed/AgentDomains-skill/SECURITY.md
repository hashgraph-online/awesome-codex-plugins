# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities in this plugin, its skill, or the
AgentDomains service privately via
[GitHub security advisories](https://github.com/tashfeenahmed/AgentDomains-skill/security/advisories/new)
or by emailing the maintainer at the address listed at
[https://agentdomains.co](https://agentdomains.co). Do not open a public issue
for security problems.

We aim to acknowledge reports within 3 business days and to ship a fix or
mitigation within 30 days for anything confirmed.

## What this plugin does

The plugin consists of a skill definition (`skills/agentdomains/SKILL.md`) and
an optional setup script (`skills/agentdomains/scripts/setup.sh`). With the
user's consent, the agent:

1. Installs the open-source [`agentdomains` CLI](https://github.com/tashfeenahmed/AgentDomains)
   via `go install github.com/tashfeenahmed/AgentDomains/cmd/agentdomains@latest`
   (the Go module published from the tashfeenahmed/AgentDomains repository, not
   this one), or points the user at prebuilt binaries on that repository's
   GitHub releases page.
2. Creates an AgentDomains account (`agentdomains signup`) — signup needs no
   credentials; the account's first domain claim needs an email address the
   user supplies.
3. Calls the public AgentDomains API at `https://api.agentdomains.co` over HTTPS
   using an API key that is stored locally in `~/.agentdomains/config.json`
   and never leaves the machine except in the `Authorization` header of
   requests to that API.

## Trust boundary

- The skill instructs the agent never to pay for anything and never to create
  DNS records the user has not asked for.
- The API key grants domain management on one AgentDomains account only.
  Revoke it at any time by deleting the account (`agentdomains account-delete`)
  or contacting support.
- The plugin itself executes no code on install; the setup script only runs if
  the agent or user runs it explicitly.

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| < latest| :x: (update first) |
