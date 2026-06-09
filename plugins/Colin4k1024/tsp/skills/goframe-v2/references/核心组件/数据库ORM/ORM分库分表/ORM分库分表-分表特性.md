## 基本介绍

`ORM`分表（`Table Sharding`）是`GoFrame ORM`提供的一种数据分片解决方案，允许开发者将一个逻辑表的数据分散存储到多个物理表中。分表是解决单表数据量过大问题的有效手段，通过将数据分散到不同的表中，可以显著提高查询性能和系统可扩展性。

## 分表的优点

1. **提高查询性能**：通过减少单表数据量，降低索引深度，提高查询效率
2. **优化写入性能**：分散写入压力，减少锁竞争，提高并发写入能力
3. **简化维护**：便于按分片进行数据备份、恢复和归档
4. **突破单表数据量限制**：规避数据库单表数据量上限的限制
5. **提高可用性**：单个分片故障不会影响整个系统

## 应用场景

1. **大规模用户系统**：按用户ID分表，应对海量用户数据
2. **订单系统**：按订单ID或时间分表，处理高并发订单写入和查询
3. **日志系统**：按时间分表，便于日志的存储和清理
4. **物联网数据**：按设备ID或时间分表，处理海量传感器数据
5. **社交媒体**：按用户ID分表，处理用户产生的大量社交数据

## 基本使用

`GoFrame ORM`提供了简单易用的分表API，通过`Sharding`和`ShardingValue`方法即可实现分表功能。

### 分表配置

```go
// 创建分表配置
shardingConfig := gdb.ShardingConfig{
    Table: gdb.ShardingTableConfig{
        Enable: true,      // 启用分表
        Prefix: "user_",   // 分表前缀
        Rule: &gdb.DefaultShardingRule{
            TableCount: 4, // 分表数量
        },
    },
}

// 使用分表配置和分片值
model := db.Model("user").
    Sharding(shardingConfig).
    ShardingValue(10001) // 分片值，用于计算数据路由到哪个表，通常是主键ID值
```

### 默认分表规则

`GoFrame ORM`提供了默认的分表规则`DefaultShardingRule`，它基于分片值的哈希取模来确定表名：

```go
// 默认分表规则实现
func (r *DefaultShardingRule) TableName(ctx context.Context, config ShardingTableConfig, value any) (string, error) {
    if r.TableCount == 0 {
        return "", gerror.NewCode(
            gcode.CodeInvalidParameter, "table count should not be 0 using DefaultShardingRule when table sharding enabled",
        )
    }
    hashValue, err := getHashValue(value)
    if err != nil {
        return "", err
    }
    tableIndex := hashValue % uint64(r.TableCount)
    return fmt.Sprintf("%s%d", config.Prefix, tableIndex), nil
}
```

## 完整示例

首先，以`MySQL`数据库为例，我们需要创建相应的数据库表结构。对于分表示例，我们需要创建多个具有相同结构的物理表：

```sql
CREATE TABLE `user_0` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_1` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_2` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `user_3` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 基本CRUD操作

以下示例展示了如何在分表环境下进行基本的`CRUD`操作：

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
)

// User 用户结构体
type User struct {
    Id   int    `json:"id"`
    Name string `json:"name"`
}

func main() {
    // 创建分表配置
    shardingConfig := gdb.ShardingConfig{
        Table: gdb.ShardingTableConfig{
            Enable: true,    // 启用分表
            Prefix: "user_", // 分表前缀
            Rule: &gdb.DefaultShardingRule{
                TableCount: 4, // 分表数量
            },
        },
    }

    // 准备测试数据
    user := User{
        Id:   1,
        Name: "John",
    }

    // 创建分表模型
    db := g.DB()
    db.SetDebug(true)
    model := db.Model("user").
        Sharding(shardingConfig).
        ShardingValue(user.Id) // 使用用户ID作为分片值

    // 插入数据
    _, err := model.Data(user).Insert()
    if err != nil {
        panic(err)
    }
    // INSERT INTO `user_1`(`id`,`name`) VALUES(1,'John')

    // 查询数据
    var result User
    err = model.Where("id", user.Id).Scan(&result)
    if err != nil {
        panic(err)
    }
    // SELECT * FROM `user_1` WHERE `id`=1 LIMIT 1
    g.DumpJson(result)

    // 更新数据
    _, err = model.Data(g.Map{"name": "John Doe"}).
        Where("id", user.Id).
        Update()
    if err != nil {
        panic(err)
    }
    // UPDATE `user_1` SET `name`='John Doe' WHERE `id`=1

    // 删除数据
    _, err = model.Where("id", user.Id).Delete()
    if err != nil {
        panic(err)
    }
    // DELETE FROM `user_1` WHERE `id`=1
}
```

