`Loader` 是 `gcfg` 组件提供的通用配置管理器，从 `v2.10.0` 版本开始提供。它提供了类似于 `Spring Boot`的 `@ConfigurationProperties` 的配置加载、监控、更新和管理功能。

## 功能特性

- **泛型支持**：使用`Go`泛型，提供类型安全的配置绑定
- **配置加载**：从配置源加载数据并自动绑定到结构体
- **配置监控**：自动监控配置变化并实时更新
- **自定义转换器**：支持自定义数据转换函数
- **回调处理**：支持配置变更时的回调函数
- **错误处理**：提供灵活的错误处理机制

## 基本使用

### 方式一：使用全局配置对象

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gcfg"
    "github.com/gogf/gf/v2/os/gctx"
)

type AppConfig struct {
    Name     string       `json:"name"`
    Version  string       `json:"version"`
    Server   ServerConfig `json:"server"`
    Database DBConfig     `json:"database"`
}

type ServerConfig struct {
    Host string `json:"host"`
    Port int    `json:"port"`
}

type DBConfig struct {
    Host     string `json:"host"`
    Port     int    `json:"port"`
    Username string `json:"username"`
    Password string `json:"password"`
}

func main() {
    ctx := gctx.New()
    
    // 创建 Loader 实例，使用全局配置
    loader := gcfg.NewLoader[AppConfig](g.Cfg(), "")
    
    // 加载并监听配置
    loader.MustLoadAndWatch(ctx, "app-config-watcher")
    
    // 获取配置
    config := loader.Get()
    fmt.Printf("应用名称: %s\n", config.Name)
    fmt.Printf("服务地址: %s:%d\n", config.Server.Host, config.Server.Port)
}
```

### 方式二：使用独立的配置适配器

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/os/gcfg"
    "github.com/gogf/gf/v2/os/gctx"
)

type AppConfig struct {
    Name     string       `json:"name"`
    Version  string       `json:"version"`
    Server   ServerConfig `json:"server"`
}

type ServerConfig struct {
    Host string `json:"host"`
    Port int    `json:"port"`
}

func main() {
    ctx := gctx.New()
    
    // 创建独立的配置文件适配器
    adapter, err := gcfg.NewAdapterFile("config.yaml")
    if err != nil {
        panic(err)
    }
    
    // 使用适配器创建 Loader
    loader := gcfg.NewLoaderWithAdapter[AppConfig](adapter, "")
    
    // 加载并监听配置
    loader.MustLoadAndWatch(ctx, "app-watcher")
    
    // 获取配置
    config := loader.Get()
    fmt.Printf("应用: %s v%s\n", config.Name, config.Version)
}
```

## 配置文件示例

以下是配置文件 `config.yaml` 的示例：

```yaml
name: "MyApp"
version: "1.0.0"
server:
  host: "127.0.0.1"
  port: 8080
database:
  host: "localhost"
  port: 3306
  username: "root"
  password: "123456"
```

## 高级特性

### 监控特定配置键

如果你只想监控配置文件中的特定部分，可以指定 `propertyKey` 参数：

```go
// 只监控并加载 server 配置部分
loader := gcfg.NewLoader[ServerConfig](g.Cfg(), "server")
loader.MustLoadAndWatch(ctx, "server-watcher")

config := loader.Get()
fmt.Printf("服务器配置: %s:%d\n", config.Host, config.Port)
```

对应的配置文件：

```yaml
server:
  host: "127.0.0.1"
  port: 8080
database:
  host: "localhost"
  port: 3306
```

### 配置变更回调

当配置文件发生变化时，可以通过回调函数执行自定义逻辑：

```go
loader := gcfg.NewLoader[AppConfig](g.Cfg(), "")

// 设置配置变更回调
loader.OnChange(func(updated AppConfig) error {
    fmt.Printf("配置已更新，新的应用名称: %s\n", updated.Name)
    
    // 在这里可以执行其他逻辑，例如：
    // - 重新连接数据库
    // - 更新缓存
    // - 通知其他服务
    
    return nil
})

// 加载并监听
loader.MustLoadAndWatch(ctx, "my-watcher")
```

