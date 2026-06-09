---
title: JSON数组响应
slug: /examples/httpserver/response-json-array
keywords: [http, 服务器, json, 数组, goframe]
description: 演示在GoFrame HTTP服务器中处理JSON数组响应用于RESTful API开发。本示例展示了返回JSON数组作为HTTP响应、适当的content-type头配置、带有自定义格式的数组序列化、大型数据集的分页支持、大型数组的高效内存管理、以及与GoFrame响应写入系统集成。主要功能包括:自动JSON序列化、适当的HTTP状态码、空数组处理、大型数据集的流式支持、错误响应格式化、RESTful API模式。非常适合构廻返回集合的REST API、实现列表和搜索端点、处理批量数据响应、确保一致的API响应格式、以及优化JSON序列化性能。通过本示例可以学习JSON数组响应的最佳实践、RESTful API设计、以及高效数据序列化。
hide_title: true
sidebar_position: 99
---

# HTTP 服务器 JSON 数组响应

## 介绍

本示例展示了如何使用 `GoFrame` 实现一个返回 `JSON` 数组响应的 `HTTP` 服务器。它展示了如何：
- 将 `API` 响应构造为 `JSON` 数组
- 配置 `OpenAPI/Swagger` 文档
- 使用 `GoFrame` 的中间件实现一致的响应处理
- 定义类型安全的请求和响应结构

本示例实现了一个返回 `JSON` 数组格式用户列表的 `/user` 端点。

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 目录结构

- `go.mod`: Go 模块文件
- `main.go`: 主程序入口

## 使用说明

1. 启动服务：
   ```bash
   go run main.go
   ```

2. 测试接口：http://localhost:8000/user

3. 接口文档：http://127.0.0.1:8000/swagger