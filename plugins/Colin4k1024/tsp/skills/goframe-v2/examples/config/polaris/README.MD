---
title: Polaris
slug: /examples/config/polaris
keywords: [config, polaris, goframe]
description: Demonstrates seamless integration of Tencent Cloud Polaris configuration center with GoFrame applications for service mesh configuration management. This example showcases Polaris client setup and initialization, configuration adapter implementation for GoFrame's config component, dynamic configuration loading and hot-reloading, real-time configuration watch and synchronization, namespace and file group management, error handling and logging mechanisms, and secure configuration value retrieval. Features include centralized configuration management through Polaris, support for multiple namespaces and configuration groups, automatic configuration refresh capabilities, integration with Polaris service mesh for unified service governance, type-safe configuration access, and production-ready monitoring. Ideal for building cloud-native microservices on Tencent Cloud or using Polaris mesh requiring dynamic configuration, service discovery, traffic management, and unified configuration governance.
hide_title: true
---

# `Polaris` Configuration Center Example

## Description

This directory contains an example demonstrating how to integrate `Polaris` configuration center with `GoFrame` applications. It shows:

1. `Polaris` Client Configuration
   - `Polaris` client setup and initialization
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
│   └── boot.go     # Polaris client initialization
├── main.go         # Main application entry
├── testdata/       # Test configuration files
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Polaris Config](https://github.com/gogf/gf/tree/master/contrib/config/polaris)
- [Polaris Server](https://github.com/polarismesh/polaris)

## Features

The example showcases the following features:

1. `Polaris` Integration
   - Client configuration
   - Server connection management
   - Configuration namespace
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

### `Polaris` Server
1. Server Configuration:
   - Default port: 8090
   - Default address: localhost
   - Default protocol: `gRPC`

2. Authentication:
   - Namespace isolation
   - Group level access control
   - Access token support

### Client Configuration
1. Basic Settings:
   - Namespace
   - File group
   - File name
   - Configuration path
   - Log directory

2. Advanced Options:
   - Watch mode
   - Retry settings
   - Cache management
   - Logging configuration

## Usage

1. Start `Polaris` Server:
   ```bash
   # Start Polaris server using Docker
   docker run -d --name polaris \
      -p 8090:8090 -p 8091:8091 \
      polarismesh/polaris-server
   ```

2. Configure `Polaris`:
   - Access `Polaris` console at http://localhost:8090
   - Create configuration items
   - Set up access control

3. Run Example:
   ```bash
   go run main.go
   ```

## Implementation Details

1. Client Setup (`boot/boot.go`):
   - Namespace configuration
   - File group and name setup
   - Configuration path setup
   - Log directory configuration
   - Watch mode enablement

2. Configuration Access (`main.go`):
   - Configuration availability check
   - Bulk configuration retrieval
   - Single value access
   - Error handling

## Notes

- The example uses Polaris's configuration center features
- Configuration changes in Polaris are automatically reflected when watch mode is enabled
- Configuration is organized by namespace and file group
- Log files are stored in the specified log directory
- Configuration path points to the Polaris server configuration file
- Watch mode enables dynamic configuration updates
