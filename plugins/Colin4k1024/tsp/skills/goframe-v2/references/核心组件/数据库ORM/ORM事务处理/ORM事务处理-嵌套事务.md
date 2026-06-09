从 `GoFrame ORM` 支持数据库嵌套事务，嵌套事务在业务项目中用得比较多，特别是业务模块之间的相互调用，保证各个业务模块的数据库操作都处于一个事务中，其原理是通过传递的 `context` 上下文来隐式传递和关联同一个事务对象。需要注意的是，数据库服务往往并不支持嵌套事务，而是依靠 `ORM` 组件层通过 `Transaction Save Point` 特性实现的。同样的，我们推荐使用 `Transaction` 闭包方法来实现嵌套事务操作。为了保证文档的完整性，因此我们这里仍然从最基本的事务操作方法开始来介绍嵌套事务操作。

## 一、示例SQL

一个简单的示例 `SQL`，包含两个字段 `id` 和 `name`：

```sql
CREATE TABLE `user` (
  `id` int(10) unsigned NOT NULL COMMENT '用户ID',
  `name` varchar(45) NOT NULL COMMENT '用户名称',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

## 二、常规操作（不推荐）

```go
db := g.DB()

tx, err := db.Begin()
if err != nil {
    panic(err)
}
if err = tx.Begin(); err != nil {
    panic(err)
}
_, err = tx.Model(table).Data(g.Map{"id": 1, "name": "john"}).Insert()
if err = tx.Rollback(); err != nil {
    panic(err)
}
_, err = tx.Model(table).Data(g.Map{"id": 2, "name": "smith"}).Insert()
if err = tx.Commit(); err != nil {
    panic(err)
}
```

### 1、 `db.Begin` 与 `tx.Begin`

可以看到，在我们的嵌套事务中出现了 `db.Begin` 和 `tx.Begin` 两种事务开启方式，两者有什么区别呢？ `db.Begin` 是在数据库服务上真正开启一个事务操作，并返回一个事务操作对象 `tx`，随后所有的事务操作都是通过该 `tx` 事务对象来操作管理。 `tx.Begin` 表示在当前事务操作中开启嵌套事务，默认情况下会对嵌套事务的 `SavePoint` 采用自动命名，命名格式为 `transactionN`，其中的 `N` 表示嵌套的层级数量，如果您看到日志中出现 ``SAVEPOINT `transaction1` `` 表示当前嵌套层级为 `2`（从 `0` 开始计算）。

### 2、更详细的日志

`goframe` 的 `ORM` 拥有相当完善的日志记录机制，如果您打开 `SQL` 日志，那么将会看到以下日志信息，展示了整个数据库请求的详细执行流程：

```html
2021-05-22 21:12:10.776 [DEBU] [  4 ms] [default] [txid:1] BEGIN
2021-05-22 21:12:10.776 [DEBU] [  0 ms] [default] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:12:10.789 [DEBU] [ 13 ms] [default] [txid:1] SHOW FULL COLUMNS FROM `user`
2021-05-22 21:12:10.790 [DEBU] [  1 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(1,'john')
2021-05-22 21:12:10.791 [DEBU] [  1 ms] [default] [txid:1] ROLLBACK TO SAVEPOINT `transaction0`
2021-05-22 21:12:10.791 [DEBU] [  0 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(2,'smith')
2021-05-22 21:12:10.792 [DEBU] [  1 ms] [default] [txid:1] COMMIT
```

其中的 `[txid:1]` 表示 `ORM` 组件记录的事务ID，多个真实的事务同时操作时，每个事务的ID将会不同。在同一个真实事务下的嵌套事务的事务ID是一样的。

执行后查询数据库结果：

```
mysql> select * from `user`;
+----+-------+
| id | name  |
+----+-------+
|  2 | smith |
+----+-------+
1 row in set (0.00 sec)
```

可以看到第一个操作被成功回滚，只有第二个操作执行并提交成功。

## 三、闭包操作(推荐)

我们也可以通过闭包操作来实现嵌套事务，同样也是通过 `Transaction` 方法实现。

```go
db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
    // Nested transaction 1.
    if err := tx.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := tx.Model(table).Ctx(ctx).Data(g.Map{"id": 1, "name": "john"}).Insert()
        return err
    }); err != nil {
        return err
    }
    // Nested transaction 2, panic.
    if err := tx.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := tx.Model(table).Ctx(ctx).Data(g.Map{"id": 2, "name": "smith"}).Insert()
        // Create a panic that can make this transaction rollback automatically.
        panic("error")
        return err
    }); err != nil {
        return err
    }
    return nil
})
```

嵌套事务的闭包嵌套中也可以不使用其中的 `tx` 对象，而是直接使用 `db` 对象或者 `dao` 包，这种方式更常见一些。特别是在方法层级调用时，使得对于开发者来说并不用关心 `tx` 对象的传递，也并不用关心当前事务是否需要嵌套执行，一切都由组件自动维护，极大减少开发者的心智负担。但是务必记得将 `ctx` 上下文变量层层传递下去哦。例如：

```go
db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
    // Nested transaction 1.
    if err := db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := db.Model(table).Ctx(ctx).Data(g.Map{"id": 1, "name": "john"}).Insert()
        return err
    }); err != nil {
        return err
    }
    // Nested transaction 2, panic.
    if err := db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := db.Model(table).Ctx(ctx).Data(g.Map{"id": 2, "name": "smith"}).Insert()
        // Create a panic that can make this transaction rollback automatically.
        panic("error")
        return err
    }); err != nil {
        return err
    }
    return nil
})
```

如果您打开 `SQL` 日志，那么执行后将会看到以下日志信息，展示了整个数据库请求的详细执行流程：

```html
2021-05-22 21:18:46.672 [DEBU] [  2 ms] [default] [txid:1] BEGIN
2021-05-22 21:18:46.672 [DEBU] [  0 ms] [default] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:18:46.673 [DEBU] [  0 ms] [default] [txid:1] SHOW FULL COLUMNS FROM `user`
2021-05-22 21:18:46.674 [DEBU] [  0 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(1,'john')
2021-05-22 21:18:46.674 [DEBU] [  0 ms] [default] [txid:1] RELEASE SAVEPOINT `transaction0`
2021-05-22 21:18:46.675 [DEBU] [  1 ms] [default] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:18:46.675 [DEBU] [  0 ms] [default] [txid:1] INSERT INTO `user`(`name`,`id`) VALUES('smith',2)
2021-05-22 21:18:46.675 [DEBU] [  0 ms] [default] [txid:1] ROLLBACK TO SAVEPOINT `transaction0`
2021-05-22 21:18:46.676 [DEBU] [  1 ms] [default] [txid:1] ROLLBACK
```
:::warning
假如 `ctx` 上下文变量没有层层传递下去，那么嵌套事务将会失败，我们来看一个错误的例子：

```go
db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
    // Nested transaction 1.
    if err := db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := db.Model(table).Ctx(ctx).Data(g.Map{"id": 1, "name": "john"}).Insert()
        return err
    }); err != nil {
        return err
    }
    // Nested transaction 2, panic.
    if err := db.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        _, err := db.Model(table).Data(g.Map{"id": 2, "name": "smith"}).Insert()
        // Create a panic that can make this transaction rollback automatically.
        panic("error")
        return err
    }); err != nil {
        return err
    }
    return nil
})
```

打开 `SQL` 执行日志，执行后，您将会看到以下日志内容：

```html
2021-05-22 21:29:38.841 [DEBU] [  3 ms] [default] [txid:1] BEGIN
2021-05-22 21:29:38.842 [DEBU] [  1 ms] [default] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:29:38.843 [DEBU] [  1 ms] [default] [txid:1] SHOW FULL COLUMNS FROM `user`
2021-05-22 21:29:38.845 [DEBU] [  2 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(1,'john')
2021-05-22 21:29:38.845 [DEBU] [  0 ms] [default] [txid:1] RELEASE SAVEPOINT `transaction0`
2021-05-22 21:29:38.846 [DEBU] [  1 ms] [default] [txid:1] SAVEPOINT `transaction0`
2021-05-22 21:29:38.847 [DEBU] [  1 ms] [default] INSERT INTO `user`(`id`,`name`) VALUES(2,'smith')
2021-05-22 21:29:38.848 [DEBU] [  0 ms] [default] [txid:1] ROLLBACK TO SAVEPOINT `transaction0`
2021-05-22 21:29:38.848 [DEBU] [  0 ms] [default] [txid:1] ROLLBACK
```

可以看到，第二条 `INSERT` 操作 ``INSERT INTO `user`(`id`,`name`) VALUES(2,'smith') `` 没有事务ID打印，表示没有使用到事务，那么该操作将会被真正提交到数据库执行，并不能被回滚。
:::
## 四、 `SavePoint/RollbackTo`

开发者也可以灵活使用 `Transaction Save Point` 特性，并实现自定义的 `SavePoint` 命名以及指定 `Point` 回滚操作。

```go
tx, err := db.Begin()
if err != nil {
    panic(err)
}
defer func() {
    if err := recover(); err != nil {
        _ = tx.Rollback()
    }
}()
if _, err = tx.Model(table).Data(g.Map{"id": 1, "name": "john"}).Insert(); err != nil {
    panic(err)
}
if err = tx.SavePoint("MyPoint"); err != nil {
    panic(err)
}
if _, err = tx.Model(table).Data(g.Map{"id": 2, "name": "smith"}).Insert(); err != nil {
    panic(err)
}
if _, err = tx.Model(table).Data(g.Map{"id": 3, "name": "green"}).Insert(); err != nil {
    panic(err)
}
if err = tx.RollbackTo("MyPoint"); err != nil {
    panic(err)
}
if err = tx.Commit(); err != nil {
    panic(err)
}
```

如果您打开 `SQL` 日志，那么将会看到以下日志信息，展示了整个数据库请求的详细执行流程：

```html
2021-05-22 21:38:51.992 [DEBU] [  3 ms] [default] [txid:1] BEGIN
2021-05-22 21:38:52.002 [DEBU] [  9 ms] [default] [txid:1] SHOW FULL COLUMNS FROM `user`
2021-05-22 21:38:52.002 [DEBU] [  0 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(1,'john')
2021-05-22 21:38:52.003 [DEBU] [  1 ms] [default] [txid:1] SAVEPOINT `MyPoint`
2021-05-22 21:38:52.004 [DEBU] [  1 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(2,'smith')
2021-05-22 21:38:52.005 [DEBU] [  1 ms] [default] [txid:1] INSERT INTO `user`(`id`,`name`) VALUES(3,'green')
2021-05-22 21:38:52.006 [DEBU] [  0 ms] [default] [txid:1] ROLLBACK TO SAVEPOINT `MyPoint`
2021-05-22 21:38:52.006 [DEBU] [  0 ms] [default] [txid:1] COMMIT
```

执行后查询数据库结果：

```
mysql> select * from `user`;
+----+------+
| id | name |
+----+------+
|  1 | john |
+----+------+
1 row in set (0.00 sec)
```

可以看到，通过在第一个 `Insert` 操作后保存了一个 `SavePoint` 名称 `MyPoint`，随后的几次操作都通过 `RollbackTo` 方法被回滚掉了，因此只有第一次 `Insert` 操作被成功提交执行。

## 五、嵌套事务在工程中的参考示例

为了简化示例，我们还是使用用户模块相关的示例，例如用户注册，通过事务操作保存用户基本信息( `user`)、详细信息( `user_detail`)两个表，任一个表操作失败整个注册操作都将失败。为展示嵌套事务效果，我们将用户基本信息管理和用户详细信息管理划分为了两个 `dao` 对象。

假如我们的项目按照 `goframe` 标准项目工程化分为三层 `api-service-dao`，那么我们的嵌套事务操作可能是这样的。

### `controller`

```go
// 用户注册HTTP接口
func (*cUser) Signup(r *ghttp.Request) {
    // ....
    service.User().Signup(r.Context(), userServiceSignupReq)
    // ...
}
```

承接HTTP请求，并且将 `Context` 上下文边变量传递给后续的流程。

### `service`

```go
// 用户注册业务逻辑处理
func (*userService) Signup(ctx context.Context, r *model.UserServiceSignupReq) {
    // ....
    dao.User.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) error {
        err := dao.User.Ctx(ctx).Save(r.UserInfo)
        if err != nil {
            return err
        }
        err := dao.UserDetail.Ctx(ctx).Save(r.UserDetail)
        if err != nil {
            return err
        }
        return nil
    })
    // ...
}
```

可以看到，内部的 `user` 表和 `user_detail` 表使用了嵌套事务来统一执行事务操作。注意在闭包内部需要通过 `Ctx` 方法将上下文变量传递给下一层级。假如在闭包中存在对其他 `service` 对象的调用，那么也需要将 `ctx` 变量传递过去，例如：

```go
func (*userService) Signup(ctx context.Context, r *model.UserServiceSignupReq) {
    // ....
    dao.User.Transaction(ctx, func(ctx context.Context, tx gdb.Tx) (err error) {
        if err = dao.User.Ctx(ctx).Save(r.UserInfo); err != nil {
            return err
        }
        if err = dao.UserDetail.Ctx(ctx).Save(r.UserDetail); err != nil {
            return err
        }
        if err = service.XXXA().Call(ctx, ...); err != nil {
            return err
        }
        if err = service.XXXB().Call(ctx, ...); err != nil {
            return err
        }
        if err = service.XXXC().Call(ctx, ...); err != nil {
            return err
        }
        // ...
        return nil
    })
    // ...
}
```

### `dao`

`dao` 层的代码由 `goframe cli` 工具全自动化生成及维护即可。