---
title: Swagger Auth
slug: /examples/httpserver/swagger-auth
keywords: [http, server, swagger, auth, basic auth, goframe]
description: Demonstrates Swagger API documentation with Basic Authentication integration using GoFrame for secure API documentation access. This example showcases Swagger UI integration with GoFrame HTTP server, Basic Authentication protection for Swagger endpoints, OpenAPI specification generation and serving, authentication middleware for documentation access, custom Swagger UI configuration, and integration with GoFrame's routing system. Features include protected API documentation, automatic OpenAPI spec generation, interactive API testing with authentication, customizable Swagger UI themes, credential-based access control, and development-friendly patterns. Ideal for securing API documentation in production, providing authenticated access to internal APIs, enabling interactive API testing with auth, documenting and protecting REST APIs, and maintaining API specifications with access control.
hide_title: true
---

# HTTP Server Swagger Auth

## Description

This example demonstrates how to implement Basic Authentication for Swagger API documentation using GoFrame framework. The example shows how to:

1. Set up a basic HTTP server with OpenAPI/Swagger documentation
2. Protect the Swagger documentation with Basic Authentication
3. Define and implement a simple REST API endpoint

## Requirements

- [Go](https://golang.org/dl/) 1.22 or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

```text
.
├── README.MD        # English documentation
├── README.ZH.MD     # Chinese documentation
├── go.mod          # Go module file
└── main.go         # Main application entry point
```

## Features

- OpenAPI/Swagger documentation integration
- Basic Authentication protection for API documentation
- RESTful API endpoint implementation
- Request/Response validation
- API documentation comments

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/swagger-auth
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

1. Start the server:
   ```bash
   go run main.go
   ```

2. Access the protected Swagger documentation:
   - URL: http://localhost:8000/swagger
   - Basic Auth Credentials:
     - Username: admin
     - Password: 123456

3. Test the API endpoint:
   - Access: http://localhost:8000/hello?name=GoFrame
   - Method: GET
   - Response: JSON containing greeting message

## Implementation Details

The example demonstrates several key features:

1. Swagger Integration:
   - OpenAPI JSON at `/api.json`
   - Swagger UI at `/swagger`
   - Both protected by Basic Authentication

2. Basic Authentication:
   - Username: admin
   - Password: 123456
   - Realm: "Restricted"

3. API Endpoint:
   - Path: `/hello`
   - Method: GET
   - Required Parameter: name
   - Response: JSON with greeting message

## Notes

- The Basic Authentication is implemented using GoFrame's built-in `BasicAuth` method
- API documentation is automatically generated from code comments and struct tags
- The server runs on port 8000 by default
- All API responses are automatically wrapped in a standard format using middleware
