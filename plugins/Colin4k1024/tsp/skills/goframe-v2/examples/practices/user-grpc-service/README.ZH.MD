---
title: gRPC项目示例
slug: /examples/practices/user-grpc-service
keywords: [grpc, 用户, 服务, crud, mysql, dao, goframe, 微服务, protobuf, 数据库, 用户管理, 认证, 接口, 后端服务, web服务, 依赖注入, 业务逻辑, 数据访问, 模型, 实体]
description: 演示基于gRPC的用户管理微服务，包含用户增删改查操作。展示Protocol Buffers协议定义、MySQL数据库集成、DAO模式数据访问、Service层业务逻辑封装等特性。适合学习GoFrame框架构建gRPC微服务和掌握微服务架构的开发者。
hide_title: true
---

# 用户 gRPC 服务实践

## 介绍

本示例展示了一个完整的基于`gRPC`和`GoFrame`框架构建的用户微服务。该示例包含：
- 用户的完整`CRUD`操作（创建、查询、列表、删除）
- 基于`Protocol Buffers`的`gRPC`服务实现
- `MySQL`数据库集成与`DAO`模式数据访问
- `Service`层业务逻辑封装
- 从数据库`Schema`自动生成代码
- 生产级项目结构组织

## 目录结构

```text
.
├── api/                   # API 定义
│   ├── pbentity/          # 自动生成的protobuf实体(自动生成)
│   └── user/              # 用户服务 API
│       └── v1/            # API版本v1(自动生成)
├── hack/                  # 开发工具
│   └── config.yaml        # CLI 工具配置
├── internal/              # 内部包
│   ├── cmd/               # 命令定义
│   ├── consts/            # 常量
│   ├── controller/        # gRPC 控制器
│   │   └── user/          # 用户控制器
│   ├── dao/               # 数据访问对象(自动生成)
│   ├── model/             # 数据模型
│   │   ├── do/            # 领域对象(自动生成)
│   │   └── entity/        # 数据库实体(自动生成)
│   └── service/           # 业务逻辑
│       └── user/          # 用户服务
├── manifest/              # 部署清单
│   ├── config/            # 配置文件
│   │   └── config.yaml    # 应用配置
│   ├── deploy/            # 部署文件
│   ├── docker/            # Docker 文件
│   ├── protobuf/          # Protocol Buffer 定义
│   │   ├── pbentity/      # 实体定义(自动生成)
│   │   └── user/          # 用户服务定义
│   └── sql/               # SQL 脚本
│       └── create.sql     # 数据库表结构
├── main.go                # 应用入口
├── go.mod                 # Go 模块文件
└── Makefile               # 构建自动化
```

## 功能特性

本示例展示了以下功能特性：

### 服务实现
- 基于`Protocol Buffers`的`gRPC`服务器
- 用户`CRUD`操作（`Create`、`GetOne`、`GetList`、`Delete`）
- 请求参数验证
- 错误处理
- 上下文管理

### 数据库集成
- `MySQL`数据库连接
- `DAO`模式数据访问
- 自动生成`DAO`、`DO`和`Entity`代码
- 事务支持
- 查询构建器

### 项目组织
- 标准`GoFrame`项目结构
- 关注点分离（`Controller`、`Service`、`DAO`）
- 配置管理
- 日志支持
- `Makefile`构建自动化

## 环境要求

