---
title: Nacos
slug: /examples/config/nacos
keywords: [config, nacos, goframe]
description: Demonstrates seamless integration of Alibaba Nacos configuration center with GoFrame applications for dynamic configuration management. This example showcases Nacos client initialization and configuration, configuration adapter implementation for GoFrame, dynamic configuration loading and hot-reloading, real-time configuration listening and updates, namespace and group management, error handling and logging, and secure configuration value retrieval. Features include centralized configuration management through Nacos, support for multiple environments and namespaces, automatic configuration refresh without service restart, configuration versioning and rollback, type-safe configuration access, and production-ready monitoring. Ideal for building cloud-native microservices in Alibaba Cloud or on-premises environments requiring dynamic configuration, service discovery, and configuration sharing across distributed systems.
hide_title: true
---

## `Nacos` Configuration Center Example

## Description

This directory contains an example demonstrating how to integrate `Nacos` configuration center with `GoFrame` applications. It shows:

1. `Nacos` Client Configuration
   - `Nacos` client setup and initialization
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
│   └── boot.go     # Nacos client initialization
├── main.go         # Main application entry
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Nacos Config](https://github.com/gogf/gf/tree/master/contrib/config/nacos)
- [Nacos Server](https://nacos.io/)

## Features

The example showcases the following features:

1. `Nacos` Integration
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

### `Nacos` Server
1. Server Configuration:
   - Default port: 8848
   - Default address: localhost
   - Default protocol: HTTP

2. Authentication:
   - Username/Password authentication
   - Namespace isolation
   - Group level access control

### Client Configuration
1. Basic Settings:
   - Server address and port
   - Cache directory
   - Log directory
   - Data ID and Group

2. Advanced Options:
   - Namespace customization
   - Cache management
   - Logging configuration
   - Retry settings

## Usage

1. Start `Nacos` Server:
   ```bash
   # Start Nacos server using Docker
   docker run -d --name nacos \
      -p 8848:8848 -p 9848:9848 \
      -e MODE=standalone \
      nacos/nacos-server:latest
   ```

2. Configure `Nacos`:
   - Access `Nacos` console at http://localhost:8848/nacos
   - Default credentials: nacos/nacos
   - Create configuration items

3. Run Example:
   ```bash
   go run main.go
   ```
