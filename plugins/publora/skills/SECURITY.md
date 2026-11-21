# Security Policy

## Supported versions

Only the latest release receives fixes. Install from `main` or the newest tag.

| Version | Supported |
| ------- | --------- |
| latest release | yes |
| older tags | no |

## Reporting a vulnerability

These skills instruct an AI agent to publish on someone's behalf using their API
key, so a defect here can post something the user never approved, or leak a
credential. Report privately rather than in a public issue:

- **Preferred:** [GitHub Security Advisories](https://github.com/publora/skills/security/advisories/new)
- **Alternative:** email `support@publora.com` with the subject `[SECURITY] skills`

Include what the issue is and where it lives, how to reproduce it, and the impact
you believe it has. Expect an acknowledgement within 72 hours and a fix or a
disclosure decision within 14 days.

Things worth reporting even if they look small:

- an instruction that would publish outside the user's requested scope
- an instruction that could be turned against the user by text the agent reads
  (a caption, a profile, an error message that tells the agent to do something)
- anything that would put an API key somewhere it can be read back

## Scope

**No credentials ship in this repository.** The API key belongs to the user and
reaches the server through their MCP client configuration or the `x-publora-key`
header. The CI drift scripts read a dedicated key from environment variables
and send it to the Publora endpoints described below.

**Check dependencies are separate from using the skills.** The frontmatter
validator uses the pinned PyYAML dependency in `requirements-dev.txt` with
`safe_load`, which does not construct arbitrary Python objects. The other checks
use the Python standard library. The link checker fetches documentation URLs;
the authenticated drift checks call Publora endpoints. No check executes content
fetched from those endpoints.

**One CI secret exists.** `PUBLORA_DRIFT_KEY` is used by the weekly drift check,
which calls MCP `initialize` and `tools/list` and REST
`GET /api/v1/platform-limits`. It is required to be a Starter key with no connected
accounts, so that even a leaked value cannot publish anywhere. If you find that
secret being used for anything else, that is a bug.

**There is no enforced approval step in this package.** `create_post` without
`scheduledTime` creates a draft; supplying a valid publication time schedules the
post. The skills do not implement a separate preview or approval mechanism.
Whether a confirmation prompt appears depends on the agent and client settings
and instructions. This package does not guarantee that every publication is
preceded by a user-approved draft.

**Text the agent reads is untrusted input.** A platform error message, a pasted
caption or a profile bio can contain instructions aimed at the agent rather than
the user. Skills must treat that content as data.

Please do not test vulnerabilities against the live platforms (LinkedIn, X, Meta,
TikTok, Telegram, Bluesky) outside their own disclosure programmes.
