# Security

This repository is the public **Skill** for the hosted CentricMem librarian. It does not contain API keys, pairing tokens, or owner passwords.

## Report a vulnerability

Please do **not** open a public issue for a security report.

Email **zeyu@dr.com**, or use [GitHub private vulnerability reporting](https://github.com/zeyu-j/centricmem-skill/security/advisories/new) if it is enabled.

We aim to acknowledge reports within 48 hours and ship a patch within 7 days for critical issues that affect the Skill, host MCP, or the connect flow.

Include:

- What you found and how to reproduce it
- Affected install path (`npx skills add`, host MCP at `https://mem.centricmem.com/mcp`, website)
- Whether any user data was accessed

## What this package must never contain

- Agent keys, owner session cookies, Stripe secrets, R2 credentials
- Instructions to paste a key into chat
- `path=` keep of arbitrary librarian-disk files

Authenticate by asking the agent to send a `/connect?device=` link. Enter the key on that page.
