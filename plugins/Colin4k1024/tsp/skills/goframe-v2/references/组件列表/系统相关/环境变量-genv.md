环境变量管理组件。

**使用方式**：

```go
import "github.com/gogf/gf/v2/os/genv"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/os/genv](https://pkg.go.dev/github.com/gogf/gf/v2/os/genv)

## `SetMap`

```go
func SetMap(m map[string]string) error
```

该方法用于批量设置环境变量。使用示例：

```
genv.SetMap(g.MapStrStr{
    "APPID":     "order",
    "THREAD":    "16",
    "ENDPOINTS": "127.0.0.1:6379",
})
```

## `GetWithCmd`

```go
func GetWithCmd(key string, def ...interface{}) *gvar.Var
```

该方法用于获取环境变量中指定的选项数值，如果该环境变量不存在时，则从命令行选项中读取。但是两者的名称规则会不一样。例如： `genv.GetWithCmd("gf.debug")` 将会优先去读取 `GF_DEBUG` 环境变量的值，当不存在时则去命令行中的 `gf.debug` 选项。

需要注意的是参数命名转换规则：

- 环境变量会将名称转换为大写，名称中的 `.` 字符转换为 `_` 字符。
- 命令行中会将名称转换为小写，名称中的 `_` 字符转换为 `.` 字符。

## `All`

```go
func All() []string
```

该方法表示返回环境变量中的字符串，并且以\` `key=value` \`的形式返回。

## `Map`

```go
func Map() map[string]string
```

该方法表示返回环境变量中的字符串，并且以\` `map` \`的形式返回。

## `Get`

```go
func Get(key string, def ...interface{}) *gvar.Var
```

该方法用于创建返回一个泛型类型的环境变量，如果给定的 `key` 不存在则返回一个默认的泛型类型的环境变量。

## `Set`

```go
func Set(key, value string) error
```

该方法是通过存放 `key` 和 `value` 的环境变量，如果有报错则返回一个 `Error` 类型。

## `SetMap`

```go
func SetMap(m map[string]string) error
```

该方法通过 `map` 类型的参数存放环境变量。

## `Contains`

```go
func Contains(key string) bool
```

该方法通过检查环境变量中是否存在 `key`。

## `Remove`

```go
func Remove(key ...string) error
```

该方法可以删除一个或者多个环境变量。

## `Build`

```go
func Build(m map[string]string) []string
```

该方法将 `map` 的参数以数组的形式构建并且返回。