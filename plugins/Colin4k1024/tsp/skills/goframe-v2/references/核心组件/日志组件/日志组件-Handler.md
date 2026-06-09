从 `v2.0` 版本开始， `glog` 组件提供了超级强大的、可自定义日志处理的 `Handler` 特性。 `Handler` 采用了中间件设计方式，开发者可以为日志对象注册多个处理 `Handler`，也可以在 `Handler` 中覆盖默认的日志组件处理逻辑。

## 相关定义

### `Handler` 方法定义

```go
// Handler is function handler for custom logging content outputs.
type Handler func(ctx context.Context, in *HandlerInput)
```

可以看到第二个参数为日志处理的日志信息，并且为指针类型，意味着在 `Handler` 中可以修改该参数的任意属性信息，并且修改后的内容将会传递给下一个 `Handler`。

### `Handler` 参数定义

```go
// HandlerInput is the input parameter struct for logging Handler.
type HandlerInput struct {
    Logger      *Logger       // Current Logger object.
    Buffer      *bytes.Buffer // Buffer for logging content outputs.
    Time        time.Time     // Logging time, which is the time that logging triggers.
    TimeFormat  string        // Formatted time string, like "2016-01-09 12:00:00".
    Color       int           // Using color, like COLOR_RED, COLOR_BLUE, etc. Eg: 34
    Level       int           // Using level, like LEVEL_INFO, LEVEL_ERRO, etc. Eg: 256
    LevelFormat string        // Formatted level string, like "DEBU", "ERRO", etc. Eg: ERRO
    CallerFunc  string        // The source function name that calls logging, only available if F_CALLER_FN set.
    CallerPath  string        // The source file path and its line number that calls logging, only available if F_FILE_SHORT or F_FILE_LONG set.
    CtxStr      string        // The retrieved context value string from context, only available if Config.CtxKeys configured.
    TraceId     string        // Trace id, only available if OpenTelemetry is enabled.
    Prefix      string        // Custom prefix string for logging content.
    Content     string        // Content is the main logging content without error stack string produced by logger.
    Values      []any         // The passed un-formatted values array to logger.
    Stack       string        // Stack string produced by logger, only available if Config.StStatus configured.
    IsAsync     bool          // IsAsync marks it is in asynchronous logging.
}
```

开发者有 **两种方式** 通过 `Handler` 自定义日志输出内容：

- 一种是直接修改 `HandlerInput` 中的属性信息，然后继续执行 `in.Next(ctx)`，默认的日志输出逻辑会将 `HandlerInput` 中的属性打印为字符串输出。
- 另一种是将日志内容写入到 `Buffer` 缓冲对象中即可，默认的日志输出逻辑如果发现 `Buffer` 已经存在日志内容将会忽略默认日志输出逻辑。

### `Handler` 注册到 `Logger` 方法

```go
// SetHandlers sets the logging handlers for current logger.
func (l *Logger) SetHandlers(handlers ...Handler)
```

## 使用示例

我们来看两个示例便于更快速了解 `Handler` 的使用。

### 示例1\. 将日志输出转换为 `Json` 格式输出

在本示例中，我们采用了前置中间件的设计，通过自定义 `Handler` 将日志内容输出格式修改为了 `JSON` 格式。

```go
package main

import (
    "context"
    "encoding/json"
    "os"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/text/gstr"
)

// JsonOutputsForLogger is for JSON marshaling in sequence.
type JsonOutputsForLogger struct {
    Time    string `json:"time"`
    Level   string `json:"level"`
    Content string `json:"content"`
}

// LoggingJsonHandler is a example handler for logging JSON format content.
var LoggingJsonHandler glog.Handler = func(ctx context.Context, in *glog.HandlerInput) {
    jsonForLogger := JsonOutputsForLogger{
        Time:    in.TimeFormat,
        Level:   gstr.Trim(in.LevelFormat, "[]"),
        Content: gstr.Trim(in.Content), // 2.7以上版本用in.ValuesContent()
    }
    jsonBytes, err := json.Marshal(jsonForLogger)
    if err != nil {
        _, _ = os.Stderr.WriteString(err.Error())
        return
    }
    in.Buffer.Write(jsonBytes)
    in.Buffer.WriteString("\n")
    in.Next(ctx)
}

func main() {
    g.Log().SetHandlers(LoggingJsonHandler)
    ctx := context.TODO()
    g.Log().Debug(ctx, "Debugging...")
    g.Log().Warning(ctx, "It is warning info")
    g.Log().Error(ctx, "Error occurs, please have a check")
}
```

可以看到，我们可以在 `Handler` 中通过 `Buffer` 属性操作来控制输出的日志内容。如果在所有的前置中间件 `Handler` 处理后 `Buffer` 内容为空，那么继续 `Next` 执行后将会执行日志中间件默认的 `Handler` 逻辑。执行本示例的代码后，终端输出：

```html
{"time":"2021-12-31 11:03:25.438","level":"DEBU","content":"Debugging..."}
{"time":"2021-12-31 11:03:25.438","level":"WARN","content":"It is warning info"}
{"time":"2021-12-31 11:03:25.438","level":"ERRO","content":"Error occurs, please have a check \nStack:\n1.  main.main\n    C:/hailaz/test/main.go:42"}
```

### 示例2\. 将内容输出到第三方日志搜集服务中

在本示例中，我们采用了后置中间件的设计，通过自定义 `Handler` 将日志内容输出一份到第三方 `graylog` 日志搜集服务中，并且不影响原有的日志输出处理。

