# Expose AgentKit over MCP — Node

Same path as `SKILL.md`: create the MCP config once → print auth links → mint a session token per run → one Streamable HTTP client call.

Use this file when the repo is Node. Do not run the Python samples in `SKILL.md`. Docs: https://docs.scalekit.com/agentkit/mcp/configure-mcp-server/ and https://docs.scalekit.com/agentkit/mcp/session-tokens/

Env names: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`.

Field names are `connectionName` and `connectionToolMappings`. Never pass a `connector` field.

## Step 2 — Init the SDK

```bash
npm install @scalekit-sdk/node @modelcontextprotocol/sdk dotenv
```

```typescript
import 'dotenv/config';
import { ScalekitClient } from '@scalekit-sdk/node';

const scalekit = new ScalekitClient(
  process.env.SCALEKIT_ENVIRONMENT_URL!,
  process.env.SCALEKIT_CLIENT_ID!,
  process.env.SCALEKIT_CLIENT_SECRET!,
);
const mcp = scalekit.actions.mcp;
```

**Done when:** the client initializes from those three env vars, and source files do not hardcode the secret.

## Step 3 — Create the MCP config

Replace `'gmail'` and `'MY_CALENDAR'` with the recorded Connection Names. Create the config once. Reuse `configId` and `mcpServerUrl`.

```typescript
const { config } = await mcp.createConfig({
  name: 'reminder-manager',
  description: 'Summarizes latest email and creates a reminder event',
  connectionToolMappings: [
    { connectionName: 'gmail', tools: ['gmail_fetch_mails'] },
    { connectionName: 'MY_CALENDAR', tools: ['googlecalendar_create_event'] },
  ],
});
const configId = config!.id;
const mcpServerUrl = config!.mcpServerUrl;
if (!mcpServerUrl) throw new Error('mcpServerUrl is empty. Check the environment has Virtual MCP enabled.');
console.log('MCP server URL:', mcpServerUrl);
```

**Done when:** `configId` and a non-empty static `mcpServerUrl` exist.

## Step 4 — Print auth links if needed

Replace `'user_123'` with the project's user id.

```typescript
const { connectedAccounts } = await mcp.listConnectedAccounts({
  configId,
  identifier: 'user_123',
  includeAuthLink: true,
});
for (const a of connectedAccounts) {
  if (a.connectedAccountStatus !== 'ACTIVE') {
    console.log(`${a.connectionName} is ${a.connectedAccountStatus}: ${a.authenticationLink}`);
  }
}
```

Tell the user to open every printed auth link and finish OAuth. A non-interactive run stops here until they do.

**Done when:** each mapped connection is `ACTIVE`, or every needed auth link is printed.

## Step 5 — Mint a session token and call over Streamable HTTP

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';

const session = await mcp.createSessionToken({
  mcpConfigId: configId,
  identifier: 'user_123',
  expirySeconds: 60 * 60,
});

const transport = new StreamableHTTPClientTransport(new URL(mcpServerUrl), {
  requestInit: { headers: { Authorization: `Bearer ${session.token}` } },
});
const mcpClient = new Client({ name: 'reminder-manager', version: '1.0.0' });
await mcpClient.connect(transport);
const { tools } = await mcpClient.listTools();
console.log(tools.map((tool) => tool.name));
await mcpClient.close();
```

Mint a new token before the next run. `expirySeconds` must be between 60 and 86400.

**Done when:** the Streamable HTTP client lists the mapped tools with the session token.
