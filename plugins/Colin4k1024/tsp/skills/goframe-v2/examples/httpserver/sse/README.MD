---
title: Server-Sent Events(SSE)
slug: /examples/httpserver/sse
keywords: [http, server, sse, server-sent events, streaming, goframe]
description: Demonstrates Server-Sent Events (SSE) implementation using GoFrame for real-time server-to-client streaming. This example showcases SSE server setup with persistent connections, event stream formatting with data, event types and IDs, automatic client reconnection handling with Last-Event-ID, sending real-time updates and notifications, proper content-type and headers configuration, and connection lifecycle management. Features include unidirectional streaming from server to client, automatic reconnection support, event-driven architecture, lightweight compared to WebSocket, heartbeat and keepalive support, and production-ready patterns. Ideal for building real-time notifications and updates, implementing live dashboards and monitoring, creating chat and messaging features, enabling server push without WebSocket, and building event-driven applications.
hide_title: true
---

# Server-Sent Events(SSE)

## Description

This example demonstrates how to implement Server-Sent Events (SSE) using `GoFrame`. Server-Sent Events is a technology that allows a server to push updates to a client via `HTTP` connection. Unlike `WebSocket`, `SSE` is unidirectional - only the server can send data to the client.

The example implements a simple `SSE` server that streams responses character by character, simulating a real-time typing effect commonly seen in modern AI chat applications.

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

```text
- go.mod: The Go module file.
- main.go: The main application entry point with SSE implementation.
```

## Features

- Server-Sent Events implementation
- Character-by-character streaming response for simulated AI chat
- Proper HTTP headers for SSE

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/sse
    ```

2. Install the dependencies:
    ```bash
    go mod tidy
    ```

3. Run the application:
    ```bash
    go run main.go
    ```

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. The server will start at: http://127.0.0.1:8000

3. Access the SSE endpoint:
   - In a browser, navigate to: http://127.0.0.1:8000/ai/chat
   - You should see words appearing one by one with a typing effect



## Implementation Details

The SSE implementation includes:

- Setting the correct HTTP headers for SSE:
  - `Content-Type: text/event-stream`
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`

- Streaming response with proper flushing
- Simulated typing delay using `time.Sleep`
- Simple HTTP routing with GoFrame's router

## Notes

- `SSE` connections remain open until explicitly closed by the client
- The server must flush the response buffer after each message
- For production use, consider implementing reconnection logic and event IDs
- `SSE` works over regular `HTTP/HTTPS` and supports automatic reconnection in browsers