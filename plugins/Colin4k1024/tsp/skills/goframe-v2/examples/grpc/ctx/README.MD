---
title: Context Usage
slug: /examples/grpc/ctx
keywords: [grpc, context, metadata, goframe]
description: Demonstrates advanced context and metadata management in gRPC services using GoFrame for request tracking and data propagation. This example showcases how to pass metadata through gRPC context for cross-cutting concerns, handle context values and deadlines for request cancellation, manage request context across service boundaries, process and extract context metadata, implement distributed tracing integration, and propagate authentication tokens and correlation IDs. Features include metadata injection and extraction, context timeout and cancellation handling, custom metadata keys and values, interceptor-based metadata processing, distributed tracing support, and request correlation patterns. Perfect for implementing observability in microservices, tracking requests across distributed systems, implementing authentication and authorization, managing request timeouts and cancellation, and building production-ready gRPC services with proper context management.
hide_title: true
sidebar_position: 1
---

# `gRPC` - Context Usage

## Description

This example demonstrates how to use context and metadata in `gRPC` with `GoFrame`. It shows how to:
- Pass metadata through `gRPC` context
- Handle context values and deadlines
- Manage request context
- Process context metadata

## Structure

```text
.
├── client/           # Client example
│   └── client.go     # Client implementation with context
├── controller/       # Service controllers
│   └── helloworld.go # Hello service with context handling
├── protobuf/         # Protocol buffer definitions
├── server/           # Server example
│   ├── config.yaml   # Server configuration
│   └── server.go     # Server implementation
├── go.mod            # Go module file
└── go.sum            # Go module checksums
```

## Features

The example showcases the following features:
1. Context Management
   - Metadata handling
   - Value propagation
   - Deadline management
   - Cancellation handling

2. Client Usage
   - Context creation
   - Metadata attachment
   - Context values
   - Timeout configuration

3. Server Features
   - Context extraction
   - Metadata processing
   - Value retrieval
   - Timeout handling

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [gRPC](https://grpc.io/docs/languages/go/quickstart/)

## Prerequisites

1. Protocol buffer compiler installed:
   ```bash
   # For macOS
   brew install protobuf
   
   # Install protoc-gen-go and protoc-gen-go-grpc
   go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
   ```

# Usage

1. Generate protocol buffer code:
   ```bash
   cd protobuf
   protoc --go_out=paths=source_relative:. --go-grpc_out=paths=source_relative:. *.proto
   ```

2. Start the server:
   ```bash
   cd server
   go run server.go
   ```

3. Run the client:
   ```bash
   cd client
   go run client.go
   ```

# Implementation Details

The example demonstrates:
1. Context propagation in `gRPC`
2. Metadata handling with `GoFrame`