### 自定义分表规则

您可以通过实现`ShardingRule`接口来自定义分表规则：

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "context"
    "fmt"
    "time"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gtime"
)

// TimeShardingRule 按时间分表的规则
type TimeShardingRule struct{}

// TableName 实现按月份分表的规则
func (r *TimeShardingRule) TableName(ctx context.Context, config gdb.ShardingTableConfig, value any) (string, error) {
    // 将分片值转换为时间
    t, ok := value.(time.Time)
    if !ok {
        return "", fmt.Errorf("sharding value must be time.Time for TimeShardingRule")
    }

    // 按年月生成表名，例如: log_202501
    return fmt.Sprintf("%s%04d%02d", config.Prefix, t.Year(), t.Month()), nil
}

// SchemaName 实现分库规则接口
func (r *TimeShardingRule) SchemaName(ctx context.Context, config gdb.ShardingSchemaConfig, value any) (string, error) {
    // 这里不实现分库，返回空字符串
    return "", nil
}

func main() {
    // 创建按时间分表的配置
    shardingConfig := gdb.ShardingConfig{
        Table: gdb.ShardingTableConfig{
            Enable: true,                // 启用分表
            Prefix: "log_",              // 分表前缀
            Rule:   &TimeShardingRule{}, // 自定义分表规则
        },
    }

    // 当前时间作为分片值
    now := gtime.Now().Time

    // 创建分表模型
    db := g.DB()
    db.SetDebug(true)
    model := db.Model("log").
        Sharding(shardingConfig).
        ShardingValue(now) // 使用时间作为分片值

    // 插入日志数据
    _, err := model.Data(g.Map{
        "content": "系统启动",
        "level":   "info",
        "time":    now,
    }).Insert()
    if err != nil {
        panic(err)
    }
    // INSERT INTO `log_202503`(`content`,`level`,`time`) VALUES('系统启动','info','2025-03-13 12:02:54')
}
```

## 注意事项

1. **分片值必须提供**：启用分表后，必须通过`ShardingValue`方法提供分片值，否则会返回错误
2. **分表规则必须设置**：启用分表后，必须设置分表规则，否则会返回错误
3. **跨分片查询限制**：默认情况下，查询只会路由到单个分片表，如需跨分片查询，需要自行实现
4. **事务限制**：分表事务只能在同一个数据库内进行，跨库分表事务需要使用分布式事务
5. **表结构一致性**：所有分片表的结构应保持一致

## 高级用法

### 使用`Hook`实现动态分表

`GoFrame ORM`提供了强大的`Hook`机制，可以用于实现更灵活的分表策略：

```go
// 使用Hook实现动态分表
model := db.Model("log").Hook(gdb.HookHandler{
    Select: func(ctx context.Context, in *gdb.HookSelectInput) (result gdb.Result, err error) {
        // 根据查询条件动态确定表名
        in.Table = "log_" + determineTableSuffix(in.Model.GetWhere())
        return in.Next(ctx)
    },
    Insert: func(ctx context.Context, in *gdb.HookInsertInput) (result sql.Result, err error) {
        // 根据插入数据动态确定表名
        in.Table = "log_" + determineTableSuffixFromData(in.Data)
        return in.Next(ctx)
    },
    // 其他Hook方法...
})
```

关于`Hook`特性介绍，请参考章节：[ORM链式操作-Hook特性](../ORM链式操作/ORM链式操作-Hook特性.md)

## 总结

`GoFrame ORM`的分表特性提供了简单而强大的数据分片解决方案，适用于处理大规模数据的场景。通过合理配置分表策略，可以显著提高系统的性能和可扩展性。无论是使用内置的默认分表规则，还是实现自定义分表逻辑，`GoFrame`都提供了灵活的`API`支持。

在实际应用中，建议根据业务特点选择合适的分片键和分表策略，并注意处理好跨分片查询和事务等问题。