# Security Policy

agenttrace analyzes local AI coding-agent session logs. Those logs can contain
prompts, file paths, tool arguments, repository names, API keys, or other private
data, so security reports should avoid raw private session content.

## Supported Versions

Security fixes target the latest released version of agenttrace.

## Reporting a Vulnerability

Please report sensitive issues privately through GitHub Security Advisories:

https://github.com/luoyuctl/agenttrace/security/advisories/new

If a private advisory is not available, contact the repository owner through
their GitHub profile and include only a high-level description first.

## What to Include

- agenttrace version
- operating system and install method
- affected command or parser
- impact and expected severity
- minimal redacted reproduction steps

Do not include raw private prompts, API keys, proprietary source code, customer
data, or full unredacted session logs.

## Scope

In scope:

- parsing behavior that can expose private local data unexpectedly
- generated reports that leak content outside the requested output
- install or update paths that can be tampered with
- unsafe handling of malformed local session files

Out of scope:

- findings that require publishing private logs publicly
- social engineering or phishing
- denial-of-service reports without a concrete impact path
- issues in upstream AI agent tools that agenttrace only reads from
