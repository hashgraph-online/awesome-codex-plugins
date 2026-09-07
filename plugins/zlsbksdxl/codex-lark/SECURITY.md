# Security Policy

## Credentials

Never commit or report real Lark/Feishu app secrets, OAuth tokens, verification URLs, device codes, cookies, or local configuration files.

- Store Lark/Feishu credentials only through the official `lark-cli` configuration and authentication flow.
- Revoke and rotate any credential that was accidentally committed, even if the commit is later deleted.

## Reporting

Report a suspected vulnerability privately to the repository owner through GitHub's private vulnerability reporting feature. Do not include live credentials or private user data in the report.

Security issues in Lark CLI should also be reported to the upstream project.