### 自定义转换器

如果需要对配置数据进行自定义处理，可以设置转换器：

```go
loader := gcfg.NewLoader[AppConfig](g.Cfg(), "")

// 设置自定义转换器
loader.SetConverter(func(data any, target *AppConfig) error {
    // 自定义转换逻辑
    // 例如：解密加密的配置项、格式化特殊字段等
    
    // 使用默认转换
    if err := gconv.Scan(data, target); err != nil {
        return err
    }
    
    // 额外的处理
    if target.Server.Port == 0 {
        target.Server.Port = 8080 // 设置默认端口
    }
    
    return nil
})

loader.MustLoadAndWatch(ctx, "custom-converter-watcher")
```

### 错误处理

在监控过程中，如果配置加载失败，可以通过错误处理器来处理：

```go
loader := gcfg.NewLoader[AppConfig](g.Cfg(), "")

// 设置错误处理器
loader.SetWatchErrorHandler(func(ctx context.Context, err error) {
    g.Log().Errorf(ctx, "配置加载失败: %v", err)
    // 可以发送告警通知等
})

loader.MustLoadAndWatch(ctx, "error-handler-watcher")
```

### 使用默认值

可以在创建`Loader`时提供一个带默认值的结构体：

```go
// 创建带默认值的配置结构体
defaultConfig := &AppConfig{
    Name:    "DefaultApp",
    Version: "0.0.1",
    Server: ServerConfig{
        Host: "0.0.0.0",
        Port: 8080,
    },
}

// 使用默认配置创建 Loader
loader := gcfg.NewLoader(g.Cfg(), "", defaultConfig)
loader.MustLoad(ctx)

// 如果配置文件中没有某些字段，将使用默认值
config := loader.Get()
```

## API 参考

### NewLoader

创建一个新的`Loader`实例。

```go
func NewLoader[T any](config *Config, propertyKey string, targetStruct ...*T) *Loader[T]
```

**参数：**
- `config`: 配置实例
- `propertyKey`: 监控的配置键（使用 `""` 或 `"."` 监控所有配置）
- `targetStruct`: 可选的目标结构体指针（用于设置默认值）

### NewLoaderWithAdapter

使用适配器创建`Loader`实例。

```go
func NewLoaderWithAdapter[T any](adapter Adapter, propertyKey string, targetStruct ...*T) *Loader[T]
```

### Load

从配置源加载数据并绑定到结构体。

```go
func (l *Loader[T]) Load(ctx context.Context) error
```

### MustLoad

与 `Load` 类似，但出错时会 panic。

```go
func (l *Loader[T]) MustLoad(ctx context.Context)
```

### Watch

开始监控配置变化并自动更新结构体。

```go
func (l *Loader[T]) Watch(ctx context.Context, name string) error
```

### MustWatch

与 `Watch` 类似，但出错时会 panic。

```go
func (l *Loader[T]) MustWatch(ctx context.Context, name string)
```

### MustLoadAndWatch

便捷方法，同时执行 `MustLoad` 和 `MustWatch`。

```go
func (l *Loader[T]) MustLoadAndWatch(ctx context.Context, name string)
```

### Get

返回当前的配置结构体（值副本）。

```go
func (l *Loader[T]) Get() T
```

### GetPointer

返回指向当前配置结构体的指针。

```go
func (l *Loader[T]) GetPointer() *T
```

### OnChange

设置配置变化时的回调函数。

```go
func (l *Loader[T]) OnChange(fn func(updated T) error)
```

### SetConverter

设置自定义转换函数。

```go
func (l *Loader[T]) SetConverter(converter func(data any, target *T) error)
```

### SetWatchErrorHandler

设置监控过程中的错误处理器。

```go
func (l *Loader[T]) SetWatchErrorHandler(errorFunc func(ctx context.Context, err error))
```

