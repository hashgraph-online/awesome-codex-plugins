# Security Policy

## Supported Versions

Security fixes are considered for the current published package line.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately. Use GitHub private vulnerability reporting for this repository when available, or contact the repository owner before opening a public issue.

Do not include secrets, tokens, private project files, or exploit details in public issues, pull requests, logs, screenshots, or generated artifacts.

Useful reports include:

- affected package version
- exact command or workflow involved
- impact and reproduction steps
- relevant sanitized logs
- suggested mitigation, if known

## Handling Secrets

This project should not require committed credentials. Keep local values in files such as `.env` or `.npmrc`; those files are intentionally ignored by Git and Codex context.

If a secret was committed or shared publicly, rotate it immediately and remove it from history using your normal repository incident process.
