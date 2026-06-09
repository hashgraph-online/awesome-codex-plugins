## 基本介绍

`ORM`分库（`Schema Sharding`）是`GoFrame ORM`提供的一种数据分片解决方案，允许开发者将一个逻辑表的数据分散存储到多个物理数据库中。分库是实现数据库水平扩展的重要手段，通过将数据分散到不同的数据库节点，可以显著提高系统的处理能力和可扩展性。

## 分库的优点

1. **突破单机性能瓶颈**：通过将数据分散到多个数据库节点，突破单个数据库服务器的性能限制
2. **提高并发处理能力**：分散读写压力到多个数据库节点，提高整体并发处理能力
3. **提高系统可用性**：单个数据库节点故障不会影响整个系统，提高系统的可用性
4. **地理分布优势**：可以根据地理位置分布数据，降低访问延迟，提高用户体验
5. **灵活的数据管理**：可以根据业务需求将不同类型的数据分布到不同的数据库节点

## 应用场景

1. **大规模用户系统**：按用户ID或地理位置分库，应对全球用户分布
2. **电商平台**：按商户或产品类别分库，处理大规模商品数据
3. **金融系统**：按账户类型或业务线分库，实现业务隔离和高可用性
4. **多租户SaaS平台**：按租户分库，确保数据隔离和安全
5. **大数据分析系统**：按时间或数据类型分库，优化大规模数据处理

## 基本使用

`GoFrame ORM`提供了简单易用的分库API，通过`Sharding`和`ShardingValue`方法即可实现分库功能。

### 分库配置

```go
// 创建分库配置
shardingConfig := gdb.ShardingConfig{
    Schema: gdb.ShardingSchemaConfig{
        Enable: true,     // 启用分库
        Prefix: "db_",    // 分库前缀
        Rule: &gdb.DefaultShardingRule{
            SchemaCount: 2, // 分库数量
        },
    },
}

// 使用分库配置和分片值
model := db.Model("user").
    Sharding(shardingConfig).
    ShardingValue(10001) // 分片值，用于计算数据路由到哪个数据库
```

### 默认分库规则

`GoFrame ORM`提供了默认的分库规则`DefaultShardingRule`，它基于分片值的哈希取模来确定数据库名：

```go
// 默认分库规则实现
func (r *DefaultShardingRule) SchemaName(ctx context.Context, config ShardingSchemaConfig, value any) (string, error) {
    if r.SchemaCount == 0 {
        return "", gerror.NewCode(
            gcode.CodeInvalidParameter, "schema count should not be 0 using DefaultShardingRule when schema sharding enabled",
        )
    }
    hashValue, err := getHashValue(value)
    if err != nil {
        return "", err
    }
    nodeIndex := hashValue % uint64(r.SchemaCount)
    return fmt.Sprintf("%s%d", config.Prefix, nodeIndex), nil
}
```

## 完整示例

首先，以`MySQL`数据库为例，我们需要创建多个数据库和相应的表结构。对于分库示例，我们需要创建多个具有相同表结构的数据库：

```sql
-- 创建分库所需的数据库
CREATE DATABASE IF NOT EXISTS `db_0`;
CREATE DATABASE IF NOT EXISTS `db_1`;

-- 在每个数据库中创建相同结构的表
-- 在 db_0 中创建表
USE `db_0`;
CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 在 db_1 中创建表
USE `db_1`;
CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 基本CRUD操作

以下示例展示了如何在分库环境下进行基本的`CRUD`操作：

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
    // 创建分库配置
    shardingConfig := gdb.ShardingConfig{
        Schema: gdb.ShardingSchemaConfig{
            Enable: true,  // 启用分库
            Prefix: "db_", // 分库前缀
            Rule: &gdb.DefaultShardingRule{
                SchemaCount: 2, // 分库数量
            },
        },
    }

    // 准备测试数据
    user := User{
        Id:   1,
        Name: "John",
    }

    // 创建分库模型
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
    // INSERT INTO `user`(`id`,`name`) VALUES(1,'John')
    // 注意：实际操作的是 db_1 数据库中的 user 表

    // 查询数据
    var result User
    err = model.Where("id", user.Id).Scan(&result)
    if err != nil {
        panic(err)
    }
    // SELECT * FROM `user` WHERE `id`=1 LIMIT 1
    // 注意：实际查询的是 db_1 数据库中的 user 表
    g.DumpJson(result)

    // 更新数据
    _, err = model.Data(g.Map{"name": "John Doe"}).
        Where("id", user.Id).
        Update()
    if err != nil {
        panic(err)
    }
    // UPDATE `user` SET `name`='John Doe' WHERE `id`=1
    // 注意：实际更新的是 db_1 数据库中的 user 表

    // 删除数据
    _, err = model.Where("id", user.Id).Delete()
    if err != nil {
        panic(err)
    }
    // DELETE FROM `user` WHERE `id`=1
    // 注意：实际删除的是 db_1 数据库中的 user 表
}
```

### 自定义分库规则