### SetReuseTargetStruct

设置是否重用目标结构体（默认为 true）。

```go
func (l *Loader[T]) SetReuseTargetStruct(reuse bool)
```

### StopWatch

停止监控配置变化。

```go
func (l *Loader[T]) StopWatch(ctx context.Context) (bool, error)
```

### IsWatching

返回是否正在监控配置变化。

```go
func (l *Loader[T]) IsWatching() bool
```

## 完整示例

以下是一个完整的应用示例，展示如何使用`Loader`管理应用配置：

```go
package main

import (
    "context"
    "fmt"
    "time"
    
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gcfg"
    "github.com/gogf/gf/v2/os/gctx"
)

// AppConfig 应用配置
type AppConfig struct {
    App      AppInfo      `json:"app"`
    Server   ServerConfig `json:"server"`
    Database DBConfig     `json:"database"`
    Redis    RedisConfig  `json:"redis"`
}

type AppInfo struct {
    Name    string `json:"name"`
    Version string `json:"version"`
    Debug   bool   `json:"debug"`
}

type ServerConfig struct {
    Host string `json:"host"`
    Port int    `json:"port"`
}

type DBConfig struct {
    Host     string `json:"host"`
    Port     int    `json:"port"`
    Database string `json:"database"`
    Username string `json:"username"`
    Password string `json:"password"`
}

type RedisConfig struct {
    Host     string `json:"host"`
    Port     int    `json:"port"`
    Database int    `json:"database"`
}

func main() {
    ctx := gctx.New()
    
    // 创建 Loader
    loader := gcfg.NewLoader[AppConfig](g.Cfg(), "")
    
    // 设置配置变更回调
    loader.OnChange(func(updated AppConfig) error {
        g.Log().Infof(ctx, "配置已更新: %s v%s", updated.App.Name, updated.App.Version)
        return nil
    })
    
    // 设置错误处理器
    loader.SetWatchErrorHandler(func(ctx context.Context, err error) {
        g.Log().Errorf(ctx, "配置加载失败: %v", err)
    })
    
    // 加载并监听配置
    loader.MustLoadAndWatch(ctx, "app-config")
    
    // 获取配置并使用
    config := loader.Get()
    
    fmt.Printf("应用信息:\n")
    fmt.Printf("  名称: %s\n", config.App.Name)
    fmt.Printf("  版本: %s\n", config.App.Version)
    fmt.Printf("  调试模式: %v\n", config.App.Debug)
    
    fmt.Printf("\n服务器配置:\n")
    fmt.Printf("  地址: %s:%d\n", config.Server.Host, config.Server.Port)
    
    fmt.Printf("\n数据库配置:\n")
    fmt.Printf("  地址: %s:%d\n", config.Database.Host, config.Database.Port)
    fmt.Printf("  数据库: %s\n", config.Database.Database)
    
    // 保持程序运行以监控配置变化
    select {}
}
```

对应的配置文件 `config.yaml`：

```yaml
app:
  name: "MyApplication"
  version: "1.0.0"
  debug: true

server:
  host: "0.0.0.0"
  port: 8080

database:
  host: "localhost"
  port: 3306
  database: "mydb"
  username: "root"
  password: "123456"

redis:
  host: "localhost"
  port: 6379
  database: 0
```

## 使用建议

1. **类型安全**：使用`Loader`可以获得编译时类型检查，避免运行时类型转换错误。

2. **配置监听**：在生产环境中使用配置监听功能可以实现配置热更新，无需重启应用。

3. **错误处理**：始终设置错误处理器，确保配置加载失败时能够及时发现并处理。

4. **配置分离**：对于复杂的应用，建议将不同模块的配置分离到不同的键下，使用 `propertyKey` 参数单独加载。

5. **默认值**：为关键配置项设置合理的默认值，提高应用的健壮性。

6. **回调函数**：在配置变更回调中执行必要的资源更新操作，如重建连接池、清理缓存等。