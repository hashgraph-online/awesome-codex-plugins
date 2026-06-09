---
title: Rate Limit
slug: /examples/httpserver/rate-limit
keywords: [http, server, rate limit, middleware, goframe]
description: Demonstrates rate limiting implementation in GoFrame HTTP servers for API protection and traffic control. This example showcases rate limiting middleware configuration with configurable limits, token bucket and sliding window algorithms, per-IP and per-user rate limiting strategies, custom rate limit responses and headers (X-RateLimit-*), Redis-based distributed rate limiting for scalability, and integration with GoFrame's middleware chain. Features include flexible rate limit policies, distributed rate limiting support, custom limit rules per endpoint, graceful rate limit responses, monitoring and metrics integration, and production-ready patterns. Ideal for protecting APIs from abuse and DDoS attacks, implementing fair usage policies, ensuring service stability under load, managing API quota and billing, and enabling multi-tier service levels.
hide_title: true
---

# HTTP Server Rate Limit


## Description

This example demonstrates how to implement rate limiting in a HTTP server using `GoFrame`. It showcases how to protect your API endpoints from being overwhelmed by too many requests using the token bucket algorithm implemented by `golang.org/x/time/rate` package.

The example implements:
- A simple HTTP endpoint `/hello` that returns a greeting message
- A rate limiting middleware that restricts requests to 10 per second
- Proper error handling when rate limit is exceeded (HTTP 429 Too Many Requests)

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

- `go.mod`: The Go module file.
- `main.go`: The main application entry point.

## Features

- Token bucket based rate limiting
- Configurable request rate and burst size
- Global middleware implementation
- Clean API endpoint implementation using GoFrame's binding feature
- Request validation and documentation using metadata
- Proper error handling and status codes

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. The server will start at http://127.0.0.1:8080

3. Test the rate limiting:
   ```bash
   # Normal request
   curl "http://127.0.0.1:8080/hello?name=world"
   
   # To test rate limiting, send multiple requests quickly:
   for i in {1..20}; do curl "http://127.0.0.1:8080/hello?name=world"; done
   ```

## Implementation Details

The rate limiting is implemented using:
1. `golang.org/x/time/rate.Limiter` for token bucket algorithm
2. GoFrame's middleware system for request interception
3. Clean request/response structs with validation and documentation

Key components:
- Rate limit is set to 10 requests per second
- Burst size is set to 1 (no bursting allowed)
- Requests exceeding the limit receive HTTP 429 status code
- Request validation ensures required parameters are provided

## Notes

- The rate limit is global (applies to all clients)
- No persistence of rate limit state (resets on server restart)
- Rate limit can be configured by modifying the limiter parameters
- Consider using distributed rate limiting for production environments