- [Go](https://golang.org/dl/) `1.23`或更高版本
- [MySQL](https://www.mysql.com/) `5.7`或更高版本
- [Protocol Buffers 编译器](https://grpc.io/docs/protobuf/)

## 前置准备

### 安装GoFrame CLI工具

```bash
go install github.com/gogf/gf/cmd/gf/v2@latest
```

或者使用 `Makefile`：

```bash
make cli
```

### 配置 MySQL 数据库

使用`Docker`运行`MySQL`数据库：

```bash
docker run -d \
  --name mysql-user-service \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=12345678 \
  -e MYSQL_DATABASE=test \
  mysql:8.0
```

### 初始化数据库

执行`SQL`脚本创建用户表：

```bash
# 连接到 MySQL
docker exec -i mysql-user-service mysql -uroot -p12345678 test < manifest/sql/create.sql
```

或者手动执行以下`SQL`：

```sql
CREATE TABLE `user` (
    `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'User ID',
    `passport` varchar(45) NOT NULL COMMENT 'User Passport',
    `password` varchar(45) NOT NULL COMMENT 'User Password',
    `nickname` varchar(45) NOT NULL COMMENT 'User Nickname',
    `create_at` datetime DEFAULT NULL COMMENT 'Created Time',
    `update_at` datetime DEFAULT NULL COMMENT 'Updated Time',
    `delete_at` datetime DEFAULT NULL COMMENT 'Deleted Time',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_passport` (`passport`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 配置说明

在`manifest/config/config.yaml`中更新数据库配置：

```yaml
database:
  default:
    link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
    debug: true
```

## 使用说明

### 生成代码

从数据库生成`DAO`、`DO`和`Entity`代码：

```bash
make dao
```

生成`Protocol Buffer Go`文件：

```bash
make pb
```

从数据库生成`Protocol Buffer`实体文件：

```bash
make pbentity
```

### 运行服务器

启动`gRPC`服务器：

```bash
go run main.go
```

服务器将在端口`8000`上启动。

### 测试服务

可以使用`gRPC`客户端测试服务。以下是使用`grpcurl`的示例：

1. 安装 `grpcurl`：
   ```bash
   brew install grpcurl
   ```

2. 列出可用的服务：
   ```bash
   grpcurl -plaintext localhost:8000 list
   ```

3. 创建用户：
   ```bash
   grpcurl -plaintext -d '{"Passport":"user001","Password":"123456","Nickname":"测试用户"}' \
     localhost:8000 user.User/Create
   ```

4. 根据 ID 查询用户：
   ```bash
   grpcurl -plaintext -d '{"Id":1}' \
     localhost:8000 user.User/GetOne
   ```

5. 获取用户列表：
   ```bash
   grpcurl -plaintext -d '{"Page":1,"Size":10}' \
     localhost:8000 user.User/GetList
   ```

6. 删除用户：
   ```bash
   grpcurl -plaintext -d '{"Id":1}' \
     localhost:8000 user.User/Delete
   ```

## 接口文档

### 用户服务

#### Create

创建新用户。

**请求：**
```protobuf
message CreateReq {
    string Passport = 1; // 必填
    string Password = 2; // 必填
    string Nickname = 3; // 必填
}
```

**响应：**
```protobuf
message CreateRes {}
```

#### GetOne

根据`ID`获取用户详情。

**请求：**
```protobuf
message GetOneReq {
    uint64 Id = 1; // 必填
}
```

**响应：**
```protobuf
message GetOneRes {
    pbentity.User User = 1;
}
```

#### GetList

获取分页用户列表。

**请求：**
```protobuf
message GetListReq {
    int32 Page = 1;
    int32 Size = 2;
}
```

**响应：**
```protobuf
message GetListRes {
    repeated pbentity.User Users = 1;
}
```

#### Delete

根据`ID`删除用户。

**请求：**
```protobuf
message DeleteReq {
    uint64 Id = 1; // 必填，最小值：1
}
```

**响应：**
```protobuf
message DeleteRes {}
```

## 实现细节

### Controller 层

`internal/controller/user/user.go`实现了`gRPC`服务接口：
- 处理传入的`gRPC`请求
- 验证请求参数
- 调用`Service`层处理业务逻辑
- 返回格式化的响应

### Service 层

`internal/service/user/user.go`包含业务逻辑：
- 根据`ID`查询用户
- 删除用户
- 可扩展更复杂的业务规则

### DAO 层

`internal/dao/user.go`提供数据库访问：
- 从数据库`Schema`自动生成
- 提供类型安全的数据库操作
- 支持链式查询构建器

### 数据模型

- **DO (Domain Object)：** 用于数据库操作
- **Entity：** 表示数据库表结构
- **PBEntity：** 用于`API`响应的`Protocol Buffer`实体

## 开发指南

### 生成所有代码

```bash
# 生成 DAO 文件
make dao

# 生成 Service 文件
make service

# 生成 Protocol Buffer 文件
make pb

# 生成 Protocol Buffer Entity 文件
make pbentity
```

### 构建 Docker 镜像

```bash
make image
```

### 部署到 Kubernetes

```bash
make deploy
```

## 注意事项

- 启动应用前请确保`MySQL`已运行
- 默认数据库凭据为`root:12345678`（生产环境请修改）
- 服务默认使用端口`8000`
- `Protocol Buffer`文件位于`manifest/protobuf`
- `SQL Schema`位于`manifest/sql/create.sql`

