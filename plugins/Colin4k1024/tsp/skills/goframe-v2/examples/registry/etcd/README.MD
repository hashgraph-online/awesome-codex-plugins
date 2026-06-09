---
title: Etcd
slug: /examples/registry/etcd
keywords: [registry, etcd, service discovery, goframe]
description: Demonstrates comprehensive Etcd service registry integration with GoFrame for distributed service discovery and registration. This example showcases service registration with Etcd using automatic heartbeat mechanism, service discovery and watching for real-time updates, TTL-based service health management, service metadata and endpoint configuration, automatic service deregistration on shutdown, and integration with GoFrame's server and client components. Features include distributed service registry, real-time service updates via watch mechanism, health check integration, load balancer integration, automatic failover support, and production-ready patterns. Ideal for building cloud-native microservices requiring dynamic service discovery, implementing service mesh architectures, ensuring high availability through automatic service registration, and enabling zero-downtime deployments with service discovery.
hide_title: true
---

# Registry - `Etcd` Integration

## Description

This example demonstrates how to integrate `Etcd` service registry with `GoFrame` applications. It shows how to:
- Register services with `Etcd`
- Discover services using `Etcd`
- Implement service health checks
- Build distributed systems

## Structure

```text
.
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
   - TTL-based health check
   - Metadata management
   - Lease management

2. Service Discovery
   - Dynamic service discovery
   - Load balancing
   - Failover support
   - Watch mechanism

3. Protocol Support
   - `HTTP` services
   - `gRPC` services
   - Custom protocols

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Etcd Registry](https://github.com/gogf/gf/tree/master/contrib/registry/etcd)
- [Etcd](https://etcd.io/docs/v3.5/install/)

## Prerequisites

1. Running `etcd` server:
   ```bash
   # Using docker
   docker run -d --name etcd -p 2379:2379 -e ALLOW_NONE_AUTHENTICATION=yes bitnami/etcd:3.4.24
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
1. etcd client configuration
2. Service registration process
3. Service discovery mechanism
4. Health check implementation
5. Load balancing strategies
6. Watch mechanism usage
7. Lease management

## Notes

- etcd server must be running
- Default etcd address: 127.0.0.1:2379
- Services are registered automatically
- TTL-based health checks
- Automatic lease renewal
- Load balancing is handled automatically
- Consider security in production
- Handle failover scenarios
- Monitor service health
- Implement proper error handling
- Watch for service changes
- Manage leases properly
