## 引入数据库驱动

`GoFrame`的数据库组件使用了接口化设计，接口与实现是分离的，这样能提供更好的抽象和扩展性。我们这里使用了`mysql`数据库，那么需要引入具体的`mysql`驱动实现。我们在`main.go`中加上`_ "github.com/gogf/gf/contrib/drivers/mysql/v2"`即可。

示例源码：https://github.com/gogf/quick-demo/blob/main/main.go

```go title="main.go"
package main

import (
    _ "demo/internal/packed"

    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "github.com/gogf/gf/v2/os/gctx"

    "demo/internal/cmd"
)

func main() {
    cmd.Main.Run(gctx.GetInitCtx())
}
```
数据库的驱动，项目只需要引入这一次即可，后续都不需要做调整。
更多关于数据库驱动的支持以及详细介绍，请参考章节 [数据库ORM](../../../docs/核心组件/数据库ORM/数据库ORM.md)。

如果在没有引入数据库驱动的情况下执行数据库操作，数据库ORM组件会报如下的错误提示：
```text
cannot find database driver for specified database type "mysql", did you misspell type name "mysql" or forget importing the database driver? possible reference: https://github.com/gogf/gf/tree/master/contrib/drivers
```

:::tip
在脚手架项目模板`main.go`的`import`中有一段`_ "demo/internal/packed"`，表示`GoFrame`框架的资源管理，这是一个高级特性。该特性可以将任何资源打包进二进制文件，这样我们在发布的时候，仅需要发布一个二进制文件即可。我们这里没有用到该特性，因此大家了解即可，感兴趣可以后续查阅开发手册相关章节。
:::

## 添加数据库配置

在脚手架项目模板中主要有两个配置文件。

### 工具配置 `hack/config.yaml`
在前面的章节我们已经有过介绍。这个配置文件主要是本地开发时候使用，当`cli`脚手架工具执行时会自动读取其中的配置内容。

示例源码：https://github.com/gogf/quick-demo/blob/main/hack/config.yaml

### 业务配置 `manifest/config/config.yaml`
主要维护业务项目的组件配置信息、业务模块配置，完全由开发者自行维护。在程序启动时会读取该配置文件。该业务
默认的脚手架项目模板提供的业务配置如下：
```yaml title="manifest/config/config.yaml"
# https://goframe.org/docs/web/server-config-file-template
server:
  address:     ":8000"
  openapiPath: "/api.json"
  swaggerPath: "/swagger"

# https://goframe.org/docs/core/glog-config
logger:
  level : "all"
  stdout: true

# https://goframe.org/docs/core/gdb-config-file
database:
  default:
    link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
```

默认提供了`3`项组件的配置，分别为：
- `server`：`Web Server`的配置。这里默认配置的监听地址为`:8000`，并启用了接口文档特性。
- `logger`：默认日志组件的配置。这里的日志级别是所有日志都会打印，并且都会输出到标准输出。
- `database`：数据库组件的配置。这只是一个模板，需要我们根据实际情况修改链接地址。

每一项组件配置的注释上提供了官网文档的配置参考链接。我们这里需要修改数据库配置中的链接信息，为我们真实可用的链接信息。关于数据库的配置详细介绍，感兴趣请参考章节：[ORM使用配置-配置文件](../../../docs/核心组件/数据库ORM/ORM使用配置/ORM使用配置-配置文件.md)

示例源码：https://github.com/gogf/quick-demo/blob/main/manifest/config/config.yaml

## 添加路由注册

添加我们新填写的`api`到路由非常简单，如下：

在分组路由的`group.Bind`方法中，通过`user.NewV1()`添加我们的路由对象即可。

示例源码：https://github.com/gogf/quick-demo/blob/main/internal/cmd/cmd.go

到目前为止，我们的接口已经完全开发完了，下一步，我们将启动服务，并做一些接口测试，查看效果。

## 学习小结

当我们在使用数据库功能的时候，需要引入特定的数据库驱动。在`GoFrame`官方仓库中，通过社区组件的形式提供了常用数据库的驱动实现。我们的程序主要使用的是业务配置，并且需要将其中的数据库连接地址修改为我们搭建的数据库地址。

路由注册就太简单了，添加一个`controller`对象到分组路由注册中`group.Bind`即可。

目前为止，我们已经将`CRUD`接口开发完成啦👏👏。可以看到，我们做的事情主要是这几项：
- 数据库表设计
- `api`接口定义
- 接口的业务逻辑实现
- 简单的配置和路由注册

下一步，我们启动程序看看效果吧。