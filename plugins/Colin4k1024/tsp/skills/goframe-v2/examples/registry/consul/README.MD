---
title: Consul
slug: /examples/registry/consul
keywords: [registry, consul, service discovery, goframe]
description: Demonstrates comprehensive HashiCorp Consul service registry integration with GoFrame for enterprise-grade service discovery and health monitoring. This example showcases service registration with Consul agent including health check configuration, service discovery with filtering and tag-based queries, built-in health monitoring and automatic unhealthy service removal, service metadata and versioning support, multi-datacenter service discovery, and integration with GoFrame's server and client components. Features include enterprise service registry, automatic health check execution, DNS and HTTP service discovery interfaces, load balancer integration, service mesh compatibility, and production-ready patterns. Ideal for building microservices requiring robust service discovery, implementing enterprise service mesh, ensuring service health monitoring, and enabling dynamic service registration across multiple datacenters.
hide_title: true
---

# Registry - `Consul` Integration

## Description

This example demonstrates how to integrate `Consul` service registry with `GoFrame` applications. It shows how to:
- Register services with `Consul`
- Discover services using `Consul`
- Implement service health checks
- Build distributed systems

## Structure

```text
.
├── docker-compose/      # Docker compose files for running Consul
├── grpc/                # gRPC service examples
│   ├── client/          # gRPC client implementation
│   ├── controller/      # gRPC service controllers
│   ├── protobuf/        # Protocol buffer definitions
│   └── server/          # gRPC server implementation
│       ├── main.go      # Server startup code
│       └── config.yaml  # Server configuration
├── http/                # HTTP service examples
│   ├── client/          # HTTP client implementation
│   └── server/          # HTTP server implementation
├── go.mod               # Go module file
└── go.sum               # Go module checksums
```

## Features

The example showcases the following features:
1. Service Registration
   - Automatic service registration
   - Health check configuration
   - Metadata management

2. Service Discovery
   - Dynamic service discovery
   - Load balancing
   - Failover support

3. Protocol Support
   - `HTTP` services
   - `gRPC` services
   - Custom protocols

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Consul Registry](https://github.com/gogf/gf/tree/master/contrib/registry/consul)
- [Consul](https://developer.hashicorp.com/consul/downloads)

## Prerequisites

1. Running `Consul` server:
   ```bash
   # Using docker-compose
   cd docker-compose
   docker-compose up -d
   ```

## Usage

### `HTTP` Example

1. Start the `HTTP` server:
   ```bash
   cd http/server
   go run server.go
   ```

2. Run the `HTTP` client:
   ```bash
   cd http/client
   go run client.go
   ```

### `gRPC` Example

1. Start the `gRPC` server:
   ```bash
   cd grpc/server
   go run server.go
   ```

2. Run the `gRPC` client:
   ```bash
   cd grpc/client
   go run client.go
   ```

## Implementation Details

The example demonstrates:
1. `Consul` client configuration
2. Service registration process
3. Service discovery mechanism
4. Health check implementation
5. Load balancing strategies
