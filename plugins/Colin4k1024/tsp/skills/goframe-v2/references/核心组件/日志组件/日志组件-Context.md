从`v2`版本开始，`glog`组件将`ctx`上下文变量作为日志打印的必需参数。

## 自定义`CtxKeys`

日志组件支持自定义的键值打印，通过`ctx`上下文变量中读取。

### 使用配置

```yaml
# 日志组件配置
logger:
  Level:   "all"
  Stdout:  true
  CtxKeys: ["RequestId", "UserId"]
```

其中`CtxKeys`用于配置需要从`context.Context`接口对象中读取并输出的键名。

### 日志输出

使用上述配置，然后在输出日志的时候，通过 `Ctx` 链式操作方法指定输出的 `context.Context` 接口对象，请注意 **不要使用自定义类型作为Key**，否则无法输出到日志文件中，例如：

```go
package main

import (
    "context"

    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    var ctx = context.Background()

    // 可以直接使用String作为Key
    ctx = context.WithValue(ctx, "RequestId", "123456789")

    // 如需将Key提取为公共变量，可以使用gctx.StrKey类型，或直接使用string类型
    const userIdKey gctx.StrKey = "UserId" // or const userIdKey = "UserId"
    ctx = context.WithValue(ctx, userIdKey, "10000")

    // 不能自定义类型
    type notPrintKeyType string
    const notPrintKey notPrintKeyType = "NotPrintKey"
    ctx = context.WithValue(ctx, notPrintKey, "notPrintValue") // 不会打印 notPrintValue

    g.Log().Error(ctx, "runtime error")
}
```

执行后，终端输出：

```html
2024-09-26 11:45:33.790 [ERRO] {123456789, 10000} runtime error
Stack:
1.  main.main
    /Users/teemo/GolandProjects/gogf/demo/main.go:24

```

### 日志示例

## 传递给 `Handler`

如果开发者自定义了日志对象的 `Handler`，那么每个日志打印传递的 `ctx` 上下文变量将会传递给 `Handler` 中。关于日志 `Handler` 的介绍请参考章节： [日志组件-Handler](日志组件-Handler.md)

## 链路跟踪支持

`glog` 组件支持 `OpenTelemetry` 标准的链路跟踪特性，该支持是内置的，无需开发者做任何设置，具体请参考章节： [服务链路跟踪](../../服务可观测性/服务链路跟踪/服务链路跟踪.md)