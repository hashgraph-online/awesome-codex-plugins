---
title: Nacos
slug: /examples/registry/nacos
keywords: [registry, nacos, service discovery, goframe]
description: Demonstrates comprehensive Alibaba Nacos service registry integration with GoFrame for dynamic service management and configuration. This example showcases service registration with Nacos using namespace and group isolation, service discovery with instance filtering and selection strategies, built-in health monitoring and heartbeat mechanism, service metadata and weight-based load balancing, integration with Nacos configuration center, and seamless GoFrame component integration. Features include centralized service registry, real-time service status updates, health check automation, weighted load balancing support, namespace-based service isolation, and production-ready patterns. Ideal for building cloud-native microservices on Alibaba Cloud, implementing dynamic service discovery with configuration management, ensuring service health and availability, and enabling enterprise-grade service governance.
hide_title: true
---

# Registry - `Nacos` Integration

## Description

This example demonstrates how to integrate `Nacos` service registry with `GoFrame` applications. It shows how to:
- Register services with `Nacos`
- Discover services using `Nacos`
- Implement service health checks
- Build distributed systems

## Structure

```text
.
├── docker-compose/     # Docker compose files for running Nacos
│   ├── standalone/     # Standalone mode configuration
│   └── cluster/        # Cluster mode configuration
├── grpc/               # gRPC service examples
│   ├── client/         # gRPC client implementation
│   ├── controller/     # gRPC service controllers
│   ├── protobuf/       # Protocol buffer definitions
│   └── server/         # gRPC server implementation
│       ├── main.go     # Server startup code
│       └── config.yaml # Server configuration
├── http/               # HTTP service examples
│   ├── client/         # HTTP client implementation
│   └── server/         # HTTP server implementation
├── go.mod              # Go module file
└── go.sum              # Go module checksums
```

## Features

The example showcases the following features:
1. Service Registration
   - Automatic service registration
   - Health check configuration
   - Metadata management
   - Namespace support
   - Group management

2. Service Discovery
   - Dynamic service discovery
   - Load balancing
   - Failover support
   - Service grouping
   - Namespace isolation

3. Protocol Support
   - `HTTP` services
   - `gRPC` services
   - Custom protocols

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Nacos Registry](https://github.com/gogf/gf/tree/master/contrib/registry/nacos)
- [Nacos](https://nacos.io/en-us/docs/v2/quickstart/quick-start.html)

## Prerequisites

1. Running `Nacos` server:
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
1. `Nacos` client configuration
2. Service registration process
3. Service discovery mechanism
4. Health check implementation
5. Load balancing strategies
6. Namespace management
7. Group configuration