> `Graylog` 是与 `ELK` 可以相提并论的一款集中式日志管理方案，支持数据收集、检索、可视化 `Dashboard`。在本示例中使用到了一个简单的第三方 `graylog` 客户端组件。

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/glog"
    gelf "github.com/robertkowalski/graylog-golang"
)

var grayLogClient = gelf.New(gelf.Config{
    GraylogPort:     80,
    GraylogHostname: "graylog-host.com",
    Connection:      "wan",
    MaxChunkSizeWan: 42,
    MaxChunkSizeLan: 1337,
})

// LoggingGrayLogHandler is an example handler for logging content to remote GrayLog service.
var LoggingGrayLogHandler glog.Handler = func(ctx context.Context, in *glog.HandlerInput) {
    in.Next(ctx)
    grayLogClient.Log(in.Buffer.String())
}

func main() {
    g.Log().SetHandlers(LoggingGrayLogHandler)
    ctx := context.TODO()
    g.Log().Debug(ctx, "Debugging...")
    g.Log().Warning(ctx, "It is warning info")
    g.Log().Error(ctx, "Error occurs, please have a check")
    glog.Print(ctx, "test log")
}
```

## 全局默认 `Handler`

日志对象默认是没有设置任何的 `Handler`，从 `v2.1` 版本开始，框架提供了可以设置全局默认 `Handler` 的功能特性。全局默认 `Handler` 将对所有的使用该日志组件，并且没有自定义 `Handler` 的日志打印功能生效。同时，全局默认 `Handler` 将会影响日志包方法的日志打印行为。

开发者可以通过以下两个方法来设置和获取全局默认的 `Handler`。

```go
// SetDefaultHandler sets default handler for package.
func SetDefaultHandler(handler Handler)

// GetDefaultHandler returns the default handler of package.
func GetDefaultHandler() Handler
```

需要注意，这种全局包配置的方法不是并发安全的，并且往往需要在项目启动逻辑最顶部执行。

使用示例，我们将项目所有的日志输出均采用 `JSON` 格式输出，以保证日志内容结构化并且每次日志输出都是单行，方便日志采集期采集日志：

```go
package main

import (
    "context"
    "encoding/json"
    "os"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/text/gstr"
)

// JsonOutputsForLogger is for JSON marshaling in sequence.
type JsonOutputsForLogger struct {
    Time    string `json:"time"`
    Level   string `json:"level"`
    Content string `json:"content"`
}

// LoggingJsonHandler is a example handler for logging JSON format content.
var LoggingJsonHandler glog.Handler = func(ctx context.Context, in *glog.HandlerInput) {
    jsonForLogger := JsonOutputsForLogger{
        Time:    in.TimeFormat,
        Level:   gstr.Trim(in.LevelFormat, "[]"),
        Content: gstr.Trim(in.Content), // 2.7以上版本用in.ValuesContent()
    }
    jsonBytes, err := json.Marshal(jsonForLogger)
    if err != nil {
        _, _ = os.Stderr.WriteString(err.Error())
        return
    }
    in.Buffer.Write(jsonBytes)
    in.Buffer.WriteString("\n")
    in.Next(ctx)
}

func main() {
    ctx := context.TODO()
    glog.SetDefaultHandler(LoggingJsonHandler)

    g.Log().Debug(ctx, "Debugging...")
    glog.Warning(ctx, "It is warning info")
    glog.Error(ctx, "Error occurs, please have a check")
}
```

执行后，终端输出：

```html
{"time":"2022-06-20 10:51:50.235","level":"DEBU","content":"Debugging..."}
{"time":"2022-06-20 10:51:50.235","level":"WARN","content":"It is warning info"}
{"time":"2022-06-20 10:51:50.235","level":"ERRO","content":"Error occurs, please have a check"}
```

## 组件通用 `Handler`

组件提供了一些通用性的日志 `Handler`，方便开发者使用，提高开发效率。

### `HandlerJson`

该 `Handler` 可以将日志内容转换为 `Json` 格式打印。使用示例：

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/glog"
)

func main() {
    ctx := context.TODO()
    glog.SetDefaultHandler(glog.HandlerJson)

    g.Log().Debug(ctx, "Debugging...")
    glog.Warning(ctx, "It is warning info")
    glog.Error(ctx, "Error occurs, please have a check")
}
```

执行后，终端输出：

```html
{"Time":"2022-06-20 20:04:04.725","Level":"DEBU","Content":"Debugging..."}
{"Time":"2022-06-20 20:04:04.725","Level":"WARN","Content":"It is warning info"}
{"Time":"2022-06-20 20:04:04.725","Level":"ERRO","Content":"Error occurs, please have a check","Stack":"1.  main.main\n    /Users/john/Workspace/Go/GOPATH/src/github.com/gogf/gf/.test/main.go:16\n"}
```

### `HandlerStructure`

该 `Handler` 可以将日志内容转换为结构化格式打印，主要是为了和 `Golang` 新版本的 `slog` 日志输出内容保持一致。需要注意，日志结构化打印的特性需要保证所有日志记录均采用结构化输出才更具意义。使用示例：

```go
package main

import (
    "context"
    "net"

    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/glog"
)

func main() {
    ctx := context.TODO()
    glog.SetDefaultHandler(glog.HandlerStructure)

    g.Log().Info(ctx, "caution", "name", "admin")
    glog.Error(ctx, "oops", net.ErrClosed, "status", 500)
}

```

执行后，终端输出：

```html
Time="2023-11-23 21:00:08.671" Level=INFO Content=caution name=admin
Time="2023-11-23 21:00:08.671" Level=ERRO oops="use of closed network connection" status=500 Stack="1.  main.main\n    /Users/txqiangguo/Workspace/gogf/gf/example/.test/main.go:16\n"
```