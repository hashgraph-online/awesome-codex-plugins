---
title: Polaris Integration
slug: /examples/balancer/polaris
keywords: [load balancer, polaris, service discovery, goframe]
description: Demonstrates HTTP service load balancing implementation using GoFrame integrated with Polaris service mesh platform. This example showcases service registration and discovery using Polaris, client-side load balancing with round-robin strategy, local cache configuration for improved performance, and centralized logging. Features include Polaris-based service registry, configurable TTL (Time To Live) for service heartbeat, automatic service discovery, dynamic request routing, and seamless integration with GoFrame's HTTP server and client components for building cloud-native microservices architectures with advanced traffic management capabilities.
hide_title: true
---

# Load Balancer - `Polaris` Integration Example

## Description

This example demonstrates how to implement HTTP service load balancing with `GoFrame` using `Polaris`. It shows:
- Service registration using `Polaris`
- Client-side load balancing
- Round-robin load balancing strategy
- HTTP service communication
- Local cache and logging configuration

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Polaris Registry](https://github.com/gogf/gf/tree/master/contrib/registry/polaris)

## Structure

```text
.
├── client/           # HTTP client implementation with load balancing
│   └── client.go     # Client code with round-robin balancer
├── server/           # HTTP server implementation
│   └── server.go     # Server code with service registration
├── go.mod            # Go module file
└── go.sum            # Go module checksums
```

## Prerequisites

1. Running `Polaris` server:
   ```bash
   # Using docker
   docker run -d --name polaris \
      -p 8090:8090 -p 8091:8091 -p 8093:8093 -p 9090:9090 -p 9091:9091 \
      polarismesh/polaris-standalone:v1.17.2
   ```

## Configuration

The example uses the following `Polaris` configurations:
- Server address: `127.0.0.1:8091`
- Local cache directory: `<TempDir>/polaris/backup`
- Log directory: `<TempDir>/polaris/log`
- Service TTL: 10 seconds

## Usage

1. Start multiple server instances (use random different ports):
   ```bash
   # Terminal 1
   cd server
   go run server.go

   # Terminal 2
   cd server
   go run server.go

   # Terminal 3
   cd server
   go run server.go
   ```

2. Run the client to test load balancing:
   ```bash
   cd client
   go run client.go
   ```

## Implementation Details

1. Server Implementation (`server/server.go`):
   - HTTP server setup using `GoFrame`
   - Service registration with `Polaris`
   - Simple HTTP endpoint that returns "Hello world"
   - Automatic service discovery registration
   - Configurable TTL for service registration

2. Client Implementation (`client/client.go`):
   - Service discovery using `Polaris`
   - Round-robin load balancing strategy
   - Multiple request demonstration with timing information
   - Automatic service discovery and load balancing
   - Local cache and logging configuration

## Notes

- The example uses `Polaris` for service registration and discovery
- Round-robin load balancing is implemented for demonstration
- The client automatically handles service discovery and load balancing
- Local cache is used to improve performance
- Logging is configured for better debugging
