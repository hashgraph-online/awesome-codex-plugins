---
title: 反向代理
slug: /examples/httpserver/proxy
keywords: [http, 服务器, 代理, 反向代理, goframe]
description: 演示使用GoFrame实现反向代理服务器以进行请求转发和负载分发。本示例展示了带有目标后端服务器的反向代理设置和配置、带有头保留的HTTP请求和响应转发、自定义头操作和转换、连接池和keepalive管理、错误处理和故障转移逻辑、以及与GoFrame中间件系统集成。主要功能包括:灵活的代理配置、透明请求转发、响应流支持、自定义路由规则、负载均衡集成、生产级模式。适合构建API网关和服务代理、实现微服务路由、添加认证和限流层、实现A/B测试和金丝雀部署、以及创建开发代理服务器。
hide_title: true
sidebar_position: 1
---

# HTTP 服务器代理

## 介绍

本示例展示了如何使用 `GoFrame` 创建一个反向代理服务器。示例包含两个服务器：

1. 在 `8198` 端口运行的后端服务器，提供实际服务
2. 在 `8000` 端口运行的代理服务器，将请求转发到后端服务器

代理服务器实现了以下功能：
- 使用 `httputil.NewSingleHostReverseProxy` 实现反向代理功能
- 自定义代理失败的错误处理
- `URL` 路径重写
- 请求体处理
- 详细的代理操作日志


## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 使用说明

1. 运行服务:
   ```bash
   go run main.go
   ```

2. 服务监听两个端口:
   - 后端服务器在 http://127.0.0.1:8198
   - 代理服务器在 http://127.0.0.1:8000

3. 测试代理:
   - 通过代理访问：http://127.0.0.1:8000/proxy/user/1
   - 直接访问后端：http://127.0.0.1:8198/user/1

