寄语：

- 请使用页面右上角的搜索功能，全文快速检索常见问题。
- 欢迎大家积极参与编辑，把自己遇到的坑怎么填的记录起来。 **众人拾柴火焰高**

## 一、Golang基础

### 1、程序产生异常，但是程序直接崩溃未被框架自动捕获

使用 `GoFrame` 框架是严谨和安全的，如果程序产生了异常，会默认被框架捕获。如果未被自动捕获，那么可能是由于程序逻辑自行开了新的 `goroutine`，在新的 `goroutine` 中产生了异常。因此这里有两个方案可供大家选择：

- 不建议在请求中再开 `goroutine` 来处理请求，这样或使得 `goroutine` 快速膨胀，当 `goroutine` 多了之后也会在 `Go` 引擎层面影响程序的整体调度。
- 如果实在有必要新开 `goroutine` 的场景下，可以考虑使用 `grpool.AddWithRecover` 来创建新的 `goroutine`，见名知意，它会自动捕获异常。更详细的介绍请参考： [协程管理-grpool](组件列表/系统相关/协程管理-grpool.md)

### 2、 `json` 输出时屏蔽掉一些字段

可以通过结构体嵌套的方式实现，通过使用 `*struct{}` 类型不占用空间以及 `omitempty` 字段为空不输出字段的特性

```go
type User struct {
    Pwd string `json:"pwd"`
    Age int    `json:"age"`
}

type UserOut struct {
    User
    Pwd *struct{} `json:"pwd,omitempty"`// 这里的字段json名需要和嵌套的字段json名一致，否则无效
}

func TestJson(t *testing.T) {
    u := User{Pwd: "123", Age: 1}
    bb := UserOut{User: u}
    b, _ := json.MarshalIndent(bb, "", "    ")
    t.Log(string(b))
}
```

## 二、兼容性相关

### 1、 `client_tracing.go:73:3: undefined: attribute.Any`

以下错误：

```bash
D:\Program Files\Go\bin\pkg\mod\github.com\gogf\gf@v1.16.6\net\ghttp\internal\client\client_tracing.go:73:3: undefined: attribute.Any
D:\Program Files\Go\bin\pkg\mod\github.com\gogf\gf@v1.16.6\net\ghttp\internal\client\client_tracing_tracer.go:150:3: undefined: attribute.Any
D:\Program Files\Go\bin\pkg\mod\github.com\gogf\gf@v1.16.6\net\ghttp\internal\client\client_tracing_tracer.go:151:3: undefined: attribute.Any
```

导致该错误的原因在于目前您正在使用的 `goframe` 依赖的 `otel` 包版本过低（ `otel` 包是 `OpenTelemetry` 使用 `Golang` 实现的第三方包，比较常用，很多第三方基础组件都会依赖），而项目中其他的第三方依赖的 `otel` 包过高，按照 `Golang module` 的管理策略，项目将会使用最新的 `otel` 包，于是导致了版本不兼容。

根因还是在于 `otel` 的包在迭代中出现了不兼容升级导致，不过目前 `otel` 包已经较稳定，出现不兼容的可能性降低。

解决的办法是只有升级 `goframe` 的版本， `goframe` 最新版本已经更新使用了稳定的 `otel` 包。如果您使用的已经是 `v1` 的最新版本（ `v1.16`），那么请升级为 `v2` 版本解决。

### 2、使用 `gf` 依赖 `v1.16.2` 时 `go mod tidy` 失败

`found (v0.36.0), but does not contain package go.opentelemetry.io/otel/metric/registry`

解决办法，升级 `gf` 依赖到 `v1.16.9` 再 `go mod tidy`

### 3、升级引起兼容性报错 ..\..\net\ghttp\ghttp_server.go:300:9: table.SetHeader undefined (type *tablewriter.Table has no field or method SetHeader)

