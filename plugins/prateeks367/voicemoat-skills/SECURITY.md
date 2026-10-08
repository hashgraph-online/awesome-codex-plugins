# Security policy

## What is in this repository

Agent Skills as plain Markdown `SKILL.md` files, plugin manifests in JSON, and
an icon. There are no scripts, no hooks, no MCP server settings and no
dependencies. Installing these skills runs no code on your machine. A skill
only changes how your assistant approaches one job.

## Supported versions

| Version | Supported |
|---|---|
| Latest release on `main` | Yes |
| Anything older | No |

Fixes go to `main`. Update to the latest release to get them.

## The optional VoiceMoat connection

The skills work on their own. Some of them can also use VoiceMoat's hosted MCP
server, if you connect it separately in your assistant. That connection is not
part of this repository.

It uses OAuth. You sign in on VoiceMoat's own sign-in page and your assistant
keeps the token. No API key, password or token is ever stored in a file here.
Posting through it always takes two calls: the first returns a preview and a
one-time code and posts nothing, and only a second call with that code
publishes.

## Skills that read other people's content

Five skills read text that someone other than you wrote:

- `draft-my-comments`
- `extract-the-hook`
- `get-seen-in-replies`
- `handle-my-replies`
- `why-did-that-one-take-off`

Each one tells the assistant to treat that text as data, not as instructions.
So a post or a reply that tries to tell your assistant what to do, claims to
come from you, or asks for something to be published is still just text
somebody typed. Only you decide what gets written or sent, and none of these skills
publishes anything by itself.

This lowers the risk of prompt injection. It does not remove it, so read a
draft before you post it.

## Reporting a vulnerability

Email founder@voicemoat.com with "Security" in the subject line. Say which
file and line is involved, what you expected and what happened. Please do not
open a public issue for anything that could be misused before it is fixed.

Useful reports include a skill instruction that could make an assistant leak
data, run a command or publish without your confirmation, and a manifest that
points somewhere it should not. Problems with the VoiceMoat app or its MCP
server can go to the same address.
