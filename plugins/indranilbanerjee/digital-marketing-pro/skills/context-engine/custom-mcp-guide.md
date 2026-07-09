# Custom MCP Integration Guide — Adding & Building MCP Servers

## What MCPs Are

Model Context Protocol (MCP) servers connect Claude to external services. Each MCP provides **tools** (functions Claude can call), **resources** (data Claude can read), and **prompts** (pre-defined interaction templates). MCP servers run as separate processes that communicate with Claude via JSON-RPC over stdin/stdout.

In this plugin, MCPs are the execution bridge between the agent layer (Claude reasoning about marketing strategy) and external platforms (publishing a blog post, sending an email campaign, querying a CRM). The 67 MCP servers configured in `.mcp.json` cover social publishing, email, CRM, analytics, memory, knowledge, CMS, communication, project management, testing, and databases.

---

## How MCPs Work in This Plugin

### Configuration

The `.mcp.json` file in the plugin root defines all MCP server configurations. Claude discovers available MCPs at session start and can call their tools during a session.

**`.mcp.json` schema:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": {
        "API_KEY": "${ENV_VAR_NAME}"
      },
      "description": "What this server provides"
    }
  }
}
```

### Key Mechanics

- **`command`**: The executable to run — typically `npx` (for npm packages), `node` (for local scripts), or `python` (for Python-based MCPs)
- **`args`**: Arguments passed to the command — package name for npx, file path for node/python
- **`env`**: Environment variables injected into the MCP process — use `${VAR_NAME}` syntax to reference variables from `.env` or the shell environment
- **`description`**: Human-readable explanation that helps Claude understand when to use this MCP

### How Claude Uses MCPs at Runtime

1. **Session start:** Claude reads `.mcp.json` and starts configured MCP servers
2. **Tool discovery:** Claude calls `tools/list` on each server to learn available tools
3. **Tool invocation:** During conversation, Claude calls MCP tools by name with JSON parameters
4. **Safety gate:** The `hooks.json` `PreToolUse` hook intercepts all `mcp_.*` tool calls and checks whether the operation is a write (requires user approval) or read (auto-approved)
5. **Response:** MCP server executes the operation and returns results to Claude

---

## Adding an Existing MCP Package

### Step-by-Step

1. **Identify the service** you want to connect (e.g., Mailchimp, HubSpot, Airtable)

2. **Search for existing MCP packages:**
   ```bash
   npx -y @anthropic-ai/mcp search <service-name>
   ```
   Also check: https://github.com/modelcontextprotocol/servers and npm for `mcp-server-*` or `@*/mcp` packages

3. **Test the package locally:**
   ```bash
   npx -y <package-name> --help
   ```

4. **Add to `.mcp.json`:**
   ```json
   {
     "mcpServers": {
       "mailchimp": {
         "command": "npx",
         "args": ["-y", "mcp-server-mailchimp"],
         "env": {
           "MAILCHIMP_API_KEY": "${MAILCHIMP_API_KEY}",
           "MAILCHIMP_SERVER_PREFIX": "${MAILCHIMP_SERVER_PREFIX}"
         },
         "description": "Mailchimp email marketing — list management, campaign creation, audience segmentation"
       }
     }
   }
   ```

5. **Add credentials to `.env`:**
   ```
   MAILCHIMP_API_KEY=your-api-key-here
   MAILCHIMP_SERVER_PREFIX=us14
   ```

6. **Verify connectivity:** Start a new Claude session and ask Claude to list available tools from the new MCP

7. **Document:** Update `docs/integrations-guide.md` with the new integration

### Pre-Flight Checklist

- [ ] MCP package exists and is actively maintained (check npm downloads + last publish date)
- [ ] Package version is stable (avoid 0.x.x for production use unless no alternative)
- [ ] Required credentials are available (API key, OAuth tokens, etc.)
- [ ] Credentials added to `.env` with correct variable names
- [ ] `.mcp.json` entry uses `${VAR}` syntax for all secrets (never hardcode credentials)
- [ ] Server starts without error in a new session
- [ ] `tools/list` returns expected tools
- [ ] Read operations return valid data
- [ ] Write operations trigger the approval hook correctly

---

## Environment Variable Conventions

### Naming Standards

| Type | Pattern | Example |
|---|---|---|
| **API Key** | `{SERVICE}_API_KEY` | `MAILCHIMP_API_KEY`, `HUBSPOT_API_KEY` |
| **Base URL** | `{SERVICE}_URL` | `ODOO_URL`, `CUSTOM_API_URL` |
| **OAuth Client ID** | `{SERVICE}_CLIENT_ID` | `GOOGLE_CLIENT_ID`, `META_CLIENT_ID` |
| **OAuth Client Secret** | `{SERVICE}_CLIENT_SECRET` | `GOOGLE_CLIENT_SECRET` |
| **Access Token** | `{SERVICE}_ACCESS_TOKEN` | `SLACK_ACCESS_TOKEN`, `NOTION_ACCESS_TOKEN` |
| **Server/Region** | `{SERVICE}_SERVER_PREFIX` | `MAILCHIMP_SERVER_PREFIX`, `AWS_REGION` |
| **Database** | `{SERVICE}_DB_NAME` | `POSTGRES_DB_NAME`, `MONGO_DB_NAME` |

### Storage Rules

- **All credentials** go in `.env` at the project root — never in `.mcp.json`, never in scripts, never committed to git
- **`.env` is gitignored** — verify this before any commit
- **Agency mode:** Per-client credentials stored at `~/.claude-marketing/credentials/{profile-name}.json` (see Credential Profiles section below)
- **Rotation:** Rotate API keys quarterly. Use short-lived tokens (OAuth) where possible.

---

## Building a Custom MCP Server

When no existing package covers your service, build a custom MCP server.

### Project Setup

```bash
mkdir mcp-server-yourservice
cd mcp-server-yourservice
npm init -y
npm install @modelcontextprotocol/sdk zod
```

### Minimal Server Template

```javascript
#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "yourservice",
  version: "1.0.0",
  description: "MCP server for YourService — describe what it provides",
});

