# Security Policy

## Reporting a vulnerability

Please do not open public GitHub issues for suspected security vulnerabilities.

Use one of these paths instead:

- GitHub Security Advisories for private vulnerability reporting, if enabled on the repository
- A direct maintainer contact channel documented in the repository settings

## What to include

- A clear description of the issue
- Affected files, commands, or workflows
- Reproduction steps or proof-of-concept when possible
- Expected impact and any suggested mitigations

## Scope

This project treats the following as security-sensitive:

- Real credentials, tokens, private keys, or secrets in the repository or package output
- Install flows that expose private overlay details by default
- Supply-chain risks in packaged artifacts, workflow permissions, or release automation
- Unsafe defaults that could leak local machine or organization-specific context

## Response expectations

We aim to acknowledge reports promptly, validate them, and coordinate a fix before public disclosure when appropriate.
