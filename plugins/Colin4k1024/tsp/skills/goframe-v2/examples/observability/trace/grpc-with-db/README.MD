---
title: gRPC with Database
slug: /examples/observability/trace/grpc-with-db
keywords: [trace, grpc, database, opentelemetry, goframe]
description: Demonstrates comprehensive distributed tracing in gRPC services with database operations using GoFrame and OpenTelemetry. This example showcases end-to-end trace instrumentation from gRPC calls through database queries, automatic gRPC method and database operation tracing, trace context propagation in RPC communication, span relationships between service calls and database operations, service discovery integration with tracing, and performance monitoring for distributed systems. Features include full-stack gRPC trace visibility, automatic database query instrumentation, service mesh observability, distributed transaction tracking, cross-service trace correlation, and production-ready patterns. Ideal for monitoring microservices architecture performance, debugging distributed gRPC systems, optimizing database query performance, ensuring observability in service mesh environments, and building enterprise monitoring solutions.
hide_title: true
---

# Tracing - gRPC with Database

## Description

This example demonstrates how to implement distributed tracing in a gRPC service that interacts with a database using `GoFrame`. It shows how to:
- Configure tracing in gRPC services
- Trace database operations
- Propagate trace context
- Visualize distributed traces

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame gRPCx](https://github.com/gogf/gf/tree/master/contrib/rpc/grpcx)
- [GoFrame MySQL Driver](https://github.com/gogf/gf/tree/master/contrib/drivers/mysql)
- [GoFrame Etcd Registry](https://github.com/gogf/gf/tree/master/contrib/registry/etcd)
- [GoFrame OpenTelemetry Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlpgrpc)

## Structure

```text
.
├── client/          # Client example
│   └── client.go    # Client with tracing
├── controller/      # Service controllers
├── protobuf/        # Protocol buffer definitions
│   └── user/        # User service proto files
├── server/          # Server example
│   ├── server.go    # Server with tracing
│   └── config.yaml  # Server configuration
├── sql.sql         # Database schema
├── go.mod          # Go module file
└── go.sum          # Go module checksums
```

## Features

The example showcases the following features:
1. Distributed Tracing
   - Trace propagation
   - Span management
   - Trace visualization

2. Database Operations
   - Query tracing
   - Transaction tracing
   - Error tracking

3. gRPC Integration
   - Service tracing
   - Context propagation
   - Error handling

## Prerequisites

1. Running MySQL instance:
   ```bash
   docker run -d --name mysql \
   -p 3306:3306 \
   -e MYSQL_DATABASE=test \
   -e MYSQL_ROOT_PASSWORD=12345678 \
   mysql:5.7
   ```

2. Initialize database schema:
   ```bash
   # Connect to MySQL container
   docker exec -i mysql mysql -uroot -p12345678 test < sql.sql
   ```

3. Running Redis instance:
   ```bash
   docker run -d --name redis \
   -p 6379:6379 \
   redis:6.0
   ```

4. Running Jaeger instance:
   ```bash
   docker run --rm --name jaeger \
   -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
   -p 6831:6831/udp \
   -p 6832:6832/udp \
   -p 5778:5778 \
   -p 16686:16686 \
   -p 4317:4317 \
   -p 4318:4318 \
   -p 14250:14250 \
   -p 14268:14268 \
   -p 14269:14269 \
   -p 9411:9411 \
   jaegertracing/all-in-one:1.55
   ```

5. Protocol buffer compiler:
   ```bash
   # For macOS
   brew install protobuf
   
   # Install protoc-gen-go and protoc-gen-go-grpc
   go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
   go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
   ```

## Configuration

The server configuration is defined in `server/config.yaml`:

```yaml
grpc:
  name:            "demo"            # Service name
  logStdout:        true            # Enable stdout logging
  errorLogEnabled:  true            # Enable error logging
  accessLogEnabled: true            # Enable access logging
  errorStack:       true            # Enable error stack trace

database:
  logger:
    level: "all"                    # Log all SQL operations
    stdout: true                    # Print to stdout
  default:
    link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
    debug: true                     # Enable debug mode

redis:
  default:
    address: 127.0.0.1:6379        # Default Redis instance
    db:      0
  cache:
    address: 127.0.0.1:6379        # Cache Redis instance
    db:      1
```

## Usage

1. Generate protocol buffer code:
   ```bash
   cd protobuf
   protoc --go_out=paths=source_relative:. --go-grpc_out=paths=source_relative:. ./user/*.proto
   ```

2. Start the server:
   ```bash
   cd server
   go run server.go
   ```

3. Run the client:
   ```bash
   cd client
   go run client.go
   ```

4. View traces:
   Open http://localhost:16686 in your browser to view traces in `Jaeger` UI.

## Implementation Details

The example demonstrates:
1. Trace context propagation
2. Database operation tracing

## Troubleshooting

1. Database Connection Issues:
   - Ensure `MySQL` is running: `docker ps | grep mysql`
   - Check `MySQL` connection: `docker exec -it mysql mysql -uroot -p12345678 -e "SELECT 1"`
   - Verify database schema: `docker exec -it mysql mysql -uroot -p12345678 test -e "DESC user"`

2. Redis Connection Issues:
   - Ensure `Redis` is running: `docker ps | grep redis`
   - Test `Redis` connection: `docker exec -it redis redis-cli ping`

3. Tracing Issues:
   - Verify `Jaeger` is running: `docker ps | grep jaeger`
   - Check `Jaeger` UI accessibility: http://localhost:16686
   - Ensure trace endpoint is correct in configuration

4. gRPC Issues:
   - Check if protobuf files are generated correctly
   - Verify service registration in `etcd`
   - Ensure server is listening on correct port