// --- Read Tool (auto-approved by hooks.json) ---
server.tool(
  "list_items",
  "List all items from YourService",
  { status: z.enum(["active", "archived", "all"]).optional() },
  async ({ status }) => {
    const response = await fetch(`${process.env.YOURSERVICE_URL}/api/items?status=${status || "active"}`, {
      headers: { "Authorization": `Bearer ${process.env.YOURSERVICE_API_KEY}` },
    });
    const data = await response.json();
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// --- Write Tool (requires approval via hooks.json) ---
server.tool(
  "create_item",
  "Create a new item in YourService",
  { name: z.string(), description: z.string().optional() },
  async ({ name, description }) => {
    const response = await fetch(`${process.env.YOURSERVICE_URL}/api/items`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${process.env.YOURSERVICE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, description }),
    });
    const data = await response.json();
    return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
  }
);

// --- Start Server ---
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Adding to `.mcp.json` (Local Server)

```json
{
  "mcpServers": {
    "yourservice": {
      "command": "node",
      "args": ["path/to/mcp-server-yourservice/index.js"],
      "env": {
        "YOURSERVICE_URL": "${YOURSERVICE_URL}",
        "YOURSERVICE_API_KEY": "${YOURSERVICE_API_KEY}"
      },
      "description": "YourService integration — item management, data queries"
    }
  }
}
```

---

## Naming Conventions

### Server Naming

| Item | Convention | Example |
|---|---|---|
| **`.mcp.json` key** | lowercase-kebab-case, matching service | `"mailchimp"`, `"google-sheets"`, `"hubspot-crm"` |
| **npm package** | `mcp-server-{service}` or `@scope/mcp-server-{service}` | `mcp-server-mailchimp`, `@company/mcp-server-crm` |
| **Tool names** | `{action}_{noun}` — verb_object pattern | `list_campaigns`, `create_contact`, `send_email`, `get_report` |
| **Resource URIs** | `{service}://{resource-type}/{id}` | `mailchimp://lists/abc123`, `hubspot://contacts/456` |

