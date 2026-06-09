---
title: Apollo
slug: /examples/config/apollo
keywords: [配置中心, apollo, goframe]
description: 演示如何在GoFrame应用程序中无缝集成Apollo配置中心实现集中式配置管理。本示例展示了Apollo客户端的初始化与配置、配置适配器的实现方法、动态配置加载与解析、实时配置更新机制、完善的错误处理和日志记录、以及配置值的获取方式。主要功能包括:通过Apollo实现集中式配置管理、支持多环境和命名空间、自动配置刷新能力、使用GoFrame配置组件进行类型安全的配置访问、生产级错误处理机制。适用于构建需要集中配置管理、无需重启即可动态更新配置、支持配置版本管理和回滚的微服务应用。通过本示例可以学习配置中心在分布式系统中的最佳实践。
hide_title: true
sidebar_position: 1
---

# `Apollo` 配置中心示例

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中通过配置管理组件集成 `Apollo` 配置中心。


## 目录结构

```text
.
├── boot/           # 启动配置
│   └── boot.go     # Apollo 客户端初始化
├── main.go         # 主程序入口
├── go.mod          # Go 模块文件
└── go.sum          # Go 模块校验和
```

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Apollo Config](https://github.com/gogf/gf/tree/master/contrib/config/apollo)

## 使用说明

1. 确保 `Apollo` 服务端已启动

2. 配置 `Apollo` 连接信息：
   ```yaml
   apollo:
     appId: "your-app-id"
     cluster: "default"
     namespaceName: "application"
     ip: "localhost:8080"
   ```

3. 运行示例：
   ```bash
   go run main.go
   ```
