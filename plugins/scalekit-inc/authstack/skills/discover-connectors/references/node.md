# Discover connectors — Node

Same default path as `SKILL.md`: name the connector from the live catalog or Scalekit MCP, page tools, print schemas, stop.

Use this file when the repo is Node. Do not run the Python samples in `SKILL.md`.

Env names: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL`; use `SCALEKIT_ENVIRONMENT_URL` here.

`filter.provider` is the connector identifier from the catalog or `search_connectors` (for example `GMAIL`). It is not the dashboard Connection Name. Never pass a `connector` field on `actions.*`.

If Scalekit MCP at https://mcp.scalekit.com is already connected, call `search_connectors` then `search_tools` (`summary=false`, page until the next token is empty) and skip the SDK loop.

## Step 2 — Init the SDK

If env vars are missing, collect them from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Put them in the project env file. Do not invent values.

```bash
npm install @scalekit-sdk/node dotenv
```

```typescript
import { ScalekitClient } from '@scalekit-sdk/node';
import 'dotenv/config';

const client = new ScalekitClient(
  process.env.SCALEKIT_ENVIRONMENT_URL!,
  process.env.SCALEKIT_CLIENT_ID!,
  process.env.SCALEKIT_CLIENT_SECRET!
);
```

**Done when:** the client initializes from those three env vars, and source files do not hardcode the secret.

## Step 3 — Page tools and schemas

Replace `'GMAIL'` with the identifier from Step 1. Page until `nextPageToken` is empty.

```typescript
let pageToken: string | undefined;
do {
  const page = await client.tools.listTools({
    filter: { provider: 'GMAIL' },
    pageSize: 100,
    pageToken,
  });
  for (const tool of page.tools) {
    const definition = tool.definition ?? {};
    console.log(definition.name, definition.description);
    console.log(definition.input_schema);
  }
  pageToken = page.nextPageToken || undefined;
} while (pageToken);
```

For one tool by name:

```typescript
const page = await client.tools.listTools({
  filter: { toolName: ['gmail_fetch_mails'] },
  pageSize: 1,
});
```

**Done when:** every page is collected, or the named tool's schema is printed. No tool was executed.