使用`go get -u`导致间接依赖版本提升，出现如下的报错。
>..\..\net\ghttp\ghttp_server.go:300:9: table.SetHeader undefined (type *tablewriter.Table has no field or method SetHeader)
..\..\net\ghttp\ghttp_server.go:301:9: table.SetRowLine undefined (type *tablewriter.Table has no field or method SetRowLine)
..\..\net\ghttp\ghttp_server.go:302:9: table.SetBorder undefined (type *tablewriter.Table has no field or method SetBorder)
..\..\net\ghttp\ghttp_server.go:303:9: table.SetCenterSeparator undefined (type *tablewriter.Table has no field or method SetCenterSeparator)

原因：

使用`go get -u`命令升级了，如"github.com/gogf/gf/contrib/drivers/mysql/v2"这样的依赖了"github.com/gogf/gf/v2"主库的组件，会导致间接依赖被同时升级到最新版本。

间接依赖被升级到最新版本后，如果间接依赖不兼容的旧版就会报错。

解决方式：
```bash
// linux
go list -m -f '{{if and .Indirect (not .Main)}}{{.Path}}{{end}}' all | xargs -I {} go mod edit -droprequire={} && go mod tidy

// windows cmd
(FOR /F "tokens=*" %G IN ('go list -m -f "{{if and .Indirect (not .Main)}}{{.Path}}{{end}}" all') DO @go mod edit -droprequire=%G) & go mod tidy

// 以上方式还不能解决的时候，手动修改 go.mod 的版本号降级，然后执行 go mod tidy
// 例如
// 将 go.mod 文件中的 tablewriter 依赖版本从较高版本降级为 v0.0.5：
// 修改前（go.mod 部分）:
// github.com/olekukonko/tablewriter v1.0.9 // indirect
// 修改后（go.mod 部分）:
// github.com/olekukonko/tablewriter v0.0.5 // indirect
// 保存 go.mod 后，执行 go mod tidy 以更新依赖。
```

## 三、数据库相关

请参考章节： [ORM常见问题](核心组件/数据库ORM/ORM常见问题.md)

## 四、使用相关

### 1、不同环境如何，加载不同的配置文件?

不同环境指的是：开发环境/测试环境/预发环境/生产环境等。

- 首先，在一些互联网项目中，特别是分布式或者微服务化的架构下，一般会使用配置管理中心，不同的环境会对应不同的配置管理中心，所以这样的场景不会存在这样的问题。
- 其次，如果是传统的项目管理方式下，可能会将配置文件放到代码仓库中共同管理，这样的方式是不推荐的。如果您仍然想要这么做，您可以通过系统环境变量或者命令行启动参数，让程序自动选择配置文件或者指定配置目录，参考 [配置管理](核心组件/配置管理/配置管理.md) 章节。例如： `./app --gf.gcfg.file config-prod.toml ` 则通过命令行启动参数的方式将默认读取的配置文件修改为了 `config-prod.toml` 文件。

我们不建议您在程序中通过代码逻辑来区分和读取不同环境的配置文件。

### 2、 `glog with "ERROR: logging before flag.Parse"`

`Golang` 官方有个简单的日志库包名也叫做 `glog`，检查你文件顶部 `import` 的包名，将 `github.com/golang/glog` 修改为框架的日志组件即可，日志组件使用请参考： [日志组件](核心组件/日志组件/日志组件.md)

### 3、 `gcron` 与 `http` 如何同时使用?

```go
func main() {
    //定时任务1
    gcron.AddSingleton("*/5 * * * * *", func() {
        task.Test()
        glog.Debug("gcron1")
    })

    //定时任务2
    gcron.AddSingleton("*/10 * * * * *", func() {
        glog.Debug("gcron2")
    })

    //接收http请求
    g.Server().Run()
}
```

注意, `gcron` 一定要在 `g.Server().Run` 的前面。

### 4、 `GoFrame` 的 `struct tag`(标签) 有哪些？

参数请求、数据校验、 `OpenAPIv3`、命令管理、数据库ORM。