### Tool Naming for Read vs Write Classification

The `hooks.json` safety gate classifies tools as read or write based on their name prefix:

| Prefix | Classification | Approval Required |
|---|---|---|
| `list_`, `get_`, `query_`, `search_`, `fetch_`, `count_` | **Read** | No (auto-approved) |
| `create_`, `update_`, `delete_`, `send_`, `publish_`, `schedule_`, `import_`, `sync_` | **Write** | Yes (user must approve) |

**Always name your tools using these prefixes** so the safety gate works correctly. If a tool has side effects, use a write prefix even if it also reads data.

---

## Common Integration Patterns

### Pattern 1: REST API Wrapper (Most Common)

Map REST endpoints directly to MCP tools:

| REST Endpoint | MCP Tool | Type |
|---|---|---|
| `GET /api/contacts` | `list_contacts` | Read |
| `GET /api/contacts/:id` | `get_contact` | Read |
| `POST /api/contacts` | `create_contact` | Write |
| `PUT /api/contacts/:id` | `update_contact` | Write |
| `DELETE /api/contacts/:id` | `delete_contact` | Write |
| `GET /api/contacts/search?q=` | `search_contacts` | Read |

**Pagination:** Implement cursor-based pagination within the tool. Accept `page` or `cursor` parameter, return results + next cursor.

### Pattern 2: GraphQL Wrapper

For GraphQL APIs, create a single flexible query tool plus specific mutation tools:

- `query_data` — accepts GraphQL query string, returns results (read)
- `create_record` — specific mutation with typed inputs (write)
- `update_record` — specific mutation with typed inputs (write)

### Pattern 3: Webhook Receiver

For event-driven integrations:
- Register webhooks via a `register_webhook` tool (write, one-time setup)
- MCP server listens for incoming events and surfaces them as resources
- Claude reads events via `get_recent_events` tool (read)

### Pattern 4: Database Connector

- `query_database` — parameterized SQL/NoSQL query (read)
- `insert_record` / `update_record` — typed data mutations (write)
- **Always default to read-only.** Write access should require explicit configuration.

---

## Credential Profiles for Agency Mode

In agency mode, different clients use different credentials for the same services (e.g., each client has their own Mailchimp account).

### Profile Structure

Stored at `~/.claude-marketing/credentials/{profile-name}.json`:

```json
{
  "profile_name": "acme-corp",
  "created_at": "2026-01-15T10:00:00Z",
  "credentials": {
    "mailchimp": {
      "MAILCHIMP_API_KEY": "key-us14-abc123",
      "MAILCHIMP_SERVER_PREFIX": "us14"
    },
    "hubspot": {
      "HUBSPOT_API_KEY": "pat-na1-xyz789"
    },
    "google-analytics": {
      "GA_PROPERTY_ID": "123456789"
    }
  }
}
```

### How Profile Switching Works

1. User runs `/digital-marketing-pro:credential-switch --profile acme-corp`
2. `credential-manager.py` loads the profile JSON
3. Environment variables are injected for the session
4. MCP servers restart with the new credentials
5. All subsequent MCP calls use the client's accounts

### Security Rules for Profiles

- [ ] Profile files are stored outside the plugin directory (in `~/.claude-marketing/`)
- [ ] Profile files are never committed to git
- [ ] Each profile only contains credentials for services that client uses
- [ ] API keys in profiles are encrypted at rest (if using `credential-manager.py` encryption feature)
- [ ] Profile access is logged — `credential-manager.py` records which profile was loaded and when

---

## Testing a New MCP Integration

### Testing Checklist

