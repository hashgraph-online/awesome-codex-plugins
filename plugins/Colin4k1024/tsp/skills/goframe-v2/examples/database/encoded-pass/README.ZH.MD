---
title: 加密密码数据库连接
slug: /examples/database/encoded-pass
keywords: [数据库, 安全, 加密密码, 加密, goframe]
description: 演示如何在GoFrame中实现自定义数据库驱动以处理加密的数据库密码，提升应用程序安全性。本示例展示了如何创建带有AES加密和Base64编码的自定义MySQL驱动、连接建立时的自动密码解密机制、配置文件中的安全凭据存储、透明的数据库连接处理、以及与GoFrame数据库组件的无缝集成。主要功能包括:加密密码存储、自定义驱动注册、自动解密中间件、生产级安全模式、对现有数据库操作零影响。非常适合需要增强数据库安全性、符合安全策略合规要求、保护版本控制中的敏感凭据、无需代码更改即可实现安全配置管理的应用程序。通过本示例可以学习如何在不影响开发效率的前提下提升数据库连接的安全性，以及如何实现自定义数据库驱动扩展GoFrame的能力。
hide_title: true
sidebar_position: 1
---

# 加密密码数据库连接

## 介绍

本示例展示了如何在`GoFrame`中实现一个自定义数据库驱动，用于处理加密的数据库密码。该实现允许您在配置文件中存储加密的密码，这些密码在建立数据库连接时会自动解密。

示例使用`AES`加密结合`Base64`编码来保护数据库密码，为应用程序的数据库凭据提供额外的安全层。

## 环境要求

- [Go](https://golang.org/dl/) `1.18` 或更高版本
- [Git](https://git-scm.com/downloads)
- [GoFrame](https://goframe.org)
- `MySQL` 数据库

## 目录结构

```text
.
├── config.yaml           # 包含加密数据库密码的配置文件
├── dbdriver/             # 自定义数据库驱动实现
│   ├── dbdriver.go       # 带密码解密功能的自定义 MySQL 驱动
│   └── dbdriver_test.go  # 密码加密/解密测试
├── go.mod                # Go 模块文件
├── go.sum                # Go 模块校验和
└── main.go               # 应用程序入口点
```

## 功能特点

- 自定义数据库驱动实现
- 使用`AES-CBC`进行密码加密
- 使用`Base64`编码处理二进制数据
- 与`GoFrame`数据库操作无缝集成
- 安全存储数据库凭据

## 设置步骤

1. 克隆代码库:
   ```bash
   git clone https://github.com/gogf/examples.git
   cd examples/database/encoded-pass
   ```

2. 安装依赖:
   ```bash
   go mod tidy
   ```

3. 设置 MySQL 数据库:
   ```bash
   docker run --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=12345678 -e MYSQL_DATABASE=test -d mysql:8.0
   ```

4. 使用加密的数据库密码更新配置文件（参见下面的密码加密部分）。

5. 运行应用程序:
   ```bash
   go run main.go
   ```

## 密码加密

要加密您的数据库密码:

1. 运行演示加密过程的测试函数:
   ```bash
   cd dbdriver
   go test -v -run Test_Encode
   ```

2. 测试将输出:
   - 原始密码
   - `Base64`编码的密码
   - `AES`加密并 `Base64` 编码的密码（在 `config.yaml` 中使用这个）
   - 解密后的密码（用于验证）

3. 使用您的加密密码更新 `config.yaml` 文件:
   ```yaml
   database:
     default:
       link: "mysql:root:您的加密密码@tcp(127.0.0.1:3306)/test?loc=Local&parseTime=true"
   ```

## 实现细节

自定义数据库驱动扩展了`GoFrame`提供的标准`MySQL`驱动，并重写了`Open`接口方法来处理密码解密:

1. 从数据库连接字符串中提取加密密码
2. 对密码进行 `Base64` 解码，获取二进制加密数据
3. 使用预定义的加密密钥应用 `AES-CBC` 解密
4. 对解密后的数据再次进行 `Base64` 解码，获取原始密码
5. 使用原始密码建立数据库连接

## 注意事项

- 在此示例中，加密密钥是硬编码的（`encodeKey`）。在生产环境中，您应该使用安全的方法来管理此密钥。
- 这种方法可以扩展到加密配置文件中的其他敏感信息。
- 示例使用`AES-CBC`加密，但您可以修改它以使用`GoFrame`提供的其他加密算法。
