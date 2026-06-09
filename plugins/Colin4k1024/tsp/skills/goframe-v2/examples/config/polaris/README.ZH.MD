---
title: Polaris
slug: /examples/config/polaris
keywords: [配置中心, polaris, goframe]
description: 演示如何在GoFrame应用程序中无缝集成腾讯云Polaris配置中心实现服务网格配置管理。本示例展示了Polaris客户端的设置与初始化、GoFrame配置组件适配器的实现、动态配置加载与热更新、实时配置监听与同步、命名空间和文件分组管理、完善的错误处理和日志记录、以及安全的配置值获取。主要功能包括:通过Polaris实现集中式配置管理、支持多命名空间和配置分组、自动配置刷新能力、与Polaris服务网格集成实现统一服务治理、类型安全的配置访问、生产级监控能力。非常适合构建基于腾讯云或使用Polaris网格的云原生微服务应用,特别是需要动态配置、服务发现、流量管理、统一配置治理的场景。通过本示例可以深入学习Polaris在配置管理和服务网格方面的企业级应用实践。
hide_title: true
sidebar_position: 1
---

# `Polaris` 配置中心示例

## 介绍

本示例展示了如何在 `GoFrame` 应用程序中通过配置管理组件集成 `Polaris` 配置中心。

## 目录结构

```text
.
├── boot/           # 启动配置
│   └── boot.go     # Polaris 客户端初始化
├── main.go         # 主程序入口
├── go.mod          # Go 模块文件
└── go.sum          # Go 模块校验和
```

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [GoFrame Polaris Config](https://github.com/gogf/gf/tree/master/contrib/config/polaris)
- [Polaris Server](https://polarismesh.cn/)

## 使用说明

1. 启动 `Polaris`：
   ```bash
   docker run -d --name polaris \
      -p 8090:8090 -p 8091:8091 -p 8093:8093 -p 9090:9090 -p 9091:9091 \
      polarismesh/polaris-standalone:v1.17.2
   ```

2. 启动服务：
   ```bash
   go run main.go
   ```
