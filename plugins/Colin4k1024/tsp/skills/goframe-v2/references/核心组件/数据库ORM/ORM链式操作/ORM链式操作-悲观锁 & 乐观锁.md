`悲观锁（Pessimistic Lock）`，顾名思义，就是很悲观，每次去拿数据的时候都认为别人会修改，所以每次在拿数据的时候都会上锁，这样别人想拿这个数据就会阻塞直到它拿到锁。传统的关系型数据库里边就用到了很多这种锁机制，比如行锁、表锁、读锁、写锁等，都是在做操作之前先上锁。

`乐观锁（Optimistic Lock）`，顾名思义，就是很乐观，每次去拿数据的时候都认为别人不会修改，所以不会上锁，但是在更新的时候会判断一下在此期间别人有没有去更新这个数据，可以使用版本号等机制实现。乐观锁适用于多读的应用类型，这样可以提高吞吐量。

### 悲观锁使用

相关方法：

```go
func (m *Model) LockUpdate() *Model
func (m *Model) LockShared() *Model
func (m *Model) LockUpdateSkipLocked() *Model
```

`gdb` 模块的链式操作提供了两个方法帮助您在 `SQL` 语句中实现“悲观锁”。可以在查询中使用 `LockShared` 方法从而在运行语句时带一把”共享锁“。共享锁可以避免被选择的行被修改直到事务提交：

```go
g.Model("users").Ctx(ctx).Where("votes>?", 100).LockShared().All();
```

上面这个查询等价于下面这条 SQL 语句：

```sql
SELECT * FROM `users` WHERE `votes` > 100 LOCK IN SHARE MODE
```

此外你还可以使用 `LockUpdate` 方法。该方法用于创建 `FOR UPDATE` 锁，避免选择行被其它共享锁修改或删除：

```go
g.Model("users").Ctx(ctx).Where("votes>?", 100).LockUpdate().All();
```

上面这个查询等价于下面这条 SQL 语句：

```sql
SELECT * FROM `users` WHERE `votes` > 100 FOR UPDATE
```

#### 跳过已锁定的行（Skip Locked）

:::tip
版本要求：`v2.10.0`
:::

从 `v2.10.0` 版本开始，新增了 `LockUpdateSkipLocked` 方法，支持在高并发场景下跳过已被锁定的行，避免等待，提升系统吞吐量。

**使用方法：**

```go
g.Model("tasks").Ctx(ctx).Where("status", "pending").Limit(10).LockUpdateSkipLocked().All()
```

上面这个查询等价于下面这条`SQL`语句：

```sql
SELECT * FROM `tasks` WHERE `status` = 'pending' LIMIT 10 FOR UPDATE SKIP LOCKED
```

**应用场景：**

`SKIP LOCKED` 特别适用于任务队列、工单分配等高并发场景。当多个工作进程同时争抢任务时：

- 使用 `LockUpdate()`：所有进程会排队等待锁释放，导致性能下降
- 使用 `LockUpdateSkipLocked()`：每个进程跳过已被其他进程锁定的行，立即获取可用的任务，提升并发处理能力

**示例：任务队列处理**

```go
package main

import (
    "context"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    ctx := gctx.New()
    
    // 开启事务
    err := g.DB().Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
        // 获取未被锁定的待处理任务
        records, err := g.Model("tasks").Ctx(ctx).
            Where("status", "pending").
            Limit(10).
            LockUpdateSkipLocked().  // 跳过已被其他进程锁定的任务
            All()
        if err != nil {
            return err
        }
        
        // 处理任务...
        for _, record := range records {
            // 更新任务状态为处理中
            _, err = g.Model("tasks").Ctx(ctx).
                Data(g.Map{"status": "processing"}).
                Where("id", record["id"]).
                Update()
            if err != nil {
                return err
            }
        }
        
        return nil
    })
    
    if err != nil {
        g.Log().Error(ctx, err)
    }
}
```

**数据库支持：**

`SKIP LOCKED` 功能由以下数据库支持：
- `PostgreSQL 9.5+`
- `Oracle`
- `MySQL 8.0+`
- `MariaDB 10.6+`

:::warning
使用 `LockUpdateSkipLocked()` 前请确认您的数据库版本支持该特性，否则会导致`SQL`执行错误。
:::

**性能对比：**

在高并发任务分配场景下：
- 使用 `LockUpdate()`：`10`个工作进程处理`100`个任务可能需要`10`秒（排队等待）
- 使用 `LockUpdateSkipLocked()`：`10`个工作进程可以同时各自获取`10`个任务并行处理，时间缩短为`1`秒

#### 锁机制对比

`FOR UPDATE` 与 `LOCK IN SHARE MODE` 都是用于确保被选中的记录值不能被其它事务更新（上锁），两者的区别在于 `LOCK IN SHARE MODE` 不会阻塞其它事务读取被锁定行记录的值，而 `FOR UPDATE` 会阻塞其他锁定性读对锁定行的读取（非锁定性读仍然可以读取这些记录， `LOCK IN SHARE MODE` 和 `FOR UPDATE` 都是锁定性读）。

这么说比较抽象，我们举个计数器的例子：在一条语句中读取一个值，然后在另一条语句中更新这个值。使用 `LOCK IN SHARE MODE` 的话可以允许两个事务读取相同的初始化值，所以执行两个事务之后最终计数器的值 `+1`；而如果使用 `FOR UPDATE` 的话，会锁定第二个事务对记录值的读取直到第一个事务执行完成，这样计数器的最终结果就是 `+2` 了。

### 乐观锁使用

乐观锁，大多是基于数据版本 （ `Version`）记录机制实现。何谓数据版本？即为数据增加一个版本标识，在基于数据库表的版本解决方案中，一般是通过为数据库表增加一个 " `version`" 字段来实现。

读取出数据时，将此版本号一同读出，之后更新时，对此版本号加一。此时，将提交数据的版本数据与数据库表对应记录的当前版本信息进行比对，如果提交的数据版本号大于数据库表当前版本号，则予以更新，否则认为是过期数据。

### 锁机制总结

两种锁各有优缺点，不可认为一种好于另一种，像乐观锁适用于写比较少的情况下，即冲突真的很少发生的时候，这样可以省去了锁的开销，加大了系统的整个吞吐量。但如果经常产生冲突，上层应用会不断的进行重试，这样反倒是降低了性能，所以这种情况下用悲观锁就比较合适。