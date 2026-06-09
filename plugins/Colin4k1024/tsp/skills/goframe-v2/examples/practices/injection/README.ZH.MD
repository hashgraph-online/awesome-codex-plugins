---
title: 依赖注入
slug: /examples/practices/injection
keywords: [依赖注入, 测试, goframe, di]
description: 演示在GoFrame框架中使用do包实现依赖注入模式的全面示例。展示了如何通过接口抽象实现松耦合架构、使用do包管理依赖关系、注册和解析服务实例、单例模式管理、接口注入与实现替换、以及单元测试Mock实现。包含User服务、Gateway网关等实际应用场景，演示了服务分层、接口定义、实现注册、依赖解析等完整流程。非常适合微服务架构开发、可测试代码编写、模块化系统设计、接口驱动开发、以及需要灵活依赖管理的企业级应用。通过本示例可以学习如何构建高可维护、易测试的Go应用程序。
hide_title: true
---

# 依赖注入示例

## 简介

本示例展示了如何在使用`GoFrame`的应用程序中实现依赖注入。

主要演示：
1. 使用大仓模式管理代码仓库
2. 基础依赖注入设置
3. 使用`DI`的服务层实现
4. 集成`gRPC`的控制器层
5. 使用模拟依赖的单元测试

实现重点在于使核心业务逻辑易于测试：
- 使用依赖注入分离关注点
- 为服务依赖提供清晰的接口
- 每一层都可以独立执行单元测试，保障代码质量

## 环境要求

- [Go](https://golang.org/dl/) `1.22` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- [MongoDB](https://www.mongodb.com)
- [Redis](https://redis.io)
- [github.com/samber/do](https://github.com/samber/do)

## 目录结构

```text
injection/
├── app/
│   ├── gateway/         # API网关服务,调用user grpc服务实现HTTP接口
│   │   ├── api/         # API定义
│   │   ├── internal/    # 内部实现
│   │   │   ├── cmd/         # 命令行工具
│   │   │   ├── controller/  # 控制器
│   │   │   ├── model/       # 数据模型
│   │   │   └── service/     # 业务逻辑
│   │   └── manifest/   # 配置文件
│   └── user/           # 用户微服务
│       ├── api/        # API定义
│       │   ├── entity/ # 实体定义
│       │   └── user/   # 用户API pb
│       ├── internal/   # 内部实现
│       │   ├── cmd/         # 命令行工具
│       │   ├── controller/  # 控制器
│       │   ├── dao/         # 数据访问对象
│       │   ├── model/       # 数据模型
│       │   └── service/     # 业务逻辑
│       └── manifest/   # 配置文件
├── hack/               # 开发工具
└── utility/            # 通用工具
    ├── injection/      # DI工具
    └── mongohelper/    # MongoDB辅助工具
```

## 功能特性

- 依赖注入使用
- `MongoDB`和`Redis`集成
- `gRPC`服务实现
- 完整的单元测试
- 清理资源的关闭处理
- 命名依赖支持

## 安装设置

1. 克隆仓库：
    ```bash
    git clone https://github.com/gogf/examples.git
    cd examples/practices/injection
    ```

2. 安装依赖：
    ```bash
    go mod tidy
    ```

3. 使用`Docker`启动所需服务：
    ```bash
    # 启动MongoDB
    docker run -d --name mongo -p 27017:27017 mongo:latest

    # 启动Redis
    docker run -d --name redis -p 6379:6379 redis:latest
    ```

## 使用方法

1. 运行`gRPC Server`服务：
   ```bash
   cd examples/practices/injection/app/user
   go run main.go server
   ```

2. 运行`HTTP Server`服务：
   ```bash
   cd examples/practices/injection/app/gateway
   go run main.go server
   ```

3. （可选）运行异步守护进程，仅演示多命令功能，无实际逻辑：
   ```bash
   cd examples/practices/injection/app/gateway
   go run main.go worker
   ```
   
4. （可选）运行测试：
   ```bash
   go test ./...
   ```

## 实现细节

### 依赖注入设置
- 使用`github.com/samber/do`包进行依赖管理
- 支持命名和未命名依赖管理
- 提供常用操作的辅助函数

### 服务层

- 清晰的关注点分离
- 基于接口的设计
- 易于使用模拟实现进行测试

### 控制器层
- 支持`DI`的`gRPC`集成
- 清晰的错误处理
- 合理的资源管理

### 可测试性
- 数据层(`dao`)、业务层(`service`)、接口层(`controller`)完整的单元测试
- 依赖模拟，单元测试使用的数据库配置通过`manifest/config`管理
- 通过配置文件管理微服务链接的服务地址或者域名，以便于控制依赖的服务模拟

## 注意事项

- 依赖注入的注册时，需要在`Shutdown`方法中正确清理资源
- 使用依赖注入时，如果需要同类型的多个实例时使用命名依赖

