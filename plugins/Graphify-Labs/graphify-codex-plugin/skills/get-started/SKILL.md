---
name: get-started
description: Sign in to Graphify and confirm the agent can list the repositories indexed in your workspace.
---

# Get started with Graphify

Graphify is already connected as an MCP server at `https://api.graphify.com/mcp`. Sign-in uses OAuth in the browser. There is no API key to paste.

1. If tools fail because the account is not signed in, complete the Graphify OAuth prompt.
2. Call `list_repositories` and show the repositories the workspace can access. If the tool fails, report the error instead of guessing.
3. If the list is empty, the user needs at least one repository with status Indexed in [Graphify](https://app.graphify.com). The [Codex setup guide](https://docs.graphify.com/integrations/codex) covers install, sign-in and common errors.
4. Once a repository is on the list, ask which one to explore first.

The hosted MCP serves the code graph, Memory and `review_status`. Wiki is in the Graphify app at [app.graphify.com](https://app.graphify.com), not over MCP.
