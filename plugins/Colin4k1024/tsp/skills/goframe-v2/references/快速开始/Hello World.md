`GoFrame` 是一款基础设施建设比较完善的模块化框架， 
`Web Server` 模块是其中比较核心的模块，我们这里将 `Web` 服务开发作为框架入门的选择，便于大家更容易学习和理解。

## Hello World

我们先来开发一个简单的`Web Server`程序。

- 新建`main.go`文件
  ```go title="main.go"
  package main

  import (
      "github.com/gogf/gf/v2/frame/g"
      "github.com/gogf/gf/v2/net/ghttp"
  )

  func main() {
      s := g.Server()
      s.BindHandler("/", func(r *ghttp.Request) {
          r.Response.Write("Hello World!")
      })
      s.SetPort(8000)
      s.Run()
  }
  ```
- 配置`go mod`并安装依赖
  ```shell
  go mod init main
  go mod tidy
  ```

我们来看看这段代码：
- 任何时候，您都可以通过 `g.Server()` 方法获得一个默认的 `Server` 对象，该方法采用**单例模式**设计，
  也就是说，多次调用该方法，返回的是同一个 `Server` 对象。其中的`g`组件是框架提供的一个耦合组件，封装和初始化一些常用的组件对象，为业务项目提供便捷化的使用方式。
- 通过`Server`对象的`BindHandler`方法绑定路由以及路由函数。在本示例中，我们绑定了`/`路由，并指定路由函数返回`Hello World`。
- 在路由函数中，输入参数为当前请求对象`r *ghttp.Request`，该对象包含当前请求的上下文信息。在本示例中，我们通过`r.Response`返回对象直接`Write`返回结果信息。
- 通过`SetPort`方法设置当前`Server`监听端口。在本示例中，我们监听`8000`端口，如果在没有设置端口的情况下，它默认会监听一个随机的端口。
- 通过 `Run()` 方法阻塞执行 `Server` 的监听运行。

## 执行结果

运行该程序，您将在终端看到类似以下日志信息：
```html
$ go run main.go
2024-10-27 21:30:39.412 [INFO] pid[58889]: http server started listening on [:8000]
2024-10-27 21:30:39.412 [INFO] {08a0b0086e5202184111100658330800} openapi specification is disabled

  ADDRESS | METHOD | ROUTE |     HANDLER     | MIDDLEWARE  
----------|--------|-------|-----------------|-------------
  :8000   | ALL    | /     | main.main.func1 |             
----------|--------|-------|-----------------|-------------
```

在默认的日志打印中包含以下信息：
- 当前进程号`58889`，以及监听的地址`:8000`（表示监听本机所有IP地址的`8000`端口）。
- 由于框架带有自动接口文档生成功能，本示例中未启用，因此提示`openapi specification is disabled`。
  关于接口文档的自动生成，在开发手册中对应章节会详细讲解，本示例不作介绍。
- 最后会打印当前`Server`的路由列表。由于我们只监听了`/`路由，那么这里只打印了一个路由信息。在路由信息表中：

  | 路由字段 | 字段描述 |
  |----------|----------|
  | `ADDRESS` | 表示该路由的监听地址，同一个进程可以同时运行多个`Server`，不同的`Server`可以监听不同的地址。 |
  | `METHOD` | 表示路由监听的`HTTP Method`信息，比如`GET/POST/PUT/DELETE`等。这里的`ALL`标识监听所有的`HTTP Method`。 |
  | `ROUTE` | 表示监听的具体路由地址信息。 |
  | `HANDLER` | 表示路由函数的名称。由于本示例使用的是闭包函数，因此看到的是一个临时函数名称`main.main.func1`。 |
  | `MIDDLEWARE` | 表示绑定到当前路由的中间件函数名称，中间件是`Server`中一种经典的拦截器，后续章节中会有详细讲解，这里暂不做介绍。 |

运行后，我们尝试访问 http://127.0.0.1:8000/ 您将在页面中看到输出

## 学习小结

太棒了！您使用`GoFrame`框架开发第一个`Web Server`程序！

下一步，我们将会学习如何在`Web Server`中获取客户端提交的参数数据。