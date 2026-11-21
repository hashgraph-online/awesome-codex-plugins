# Hosted MCP

The hosted server is `https://mcp.tweetapi.com/mcp`. It requires OAuth: the user signs in to TweetAPI in the browser and picks the API key behind the connection. The key never reaches the MCP client or the chat, and a raw API key can't be used in place of the sign-in.

## Connect a client

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

Cursor, in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "tweetapi": {
      "url": "https://mcp.tweetapi.com/mcp"
    }
  }
}
```

Plugin hosts that read this repository's `.mcp.json` connect to the same server and ask the user to sign in.

To check the connection without spending units, ask for something from the docs:

> Find the current TweetAPI endpoint and parameters for looking up a public user by username. Don't make a live data request.

## Find the right tool

- `tweetapi_tool_catalog` lists every tool with its inputs, result formats, link inputs and estimated cost. Filter it by `toolName` or by `category`: `user`, `tweet`, `list`, `community`, `search`, `space`, `trends`, `account` or `docs`.
- The docs tools are free and make no API calls: `tweetapi_docs_search`, `tweetapi_endpoint_lookup`, `tweetapi_docs_get_page`, `tweetapi_sdk_guidance` and `tweetapi_tool_catalog`.
- Call only tools the client actually lists.

## Inputs

- Post, profile, list, community and Space fields accept x.com or twitter.com links, and username fields also accept @handles. When you pass one, the result's `resolvedInput` shows the ID or username the server used.
- Fields named `userId` need the numeric ID. If you only have a handle, look it up first with `tweetapi_user_by_username`, which is one more request.
- To read several users or posts, use a batch tool: `tweetapi_user_by_usernames` or `tweetapi_user_by_ids` (up to 100 users), or `tweetapi_tweet_details_by_ids` (up to 200 posts). Each is one request.
- `tweetapi_trends` takes `country`, such as `US`, or `woeid`, not both. Leave both out for worldwide trends. `tweetapi_trend_locations` lists the supported places.
- `tweetapi_account_usage` takes no inputs and costs nothing, but it counts toward the per-minute limit.

## Results

Every live result includes:

- `cost`: the estimated units, from the published pricing rules. It is not a billing record.
- `completeness`: whether this is a page, a batch or a single object, the next cursor, and anything requested but not returned. Read its `note`. For the next page, call the same tool again with `cursor` set to `completeness.nextCursor`.
- `retrievedAt`: when the server received the response. It is not the date of a post.
- `output`: the format, and which fields compact mode left out.

Pass `responseFormat: "compact"` when a tool offers it and you don't need every field. Compact keeps the full post text, IDs, links, original dates, counts and cursors, and never drops items. The default, `full`, returns TweetAPI's JSON unchanged.

Users that appear inside posts or lists can show `listedCount` 0, `isIdentityVerified` false and `verifiedSince` null, because X leaves those details out there. Fetch the profile when those fields matter.

## Errors

A failed tool call has `isError` set, and `error.details.layer` says where it failed:

- `mcp_input`: the input was invalid. Nothing was sent or billed.
- `mcp_connection`: there is no API key behind the connection.
- `tweetapi_api_key`: the sign-in worked, but TweetAPI didn't accept the key behind it, for example because it has no plan or balance. Signing in again with the same key won't help. The user can add a plan or balance in the TweetAPI dashboard, or reconnect and pick another key.
- `tweetapi_api`: TweetAPI answered with an error. On a 429, `details.reason` says whether it's the per-minute limit, which passes after `retryAfterSeconds`, or used-up units or an inactive plan, which waiting won't fix.
- `network`: the request failed or timed out, and it may or may not have been billed.

Problems with the sign-in itself show up as a sign-in prompt from the client. If signing in keeps failing, point the user to <https://tweetapi.com/docs/getting-started/agents>. If the client can't use remote OAuth servers, call the REST API from server code instead ([integration.md](integration.md)).
