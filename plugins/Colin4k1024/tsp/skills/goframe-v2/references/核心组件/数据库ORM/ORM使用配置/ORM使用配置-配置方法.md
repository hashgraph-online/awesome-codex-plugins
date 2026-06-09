:::tip
以下为数据库底层管理配置介绍，如果您对数据库的底层配置管理比较感兴趣，可继续阅读后续章节。
:::
## 数据结构

`gdb` 数据库管理模块的内部配置管理数据结构如下：

`ConfigNode` 用于存储一个数据库节点信息； `ConfigGroup` 用于管理多个数据库节点组成的配置分组(一般一个分组对应一个业务数据库集群)； `Config` 用于管理多个 `ConfigGroup` 配置分组。

**配置管理特点：**

1. 支持多节点数据库集群管理；
2. 每个节点可以单独配置连接属性；
3. 采用单例模式管理数据库实例化对象；
4. 支持对数据库集群分组管理，按照分组名称获取实例化的数据库操作对象；
5. 支持多种关系型数据库管理，可通过 `ConfigNode.Type` 属性进行配置；
6. 支持 `Master-Slave` 读写分离，可通过 `ConfigNode.Role` 属性进行配置；
7. 支持客户端的负载均衡管理，可通过 `ConfigNode.Weight` 属性进行配置，值越大，优先级越高；

```go
type Config      map[string]ConfigGroup // 数据库配置对象
type ConfigGroup []ConfigNode           // 数据库分组配置
// 数据库配置项(一个分组配置对应多个配置项)
type ConfigNode  struct {
    Host             string        // 地址
    Port             string        // 端口
    User             string        // 账号
    Pass             string        // 密码
    Name             string        // 数据库名称
    Type             string        // 数据库类型：mysql, sqlite, mssql, pgsql, oracle
    Link             string        // (可选)自定义链接信息，当该字段被设置值时，以上链接字段(Host,Port,User,Pass,Name)将失效(该字段是一个扩展功能)
    Extra            string        // (可选)不同数据库的额外特性配置，由底层数据库driver定义
    Role             string        // (可选，默认为master)数据库的角色，用于主从操作分离，至少需要有一个master，参数值：master, slave
    Debug            bool          // (可选)开启调试模式
    Charset          string        // (可选，默认为 utf8)编码，默认为 utf8
    Prefix           string        // (可选)表名前缀
    Weight           int           // (可选)用于负载均衡的权重计算，当集群中只有一个节点时，权重没有任何意义
    MaxIdleConnCount int           // (可选)连接池最大闲置的连接数
    MaxOpenConnCount int           // (可选)连接池最大打开的连接数
    MaxConnLifetime  time.Duration // (可选，单位秒)连接对象可重复使用的时间长度
}
```

特别说明， `gdb` 的配置管理最大的 **特点** 是，（同一进程中）所有的数据库集群信息都使用同一个配置管理模块进行统一维护， **不同业务的数据库集群配置使用不同的分组名称** 进行配置和获取。

## 配置方法

这是原生调用 `gdb` 模块来配置管理数据库。如果开发者想要自行控制数据库配置管理可以参考以下方法。若无需要可忽略该章节。

接口文档： [https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb](https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb)

```go
// 添加一个数据库节点到指定的分组中
func AddConfigNode(group string, node ConfigNode)
// 添加一个配置分组到数据库配置管理中(同名覆盖)
func AddConfigGroup(group string, nodes ConfigGroup)

// 添加一个数据库节点到默认的分组中(默认为default，可修改)
func AddDefaultConfigNode(node ConfigNode)
// 添加一个配置分组到数据库配置管理中(默认分组为default，可修改)
func AddDefaultConfigGroup(nodes ConfigGroup)

// 设置默认的分组名称，获取默认数据库对象时将会自动读取该分组配置
func SetDefaultGroup(groupName string)

// 设置数据库配置为定义的配置信息，会将原有配置覆盖
func SetConfig(c Config)

// 获取所有数据库配置信息（从版本v2.10.0开始支持）
func GetAllConfig() Config
```

默认分组表示，如果获取数据库对象时不指定配置分组名称，那么 `gdb` 默认读取的配置分组。例如： `gdb.NewByGroup()` 可获取一个默认分组的数据库对象。简单的做法，我们可以通过 `gdb` 包的 `SetConfig` 配置管理方法进行自定义的数据库全局配置，例如：

```go
gdb.SetConfig(gdb.Config {
    "default" : gdb.ConfigGroup {
        gdb.ConfigNode {
            Host     : "192.168.1.100",
            Port     : "3306",
            User     : "root",
            Pass     : "123456",
            Name     : "test",
            Type     : "mysql",
            Role     : "master",
            Weight   : 100,
        },
        gdb.ConfigNode {
            Host     : "192.168.1.101",
            Port     : "3306",
            User     : "root",
            Pass     : "123456",
            Name     : "test",
            Type     : "mysql",
            Role     : "slave",
            Weight   : 100,
        },
    },
    "user-center" : gdb.ConfigGroup {
        gdb.ConfigNode {
            Host     : "192.168.1.110",
            Port     : "3306",
            User     : "root",
            Pass     : "123456",
            Name     : "test",
            Type     : "mysql",
            Role     : "master",
            Weight   : 100,
        },
    },
})
```

随后，我们可以使用 `gdb.NewByGroup("数据库分组名称")` 来获取一个数据库操作对象。该对象用于后续的数据库一系列方法/链式操作。

## 获取所有配置

从版本`v2.10.0`开始，`gdb`提供了`GetAllConfig`方法用于获取所有数据库配置信息，方便进行配置验证、配置导出等业务操作。

### 方法定义

```go
func GetAllConfig() Config
```

该方法返回类型为`Config`，即`map[string]ConfigGroup`，包含了所有已注册的数据库分组配置。

### 使用示例

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/database/gdb"
)

func main() {
    // 获取所有数据库配置
    allConfig := gdb.GetAllConfig()
    
    // 遍历所有配置分组
    for groupName, configGroup := range allConfig {
        fmt.Printf("数据库分组: %s\n", groupName)
        
        // 遍历分组中的所有节点
        for i, node := range configGroup {
            fmt.Printf("  节点 %d:\n", i+1)
            fmt.Printf("    Host: %s\n", node.Host)
            fmt.Printf("    Port: %s\n", node.Port)
            fmt.Printf("    Name: %s\n", node.Name)
            fmt.Printf("    Type: %s\n", node.Type)
            fmt.Printf("    Role: %s\n", node.Role)
        }
    }
}
```

### 应用场景

`GetAllConfig`方法主要用于以下场景：

1. **配置验证**：在应用启动时验证所有数据库配置是否正确。
2. **配置导出**：将当前数据库配置导出到文件或其他存储介质。
3. **监控和诊断**：在运行时检查数据库配置，用于故障排查。
4. **配置管理界面**：为管理后台提供配置查看和编辑功能。