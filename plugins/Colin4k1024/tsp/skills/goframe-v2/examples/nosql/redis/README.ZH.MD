---
title: Redis 
slug: /examples/nosql/redis
keywords: [nosql, redis, cache, database, goframe]
description: 演示在GoFrame中全面集成Redis用于缓存、会话存储和数据持久化。本示例展示了使用GoFrame的redis组件进行Redis连接设置和配置、基本操作包括GET/SET/DEL、数据结构操作(字符串、哈希、列表、集合、有序集合)、TTL和过期管理、管道和事务支持、发布/订阅消息模式、以及连接池配置。主要功能包括:支持单机和集群模式、自动连接管理、错误处理和重试逻辑、与GoFrame缓存组件集成、序列化和反序列化助手、生产级模式。非常适合实现应用缓存、会话管理、限流、分布式锁、实时消息、以及在微服务架构中实现高性能数据存储。通过本示例可以学习如何在GoFrame中使用Redis、Redis数据结构的最佳实践、以及构建高性能缓存系统。
hide_title: true
sidebar_position: 1
---

# GoFrame Redis 示例

此示例演示了如何在 `GoFrame` 框架中使用 `Redis`。

## 概述

本示例展示了：
1. 如何使用 `YAML` 配置文件配置 `Redis` 连接
2. 如何创建 `Redis` 客户端
3. 基本的 `Redis` 操作（`SET/GET`）

## 环境要求

- `Go 1.15` 或更高版本
- `Redis` 服务器
- `GoFrame v2`

## 代码结构

- `main.go`: 包含主要逻辑和 `Redis` 客户端初始化
- `config.yaml`: `Redis` 配置文件

## 配置说明

`Redis` 配置存储在 `config.yaml` 文件中：

```yaml
redis:
  address: "127.0.0.1:6379"
  password:
```

您可以根据自己的 `Redis` 服务器配置修改这些设置。

## 使用 Docker 运行 Redis

如果您本地没有安装 `Redis`，可以使用 `Docker` 快速启动一个 `Redis` 实例：

```bash
# 运行 Redis 容器
docker run --name redis-test -p 6379:6379 -d redis:latest

# 验证容器是否正在运行
docker ps

# 如果需要停止容器
docker stop redis-test

# 如果需要删除容器
docker rm redis-test
```

如果需要带密码认证的 `Redis`：

```bash
# 运行带密码的 Redis
docker run --name redis-test -p 6379:6379 -d redis:latest redis-server --requirepass your_password

# 记得相应地更新 config.yaml：
# redis:
#   address: "127.0.0.1:6379"
#   password: "your_password"
```

## 运行示例

1. 确保 `Redis` 服务器正在运行
2. 根据需要更新 `config.yaml`
3. 运行示例：

```bash
go run main.go
```




## 更多参考

更多 `Redis` 的使用方法请参考第三方组件 [github.com/redis/go-redis](https://github.com/redis/go-redis)。
