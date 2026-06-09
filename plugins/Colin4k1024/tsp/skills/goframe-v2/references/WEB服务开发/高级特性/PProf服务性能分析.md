`GoFrame` 框架的 `Web Server` 提供了非常强大和简便的服务性能分析功能，内部完美集成了 `pprof` 性能分析工具，可以在任何时候通过 `EnablePProf` 方法启用性能分析特性，并可自定义性能分析工具页面路由地址，不传递路由地址时，默认URI地址为 `/debug/pprof`。

## `PProf` 启用
:::warning
`PProf` 特性的启用会对程序性能产生一定影响，具体影响程度需要根据当前业务场景在 `PProd` 启用前后进行对比。
:::
### `EnablePProf`

我们来看一个简单的例子：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
    "runtime"
)

func main() {
    runtime.SetMutexProfileFraction(1) // (非必需)开启对锁调用的跟踪
    runtime.SetBlockProfileRate(1)     // (非必需)开启对阻塞操作的跟踪

    s := g.Server()
    s.EnablePProf()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln("哈喽世界！")
    })
    s.SetPort(8199)
    s.Run()
}
```

这个例子使用了 `s.EnablePProf()` 启用了性能分析，默认会自动注册以下几个路由规则：

```html
/debug/pprof/*action
/debug/pprof/cmdline
/debug/pprof/profile
/debug/pprof/symbol
/debug/pprof/trace
```

其中 `/debug/pprof/*action` 为页面访问的路由，其他几个地址为 `go tool pprof` 命令准备的。

### `StartPProfServer`

也可以使用 `StartPProfServer` 方法，快速开启一个独立的 `PProf Server`，常用于一些没有 `HTTP Server` 的常驻的进程中（例如定时任务、 `GRPC` 服务中），可以快速开启一个 `PProf Server` 用于程序性能分析。该方法的定义如下：

```go
func StartPProfServer(port int, pattern ...string)
```

一般的场景是使用异步 `goroutine` 运行该 `PProd Server`，即往往是这么来使用：

```go
package main

import (
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    go ghttp.StartPProfServer(8199)
    // 其他服务启动、运行
    // ...
}
```

以上示例可以改进为：

```go
package main

import (
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/net/ghttp"
)

func main() {
    go ghttp.StartPProfServer(8299)

    s := g.Server()
    s.EnablePProf()
    s.BindHandler("/", func(r *ghttp.Request) {
        r.Response.Writeln("哈喽世界！")
    })
    s.SetPort(8199)
    s.Run()
}
```

## `PProf` 指标

- `heap`: 报告内存分配样本；用于监视当前和历史内存使用情况，并检查内存泄漏。
- `threadcreate`: 报告了导致创建新OS线程的程序部分。
- `goroutine`: 报告所有当前 `goroutine` 的堆栈跟踪。
- `block`: 显示 `goroutine` 在哪里阻塞同步原语（包括计时器通道）的等待。默认情况下未启用，需要手动调用 `runtime.SetBlockProfileRate` 启用。
- `mutex`: 报告锁竞争。默认情况下未启用，需要手动调用 `runtime.SetMutexProfileFraction` 启用。

## `PProf` 页面

简单的性能分析我们直接访问 `/debug/pprof` 地址即可，内容如下：

1、 `pprof` 页面

2、堆使用量

3、当前进程中的 `goroutine` 详情

## 性能采集分析🔥
:::tip
以下示例截图来源于示例项目，仅供参考。
:::
如果想要进行详细的性能分析，基本上离不开 `go tool pprof` 命令行工具的支持，在开启性能分析支持后，我们可以使用以下命令执行性能采集分析：

```bash
go tool pprof -http :8080 "http://127.0.0.1:8199/debug/pprof/profile"
```

也可以将pprof文件导出后再通过go tool pprof命令打开：

```bash
curl http://127.0.0.1:8199/debug/pprof/profile > pprof.profile
go tool pprof -http :8080 pprof.profile
```

执行后 `profile` 的 `pprof` 工具经过约 `30` 秒左右的接口信息采集（这 `30` 秒期间 `WebServer` 应当有流量进入），然后生成性能分析报告，随后可以通过 `top10`/ `web` 等 `pprof` 命令查看报告结果，更多命令可使用 `go tool pprof` 查看。关于 `pprof` 的详细使用介绍，请查看 `Golang` 官方： [blog.golang.org/profiling-go-programs](https://blog.golang.org/profiling-go-programs)

### CPU性能分析

本示例中的命令行性能分析结果如下：

```bash
$ go tool pprof -http :8080 "http://127.0.0.1:8199/debug/pprof/profile"
Serving web UI on http://localhost:8080
```
:::tip
图形化展示 `pprof` 需要安装 `Graphviz` 图形化工具，以我目前的系统为 `Ubuntu` 为例，直接执行 `sudo apt-get install graphviz` 命令即可安装完成图形化工具（如果是 `MacOS`，使用 `brew install Graphviz` 安装）。
:::
运行后将会使用默认的浏览器打开以下图形界面，展示这段时间抓取的CPU开销链路：

也可以查看火炬图，可能更形象一些：

### 内存使用分析

与 `CPU` 性能分析类似，内存使用分析同样使用到 `go tool pprof` 命令：

```bash
$ go tool pprof -http :8080 "http://127.0.0.1:8199/debug/pprof/heap"
Serving web UI on http://localhost:8080
```

图形展示类似这样的：

同样的，也可以查看火炬图，可能更形象一些：

### goroutine使用分析

与上面的分析类似， `goroutine` 使用分析同样使用到 `go tool pprof` 命令：

```bash
$ go tool pprof -http :8080 "http://127.0.0.1:8199/debug/pprof/goroutine"
Serving web UI on http://localhost:8080
```

图形展示类似这样的，通常 `goroutine` 看这个图的话就差不多了，当然也有火炬图。