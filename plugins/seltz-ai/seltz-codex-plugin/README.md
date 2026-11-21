# Seltz Codex plugin

Seltz gives Codex access to current, source-backed web knowledge through Seltz's official Streamable HTTP
MCP server. The plugin configures the hosted server and adds guidance for responsible web research.

## Install and authenticate

The official Seltz MCP endpoint is:

```text
https://mcp.seltz.ai/mcp
```

For a local Codex MCP connection:

```bash
codex mcp add seltz --url https://mcp.seltz.ai/mcp
```

Then run `/mcp` and select Seltz: Codex opens Seltz's sign-in page in your browser. Codex owns the
interactive authentication session; this plugin does not store credentials.

Never commit credentials, paste a key into chat, or put a real key in a workflow, fixture, screenshot,
or manifest.

## Use it

Ask Codex naturally:

- “Search for the latest official guidance on EU AI Act transparency obligations and link the primary sources.”
- “Find current sources comparing the leading open-source embedding models, with publication dates.”
- “Fact-check this claim with current web sources, and separate evidence from your conclusion.”

The server exposes Seltz's documented read-only tools for web search and page fetching. Codex reads the
live tool schema from the server; parameters and current limits are documented on the
[Seltz MCP page](https://docs.seltz.ai/integrations/mcp).

Preserve source URLs and publication dates. Treat search results as time-sensitive evidence, not as an
automatic guarantee of truth or completeness.

## Troubleshooting

- **401 / authentication failed:** reconnect through `/mcp` and sign in to Seltz again.
- **402 / empty balance:** the connected Seltz account has no remaining balance; top it up in the Seltz
  console, then retry.
- **403 / permission denied:** verify you connected the intended Seltz account.
- **429 or usage limit:** stop retrying, honor the server's retry interval, and check the Seltz plan.
- **Timeout or unavailable service:** retry once for a safe search; if it still fails, report that current
  Seltz data could not be retrieved.
- **Unexpected result shape:** preserve available source links and do not invent missing fields.

Queries are sent to Seltz. Avoid secrets, credentials, private identifiers, and unnecessary personal data.
Review Seltz's [Terms of Service](https://seltz.ai/terms) and [Privacy Policy](https://seltz.ai/privacy-policy)
before using or redistributing retrieved content.
