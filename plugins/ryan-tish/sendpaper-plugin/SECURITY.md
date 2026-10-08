# Security policy

## Reporting a vulnerability

Email **support@sendmypaper.com** with "Security" in the subject. Please include steps to reproduce and any affected URLs or tool names. We aim to reply within 2 business days and will tell you when a fix ships. Please don't open a public issue for security reports.

## Scope

- This repository: the Codex plugin manifest, MCP config and skill.
- The hosted MCP server at `https://sendmypaper.com/mcp` and the REST API at `https://sendmypaper.com/v1`.

## How the plugin handles money and data

- The plugin contains no API keys or secrets. The MCP server needs no authentication.
- An agent can only spend money with a Stripe shared payment token that the user approved for that amount in Stripe Link, or by handing the user a Stripe Checkout link. Sendpaper never sees card numbers.
- A person reviews every piece of mail before it is printed.
