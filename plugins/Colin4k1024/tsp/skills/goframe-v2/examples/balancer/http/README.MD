---
title: HTTP Service
slug: /examples/balancer/http
keywords: [load balancer, http, service discovery, goframe]
description: Demonstrates HTTP service load balancing implementation using GoFrame with etcd-based service registration and discovery. This example showcases client-side load balancing with round-robin strategy, automatic service discovery, and distributed request routing across multiple HTTP server instances. Features include service registration using etcd, dynamic service discovery, configurable load balancing strategies, and seamless integration with GoFrame's HTTP server and client components for building scalable microservices architectures.
hide_title: true
---

# Load Balancer - HTTP Service Example

## Description

This example demonstrates how to implement HTTP service load balancing with `GoFrame`. It shows:
- Service registration using `etcd`
- Client-side load balancing
- Round-robin load balancing strategy
- HTTP service communication

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

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

1. Running `etcd` server:
   ```bash
   # Using docker
   docker run -d --name etcd-server \
      --publish 2379:2379 \
      --publish 2380:2380 \
      --env ALLOW_NONE_AUTHENTICATION=yes \
      bitnami/etcd:latest
   ```

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
   - Service registration with `etcd`
   - Simple HTTP endpoint that returns "Hello world"
   - Automatic service discovery registration

2. Client Implementation (`client/client.go`):
   - Service discovery using `etcd`
   - Round-robin load balancing strategy
   - Multiple request demonstration
   - Automatic service discovery and load balancing

## Notes

- The example uses `etcd` for service registration and discovery
- Round-robin load balancing is implemented for demonstration
- The client automatically handles service discovery and load balancing
- Multiple server instances can be started to demonstrate load distribution
