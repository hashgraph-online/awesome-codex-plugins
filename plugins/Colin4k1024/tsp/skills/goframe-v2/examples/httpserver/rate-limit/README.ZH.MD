---
title: 访问限流
slug: /examples/httpserver/rate-limit
keywords: [http, 服务器, 限流, 中间件, goframe]
description: 演示在GoFrame HTTP服务器中实现限流功能用于API保护和流量控制。本示例展示了带有可配置限制的限流中间件配置、令牌桶和滑动窗口算法、按IP和按用户的限流策略、自定义限流响应和头(X-RateLimit-*)、用于可扩展性的基于Redis的分布式限流、以及与GoFrame中间件链集成。主要功能包括:灵活的限流策略、分布式限流支持、每个端点的自定义限制规则、优雅的限流响应、监控和指标集成、生产级模式。非常适合保护API免受滥用和DDoS攻击、实现公平使用策略、确保负载下的服务稳定性、管理API配额和计费、以及启用多层服务级别。通过本示例可以学习限流算法、如何实现高效的流量控制、以及构建安全可靠的API服务。
hide_title: true
sidebar_position: 2
---

# HTTP 服务器限流

## 介绍

本示例展示了如何在使用 `GoFrame` 的 HTTP 服务器中实现限流。
它展示了如何使用 `golang.org/x/time/rate` 包实现的令牌桶算法来保护 `API` 端点免受过多请求的影响。


## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 目录结构

- `go.mod`: Go 模块文件
- `main.go`: 主程序入口

## 使用说明

1. 启动服务器：
   ```bash
   go run main.go
   ```

2. 测试限流：
   ```bash
   # 正常请求
   curl http://localhost:8000/hello?name=world
   
   # 快速发送多个请求测试限流
   for i in {1..20}; do curl http://localhost:8000/hello?name=world; done
   ```