| Tag(简写) | 全称 | 描述 | 相关文档 |
| --- | --- | --- | --- |
| `v` | `valid` | 数据校验标签。 | [Struct校验-基本使用](核心组件/数据校验/数据校验-参数类型/数据校验-Struct校验/Struct校验-基本使用.md) |
| `p` | `param` | 自定义请求参数匹配。 | [请求输入-对象处理](WEB服务开发/请求输入/请求输入-对象处理.md) |
| `d` | `default` | 请求参数默认值绑定。 | [请求输入-默认值绑定](WEB服务开发/请求输入/请求输入-默认值绑定.md) |
| `orm` | `orm` | ORM标签，用于指定表名、关联关系。 | [数据规范-gen dao](开发工具/代码生成-gen/数据规范-gen%20dao.md)<br />[模型关联-静态关联-With特性](核心组件/数据库ORM/ORM链式操作/ORM链式操作-模型关联/模型关联-静态关联-With特性.md) |
| `dc` | `description` | 通用结构体属性描述，ORM和接口都用到。属于框架默认的属性描述标签。 |  |

其他：

- 命令行结构化管理参数： [命令管理-结构化参数](核心组件/命令管理/命令管理-结构化参数.md)
- 框架常用标签标签集中管理到了 `gtag` 组件下： [https://github.com/gogf/gf/blob/master/util/gtag/gtag.go](https://github.com/gogf/gf/blob/master/util/gtag/gtag.go)
- 在接口文档章节，由于采用了标签形式生成 `OpenAPI` 文档，因此标签比较多，具体请参考章节： [接口文档](WEB服务开发/接口文档/接口文档.md)

### 5、 `HTTP Server` 出现 `context cancel` 报错

从框架 `v2.5` 版本开始，框架的 `HTTP Server` 的 `Request` 对象将会直接继承与标准库的 `http.Request` 对象，
其中就包括其中的 `context` 上下文对象。当客户端例如浏览器、 `HTTP Client` 取消请求时，
服务端会接收到 `context cancel` 操作( `context.Done`)，但是服务端并不会直接报出 `context cancel` 的错误。
这种错误往往在业务逻辑调用了底层的数据库、消息组件等组件时，由这些组件识别到 `context cancel` 操作，
将会停止执行并往上抛出 `context cancel` 错误提醒上层已经终止执行。

这是符合标准库设计的行为，客户端终止请求后，服务端也没有继续执行下去的必要。

[服务端频繁出现contextcancel错误](../docs/WEB服务开发/常见问题.md)

## 五、环境相关

### 1、 `Linux` 下执行 `go build main.go` 提示连接超时 `connection timed out`

```bash
go: github.com/gogf/gf@v1.14.6-0.20201214132204-c685876e6f67: Get "https://proxy.golang.org/github.com/gogf/gf/@v/v1.14.6-0.20201214132204-c685876e6f67.mod":
dial tcp 172.217.160.113:443:
connect: connection timed out
```

解决办法：

```bash
export GO111MODULE=on
export GOPROXY=https://goproxy.cn
```

具体请看：

- [Go Module](其他资料/准备开发环境/Go%20Module.md)
- [https://goproxy.cn](https://goproxy.cn)

### 2、 `Linux` 下安装 `gf` 提示命令不存在 `command not found`

```bash
./gf install
安装后
执行gf -v
提示gf: command not found
且/usr/bin目录下并没有gf文件

解决方法:
拷贝sh文件到 /usr/bin目录
cp gf /usr/bin

然后执行
gf -v

就会看到
GoFrame CLI Tool v1.15.4, https://goframe.org
Install Path: /bin/gf
Build Detail:
Go Version: go1.16.2
GF Version: v1.15.3
Git Commit: 22011e76dc3e14006936164cc89e2d4c9190a36d
Build Time: 2021-03-30 15:43:22
```

### 3、 `Win10` 提示 `gf` 命令不存在

解决办法：安装 `gf.exe` 参考： [开发工具](开发工具/开发工具.md)