| Test | How to Verify | Pass Criteria |
|---|---|---|
| **Server starts** | Start new Claude session, check for errors | No startup errors in console |
| **Tool discovery** | Ask Claude "What tools are available from [server]?" | Expected tools appear in list |
| **Read operations** | Call a list/get tool with known data | Returns valid, formatted data |
| **Write operations** | Attempt a create/update tool | Approval hook fires, then operation succeeds |
| **Missing credentials** | Remove API key from `.env`, restart | Clear error message, not a crash |
| **Invalid credentials** | Use wrong API key | Structured error response, not a crash |
| **Rate limiting** | Rapid successive calls (if safe to test) | Graceful error with retry guidance |
| **Large responses** | Query that returns 100+ items | Paginated or truncated cleanly |
| **Error handling** | Invalid input parameters | Structured error with field-level detail |

### Debugging

- **MCP server logs:** Check stderr output from the MCP process for error traces
- **Network issues:** Verify the API base URL and that outbound requests are not blocked
- **Auth failures:** Confirm the env var name in `.mcp.json` exactly matches the var name in `.env`
- **Tool not appearing:** Verify the server key in `.mcp.json` is valid JSON and the tool is registered before `server.connect()`

---

## Security Considerations

### Credential Safety

- **Never** store credentials directly in `.mcp.json` — always use `${VAR}` references
- **Never** log API keys or tokens in MCP server output
- **Rotate** API keys quarterly at minimum, immediately if compromised
- **Scope** API keys to minimum required permissions (read-only where possible)
- **Audit** MCP tool calls via execution logs (`execution-tracker.py` logs all tool invocations)

### Access Control

- The `hooks.json` `PreToolUse` hook for `mcp_.*` is the primary safety gate
- Read tools (list, get, query, search, fetch) are auto-approved
- Write tools (create, update, delete, send, publish, schedule) require explicit user approval
- Custom MCPs **must** follow the naming convention so the hook classifies them correctly
- If a tool performs both read and write operations, classify it as write (use a write prefix)

### Supply Chain

- Prefer well-maintained MCP packages with 1,000+ npm weekly downloads
- Pin package versions in production (avoid `latest` tag)
- Review package source code before deploying, especially for packages with `< 100` downloads
- For sensitive integrations (CRM, payment, auth), build custom MCPs rather than using third-party packages

---

## Example Configurations

### Odoo ERP (REST/JSON-RPC)

```json
{
  "odoo": {
    "command": "node",
    "args": ["path/to/mcp-server-odoo/index.js"],
    "env": {
      "ODOO_URL": "${ODOO_URL}",
      "ODOO_DB": "${ODOO_DB}",
      "ODOO_USERNAME": "${ODOO_USERNAME}",
      "ODOO_API_KEY": "${ODOO_API_KEY}"
    },
    "description": "Odoo ERP — contacts, invoices, products, sales orders"
  }
}
```

### Generic REST API

```json
{
  "custom-api": {
    "command": "node",
    "args": ["path/to/mcp-server-rest/index.js"],
    "env": {
      "REST_BASE_URL": "${CUSTOM_API_URL}",
      "REST_API_KEY": "${CUSTOM_API_KEY}",
      "REST_AUTH_TYPE": "bearer"
    },
    "description": "Custom REST API — generic CRUD operations against your API"
  }
}
```

### Zapier Webhooks

```json
{
  "zapier": {
    "command": "npx",
    "args": ["-y", "mcp-server-zapier"],
    "env": {
      "ZAPIER_NLA_API_KEY": "${ZAPIER_NLA_API_KEY}"
    },
    "description": "Zapier Natural Language Actions — trigger Zaps, connect 5000+ apps"
  }
}
```

> **Key principle:** Every MCP integration should be tested with both valid and invalid credentials, should handle errors gracefully with structured responses, and should follow the read/write naming convention so the safety gate works automatically. When in doubt, classify a tool as write — it is always safer to require approval than to allow unintended side effects.
