# Hosted MCP use

Use the hosted server at `https://mcp.tweetapi.com/mcp`. It uses OAuth and is intended to keep the underlying TweetAPI key out of the client and conversation.

## Configure a client

Codex CLI:

```bash
codex mcp add tweetapi --url https://mcp.tweetapi.com/mcp
codex mcp login tweetapi
```

Claude Code:

```bash
claude mcp add --transport http --scope user tweetapi https://mcp.tweetapi.com/mcp
claude mcp login tweetapi
```

Cursor global MCP configuration:

```json
{
  "mcpServers": {
    "tweetapi": {
      "url": "https://mcp.tweetapi.com/mcp"
    }
  }
}
```

The repository-level `.mcp.json` provides equivalent plugin configuration for compatible hosts. Complete the OAuth flow when the host prompts for authorization.

## Start with documentation

Use a documentation-only prompt first:

> Find the current read-only TweetAPI endpoint and parameters for looking up a public user by username. Do not make a live data request.

This checks tool discovery without consuming data quota.

## Limit live lookups

Before invoking a live tool:

1. Confirm that the operation retrieves public data and has no side effect.
2. Tell the user the call consumes quota.
3. Request one result page only.
4. Make one live tool call by default.
5. Return any cursor and ask before fetching another page.

Never use MCP tools for posting, engagement, follows, profile changes, direct messages, login, billing, key management, administration, or internal operations.

## Handle authorization failures

If OAuth fails, direct the user to the TweetAPI dashboard and agent integration guide. Do not ask the user to paste an API key, Twitter cookie, password, token, or session value into the chat.

If the client does not support remote OAuth MCP servers, use a server-side REST integration. Do not put credentials in prompts or client configuration.
