---
title: '快速开发示例'
slug: '/docs/practices/quick-demo'
description: '基于GoFrame v2.10.0的快速入门HTTP RESTful API示例，展示用户CRUD操作、MySQL集成、OpenAPI/Swagger文档自动生成，以及标准项目结构的快速开发实践。'
keywords: [GoFrame, 快速开始, HTTP服务器, RESTful API, MySQL, CRUD操作, OpenAPI, Swagger, DAO模式, ORM, Web开发, Go框架, API开发, 数据库集成, 代码自动生成, 项目模板, 标准结构, 配置管理, 中间件, 响应处理]
hide_title: true
---

# 快速开发示例

## 简介

`quick-demo`是一个快速入门`HTTP`服务示例，展示如何使用`GoFrame`框架进行快速开发。它提供了完整的`RESTful API`实现，包含用户`CRUD`操作、`MySQL`数据库集成以及`OpenAPI/Swagger`文档自动生成。该示例遵循`GoFrame`的标准项目结构和最佳实践，是学习`GoFrame`或构建新项目的理想起点。

## 项目结构

```text
quick-demo/
├── api/                  # API接口定义
│   └── user/             # 用户服务 API
│       ├── user.go       # 用于API完整性实现的检测接口(自动生成)
│       └── v1/           # API定义，v1版本
├── internal/             # 内部实现
│   ├── cmd/              # 命令层
│   │   └── cmd.go        # 服务器初始化
│   ├── consts/           # 常量
│   ├── controller/       # 控制器层(自动生成 + 接口实现)
│   │   ├── hello/        # Hello控制器
│   │   └── user/         # 用户CRUD控制器
│   ├── dao/              # 数据访问对象（自动生成）
│   ├── model/            # 数据模型
│   │   ├── do/           # 数据对象（自动生成）
│   │   └── entity/       # 数据库实体（自动生成）
│   └── service/          # 业务逻辑层
├── manifest/             # 应用清单
│   ├── config/           # 配置文件
│   │   └── config.yaml   # 主配置
│   ├── deploy/           # 部署配置
│   ├── docker/           # Docker配置
│   └── i18n/             # 国际化
├── resource/             # 静态资源
├── utility/              # 工具函数
├── main.go               # 应用程序入口
└── go.mod                # Go模块定义
```

## 特性

- **RESTful API设计**：遵循`RESTful`规范的完整用户`CRUD`操作
- **MySQL集成**：使用`GoFrame`的`DAO`模式和`ORM`进行数据库操作
- **OpenAPI/Swagger**：自动生成`API`文档和`Swagger UI`
- **标准结构**：遵循`GoFrame`推荐的项目结构，具有良好的可扩展性
- **代码自动生成**：从数据库表结构自动生成`DAO`、`entity`和`model`代码
- **请求验证**：内置请求参数验证规则
- **配置管理**：基于`YAML`的配置，支持环境变量
- **中间件**：统一的响应处理中间件，确保`API`响应格式一致
- **Hello World示例**：简单示例展示基本的`HTTP`处理

## 要求

- `Go 1.23.0`或更高版本
- `MySQL 8.0`或更高版本

## 前置条件

**使用Docker启动MySQL：**

```bash
docker run -d \
  --name mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=12345678 \
  -e MYSQL_DATABASE=test \
  mysql:8.0
```

**创建用户表：**

```sql
CREATE TABLE `user` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'user id',
  `name` varchar(50) NOT NULL COMMENT 'user name',
  `status` int NOT NULL DEFAULT '0' COMMENT 'user status',
  `age` int unsigned NOT NULL COMMENT 'user age',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 安装

```bash
cd /path/to/examples/practices/quick-demo
go mod tidy
```

## 使用

**启动服务：**

```bash
go run main.go
```

服务将在`http://localhost:8000`启动。

**访问API文档：**

- `Swagger UI`: http://localhost:8000/swagger
- `OpenAPI`规范: http://localhost:8000/api.json

## API参考

### Hello API

**GET /hello**

返回"Hello World!"消息。

```bash
curl http://localhost:8000/hello
```

### 用户APIs

**创建用户**

`POST /user`

```bash
curl -X POST http://localhost:8000/user \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john",
    "age": 25
  }'
```

响应：
```json
{
  "code": 0,
  "message": "",
  "data": {
    "id": 1
  }
}
```

**更新用户**

`PUT /user/{id}`

```bash
curl -X PUT http://localhost:8000/user/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john_updated",
    "age": 26,
    "status": 0
  }'
```

**删除用户**

`DELETE /user/{id}`

```bash
curl -X DELETE http://localhost:8000/user/1
```

**获取单个用户**

`GET /user/{id}`

```bash
curl http://localhost:8000/user/1
```

响应：
```json
{
  "code": 0,
  "message": "",
  "data": {
    "id": 1,
    "name": "john",
    "status": 0,
    "age": 25
  }
}
```

**获取用户列表**

`GET /user`

```bash
# 获取所有用户
curl http://localhost:8000/user

# 按年龄过滤
curl "http://localhost:8000/user?age=25"

# 按状态过滤
curl "http://localhost:8000/user?status=0"
```

响应：
```json
{
  "code": 0,
  "message": "",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "john",
        "status": 0,
        "age": 25
      }
    ]
  }
}
```

## 实现细节

### API定义

`API`接口使用`GoFrame`的`g.Meta`标签定义，实现自动路由和文档生成：

```go
type CreateReq struct {
    g.Meta `path:"/user" method:"post" tags:"User" summary:"Create user"`
    Name   string `v:"required|length:3,10" dc:"user name"`
    Age    uint   `v:"required|between:18,200" dc:"user age"`
}
```

### 控制器实现

控制器实现每个`API`端点的业务逻辑：

```go
func (c *ControllerV1) Create(ctx context.Context, req *v1.CreateReq) (res *v1.CreateRes, err error) {
    insertId, err := dao.User.Ctx(ctx).Data(do.User{
        Name:   req.Name,
        Status: v1.StatusOK,
        Age:    req.Age,
    }).InsertAndGetId()
    if err != nil {
        return nil, err
    }
    res = &v1.CreateRes{Id: insertId}
    return
}
```

### DAO模式

项目使用`GoFrame`的`DAO`模式进行数据库操作，代码自动生成：

- `dao/`：数据访问层（自动生成）
- `model/do/`：数据库操作的数据对象（自动生成）
- `model/entity/`：数据库表结构（自动生成）

### 响应中间件

统一响应处理中间件确保`API`响应格式一致，包含`code`、`message`和`data`字段。

## 配置

配置通过`manifest/config/config.yaml`管理：

```yaml
server:
  address: ":8000"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"

database:
  default:
    link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
```

