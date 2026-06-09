---
title: JWT Authentication
slug: /examples/httpserver/jwt
keywords: [http, server, jwt, authentication, goframe]
description: Demonstrates comprehensive JWT (JSON Web Token) authentication implementation in GoFrame HTTP servers for secure API access control. This example showcases JWT token generation with custom claims and expiration, token validation and verification middleware, secure token signing using HS256/RS256 algorithms, refresh token mechanism for extended sessions, protected route implementation with authentication middleware, error handling for invalid or expired tokens, and integration with GoFrame's middleware system. Features include user login and token issuance, stateless authentication, token refresh patterns, role-based access control (RBAC) integration, secure token storage recommendations, and production-ready security practices. Ideal for building REST APIs with authentication, implementing microservices security, mobile app backends requiring stateless auth, and applications needing scalable authentication without server-side sessions.
hide_title: true
sidebar_position: 0
---

# JWT Authentication Example with GoFrame

This example demonstrates how to implement JWT (JSON Web Token) authentication in a GoFrame HTTP server using the `github.com/golang-jwt/jwt` package.

## Features

- User login endpoint that generates JWT tokens
- Protected routes using JWT middleware
- Token validation and parsing
- Example of accessing protected resources
- Standard GoFrame project structure

## Project Structure

```
jwt/
├── api/
│   └── v1/
│       └── auth.go         # API interface definitions
├── internal/
│   ├── controller/
│   │   └── auth.go        # Business logic implementation
│   └── middleware/
│       └── jwt.go         # JWT middleware
└── main.go                # Entry point
```

## API Endpoints

1. Login: `POST /login`
   ```json
   {
       "username": "admin",
       "password": "password"
   }
   ```

2. Protected Resource: `GET /api/protected`
   - Requires Bearer token in Authorization header
   - Example: `Authorization: Bearer your-token-here`

## Running the Example

1. Start the server:
   ```bash
   go run main.go
   ```

2. The server will start on port 8000

## Testing the API

1. Login to get a token:
   ```bash
   curl -X POST http://localhost:8000/login \
   -H "Content-Type: application/json" \
   -d '{"username":"admin","password":"password"}'
   ```

2. Access protected endpoint:
   ```bash
   curl http://localhost:8000/api/protected \
   -H "Authorization: Bearer your-token-here"
   ```

## Security Notes

- In production, replace the hardcoded secret key with a secure value
- Store user credentials in a database
- Implement proper password hashing
- Consider implementing refresh tokens
- Add rate limiting for login attempts

## References

For more detailed information about JWT implementation, please refer to the third-party component documentation:
- [github.com/golang-jwt/jwt](https://github.com/golang-jwt/jwt)
