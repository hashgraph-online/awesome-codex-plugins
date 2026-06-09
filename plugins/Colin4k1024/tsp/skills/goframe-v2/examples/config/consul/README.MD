---
title: Consul
slug: /examples/config/consul
keywords: [config, consul, goframe]
description: Demonstrates comprehensive integration of HashiCorp Consul configuration center with GoFrame applications for distributed configuration management. This example showcases Consul client setup and initialization, configuration adapter implementation for GoFrame's config component, dynamic configuration loading and parsing, real-time configuration watch and updates, error handling and logging mechanisms, and secure configuration value retrieval. Features include distributed configuration management through Consul KV store, support for multiple data centers and namespaces, automatic configuration synchronization, health checks and service discovery integration, type-safe configuration access, and production-ready error handling. Perfect for building cloud-native microservices requiring distributed configuration management, service mesh integration, and consistent configuration across multiple instances.
hide_title: true
---

## `Consul` Configuration Center Example

## Description

This directory contains an example demonstrating how to integrate `Consul` configuration center with `GoFrame` applications. It shows:

1. `Consul` Client Configuration
   - `Consul` client setup and initialization
   - Configuration adapter implementation
   - Error handling and logging

2. Configuration Management
   - Configuration loading and parsing
   - Dynamic configuration updates
   - Configuration value retrieval

## Directory Structure

```text
.
├── boot/           # Bootstrap configuration
│   └── boot.go     # Consul client initialization
├── main.go         # Main application entry
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Consul Config](https://github.com/gogf/gf/tree/master/contrib/config/consul)

## Features

The example showcases the following features:

1. `Consul` Integration
   - Client configuration
   - Connection management
   - Key-Value store access
   - Error handling

2. Configuration Management
   - Configuration loading
   - Value retrieval
   - Type conversion
   - Default values

3. Dynamic Updates
   - Configuration watching
   - Change notification
   - Hot reload support

## Configuration

### `Consul` Server
1. Server Configuration:
   - Default port: 8500
   - Default datacenter: dc1
   - Default scheme: http

2. Authentication:
   - Token-based authentication
   - ACL system support
   - Datacenter level isolation

### Client Configuration
1. Basic Settings:
   - Address: `Consul` server address
   - Scheme: HTTP/HTTPS
   - Datacenter: Configuration datacenter
   - Token: Access token

2. Advanced Options:
   - Path customization
   - Watch configuration
   - Transport settings
   - Retry options

## Usage

1. Start `Consul` Server:
   ```bash
   # Start Consul server using Docker
   docker run -d --name consul \
      -p 8500:8500 -p 8600:8600/udp \
      hashicorp/consul
   ```

2. Configure `Consul`:
   - Access `Consul` UI at http://localhost:8500
   - Create Key-Value pairs
   - Set up ACL tokens if needed

3. Run Example:
   ```bash
   go run main.go
   ```

## Implementation Details

1. Client Setup (`boot/boot.go`):
   - Consul client configuration
   - Transport layer setup
   - Authentication configuration
   - Error handling

2. Configuration Access (`main.go`):
   - Configuration availability check
   - Bulk configuration retrieval
   - Single value access
   - Error handling

## Notes

- The example uses Consul's Key-Value store for configuration management
- Configuration changes in Consul are automatically reflected in the application
- The client supports secure connections via HTTPS
- ACL tokens can be used for secure access
- Configuration paths can be customized based on needs
