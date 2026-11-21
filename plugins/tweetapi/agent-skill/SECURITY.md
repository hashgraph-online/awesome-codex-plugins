# Security policy

## Report a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not open a public issue containing a credential, exploit detail, private response, or user data.

If private vulnerability reporting is unavailable, contact TweetAPI through <https://tweetapi.com> without including secrets. The maintainers can provide a private follow-up channel.

## Credential handling

- Never commit TweetAPI keys or Twitter/X credentials.
- Never request or store passwords, cookies, `authToken`, `ct0`, TOTP codes, proxy credentials, or direct-message content.
- Use OAuth for the hosted MCP server.
- Keep REST and SDK API keys in a server-only secret store.
- Redact authorization headers and sensitive inputs from logs and bug reports.

Revoke an exposed credential through its issuing service before reporting the incident. Do not paste the revoked value into the report.
