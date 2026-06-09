---
title: GoFrame MCP HTTP Example
slug: /examples/httpserver/mcp-http
keywords: [mcp, http, streaming, goframe, model context protocol]
description: Demonstrates Model Context Protocol (MCP) server implementation using GoFrame with HTTP streaming for AI model integration. This example showcases MCP server setup using HTTP transport, streaming response handling for real-time model outputs, protocol message encoding and decoding, context management and propagation, integration with AI models and services, and error handling for MCP operations. Features include HTTP-based MCP transport, streaming API support, efficient message serialization, context sharing between requests, extensible protocol handlers, and production-ready patterns. Ideal for building AI agent backends, integrating language models with applications, implementing streaming AI responses, and creating MCP-compliant services for model context sharing.
hide_title: true
---

# GoFrame MCP HTTP Example

This example demonstrates how to implement a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server using GoFrame's `ghttp` server and the `mark3labs/mcp-go` SDK through HTTP streaming.

## Prerequisites

- Go 1.20 or higher
- MCP client (e.g., Claude Desktop or IDE extension)

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

The server exposes a single endpoint:
- `POST /mcp`: HTTP endpoint for handling MCP JSON-RPC messages.

### Connect to Claude Desktop

To use this MCP server in Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "goframe-mcp": {
      "command": "go",
      "args": ["run", "path/to/your/project/httpserver/mcp-http/main.go"]
    }
  }
}
```

*Note: This example uses HTTP streaming (StreamableHTTP), handling all MCP communication through a single HTTP endpoint.*

### Direct HTTP Testing

1. Start the server.
2. Send a POST request to `http://localhost:8080/mcp`.

Example request:
```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "client",
        "version": "1.0.0"
      }
    }
  }'
```

## MCP Client Configuration

If your client or IDE supports defining MCP servers through a configuration file, you can create a `.vscode/mcp.json` in your project root with the following example content:

```json
{
  "servers": {
    "add": {
      "url": "http://localhost:8080/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

Explanation:
- The key under `servers` (e.g., `add`) is the server identifier name.
- `url` points to the HTTP endpoint of the example: `http://localhost:8080/mcp`.
- `type` indicates the connection type, in this case `http` (HTTP streaming).
- `inputs` is optional and can be used to preset inputs in the client.

After saving, clients that support this configuration can use this file to connect to the MCP service.

## Features

- **Tool**: Exposes an `add` tool that accepts two numbers (`a` and `b`) and returns their sum.
- **Example**: You can send a calculation request through the MCP client:

```
mcp calculate one plus one
```

Or in Chinese:
```
mcp 计算 一加一
```

The server will return:
```
Result: 1 + 1 = 2
```

## Code Structure

- `main.go`: Contains server setup, tool registration, and route binding using `ghttp.WrapH`.

## StreamableHTTP vs SSE Comparison

| Feature | StreamableHTTP | SSE |
|---------|----------------|-----|
| Protocol | HTTP 1.1+ | HTTP (Server-Sent Events) |
| Connection | Single POST endpoint | Separate GET (SSE) and POST endpoints |
| Streaming | Supported | Supported |
| Client Implementation | Simpler | Requires event stream handling |
| Browser Support | Standard HTTP | Requires EventSource API |
| Integration | Suitable for API gateways | Suitable for real-time push scenarios |

StreamableHTTP provides a cleaner way to implement MCP communication by handling all requests and responses through a single HTTP endpoint, making it easier to integrate into existing HTTP service architectures.
