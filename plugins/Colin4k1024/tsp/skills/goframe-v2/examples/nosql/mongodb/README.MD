---
title: MongoDB
slug: /examples/nosql/mongodb
keywords: [nosql, mongodb, database, goframe]
description: Demonstrates comprehensive MongoDB integration with GoFrame for document-based data storage and retrieval. This example showcases MongoDB connection setup and configuration with official Go driver, CRUD operations (Create, Read, Update, Delete) for documents, advanced querying with filters and projections, aggregation pipeline usage for data analysis, index creation and management for performance, transaction support for data consistency, and connection pooling configuration. Features include automatic connection management, error handling patterns, integration with GoFrame's ORM concepts where applicable, document marshaling/unmarshaling, pagination support, and production-ready database operations. Ideal for building applications requiring flexible schema design, document-oriented data models, complex aggregations, horizontal scalability, and NoSQL database integration in microservices architectures.
hide_title: true
sidebar_position: 2
---

# GoFrame MongoDB Example

This example demonstrates how to use `MongoDB` with `GoFrame` framework.

## Overview

This example shows:
1. How to configure `MongoDB` connection using `YAML` configuration
2. How to create a `MongoDB` client
3. Basic `MongoDB` operations (`INSERT`, `FIND`, `UPDATE`)
4. How to use `BSON` for document operations

## Requirements

- `Go 1.15` or higher
- `MongoDB` server
- `GoFrame v2`

## Configuration

The `MongoDB` configuration is stored in `config.yaml`:

```yaml
mongo:
  database: "user"
  address: "mongodb://127.0.0.1:27017/test?retryWrites=true"
```

You can modify these settings according to your `MongoDB` server configuration.

## Running MongoDB with Docker

If you don't have `MongoDB` installed locally, you can quickly start a `MongoDB` instance using `Docker`:

```bash
# Run MongoDB container
docker run --name mongo-test -p 27017:27017 -d mongo:latest

# Verify the container is running
docker ps

# If you need to stop the container later
docker stop mongo-test

# If you need to remove the container
docker rm mongo-test
```

For `MongoDB` with authentication:

```bash
# Run MongoDB with authentication
docker run --name mongo-test -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password -d mongo:latest

# Remember to update config.yaml accordingly:
# mongo:
#   database: "user"
#   address: "mongodb://admin:password@127.0.0.1:27017/test?retryWrites=true"
```

## Running the Example

1. Make sure your `MongoDB` server is running
2. Update the `config.yaml` if needed
3. Run the example:

```bash
go run main.go
```

## Code Structure

- `main.go`: Contains the main logic and `MongoDB` client initialization
- `config.yaml`: `MongoDB` configuration file

## Features

1. `MongoDB` client initialization with error handling
2. Configuration management using `GoFrame`'s configuration system
3. Basic `MongoDB` operations demonstration
4. Proper error handling and logging
5. Use of `BSON` tags for document mapping

## Further Reading

For more advanced `MongoDB` usage, please refer to the official `MongoDB` Go driver [github.com/mongodb/mongo-go-driver](https://github.com/mongodb/mongo-go-driver).

## Notes

- The example uses the official `MongoDB` Go driver
- All operations are performed with context for proper cancellation and timeout handling
- The code includes proper error handling and logging
