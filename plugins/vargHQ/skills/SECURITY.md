# Security policy

## Supported versions

Only the latest commit on `main` is supported. Skills are published from `main` to skills.sh, ClawHub and the plugin marketplaces.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Email hello@varg.ai with "Security" in the subject, the affected skill, the steps to reproduce and the impact.

We reply within 3 business days and keep you updated until the fix ships.

## What these skills touch

- The skills are Markdown instructions plus a few helper scripts. They contain no keys or credentials.
- `how-to-make-ai-video` and the `varg-how-to` MCP server (`https://api.varg.ai/v2/skills/mcp`) are read-only search and need no key.
- Generation uses the person's own varg key (`VARG_API_KEY` or `~/.varg/credentials`) or OAuth sign-in on `https://mcp.varg.ai/mcp`. Never paste a key into a chat or commit it.
