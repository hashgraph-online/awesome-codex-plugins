---
title: Response with JSON Array
slug: /examples/httpserver/response-json-array
keywords: [http, server, json, array, goframe]
description: Demonstrates JSON array response handling in GoFrame HTTP servers for RESTful API development. This example showcases returning JSON arrays as HTTP responses, proper content-type header configuration, array serialization with custom formatting, pagination support for large datasets, efficient memory management for large arrays, and integration with GoFrame's response writing system. Features include automatic JSON marshaling, proper HTTP status codes, empty array handling, streaming support for large datasets, error response formatting, and RESTful API patterns. Ideal for building REST APIs returning collections, implementing list and search endpoints, handling bulk data responses, ensuring consistent API response formats, and optimizing JSON serialization performance.
hide_title: true
---

# HTTP Server Response with JSON Array


## Description

This example demonstrates how to implement a HTTP server that returns JSON array responses using `GoFrame`. It showcases how to:
- Structure your API response as a JSON array
- Configure OpenAPI/Swagger documentation
- Use GoFrame's middleware for consistent response handling
- Define type-safe request and response structures

The example implements a `/user` endpoint that returns a list of users in JSON array format.

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

- `go.mod`: The Go module file.
- `main.go`: The main application entry point.

## Features

- JSON array response handling
- OpenAPI/Swagger integration
- Middleware-based response processing
- Type-safe request/response structures
- Clean API documentation
- Automatic response wrapping

## Usage

1. Run the example:
   ```bash
   go run main.go
   ```

2. The server will start at http://127.0.0.1:8000

3. Access the endpoints:
   ```bash
   # Get user list
   curl "http://127.0.0.1:8000/user"
   
   # View API documentation
   # Open in browser: http://127.0.0.1:8000/swagger
   ```

## Implementation Details

The example demonstrates several key concepts:
1. Using slice types for JSON array responses
2. Configuring OpenAPI/Swagger documentation
3. Implementing middleware for consistent response handling
4. Structuring type-safe API endpoints

Key components:
- Response wrapper middleware for consistent JSON structure
- OpenAPI configuration for proper documentation
- Type definitions for request and response objects
- Swagger UI integration for API testing

## Notes

- Response format includes a wrapper with standard fields
- OpenAPI documentation is available at `/api`
- Swagger UI is available at `/swagger`
- Response data is automatically wrapped by the middleware
- All responses are properly documented in OpenAPI format
