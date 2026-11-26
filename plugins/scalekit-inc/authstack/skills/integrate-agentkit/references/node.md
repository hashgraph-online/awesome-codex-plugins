# Integrate AgentKit — Node

Same default path as `SKILL.md`: **connection** → **connected account** → authorization link if not `ACTIVE` → re-check status → one `executeTool` call.

Use this file when the repo is Node. Do not run the Python samples in `SKILL.md`. Docs: https://docs.scalekit.com/agentkit/quickstart/

Env names: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`. Some samples use `SCALEKIT_ENV_URL`; use `SCALEKIT_ENVIRONMENT_URL` here.

Field name is `connectionName`. Never pass a `connector` field.

`status` is the numeric `ConnectorStatus` enum, not a string. Compare it to `ConnectorStatus.ACTIVE`, imported from `@scalekit-sdk/node`.

Confirm a tool name on the connector's page in https://docs.scalekit.com/agentkit/connectors.md, or with `actions.listTools`, before you call it.

## Step 2 — Init the SDK

If env vars are missing, collect them from [app.scalekit.com](https://app.scalekit.com) → Developers → Settings → API Credentials. Put them in the project env file. Do not invent values.

```bash
npm install @scalekit-sdk/node dotenv
```

```typescript
import 'dotenv/config';
import { ConnectorStatus, ScalekitClient } from '@scalekit-sdk/node';

const scalekit = new ScalekitClient(
  process.env.SCALEKIT_ENVIRONMENT_URL!,
  process.env.SCALEKIT_CLIENT_ID!,
  process.env.SCALEKIT_CLIENT_SECRET!,
);
const actions = scalekit.actions;
```

**Done when:** the client initializes from those three env vars, and source files do not hardcode the secret.

## Step 3 — Create the connected account

Replace `'user_123'` with the project's stable user id. Replace `'github-connect'` with the recorded Connection Name.

```typescript
const connectionName = 'github-connect';
const userId = 'user_123';

let { connectedAccount: account } = await actions.getOrCreateConnectedAccount({
  connectionName,
  identifier: userId,
});
```

**Done when:** a connected account exists for that identifier and Connection Name.

## Step 4 — Authorize, then re-check status

If `account?.status` is `ConnectorStatus.ACTIVE`, skip this step.

Put the `readline` import at the top of the file.

```typescript
import { createInterface } from 'node:readline/promises';

if (account?.status !== ConnectorStatus.ACTIVE) {
  const { link } = await actions.getAuthorizationLink({ connectionName, identifier: userId });
  console.log(`Open this link and approve access:\n${link}`);
  if (!process.stdin.isTTY) {
    console.log('Finish OAuth in a browser, then run this script again.');
    process.exit(0);
  }
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  await rl.question("Press Enter when you're done...");
  rl.close();

  ({ connectedAccount: account } = await actions.getConnectedAccount({
    connectionName,
    identifier: userId,
  }));
  if (account?.status !== ConnectorStatus.ACTIVE) {
    throw new Error('The account is not ACTIVE yet. Run the script again.');
  }
}
```

In a web app, redirect the browser to `link`, then check the status again when the user returns.

**Done when:** status is `ConnectorStatus.ACTIVE` after the re-check, or the link is printed and a non-interactive run has stopped.

## Step 5 — Call one tool

Default: `github_user_get_authenticated`, a read-only GitHub tool with no input.

```typescript
const result = await actions.executeTool({
  toolName: 'github_user_get_authenticated',
  toolInput: {},
  connectedAccountId: account!.id,
});
console.log(result.data);
```

For another connector, list the tools on that connection and pick a read-only one:

```typescript
const { toolNames } = await actions.listTools({
  connectionName,
  identifier: userId,
  pageSize: 100,
});
console.log(toolNames);
```

Change only `toolName` and `toolInput` in Step 5. Keep Steps 3–4.

**Done when:** one `executeTool` call returns data for the connected account.
