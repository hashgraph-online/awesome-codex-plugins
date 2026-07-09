---
name: mcp-builder
description: Use when creating a new MCP (Model Context Protocol) server, extending an existing one, or debugging tool discoverability/performance. Guides through research → implementation → test → eval phases with TypeScript-first guidance matching our stack. Trigger on phrases like "build an MCP server", "expose X as an MCP tool", "write MCP tools for Y", "integrate Z via MCP".
model: sonnet
---

# MCP Server Development

Adapted from [anthropics/skills/mcp-builder](https://github.com/anthropics/skills/tree/main/skills/mcp-builder). MCP-server quality is measured by how well it lets LLMs accomplish real-world tasks — not by endpoint count.

## Stack default for our projects

- **Language:** TypeScript (matches our stack; static typing + Zod schemas + good LLM code-gen)
- **Transport:** `stdio` for local tools, **Streamable HTTP (stateless JSON)** for remote
- **SDK:** [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk)
- **Package manager:** pnpm (never npm/yarn in our repos)

## Phase 1 — Research & Plan

### 1.1 Design principles

**API coverage vs. workflow tools.** Balance comprehensive endpoint coverage with specialized workflow shortcuts. Default to coverage unless you have a clear reason — agents compose basic tools well; workflow tools ossify.

**Tool naming & discoverability.** Consistent prefix + action verb. Examples:
- `github_create_issue`, `github_list_repos`
- `gitlab_search_issues`, `gitlab_close_mr`

**Context management.** Return focused, paginated data. Agents suffer when a single tool call floods context.

**Actionable error messages.** Errors must guide the next action:

```
❌ "Invalid input"
✅ "Field 'project_id' is required. Call gitlab_list_projects to enumerate available IDs."
```

### 1.2 Read the spec

- Sitemap: `https://modelcontextprotocol.io/sitemap.xml`
- Append `.md` to any page URL for markdown (e.g. `https://modelcontextprotocol.io/specification/draft.md`)

Focus on: tool definitions, resource definitions, transport mechanisms.

### 1.3 Load SDK docs

- TS SDK README: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
- Python SDK README: `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`

Fetch via WebFetch only when needed — don't dump entire docs into context upfront.

### 1.4 Plan implementation

- Review the target service's API docs (auth, core endpoints, data models)
- List endpoints by priority — most-common operations first
- Identify destructive vs. read-only operations (matters for tool annotations)

## Tool-Hosting Pattern — In-Process vs Stdio MCP

Before writing a line of implementation code, choose a hosting pattern. The wrong choice cannot be refactored cheaply once tooling is wired.

### Decision tree

```
≤ 5 tools AND latency-critical (<50ms tool resolution)?
│
├─ Yes → tools share the SDK process AND no external auth required?
│        │
│        ├─ Yes → In-process @tool decorator (single-process, sub-ms resolution)
│        └─ No  → Stdio MCP Server
│
└─ No  → Stdio MCP Server
         (≥ 6 tools, external auth, language/runtime mismatch, long-lived process)
```

### In-process @tool decorator (Python — anthropics/claude-agent-sdk-python)

Use `create_sdk_mcp_server` when your tools live entirely inside the SDK process and you need the lowest possible latency. Source reference: [`examples/mcp_calculator.py` L11–99](https://github.com/anthropics/claude-agent-sdk-python/blob/main/examples/mcp_calculator.py).

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool(name="add", description="Add two numbers", input_schema={"a": int, "b": int})
async def add(args):
    return {"content": [{"type": "text", "text": str(args["a"] + args["b"])}]}

server = create_sdk_mcp_server(name="calc", version="1.0.0", tools=[add])
```

### In-process registration (TypeScript — @modelcontextprotocol/sdk)

Our default stack uses `McpServer.registerTool()` from `@modelcontextprotocol/sdk`. The inline Zod schema is parsed at registration time — no separate schema file needed for small tool sets.

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

const server = new McpServer({ name: 'calc', version: '1.0.0' });

server.registerTool(
  'add',
  {
    title: 'Add two numbers',
    inputSchema: { a: z.number(), b: z.number() },
  },
  async ({ a, b }) => ({
    content: [{ type: 'text', text: String(a + b) }],
  }),
);
```

### Tool annotations — `readOnlyHint` and `destructiveHint`

Annotations are first-class SDK metadata that Claude and downstream hooks use for permission decisions. Set them on every tool:

```typescript
server.registerTool(
  'delete-file',
  {
    title: 'Delete a file',
    inputSchema: { path: z.string() },
    annotations: { readOnlyHint: false, destructiveHint: true },
  },
  handler,
);
```

- **`readOnlyHint: true`** — signals the tool only reads state; Claude can call it freely without a permission prompt.
- **`destructiveHint: true`** — signals irreversible side effects; our `pre-bash-destructive-guard` hook and `agents/security-reviewer.md` both elevate review priority for tools carrying this flag. Any tool that deletes, overwrites, or mutates shared state must set this.
- Missing `destructiveHint: true` on a destructive tool is a known pitfall — see the "Common pitfalls" table below.

### Pattern comparison

| Aspect | In-Process @tool | Stdio MCP Server |
|--------|-----------------|------------------|
| Tool count | ≤ 5 | 6+ |
| Latency | Sub-ms resolution | 5–50 ms IPC overhead |
| Auth complexity | Shares SDK auth | Separate auth context |
| Language constraint | Must match SDK | Any runtime |
| Process isolation | None (in-SDK) | Full (separate child) |
| Lifecycle | Bound to SDK session | Long-lived independent |

For the **stdio MCP server** implementation path (≥ 6 tools, external auth, or language mismatch), continue with [Phase 2 — Implementation](#phase-2--implementation) below, which covers project structure, core infrastructure, and the full TypeScript stdio setup.

### Alternative: Token-Frugal CLI Driver for MCP-Only Capabilities

If a future capability is **MCP-only** (no good native CLI of its own), the token-frugal path skips full `.mcp.json` wiring:

- **Standalone CLI driver:** `mcporter generate-cli <server> --bundle` mints a schema-baked standalone CLI for one MCP server (real flags: `--compile`, `--bundler rolldown|bun`, `--output <path>`, `--include-tools <csv>` / `--exclude-tools <csv>`). A driver skill dispatches it via Bash, writes deterministic JSON to a run-dir, and the orchestrator parses from disk — never via prompt context, so token cost stays flat. This is the same pattern `skills/playwright-driver/SKILL.md` and `skills/peekaboo-driver/SKILL.md` already use (dispatch CLI → write AX-snapshot/JSON → parse from disk).
- **One-shot tool call:** `mcporter call <server>.<tool>` (also: `mcporter call --server <s> --tool <t> --args '{...}'`) invokes a single MCP tool without a standing `.mcp.json` entry — a concrete implementation of the projects-baseline **MCP-002** discipline ("no cargo-cult `.mcp.json`"). Note: MCP-002 is a baseline cross-repo reference, not a local mandate in this repo.

**MCPJungle context:** this repo's local MCP layer is `session-orchestrator` declared in `.mcp.json` (a bash-based server). Baseline MCP aggregation is **MCPJungle** (machine-level gateway, not wired here). mcporter is therefore an *alternative recipe for MCP-only drivers*, not a drop-in for MCPJungle — it is optional (`skills/repo-audit/SKILL.md` Category 9 already uses it with graceful-degrade). **Only reach for this pattern when a real MCP-only-driver need arises; this is a forward-looking planning note.**

## Phase 2 — Implementation

### 2.1 Project structure (TypeScript)

```
mcp-server-name/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts            (server entry, transport wiring)
│   ├── tools/              (one file per tool or tool group)
│   ├── schemas.ts          (shared Zod schemas)
│   └── client.ts           (API client with auth + error handling)
└── README.md               (setup + config)
```

### 2.2 Core infrastructure

Build once, reuse everywhere:
- API client with auth (env-var-driven, never hardcoded)
- Error-handler helper that returns actionable MCP error responses
- Pagination helper (most APIs paginate; most tools forget)
- Response formatter (JSON for structured, Markdown for human-readable where agents benefit from it)

### 2.3 Implement tools

For each tool:

**Input schema** — Zod, with descriptions per field:
```ts
z.object({
  projectId: z.string().describe("GitLab project ID. Call gitlab_list_projects to discover."),
  state: z.enum(["opened", "closed", "all"]).default("opened"),
});
```

**Output schema** — define `outputSchema` where possible; use `structuredContent` in tool responses (TS SDK feature). This helps downstream agents parse results.

**Annotations** — set all four:
- `readOnlyHint: true/false`
- `destructiveHint: true/false`
- `idempotentHint: true/false`
- `openWorldHint: true/false`

These inform Claude's hook decisions (destructive-guard, permission prompts).

**Implementation** — async/await for I/O; errors must surface with enough context for the LLM to fix them.

## Phase 3 — Review & Test

### 3.1 Code quality

- DRY — no duplicated API-call logic
- Consistent error handling (one helper, not ad-hoc throws)
- Full TypeScript coverage — `tsgo --noEmit` or `tsc --noEmit` clean
- Clear tool descriptions

### 3.2 Build & test

```bash
pnpm build              # or npm run build in non-pnpm projects
npx @modelcontextprotocol/inspector   # interactive testing UI
```

Walk through every tool in the Inspector. If a tool can fail, trigger the failure and verify the error message is actionable.

## Phase 4 — Evaluations

Create 10 evaluation questions. An MCP server without evals is a guess, not a deliverable.

Each question must be:
- **Independent** — doesn't depend on a previous question's answer
- **Read-only** — no destructive side effects
- **Complex** — requires multiple tool calls, not a single lookup
- **Realistic** — a real user would actually ask this
- **Verifiable** — has a single correct answer checkable by string comparison
- **Stable** — answer doesn't change over time

### Output format

```xml
<evaluation>
  <qa_pair>
    <question>Which GitLab project in group 'X' has the highest number of open issues labeled 'bug'?</question>
    <answer>project-name-here</answer>
  </qa_pair>
</evaluation>
```

Run the eval via: Claude-with-MCP-server on each question, compare output to expected answer. Any eval below 80% accuracy signals tool-design problems (usually: unclear descriptions, missing pagination, or bad error messages).

## Common pitfalls

| Pitfall | Fix |
|---------|-----|
| Tool returns 10k rows, agent context blows up | Add pagination + default page size |
| Agent can't figure out auth failure | Error message: "Set ENV_VAR_NAME — current value is empty" |
| Tool name collision across MCP servers | Always prefix with service name |
| Destructive tools without `destructiveHint: true` | Breaks our destructive-guard hook |
| Async errors swallowed | Wrap every handler in try/catch that returns structured error |

## References

Upstream reference material (worth reading once, not mirroring here):
- [MCP Best Practices](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/reference/mcp_best_practices.md)
- [TypeScript Implementation Guide](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/reference/node_mcp_server.md)
- [Python Implementation Guide](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/reference/python_mcp_server.md)
- [Evaluation Guide](https://github.com/anthropics/skills/blob/main/skills/mcp-builder/reference/evaluation.md)
