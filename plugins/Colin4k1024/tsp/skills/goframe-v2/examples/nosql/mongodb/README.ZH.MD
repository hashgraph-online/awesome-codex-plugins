---
title: MongoDB
slug: /examples/nosql/mongodb
keywords: [nosql, mongodb, database, goframe]
description: 演示在GoFrame中全面集成MongoDB用于基于文档的数据存储和检索。本示例展示了使用官方Go驱动的MongoDB连接设置和配置、文档的CRUD操作(创建、读取、更新、删除)、带有过滤器和投影的高级查询、用于数据分析的聚合管道使用、用于性能优化的索引创建和管理、用于数据一致性的事务支持、以及连接池配置。主要功能包括:自动连接管理、错误处理模式、在适用情况下与GoFrame的ORM概念集成、文档序列化/反序列化、分页支持、生产级数据库操作。非常适合构建需要灵活模式设计、面向文档的数据模型、复杂聚合、水平扩展性、以及在微服务架构中集成NoSQL数据库的应用程序。通过本示例可以学习如何在GoFrame中使用MongoDB、NoSQL数据库的最佳实践、以及构建灵活高性能的文档存储系统。
hide_title: true
sidebar_position: 2
---

# GoFrame MongoDB 示例

此示例演示了如何在 `GoFrame` 框架中使用 `MongoDB`。

## 概述

本示例展示了：
1. 如何使用 `YAML` 配置文件配置 `MongoDB` 连接
2. 如何创建 `MongoDB` 客户端
3. 基本的 `MongoDB` 操作（`INSERT`、`FIND`、`UPDATE`）
4. 如何使用 `BSON` 进行文档操作

## 环境要求

- `Go 1.15` 或更高版本
- `MongoDB` 服务器
- `GoFrame v2`

## 代码结构

- `main.go`: 包含主要逻辑和 `MongoDB` 客户端初始化
- `config.yaml`: `MongoDB` 配置文件


## 配置说明

`MongoDB` 配置存储在 `config.yaml` 文件中：

```yaml
mongo:
  database: "user"
  address: "mongodb://127.0.0.1:27017/test?retryWrites=true"
```

您可以根据自己的 `MongoDB` 服务器配置修改这些设置。

## 使用 Docker 运行 MongoDB

如果您本地没有安装 `MongoDB`，可以使用 `Docker` 快速启动一个 `MongoDB` 实例：

```bash
# 运行 MongoDB 容器
docker run --name mongo-test -p 27017:27017 -d mongo:latest

# 验证容器是否正在运行
docker ps

# 如果需要停止容器
docker stop mongo-test

# 如果需要删除容器
docker rm mongo-test
```

如果需要带认证的 `MongoDB`：

```bash
# 运行带认证的 MongoDB
docker run --name mongo-test -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=admin -e MONGO_INITDB_ROOT_PASSWORD=password -d mongo:latest

# 记得相应地更新 config.yaml：
# mongo:
#   database: "user"
#   address: "mongodb://admin:password@127.0.0.1:27017/test?retryWrites=true"
```

## 运行示例

1. 确保 `MongoDB` 服务器正在运行
2. 根据需要更新 `config.yaml`
3. 运行示例：

```bash
go run main.go
```




## 更多参考

更多 `MongoDB` 的使用方法请参考官方 `MongoDB` Go 驱动 [github.com/mongodb/mongo-go-driver](https://github.com/mongodb/mongo-go-driver)。
