---
title: Proxy
slug: /examples/httpserver/proxy
keywords: [http, server, proxy, reverse, goframe]
description: Demonstrates reverse proxy server implementation using GoFrame for request forwarding and load distribution. This example showcases reverse proxy setup and configuration with target backend servers, HTTP request and response forwarding with header preservation, custom header manipulation and transformation, connection pooling and keepalive management, error handling and failover logic, and integration with GoFrame's middleware system. Features include flexible proxy configuration, transparent request forwarding, response streaming support, custom routing rules, load balancing integration, and production-ready patterns. Ideal for building API gateways and service proxies, implementing microservices routing, adding authentication and rate limiting layers, enabling A/B testing and canary deployments, and creating development proxy servers.
hide_title: true
---

# HTTP Server Proxy


## Description

This example demonstrates how to create a reverse proxy server using `GoFrame`. The example consists of two servers:

1. A backend server running on port 8198 that provides the actual service
2. A proxy server running on port 8000 that forwards requests to the backend server

The proxy server implements the following features:
- Reverse proxy functionality using `httputil.NewSingleHostReverseProxy`
- Custom error handling for proxy failures
- URL path rewriting
- Request body handling
- Detailed logging of proxy operations

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

- `go.mod`: The Go module file.
- `main.go`: The main application entry point.

## Features

- Simple and efficient reverse proxy implementation
- Automatic URL path rewriting
- Error handling for backend server failures
- Logging of proxy operations
- Support for all HTTP methods

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/proxy
    ```

2. Install the dependencies:
    ```bash
    go mod tidy
    ```

3. Run the application:
    ```bash
    go run main.go
    ```

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. The example will start two servers:
   - Backend server at: http://127.0.0.1:8198
   - Proxy server at: http://127.0.0.1:8000

3. Test the proxy:
   - Access through proxy: http://127.0.0.1:8000/proxy/user/1
   - Direct backend access: http://127.0.0.1:8198/user/1

## Implementation Details

The proxy server uses Go's built-in `httputil.NewSingleHostReverseProxy` for implementing the reverse proxy functionality. All requests to the proxy server with the path prefix `/proxy/*` are forwarded to the backend server after removing the `/proxy` prefix.

The implementation includes:
- Request path rewriting
- Error handling for backend failures
- Request body handling for proper forwarding
- Logging of proxy operations for debugging

## Notes

- The proxy server modifies the request URL path before forwarding
- All HTTP methods are supported
- Backend server errors result in a 502 Bad Gateway response
