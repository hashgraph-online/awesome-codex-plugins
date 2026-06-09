---
title: 基本认证
slug: /examples/httpserver/basic-auth
keywords: [http, 服务器, 基本认证, 身份验证, goframe]
description: 演示在GoFrame中实现HTTP基础认证，用于简单的凭据基础访问控制。本示例展示了基础认证中间件的设置和配置、针对配置凭据的用户名和密码验证、Base64凭据编码和解码、用于浏览器提示的WWW-Authenticate头处理、受保护路由实现、自定义认证失败响应、以及与GoFrame中间件系统的集成。主要功能包括:无需外部依赖的简单认证、浏览器兼容的认证对话框、凭据验证模式、安全凭据存储建议、自定义领域配置、生产级错误处理。非常适合内部工具和管理面板、简单API保护、开发和测试环境、遗留系统集成、以及需要轻量级认证且无需复杂基础设施的应用程序。通过本示例可以学习HTTP基础认证的实现方法、如何在GoFrame中实现简单认证保护、以及基础认证的适用场景和注意事项。
hide_title: true
---

# HTTP 服务器基本认证

## 介绍

本示例展示了如何使用 `GoFrame` 框架实现 `HTTP` 基本认证（`Basic Authentication`）。基本认证是一种简单的认证机制，允许服务器在授予对受保护资源的访问权限之前请求客户端提供凭据。

示例展示了如何：
- 设置带有受保护资源的基本 HTTP 服务器
- 使用 `GoFrame` 内置的 `BasicAuth` 方法实现基本认证
- 处理认证成功和失败的情况
- 自定义认证领域（`realm`）消息

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 目录结构

```text
basic-auth/
├── README.MD     # 英文文档
├── README.ZH.MD  # 中文文档
├── go.mod        # Go 模块文件
└── main.go       # 主程序入口
```

## 功能特点

- 简单且安全的 `HTTP` 基本认证
- 自动处理认证头部
- 可自定义认证领域消息
- 清晰分离认证逻辑

## 安装设置

1. 克隆仓库：
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/basic-auth
    ```

2. 安装依赖：
    ```bash
    go mod tidy
    ```

3. 运行应用：
    ```bash
    go run main.go
    ```

## 使用方法

1. 启动服务器：
   ```bash
   go run main.go
   ```

2. 服务器将在 `8000` 端口启动。

3. 访问受保护的资源：
   - 网址：http://127.0.0.1:8000/
   - 当提示时，输入以下凭据：
     - 用户：`user`
     - 密码：`pass`

4. 认证成功后，您将看到消息："`Authentication successful!`"

## 实现细节

服务器使用 `GoFrame` 的 `BasicAuth` 方法实现 `HTTP` 基本认证。该方法：

1. 检查请求是否包含有效的基本认证凭据
2. 如果凭据缺失或无效，它会自动：
   - 设置带有指定领域的 `WWW-Authenticate` 头部
   - 返回 `401` 未授权状态码
   - 使浏览器显示认证对话框
3. 如果认证成功，它返回 `true` 并允许处理程序继续处理受保护的内容

实现非常简洁，只需要很少的代码：

```go
if r.BasicAuth("user", "pass", "Please enter username and password") {
    // 认证成功后的处理
    r.Response.Write("Authentication successful!")
}
// 如果认证失败，BasicAuth 方法会自动处理响应
```

## 注意事项

- 基本认证以 `base64` 编码传输凭据，在纯 `HTTP` 上不安全
- 在生产环境中，始终将基本认证与 `HTTPS` 结合使用
- 本示例中的凭据是硬编码的，仅用于演示目的；在实际应用中，应使用安全的凭据存储
