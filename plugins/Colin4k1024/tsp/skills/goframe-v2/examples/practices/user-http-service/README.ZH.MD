---
title: HTTP项目示例
slug: /examples/practices/user-http-service
keywords: [http, 用户, 服务, crud, mysql, dao, goframe, rest api, 认证, 会话, 中间件, swagger, openapi, web服务, 后端, 注册, 登录, 授权, jwt, 用户管理, 接口文档]
description: 演示基于HTTP RESTful API的用户管理服务，包含用户注册、登录、登出等功能。展示Session会话管理、中间件认证授权、OpenAPI文档生成、MySQL数据库集成、DAO模式数据访问等特性。适合学习GoFrame框架构建Web API服务和用户认证系统的开发者。
hide_title: true
---

# 用户 HTTP 服务实践

## 介绍

本示例展示了一个完整的基于`HTTP RESTful API`和`GoFrame`框架的用户管理服务。该示例包含：
- 用户注册、登录和登出功能
- 基于会话的认证和授权机制
- 用于上下文注入和认证的`HTTP`中间件
- 自动生成的`OpenAPI`文档和`Swagger` UI
- `MySQL`数据库集成与`DAO`模式数据访问
- 请求参数验证和错误处理
- 生产级项目结构组织

## 目录结构

```text
.
├── api/                   # API 定义
│   └── user/              # 用户服务 API
│       ├── user.go        # 用于API完整性实现的检测接口(自动生成)
│       └── v1/            # API定义，v1版本
├── hack/                  # 开发工具
│   └── config.yaml        # CLI 工具配置
├── internal/              # 内部包
│   ├── cmd/               # 命令定义
│   │   └── cmd.go         # 主命令与服务器设置
│   ├── consts/            # 常量
│   ├── controller/        # HTTP 控制器
│   │   └── user/          # 用户控制器(自动生成+补充实现)
│   ├── dao/               # 数据访问对象(自动生成)
│   ├── model/             # 数据模型
│   │   ├── do/            # 领域对象(自动生成)
│   │   └── entity/        # 数据库实体(自动生成)
│   └── service/           # 业务逻辑
│       ├── bizctx/        # 业务上下文服务
│       ├── middleware/    # 中间件服务
│       ├── session/       # 会话服务
│       └── user/          # 用户服务
├── manifest/              # 部署清单
│   ├── config/            # 配置文件
│   │   └── config.yaml    # 应用配置
│   ├── deploy/            # 部署文件
│   ├── docker/            # Docker 文件
│   └── sql/               # SQL 脚本
│       └── create.sql     # 数据库表结构
├── main.go                # 应用入口
├── go.mod                 # Go 模块文件
└── Makefile               # 构建自动化
```

## 功能特性

本示例展示了以下功能特性：

### 用户管理
- 用户注册（`SignUp`）并检查重复
- 用户认证（`SignIn`）并验证密码
- 用户登出（`SignOut`）并清理会话
- 已认证用户的用户资料查询（`Profile`）
- 用户名/昵称可用性检查

### 认证与授权
- 基于会话的用户认证
- 用于请求处理的自定义业务上下文
- 基于中间件的授权机制
- 需要认证的受保护路由
- 跨域请求的`CORS` 支持

### 接口文档
- 自动生成的`OpenAPI`规范
- 交互式`Swagger UI`位于`/swagger`
- `API`文档位于`/api.json`
- 请求/响应结构定义
- 接口描述和标签

### 数据库集成
- `MySQL`数据库连接
- `DAO`模式数据访问
- 自动生成`DAO`、`DO`和`Entity`代码
- 事务支持
- 带验证的查询构建器

### 请求处理
- 自动的请求/响应`JSON`处理
- 使用`v`标签的内置验证
- 标准化响应格式
- 错误处理和状态码
- `HTTP`方法的路由映射

## 环境要求

