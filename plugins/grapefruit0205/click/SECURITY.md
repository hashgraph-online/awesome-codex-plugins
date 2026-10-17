# Security Policy

## Reporting a vulnerability

Please do not disclose exploitable vulnerabilities, secrets, or proof-of-concept attack details in a public issue.

If GitHub's private vulnerability reporting is available for this repository, use **Security → Report a vulnerability**. Otherwise, contact the maintainer through the repository owner's GitHub profile and ask for a private reporting channel without including sensitive details publicly.

When reporting, include only what is needed to reproduce and assess the issue:

- affected Click version or commit;
- affected platform and Codex version;
- the smallest reproducible sequence of actions;
- expected versus observed security boundary;
- whether the issue can execute commands, bypass approval, escape the approved boundary, expose secrets, or modify files unexpectedly.

Please remove real credentials, personal data, and unrelated repository contents from reports.

## Security-sensitive behavior

Click intentionally uses lifecycle hooks and local command runners to enforce workflow boundaries. Security reports are especially useful for issues involving:

- approval or contract bypass;
- shell or command injection;
- unsafe path traversal or writes outside the intended repository boundary;
- secret exposure or unsafe environment handling;
- verification commands that unexpectedly mutate protected source content;
- GitHub Actions or dependency supply-chain risks.

## Supported versions

Security fixes are applied to the current release line. Users should upgrade to the latest published version before reporting an issue that may already have been fixed.
