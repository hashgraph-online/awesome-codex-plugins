## 查询缓存

`gdb` 支持对查询结果的缓存处理，常用于多读少写的查询缓存场景，并支持手动的缓存清理。需要注意的是，查询缓存仅支持链式操作，且在事务操作下不可用。

相关方法：

```go
type CacheOption struct {
    // Duration is the TTL for the cache.
    // If the parameter `Duration` < 0, which means it clear the cache with given `Name`.
    // If the parameter `Duration` = 0, which means it never expires.
    // If the parameter `Duration` > 0, which means it expires after `Duration`.
    Duration time.Duration

    // Name is an optional unique name for the cache.
    // The Name is used to bind a name to the cache, which means you can later control the cache
    // like changing the `duration` or clearing the cache with specified Name.
    Name string

    // Force caches the query result whatever the result is nil or not.
    // It is used to avoid Cache Penetration.
    Force bool
}

// Cache sets the cache feature for the model. It caches the result of the sql, which means
// if there's another same sql request, it just reads and returns the result from cache, it
// but not committed and executed into the database.
//
// Note that, the cache feature is disabled if the model is performing select statement
// on a transaction.
func (m *Model) Cache(option CacheOption) *Model
```

## 缓存管理

### 缓存对象

`ORM` 对象默认情况下提供了缓存管理对象，该缓存对象类型为 `*gcache.Cache`，也就是说同时也支持 `*gcache.Cache` 的所有特性。可以通过 `GetCache() *gcache.Cache` 接口方法获得该缓存对象，并通过返回的对象实现自定义的各种缓存操作，例如： `g.DB().GetCache().Keys()`。

### 缓存适配（ `Redis` 缓存）

默认情况下 `ORM` 的 `*gcache.Cache` 缓存对象提供的是单进程内存缓存，虽然性能非常高效，但是只能在单进程内使用。如果服务如果采用多节点部署，多节点之间的缓存可能会产生数据不一致的情况，因此大多数场景下我们都是通过 `Redis` 服务器来实现对数据库查询数据的缓存。 `*gcache.Cache` 对象采用了适配器设计模式，可以轻松实现从单进程内存缓存切换为分布式的 `Redis` 缓存。使用示例：

```go
redisCache := gcache.NewAdapterRedis(g.Redis())
g.DB().GetCache().SetAdapter(redisCache)
```

更多介绍请参考： [缓存管理-Redis缓存](../../缓存管理/缓存管理-Redis缓存.md)

### 管理方法

为简化数据库的查询缓存管理，从 `v2.2.0` 版本开始，提供了两个缓存管理方法：

```go
// ClearCache removes cached sql result of certain table.
func (c *Core) ClearCache(ctx context.Context, table string) (err error)

// ClearCacheAll removes all cached sql result from cache
func (c *Core) ClearCacheAll(ctx context.Context) (err error)
```

方法介绍如注释。可以看到这两个方法是挂载 `Core` 对象上的，而底层的 `Core` 对象已经通过 `DB` 接口暴露，因此我们这么来获取 `Core` 对象：

```go
g.DB().GetCore()
```

## 使用示例

### 数据表结构

```sql
CREATE TABLE `user` (
  `uid` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL DEFAULT '' COMMENT '昵称',
  `site` varchar(255) NOT NULL DEFAULT '' COMMENT '主页',
  PRIMARY KEY (`uid`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

### 示例代码

```go
package main

import (
    "time"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    var (
        db  = g.DB()
        ctx = gctx.New()
    )

    // 开启调试模式，以便于记录所有执行的SQL
    db.SetDebug(true)

    // 写入测试数据
    _, err := g.Model("user").Ctx(ctx).Data(g.Map{
        "name": "john",
        "site": "https://goframe.org",
    }).Insert()

    // 执行2次查询并将查询结果缓存1小时，并可执行缓存名称(可选)
    for i := 0; i < 2; i++ {
        r, _ := g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
            Duration: time.Hour,
            Name:     "vip-user",
            Force:    false,
        }).Where("uid", 1).One()
        g.Log().Debug(ctx, r.Map())
    }

    // 执行更新操作，并清理指定名称的查询缓存
    _, err = g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: -1,
        Name:     "vip-user",
        Force:    false,
    }).Data(gdb.Map{"name": "smith"}).Where("uid", 1).Update()
    if err != nil {
        g.Log().Fatal(ctx, err)
    }

    // 再次执行查询，启用查询缓存特性
    r, _ := g.Model("user").Ctx(ctx).Cache(gdb.CacheOption{
        Duration: time.Hour,
        Name:     "vip-user",
        Force:    false,
    }).Where("uid", 1).One()
    g.Log().Debug(ctx, r.Map())
}
```

执行后输出结果为（测试表数据结构仅供示例参考）：

```html
2022-02-08 17:36:19.817 [DEBU] {c0424c75f1c5d116d0df0f7197379412} {"name":"john","site":"https://goframe.org","uid":1}
2022-02-08 17:36:19.817 [DEBU] {c0424c75f1c5d116d0df0f7197379412} {"name":"john","site":"https://goframe.org","uid":1}
2022-02-08 17:36:19.817 [DEBU] {c0424c75f1c5d116d0df0f7197379412} [  0 ms] [default] [rows:1  ] UPDATE `user` SET `name`='smith' WHERE `uid`=1
2022-02-08 17:36:19.818 [DEBU] {c0424c75f1c5d116d0df0f7197379412} [  1 ms] [default] [rows:1  ] SELECT * FROM `user` WHERE `uid`=1 LIMIT 1
2022-02-08 17:36:19.818 [DEBU] {c0424c75f1c5d116d0df0f7197379412} {"name":"smith","site":"https://goframe.org","uid":1}
```

可以看到：

1. 为了方便展示缓存效果，这里开启了数据 `debug` 特性，当有任何的SQL操作时将会输出到终端。
2. 执行两次 `One` 方法数据查询，第一次走了SQL查询，第二次直接使用到了缓存，SQL没有提交到数据库执行，因此这里只打印了一条查询SQL，并且两次查询的结果也是一致的。
3. 注意这里为该查询的缓存设置了一个自定义的名称 `vip-user`，以便于后续清空更新缓存。如果缓存不需要清理，那么可以不用设置缓存名称。
4. 当执行 `Update` 更新操作时，同时根据名称清空指定的缓存。
5. 随后再执行 `One` 方法数据查询，这时重新缓存新的数据。