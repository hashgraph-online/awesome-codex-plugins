## 一、痛点描述

可以看到，通过常规的事务方法来管理事务有一些问题：

- **冗余代码较多**。代码中存在很多重复性的 `tx.Commit/Rollback` 操作。
- **操作风险较大**。非常容易遗忘执行 `tx.Commit/Rollback` 操作，或者由于代码逻辑判断 `BUG`，引发事务操作未正常关闭。在自行管理事务操作的情况下，大部分程序员都会踩到这个坑。作者已经见过了很多起由于事务未正常关闭引发的现网事故。我现在特意过来更新这段描述（2023-08-09），也是因为一个朋友由于自行通过 `tx.Commit/Rollback` 管理事务操作，细节未处理好，引发了现网事故。
- **嵌套事务实现复杂**。假如业务逻辑中存在多层级的事务处理（嵌套事务），需要考虑如何加个 `tx` 对象往下传递，处理起来更加繁琐。

## 二、闭包操作

因此为方便安全执行事务操作， `ORM` 组件同样提供了事务的闭包操作，通过 `Transaction` 方法实现，该方法定义如下：

```go
func (db DB) Transaction(ctx context.Context, f func(ctx context.Context, tx TX) error) (err error)
```

当给定的闭包方法返回的 `error` 为 `nil` 时，那么闭包执行结束后当前事务自动执行 `Commit` 提交操作；否则自动执行 `Rollback` 回滚操作。闭包中的 `context.Context` 参数为 `goframe v1.16` 版本后新增的上下文变量，主要用于链路跟踪传递以及嵌套事务管理。由于上下文变量是嵌套事务管理的重要参数，因此上下文变量通过显示的参数传递定义。
:::tip
如果闭包内部操作产生 `panic` 中断，该事务也将自动进行回滚，以保证操作安全。
:::
使用示例：

```go
g.DB().Transaction(context.TODO(), func(ctx context.Context, tx gdb.TX) error {
    // user
    result, err := tx.Ctx(ctx).Insert("user", g.Map{
        "passport": "john",
        "password": "12345678",
        "nickname": "JohnGuo",
    })
    if err != nil {
        return err
    }
    // user_detail
    id, err := result.LastInsertId()
    if err != nil {
        return err
    }
    _, err = tx.Ctx(ctx).Insert("user_detail", g.Map{
        "uid":       id,
        "site":      "https://johng.cn",
        "true_name": "GuoQiang",
    })
    if err != nil {
        return err
    }
    return nil
})
```

通过闭包操作的方式可以很简便地实现嵌套事务，且对上层业务开发同学来说无感知，具体可以继续阅读章节： [ORM事务处理-嵌套事务](ORM事务处理-嵌套事务.md)