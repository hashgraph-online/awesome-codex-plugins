`Model` 对象也可以通过 `TX` 事务接口创建，通过事务对象创建的 `Model` 对象与通过 `DB` 数据库对象创建的 `Model` 对象功能是一样的，只不过前者的所有操作都是基于事务，而当事务提交或者回滚后，对应的 `Model` 对象不能被继续使用，否则会返回错误。因为该 `TX` 接口不能被继续使用，一个事务对象仅对应于一个事务流程， `Commit`/ `Rollback` 后即结束。

本章节仅对链式操作涉及到的事务处理方法做简单介绍，更详细的介绍请参考 [ORM事务处理](../ORM事务处理/ORM事务处理.md) 章节。

## 示例1，通过 `Transaction`

为方便事务操作， `gdb` 提供了事务的闭包操作，通过 `Transaction` 方法实现，该方法定义如下：

```go
func (db DB) Transaction(ctx context.Context, f func(ctx context.Context, tx TX) error) (err error)
```

当给定的闭包方法返回的 `error` 为 `nil` 时，那么闭包执行结束后当前事务自动执行 `Commit` 提交操作；否则自动执行 `Rollback` 回滚操作。
:::tip
如果闭包内部操作产生 `panic` 中断，该事务也将进行回滚。
:::
```go
func Register() error {
    return g.DB().Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
        var (
            result sql.Result
            err    error
        )
        // 写入用户基础数据
        result, err = tx.Table("user").Insert(g.Map{
            "name":  "john",
            "score": 100,
            //...
        })
        if err != nil {
            return err
        }
        // 写入用户详情数据，需要用到上一次写入得到的用户uid
        result, err = tx.Table("user_detail").Insert(g.Map{
            "uid":   result.LastInsertId(),
            "phone": "18010576258",
            //...
        })
        return err
    })
}
```

## 示例2，通过 `TX` 链式操作

我们也可以在链式操作中通过 `TX` 方法切换绑定的事务对象。多次链式操作可以绑定同一个事务对象，在该事务对象中执行对应的链式操作。

```go
func Register() error {
    var (
        uid int64
        err error
    )
    tx, err := g.DB().Begin()
    if err != nil {
        return err
    }
    // 方法退出时检验返回值，
    // 如果结果成功则执行tx.Commit()提交,
    // 否则执行tx.Rollback()回滚操作。
    defer func() {
        if err != nil {
            tx.Rollback()
        } else {
            tx.Commit()
        }
    }()
    // 写入用户基础数据
    uid, err = AddUserInfo(tx, g.Map{
        "name":  "john",
        "score": 100,
        //...
    })
    if err != nil {
        return err
    }
    // 写入用户详情数据，需要用到上一次写入得到的用户uid
    err = AddUserDetail(tx, g.Map{
        "uid":   uid,
        "phone": "18010576259",
        //...
    })
    return err
}

func AddUserInfo(tx gdb.TX, data g.Map) (int64, error) {
    result, err := g.Model("user").TX(tx).Data(data).Insert()
    if err != nil {
        return 0, err
    }
    uid, err := result.LastInsertId()
    if err != nil {
        return 0, err
    }
    return uid, nil
}

func AddUserDetail(tx gdb.TX, data g.Map) error {
    _, err := g.Model("user_detail").TX(tx).Data(data).Insert()
    return err
}
```