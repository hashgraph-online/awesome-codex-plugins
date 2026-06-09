常规的事务操作方法为 `Begin/Commit/Rollback`，每一个方法指定特定的事务操作。开启事务操作可以通过执行 `db.Begin` 方法，该方法返回事务的操作接口，类型为 `gdb.Tx`，通过该对象执行后续的数据库操作，并可通过 `tx.Commit` 提交修改，或者通过 `tx.Rollback` 回滚修改。
:::warning
常见问题注意：开启事务操作后，请务必在不需要使用该事务对象时，通过 `Commit`/ `Rollback` 操作关闭掉该事务，建议充分利用好 `defer` 方法。如果事务使用后不关闭，在应用侧会引起 `goroutine` 不断激增泄露，在数据库侧会引起事务线程数量被打满，以至于后续的事务请求执行超时。此外，建议尽可能使用后续介绍的 `Transaction` 闭包方法来安全实现事务操作： [ORM事务处理-闭包操作](ORM事务处理-闭包操作.md)
:::
## 一、开启事务操作

```go
db := g.DB()

if tx, err := db.Begin(ctx); err == nil {
    fmt.Println("开启事务操作")
}
```

事务操作对象可以执行所有 `db` 对象的方法，具体请参考 [API文档](https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb)。

## 二、事务回滚操作

```go
if tx, err := db.Begin(ctx); err == nil {
    r, err := tx.Save("user", g.Map{
        "id"   :  1,
        "name" : "john",
    })
    if err != nil {
        tx.Rollback()
    }
    fmt.Println(r)
}
```

## 三、事务提交操作

```go
if tx, err := db.Begin(ctx); err == nil {
    r, err := tx.Save("user", g.Map{
        "id"   :  1,
        "name" : "john",
    })
    if err == nil {
       tx.Commit()
    }
    fmt.Println(r)
}
```

## 四、事务链式操作

事务操作对象仍然可以通过 `tx.Model` 方法返回一个链式操作的对象，该对象与 `db.Model` 方法返回值相同，只不过数据库操作在事务上执行，可提交或回滚。

```go
if tx, err := db.Begin(); err == nil {
    r, err := tx.Model("user").Data(g.Map{"id":1, "name": "john_1"}).Save()
    if err == nil {
       tx.Commit()
    }
    fmt.Println(r)
}
```

其他链式操作请参考 [ORM链式操作(🔥重点🔥)](../ORM链式操作/ORM链式操作.md) 章节。