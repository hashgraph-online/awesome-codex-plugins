---
title: GoFrame MCP SSE Example
slug: /examples/httpserver/mcp-sse
keywords: [mcp, server-sent events, sse, goframe, model context protocol]
description: Demonstrates Model Context Protocol (MCP) server implementation using GoFrame with Server-Sent Events (SSE) for real-time AI model communication. This example showcases MCP server setup using SSE transport for server-to-client streaming, real-time event streaming for model outputs, persistent connections for continuous communication, event formatting and client reconnection handling, integration with AI models and agents, and efficient resource management. Features include SSE-based MCP transport, unidirectional streaming from server to client, automatic reconnection support, event-driven architecture, lightweight protocol implementation, and production-ready patterns. Ideal for building real-time AI agent interfaces, implementing streaming model responses without WebSocket complexity, creating chat and assistant applications, and enabling server-push notifications for model updates.
hide_title: true
---

# GoFrame MCP Example

This example demonstrates how to implement a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server using GoFrame's `ghttp` server and the `mark3labs/mcp-go` SDK.

## Prerequisites

- Go 1.20 or higher
- An MCP client (e.g., Claude Desktop, or an IDE extension)

## Installation

1. Initialize the module (if not already done):
   ```bash
   go mod tidy
   ```

2. Run the server:
   ```bash
   go run main.go
   ```

## Usage

The server exposes two endpoints:
- `GET /sse`: The Server-Sent Events endpoint for establishing the connection.
- `POST /message`: The endpoint for sending JSON-RPC messages.

### Connecting with Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "goframe-mcp": {
      "command": "go",
      "args": ["run", "path/to/your/project/httpserver/mcp/main.go"]
    }
  }
}
```

*Note: Since this example runs an HTTP server, you might need to use an MCP client that supports SSE, or use a bridge. However, the configuration above assumes you are running it as a local process. If you want to connect via HTTP (SSE), your client must support remote MCP connections.*

For direct SSE testing:
1. Start the server.
2. Connect to `http://localhost:8080/sse`.

## MCP client configuration

If your editor or tool supports defining MCP servers via a configuration file (for example, some IDE extensions or local test tools), you can create `.vscode/mcp.json` in the project root with the following example:

```json
{
  "servers": {
    "add": {
      "url": "http://localhost:8080/sse",
      "type": "http"
    }
  },
  "inputs": []
}
```

Notes:
- The key under `servers` (e.g. `add`) is the identifier used by the client.
- `url` should point to the SSE endpoint for this example: `http://localhost:8080/sse`.
- `type` indicates connection type; this example uses `http` (SSE).
- `inputs` is optional and can be used to predefine input payloads depending on the client.

Save the file and compatible clients can read it to connect to this example MCP server.


## Features

- **Tools**: Exposes an `add` tool that takes two numbers (`a` and `b`) and returns their sum.
- **Example**: From an MCP client you can send a calculation request, for example:

```
mcp add 1 and 1
```

The server will respond with:

```
Result: 1 + 1 = 2
```

## Code Structure

- `main.go`: Contains the server setup, tool registration, and route binding using `ghttp.WrapH`.
