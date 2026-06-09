---
title: Consul
slug: /examples/config/consul
keywords: [配置中心, consul, goframe]
description: 演示如何在GoFrame应用程序中全面集成HashiCorp Consul配置中心实现分布式配置管理。本示例展示了Consul客户端的设置与初始化、GoFrame配置组件的适配器实现、动态配置加载与解析、实时配置监听与更新、完善的错误处理和日志记录、以及安全的配置值获取。主要功能包括:通过Consul KV存储实现分布式配置管理、支持多数据中心和命名空间、自动配置同步、健康检查与服务发现集成、类型安全的配置访问、生产级错误处理机制。非常适合构建需要分布式配置管理、服务网格集成、多实例间配置一致性的云原生微服务应用。通过本示例可以学习如何使用Consul实现企业级分布式配置管理和服务治理。
hide_title: true
sidebar_position: 1
---

# `Consul` 配置中心示例

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中通过配置管理组件集成 `Consul` 配置中心。


## 目录结构

```text
.
├── boot/           # 启动配置
│   └── boot.go     # Consul 客户端初始化
├── main.go         # 主程序入口
├── go.mod          # Go 模块文件
└── go.sum          # Go 模块校验和
```

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Consul Config](https://github.com/gogf/gf/tree/master/contrib/config/consul)

## 使用说明

1. 确保 `Consul` 服务端已启动

2. 配置 `Consul` 连接信息：
   ```yaml
   consul:
     address: "localhost:8500"
     scheme: "http"
     datacenter: "dc1"
   ```

3. 运行示例：
   ```bash
   go run main.go
   ```
