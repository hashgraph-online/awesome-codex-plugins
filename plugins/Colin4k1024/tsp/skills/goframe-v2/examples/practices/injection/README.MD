---
title: Dependency Injection
slug: /examples/practices/injection
keywords: [dependency injection, di, testing, goframe, do package, microservices, clean architecture, unit testing, mock, interface, separation of concerns, testability, grpc, mongodb, redis, container, lifecycle management]
description: Demonstrates dependency injection patterns using GoFrame with do package for testable and maintainable architecture. Features DI container setup, interface-based dependency management, automatic resolution, singleton and transient lifetimes, and mock testing integration. Ideal for building testable microservices with clean architecture principles.
hide_title: true
---

# Dependency Injection Example

## Introduction

This example demonstrates how to implement dependency injection in a `GoFrame` application.

Key demonstrations:
1. Using monorepo pattern for code repository management
2. Basic dependency injection setup
3. Service layer implementation with `DI`
4. Controller layer integration with `gRPC`
5. Unit testing with mock dependencies

The implementation focuses on making core business logic easily testable:
- Separation of concerns using dependency injection
- Clear interfaces for service dependencies
- Independent unit testing for each layer to ensure code quality

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [MongoDB](https://www.mongodb.com)
- [Redis](https://redis.io)
- [github.com/samber/do](https://github.com/samber/do)

## Directory Structure

```text
injection/
├── app/
│   ├── gateway/         # API Gateway service, calls user gRPC service for external interfaces
│   │   ├── api/         # API definitions
│   │   ├── internal/    # Internal implementations
│   │   │   ├── cmd/         # Command line tools
│   │   │   ├── controller/  # Controllers
│   │   │   ├── model/       # Data models
│   │   │   └── service/     # Business logic
│   │   └── manifest/   # Configuration files
│   └── user/           # User service
│       ├── api/        # API definitions
│       │   ├── entity/ # Entity definitions
│       │   └── user/   # User API proto
│       ├── internal/   # Internal implementations
│       │   ├── cmd/         # Command line tools
│       │   ├── controller/  # Controllers with DI
│       │   ├── dao/         # Data Access Objects
│       │   ├── model/       # Data models
│       │   └── service/     # Business logic with DI
│       └── manifest/   # Configuration files
├── hack/               # Development tools
└── utility/            # Common utilities
    ├── injection/      # DI utilities
    └── mongohelper/    # MongoDB helper tools
```

## Features

- Dependency injection usage
- `MongoDB` and `Redis` integration
- `gRPC` service implementation
- Complete unit testing
- Resource cleanup handling
- Named dependency support

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/practices/injection
    ```

2. Install dependencies:
    ```bash
    go mod tidy
    ```

3. Start required services using `Docker`:
    ```bash
    # Start MongoDB
    docker run -d --name mongo -p 27017:27017 mongo:latest

    # Start Redis
    docker run -d --name redis -p 6379:6379 redis:latest
    ```

## Usage

1. Run the `gRPC Server` service:
   ```bash
   cd examples/practices/injection/app/user
   go run main.go server
   ```

2. Run the `HTTP Server` service:
   ```bash
   cd examples/practices/injection/app/gateway
   go run main.go server
   ```

3. (Optional) Run async worker, only demonstrates multi-command functionality, no actual logic:
   ```bash
   cd examples/practices/injection/app/gateway
   go run main.go worker
   ```
   
4. (Optional) Run tests:
   ```bash
   go test ./...
   ```

## Implementation Details

### Dependency Injection Setup
- Using `github.com/samber/do` package for dependency management
- Support for named and unnamed dependency management
- Helper functions for common operations

### Service Layer
- Clear separation of concerns
- Interface-based design
- Easy to test with mock implementations

### Controller Layer
- `gRPC` integration with `DI` support
- Clear error handling
- Proper resource management

### Testability
- Complete unit tests for data layer (`dao`), service layer (`service`), and interface layer (`controller`)
- Mock dependencies, database configuration for unit tests managed through `manifest/config`
- Service addresses or domains for microservice connections managed through configuration files for easy service mocking

## Important Notes

- Properly clean up resources in the `Shutdown` method when registering dependency injection
- Use named dependencies when multiple instances of the same type are needed in dependency injection

