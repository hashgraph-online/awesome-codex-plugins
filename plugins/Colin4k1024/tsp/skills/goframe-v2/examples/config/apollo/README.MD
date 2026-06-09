---
title: Apollo
slug: /examples/config/apollo
keywords: [config, apollo, goframe]
description: Demonstrates seamless integration of Apollo configuration center with GoFrame applications for centralized configuration management. This example showcases Apollo client initialization and setup, configuration adapter implementation, dynamic configuration loading and parsing, real-time configuration updates, error handling and logging mechanisms, and configuration value retrieval. Features include centralized configuration management through Apollo, support for multiple environments and namespaces, automatic configuration refresh capabilities, type-safe configuration access using GoFrame's config component, and production-ready error handling. Ideal for building microservices that require centralized configuration management, dynamic configuration updates without service restart, and configuration versioning and rollback capabilities.
hide_title: true
---

# `Apollo` Configuration Center Example

## Description

This directory contains an example demonstrating how to integrate `Apollo` configuration center with `GoFrame` applications. It shows:

1. `Apollo` Client Configuration
   - `Apollo` client setup and initialization
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
│   └── boot.go     # Apollo client initialization
├── main.go         # Main application entry
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Apollo Config](https://github.com/gogf/gf/tree/master/contrib/config/apollo)

## Features

The example showcases the following features:

1. `Apollo` Integration
   - Client configuration
   - Connection management
   - Namespace handling
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

### `Apollo` Server
1. Server Configuration:
   - Default port: 8080
   - Default cluster: default
   - Default namespace: application

2. Authentication:
   - AppID based authentication
   - Optional access key support
   - Cluster level isolation

### Client Configuration
1. Basic Settings:
   - AppID: Application identifier
   - Cluster: Configuration cluster
   - IP: `Apollo` server address

2. Advanced Options:
   - Namespace customization
   - Cache management
   - Retry settings

## Usage

1. Start `Apollo` Server:
   ```bash
   # Start Apollo server using Docker
   docker run -p 8080:8080 apolloconfig/apollo-portal
   ```

2. Configure `Apollo`:
   - Create application namespace
   - Add configuration items
   - Publish configuration

3. Run Example:
   ```bash
   go run main.go
   ```

## Implementation Details

1. Client Setup
   - Apollo client initialization
   - Configuration adapter setup
   - Error handling configuration

2. Configuration Access
   - Value retrieval methods
   - Type conversion handling
   - Default value management

3. Error Handling
   - Connection errors
   - Configuration errors
   - Type conversion errors

## Best Practices

1. Client Configuration
   - Use environment variables for sensitive data
   - Configure appropriate timeouts
   - Implement proper error handling

2. Configuration Management
   - Use structured configuration keys
   - Implement configuration validation
   - Handle configuration updates gracefully

3. Error Handling
   - Log configuration errors
   - Provide fallback values
   - Implement retry mechanisms

## Troubleshooting

1. Connection Issues:
   - Verify Apollo server status
   - Check network connectivity
   - Validate authentication settings

2. Configuration Issues:
   - Check namespace configuration
   - Verify configuration format
   - Review access permissions

3. Client Issues:
   - Check client configuration
   - Verify AppID settings
   - Review cluster configuration

4. General Issues:
   - Check application logs
   - Verify dependencies
   - Review error messages
