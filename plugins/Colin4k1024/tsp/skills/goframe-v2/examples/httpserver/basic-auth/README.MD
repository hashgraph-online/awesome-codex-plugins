---
title: Basic Authentication
slug: /examples/httpserver/basic-auth
keywords: [http, server, basic auth, authentication, goframe]
description: Demonstrates HTTP Basic Authentication implementation in GoFrame for simple credential-based access control. This example showcases Basic Authentication middleware setup and configuration, username and password validation against configured credentials, Base64 credential encoding and decoding, WWW-Authenticate header handling for browser prompts, protected route implementation, custom authentication failure responses, and integration with GoFrame's middleware system. Features include simple authentication without external dependencies, browser-compatible authentication dialogs, credential validation patterns, secure credential storage recommendations, custom realm configuration, and production-ready error handling. Ideal for internal tools and admin panels, simple API protection, development and testing environments, legacy system integration, and applications requiring lightweight authentication without complex infrastructure.
hide_title: true
---

# HTTP Server Basic Authentication

## Description

This example demonstrates how to implement HTTP Basic Authentication using the `GoFrame` framework. Basic Authentication is a simple authentication mechanism that allows a server to request credentials from a client before granting access to protected resources.

The example shows how to:
- Set up a basic HTTP server with protected resources
- Implement Basic Authentication using GoFrame's built-in `BasicAuth` method
- Handle authentication success and failure cases
- Customize the authentication realm message

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## Structure

```text
basic-auth/
├── README.MD     # English documentation
├── README.ZH.MD  # Chinese documentation
├── go.mod        # Go module file
└── main.go       # Main application entry point
```

## Features

- Simple and secure HTTP Basic Authentication
- Automatic handling of authentication headers
- Customizable authentication realm message
- Clean separation of authentication logic

## Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/basic-auth
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

2. The server will start on port 8000.

3. Access the protected resource:
   - URL: http://127.0.0.1:8000/
   - When prompted, enter the following credentials:
     - Username: `user`
     - Password: `pass`

4. After successful authentication, you will see the message: "Authentication successful!"

## Implementation Details

The server uses GoFrame's `BasicAuth` method to implement HTTP Basic Authentication. This method:

1. Checks if the request contains valid Basic Authentication credentials
2. If credentials are missing or invalid, it automatically:
   - Sets the `WWW-Authenticate` header with the specified realm
   - Returns a 401 Unauthorized status code
   - Causes the browser to display an authentication dialog
3. If authentication succeeds, it returns `true` and allows the handler to proceed with the protected content

The implementation is clean and requires minimal code:

```go
if r.BasicAuth("user", "pass", "Please enter username and password") {
    // Process after successful authentication
    r.Response.Write("Authentication successful!")
}
// If authentication fails, the BasicAuth method handles the response automatically
```

## Notes

- Basic Authentication transmits credentials in base64 encoding, which is not secure over plain HTTP
- For production use, always combine Basic Authentication with HTTPS
- The credentials in this example are hardcoded for demonstration purposes; in a real application, you should use a secure credential store