您可以通过实现`ShardingRule`接口来自定义分库规则：

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "context"
    "fmt"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
)

// RegionShardingRule 按地区分库的规则
type RegionShardingRule struct {
    // 地区到数据库的映射
    RegionMapping map[string]string
}

// SchemaName 实现按地区分库的规则
func (r *RegionShardingRule) SchemaName(ctx context.Context, config gdb.ShardingSchemaConfig, value any) (string, error) {
    // 将分片值转换为地区信息
    region, ok := value.(string)
    if !ok {
        return "", fmt.Errorf("sharding value must be string for RegionShardingRule")
    }

    // 获取地区对应的数据库名
    if dbName, exists := r.RegionMapping[region]; exists {
        return dbName, nil
    }

    // 如果没有找到对应的地区，使用默认数据库
    return config.Prefix + "default", nil
}

// TableName 实现分表规则接口
func (r *RegionShardingRule) TableName(ctx context.Context, config gdb.ShardingTableConfig, value any) (string, error) {
    // 这里不实现分表，返回空字符串
    return "", nil
}

func main() {
    // 创建地区到数据库的映射
    regionMapping := map[string]string{
        "east":  "db_east",
        "west":  "db_west",
        "north": "db_north",
        "south": "db_south",
    }

    // 创建按地区分库的配置
    shardingConfig := gdb.ShardingConfig{
        Schema: gdb.ShardingSchemaConfig{
            Enable: true,                                              // 启用分库
            Prefix: "db_",                                             // 分库前缀
            Rule:   &RegionShardingRule{RegionMapping: regionMapping}, // 自定义分库规则
        },
    }

    // 分片值为用户所在地区
    region := "east"

    // 创建分库模型
    db := g.DB()
    db.SetDebug(true)
    model := g.DB().Model("user").
        Sharding(shardingConfig).
        ShardingValue(region) // 使用地区作为分片值

    // 插入用户数据
    _, err := model.Data(g.Map{
        "id":     1001,
        "name":   "John",
        "region": region,
    }).Insert()
    if err != nil {
        panic(err)
    }
    // INSERT INTO `user`(`id`,`name`,`region`) VALUES(1001,'John','east')
    // 注意：实际操作的是 db_east 数据库中的 user 表
}
```

### 结合分库分表

`GoFrame ORM`支持同时配置分库和分表，实现更精细的数据分片：

```go
// 同时配置分库和分表
shardingConfig := gdb.ShardingConfig{
    Schema: gdb.ShardingSchemaConfig{
        Enable: true,     // 启用分库
        Prefix: "db_",    // 分库前缀
        Rule: &gdb.DefaultShardingRule{
            SchemaCount: 2, // 分库数量
        },
    },
    Table: gdb.ShardingTableConfig{
        Enable: true,     // 启用分表
        Prefix: "user_",  // 分表前缀
        Rule: &gdb.DefaultShardingRule{
            TableCount: 4, // 分表数量
        },
    },
}

// 使用分库分表配置
model := g.DB().Model("user").
    Sharding(shardingConfig).
    ShardingValue(10001)  // 同一个分片值用于计算分库和分表
```

## 使用`Hook`实现动态分库

`GoFrame ORM`提供了强大的`Hook`机制，可以用于实现更灵活的分库策略：

```go
// 使用Hook实现动态分库
model := db.Model("user").Hook(gdb.HookHandler{
    Select: func(ctx context.Context, in *gdb.HookSelectInput) (result gdb.Result, err error) {
        // 根据查询条件动态确定数据库
        in.Schema = determineSchema(in.Model.GetWhere())
        return in.Next(ctx)
    },
    Insert: func(ctx context.Context, in *gdb.HookInsertInput) (result sql.Result, err error) {
        // 根据插入数据动态确定数据库
        in.Schema = determineSchemaFromData(in.Data)
        return in.Next(ctx)
    },
    // 其他Hook方法...
})
```

关于`Hook`特性介绍，请参考章节：[ORM链式操作-Hook特性](../ORM链式操作/ORM链式操作-Hook特性.md)

## 注意事项

1. **分片值必须提供**：启用分库后，必须通过`ShardingValue`方法提供分片值，否则会返回错误
2. **分库规则必须设置**：启用分库后，必须设置分库规则，否则会返回错误
3. **跨库事务限制**：默认情况下，事务无法跨多个数据库，需要使用分布式事务来解决
4. **数据库配置要求**：所有分库节点需要在配置文件中正确配置，确保可以连接
5. **跨库查询限制**：默认情况下，查询只会路由到单个分库，如需跨库查询，需要自行实现

## 总结

`GoFrame ORM`的分库特性提供了灵活而强大的数据库水平分片解决方案，适用于需要大规模数据处理能力的场景。通过合理配置分库策略，可以显著提高系统的性能和可扩展性。无论是使用内置的默认分库规则，还是实现自定义分库逻辑，`GoFrame`都提供了灵活的`API`支持。

在实际应用中，建议根据业务特点和数据分布情况选择合适的分库策略，并注意处理好跨库查询和事务等问题。