- [Go](https://golang.org/dl/) `1.23`或更高版本
- [MySQL](https://www.mysql.com/) `5.7`或更高版本

## 前置准备

### 安装 GoFrame CLI 工具

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
  --name mysql-user-http \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=12345678 \
  -e MYSQL_DATABASE=test \
  mysql:8.0
```

### 初始化数据库

执行`SQL`脚本创建用户表：

```bash
# 连接到 MySQL
docker exec -i mysql-user-http mysql -uroot -p12345678 test < manifest/sql/create.sql
```

或者手动执行以下 SQL：

```sql
CREATE TABLE `user`(
    `id`        int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'User ID',
    `passport`  varchar(45) NOT NULL COMMENT 'User Passport',
    `password`  varchar(45) NOT NULL COMMENT 'User Password',
    `nickname`  varchar(45) NOT NULL COMMENT 'User Nickname',
    `create_at` datetime DEFAULT NULL COMMENT 'Created Time',
    `update_at` datetime DEFAULT NULL COMMENT 'Updated Time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 配置说明

在`manifest/config/config.yaml`中更新数据库配置：

```yaml
server:
  address: ":8000"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"

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


### 运行服务器

启动`HTTP`服务器：

```bash
go run main.go
```

服务器将在端口`8000`上启动，提供以下接口：
- `Swagger UI`：http://localhost:8000/swagger
- `OpenAPI`规范：http://localhost:8000/api.json

### 测试服务

#### 使用 Swagger UI

在浏览器中打开 http://localhost:8000/swagger ，使用内置的`Swagger`界面与`API`交互。

#### 使用 cURL

1. **注册** - 注册新用户：
   ```bash
   curl -X POST http://localhost:8000/user/sign-up \
     -H "Content-Type: application/json" \
     -d '{
       "Passport": "user001",
       "Password": "123456",
       "Password2": "123456",
       "Nickname": "测试用户"
     }'
   ```

2. **检查账号可用性**：
   ```bash
   curl -X POST http://localhost:8000/user/check-passport \
     -H "Content-Type: application/json" \
     -d '{"Passport": "user001"}'
   ```

3. **登录** - 用户认证：
   ```bash
   curl -X POST http://localhost:8000/user/sign-in \
     -H "Content-Type: application/json" \
     -d '{
       "Passport": "user001",
       "Password": "123456"
     }' \
     -c cookies.txt
   ```

4. **检查登录状态**：
   ```bash
   curl -X POST http://localhost:8000/user/is-signed-in \
     -b cookies.txt
   ```

5. **获取用户资料**（需要认证）：
   ```bash
   curl -X GET http://localhost:8000/user/profile \
     -b cookies.txt
   ```

6. **登出**：
   ```bash
   curl -X POST http://localhost:8000/user/sign-out \
     -b cookies.txt
   ```

## 接口文档

### 公开接口

#### SignUp
**POST** `/user/sign-up`

注册新用户账号。

**请求体：**
```json
{
  "Passport": "string (6-16 字符，必填)",
  "Password": "string (6-16 字符，必填)",
  "Password2": "string (必须与 Password 相同，必填)",
  "Nickname": "string (可选)"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

#### SignIn
**POST** `/user/sign-in`

用户认证并创建会话。

**请求体：**
```json
{
  "Passport": "string (必填)",
  "Password": "string (必填)"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

#### CheckPassport
**POST** `/user/check-passport`

检查账号是否可用于注册。

**请求体：**
```json
{
  "Passport": "string (必填)"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

#### CheckNickname
**POST** `/user/check-nickname`

检查昵称是否可用于注册。

**请求体：**
```json
{
  "Nickname": "string (必填)"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

#### IsSignedIn
**POST** `/user/is-signed-in`

检查当前用户是否已登录。

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {
    "OK": true
  }
}
```

#### SignOut
**POST** `/user/sign-out`

登出当前用户并清除会话。

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {}
}
```

### 受保护接口

#### Profile
**GET** `/user/profile`

获取当前已登录用户的资料（需要认证）。

**响应：**
```json
{
  "code": 0,
  "message": "",
  "data": {
    "id": 1,
    "passport": "user001",
    "nickname": "测试用户",
    "create_at": "2026-02-10 10:30:00",
    "update_at": "2026-02-10 10:30:00"
  }
}
```

## 实现细节

### Controller 层

`internal/controller/user/`处理`HTTP`请求：
- 接收并验证请求参数
- 调用`Service`层处理业务逻辑
- 返回标准化的`JSON`响应
- 从`g.Meta`标签自动绑定路由

### Service 层

`internal/service/`包含业务逻辑：

#### 用户服务
- 带验证的用户创建
- 认证和会话管理
- 用户资料查询
- 账号/昵称可用性检查

#### 中间件服务
- 自定义业务数据的上下文注入
- 受保护路由的认证中间件
- 跨域支持的 `CORS` 中间件

#### 会话服务
- 用户会话管理
- 会话存储和检索
- 请求中的用户上下文

#### 业务上下文服务
- 自定义上下文数据注入
- 请求上下文中的用户信息
- 会话集成

### DAO 层

`internal/dao/`提供数据库访问：
- 从数据库`Schema`自动生成
- 类型安全的数据库操作
- 链式查询构建器
- 事务支持

### 数据模型

- **DO (Domain Object)：** 用于数据库操作
- **Entity：** 表示数据库表结构
- **API Models：** 带验证的请求/响应结构

## 其他操作

### 构建 Docker 镜像

```bash
make image
```

### 部署到 Kubernetes

```bash
make deploy
```

## 注意事项

- 启动应用前请确保 `MySQL` 已运行
- 默认数据库凭据为 `root:12345678`（生产环境请修改）
- 服务默认使用端口 `8000`
- 会话默认存储在内存中（生产环境请配置 Redis）
- 密码应在生产环境中加密（这是演示项目）
- `Swagger UI`位于 http://localhost:8000/swagger
- `OpenAPI`规范位于 http://localhost:8000/api.json
- `SQL Schema`位于`manifest/sql/create.sql`

## 安全建议

这是一个演示项目。生产环境使用时请考虑：
- 使用`bcrypt`或类似方式加密密码
- 使用`HTTPS`进行安全通信
- 实现速率限制
- 添加`CSRF`保护
- 使用`Redis`或类似方式存储会话
- 实现适当的日志记录和监控
- 使用`JWT`令牌实现无状态认证