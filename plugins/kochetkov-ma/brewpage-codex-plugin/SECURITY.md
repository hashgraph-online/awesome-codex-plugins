# Security Policy

## Supported versions

Only the latest release of this plugin receives fixes.

## Reporting a vulnerability

Report a vulnerability in this plugin privately through GitHub's
[private vulnerability reporting](https://github.com/kochetkov-ma/brewpage-codex-plugin/security/advisories/new),
or by e-mail to info@brewpage.app. Do not open a public issue for a security problem.

Abuse of a page hosted on brewpage.app (phishing, malware, illegal content) is not
a plugin vulnerability: report it at https://brewpage.app/report-abuse.

## What the plugin does

- Sends content only to `https://brewpage.app` (REST API and the remote MCP server at `/mcp`).
- Needs no credential. Each publish returns a management link and an owner token for
  that page. The skill gives the user the management link with the page link (it is
  private: anyone who has it can edit or delete the page) and writes the owner token to
  `./brewpage-history.md` (mode 600, git-ignored); the token is shown when the user asks,
  or at once if that file cannot be written. Neither is posted publicly.
- An unlisted link is not private: anyone who has the link can open the page.
  Never publish secrets, credentials or personal data.
