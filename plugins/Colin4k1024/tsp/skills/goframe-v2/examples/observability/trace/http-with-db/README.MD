---
title: HTTP with Database
slug: /examples/observability/trace/http-with-db
keywords: [trace, http, database, goframe]
description: Demonstrates comprehensive distributed tracing in HTTP services with database operations using GoFrame and OpenTelemetry. This example showcases end-to-end trace instrumentation from HTTP requests through database queries, automatic database operation tracing including MySQL and Redis operations, trace context propagation through the entire request lifecycle, span relationships between HTTP handlers and database calls, performance monitoring for database queries, and integration with GoFrame's ORM and cache components. Features include full-stack trace visibility, automatic database query instrumentation, slow query detection, connection pool monitoring, cache operation tracing, and production-ready observability. Ideal for monitoring full-stack application performance, debugging database-related issues, optimizing query performance, ensuring end-to-end observability in data-driven applications, and building comprehensive monitoring solutions.
hide_title: true
---

# Tracing - HTTP with Database

## Description

This example demonstrates how to implement distributed tracing in an HTTP service that interacts with a database using `GoFrame`. It shows how to:
- Configure tracing in HTTP services
- Trace database operations
- Propagate trace context
- Visualize distributed traces

## Requirements

- [Go](https://golang.org/dl/) `1.22` or higher
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame MySQL Driver](https://github.com/gogf/gf/tree/master/contrib/drivers/mysql)
- [GoFrame Redis Driver](https://github.com/gogf/gf/tree/master/contrib/nosql/redis)
- [GoFrame OpenTelemetry Tracing](https://github.com/gogf/gf/tree/master/contrib/trace/otlphttp)

## Structure

```text
.
├── client/          # Client example
│   └── client.go    # Client with tracing
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

3. HTTP Integration
   - Request tracing
   - Context propagation
   - Error handling

## Prerequisites

1. Running `MySQL` instance:
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

3. Running `Redis` instance:
   ```bash
   docker run -d --name redis \
   -p 6379:6379 \
   redis:6.0
   ```

4. Running `Jaeger` instance:
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

## Configuration

The server configuration is defined in `server/config.yaml`:

```yaml
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

1. Start the server:
   ```bash
   cd server
   go run server.go
   ```

2. Run the client:
   ```bash
   cd client
   go run client.go
   ```

3. View traces:
   Open http://localhost:16686 in your browser to view traces in `Jaeger` UI.

## API Endpoints

The server provides the following HTTP endpoints:

1. Insert User
   ```text
   POST /insert
   Request: {"Name": "string"}
   Response: {"ID": number}
   ```

2. Query User
   ```text
   GET /query
   Request: {"ID": number}
   Response: {"User": object}
   ```

3. Delete User
   ```text
   DELETE /delete
   Request: {"Id": number}
   Response: {}
   ```

## Implementation Details

The example demonstrates:
1. HTTP request tracing
2. Database operation tracing
3. Redis cache integration
4. Error handling and propagation

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

4. HTTP Issues:
   - Check if server is running: `curl http://localhost:8000/ping`
   - Verify request format matches API specification
   - Check server logs for detailed error messages
