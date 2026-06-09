---
title: Polaris
slug: /examples/registry/polaris
keywords: [注册中心, polaris, 服务发现, goframe]
description: 演示在GoFrame中全面集成腾讯云Polaris服务注册中心实现服务网格和流量管理。本示例展示了使用高级配置选项向Polaris注册服务、与熔断器和限流集成的服务发现、健康检查配置和自动实例隔离、服务路由和流量管理、与Polaris网格集成实现统一治理、以及无缝的GoFrame组件集成。主要功能包括:服务网格注册中心、流量控制策略、熔断器模式、基于健康的路由、金丝雀部署支持、生产级模式。适合在腾讯云上构建云原生微服务、实现服务网格架构、通过流量管理确保高可用性、以及实现带统一控制面板的高级服务治理。
hide_title: true
sidebar_position: 1
---

# 注册中心 - `Polaris` 集成

## 简介

本示例演示了如何在 `GoFrame` 应用程序中集成 `Polaris` 服务注册中心。主要展示：
- 使用 `Polaris` 注册服务
- 使用 `Polaris` 发现服务
- 实现服务健康检查
- 构建分布式系统

## 目录结构

```text
.
├── client/           # 客户端示例
│   └── client.go     # 基于Polaris的服务发现客户端实现
├── server/           # 服务器示例
│   └── server.go     # 基于Polaris的服务注册服务器实现
├── go.mod            # Go模块文件
└── go.sum            # Go模块校验和
```

## 功能特性

本示例展示了以下功能：

1. 服务注册
   - 自动服务注册
   - 健康检查配置
   - 元数据管理
   - 服务路由
   - 限流控制

2. 服务发现
   - 动态服务发现
   - 负载均衡
   - 故障转移支持
   - 熔断机制
   - 容错处理

3. 协议支持
   - `HTTP` 服务
   - 自定义协议
   - 协议扩展

## 环境要求

- `Go` `1.22` 或更高版本
- `Polaris` 服务器
- 本地缓存目录读写权限

## 使用说明

1. 配置 `Polaris` 服务器地址：
   ```go
   conf := config.NewDefaultConfiguration([]string{"183.47.111.80:8091"})
   ```

2. 配置本地缓存：
   ```go
   conf.Consumer.LocalCache.SetPersistDir("/tmp/polaris/backup")
   api.SetLoggersDir("/tmp/polaris/log")
   ```

3. 启动服务器：
   ```bash
   cd server
   go run server.go
   ```

4. 运行客户端：
   ```bash
   cd client
   go run client.go
   ```

## 实现说明

1. 服务器实现
   - 使用默认配置创建 `Polaris` 客户端
   - 配置本地缓存提升性能
   - 支持服务路由和限流配置
   - 提供健康检查和故障恢复

2. 客户端实现
   - 自动服务发现和负载均衡
   - 支持熔断和容错机制
   - 本地缓存提供离线能力
   - 自动重试和故障转移

## 高级特性

1. 本地缓存
   - 服务信息持久化
   - 离线运行支持
   - 性能优化

2. 可靠性保障
   - 熔断保护
   - 限流控制
   - 故障转移
   - 容错处理

## 注意事项

1. 确保配置正确的Polaris服务器地址
2. 本地缓存目录需要有读写权限
3. 建议开启日志记录便于调试
4. 合理配置熔断和限流参数
5. 注意监控服务健康状态
