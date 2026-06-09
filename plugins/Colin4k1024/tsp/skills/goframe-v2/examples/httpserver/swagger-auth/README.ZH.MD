---
title: Swagger认证
slug: /examples/httpserver/swagger-auth
keywords: [http, server, swagger, auth, basic auth, goframe]
description: 演示使用GoFrame实现带有基础认证集成的Swagger API文档用于安全的API文档访问。本示例展示了Swagger UI与GoFrame HTTP服务器集成、Swagger端点的基础认证保护、OpenAPI规范生成和服务、文档访问的认证中间件、自定义Swagger UI配置、以及与GoFrame路由系统集成。主要功能包括:受保护的API文档、自动OpenAPI规范生成、带认证的交互式API测试、可自定义的Swagger UI主题、基于凭据的访问控制、开发友好的模式。非常适合保护生产环境中的API文档、提供内部API的认证访问、实现带认证的交互式API测试、记录和保护REST API、以及维护带访问控制的API规范。通过本示例可以学习如何保护Swagger文档、集成OpenAPI规范、以及构建安全的API文档系统。
hide_title: true
---

# HTTP服务器Swagger认证

## 描述

本示例演示了如何使用`GoFrame`框架为`Swagger API`文档实现基础认证（`Basic Authentication`）。示例包含以下功能：

1. 设置带有`OpenAPI/Swagger`文档的基础HTTP服务器
2. 使用基础认证保护`Swagger`文档
3. 定义并实现一个简单的`REST API`端点

## 依赖要求

- [Go](https://golang.org/dl/) 1.22或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)

## 目录结构

```text
.
├── README.MD       # 英文文档
├── README.ZH.MD    # 中文文档
├── go.mod          # Go模块文件
└── main.go         # 主程序入口
```

## 特性

- `OpenAPI/Swagger`文档集成
- API文档的基础认证保护
- `RESTful API`端点实现
- 请求/响应验证
- `API`文档注释

## 安装设置

1. 克隆仓库：
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/httpserver/swagger-auth
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

2. 访问受保护的`Swagger`文档：
   - 地址：http://localhost:8000/swagger
   - 基础认证凭据：
     - 用户：`admin`
     - 密码：`123456`

3. 测试API端点：
   - 访问地址：http://localhost:8000/hello?name=GoFrame
   - 请求方法：`GET`
   - 响应：包含问候消息的`JSON`

## 实现细节

本示例展示了几个关键特性：

1. `Swagger`集成：
   - `OpenAPI JSON`地址：`/api.json`
   - `Swagger UI`地址：`/swagger`
   - 两者都受基础认证保护

2. 基础认证：
   - 用户：`admin`
   - 密码：`123456`
   - 认证域：`Restricted`

3. API端点：
   - 路径：`/hello`
   - 方法：`GET`
   - 必需参数：`name`
   - 响应：带有问候消息的`JSON`

## 注意事项

- 基础认证使用`GoFrame`内置的`BasicAuth`方法实现
- `API`文档根据代码注释和结构体标签自动生成
- 服务器默认运行在`8000`端口
- 所有`API`响应都通过中间件自动包装成标准格式
