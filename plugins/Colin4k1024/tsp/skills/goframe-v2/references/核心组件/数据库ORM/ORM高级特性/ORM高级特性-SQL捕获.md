:::warning
需要注意，框架SQL捕获的原理是，任何SQL操作生成的 **SQL语句模板** 加上 **SQL执行参数**，在被提交给底层数据库引擎前会被框架拦截，并通过框架组件自动格式化生成可供人工阅读的字符串， **仅供参考和调试**，并不是完整提交给底层数据库引擎的SQL语句。捕获的SQL语句和ORM组件开启调试模式后输出的SQL语句是相同的，它们都由相同组件生成。
:::
## `CatchSQL`

我们可以使用 `gdb.CatchSQL` 方法来捕获指定范围内执行的 `SQL` 列表。该方法的定义如下：

```go
// CatchSQL catches and returns all sql statements that are EXECUTED in given closure function.
// Be caution that, all the following sql statements should use the context object passing by function `f`.
func CatchSQL(ctx context.Context, f func(ctx context.Context) error) (sqlArray []string, err error)
```

可以看到，该方法通过一个闭包函数来执行 `SQL` 语句，在闭包函数执行的所有 `SQL` 操作都将被记录并作为 `[]string` 类型。这里需要注意的是，闭包中执行的 `SQL` 操作都应当传递 `ctx` 上下文对象，否则 `SQL` 操作对应的语句无法记录。使用示例：

`user.sql`

```sql
CREATE TABLE `user` (
    `id`          int(10) unsigned NOT NULL AUTO_INCREMENT,
    `passport`    varchar(45) NULL,
    `password`    char(32) NULL,
    `nickname`    varchar(45) NULL,
    `create_time` timestamp(6) NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

`main.go`

```go
package main

import (
    "context"

    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/os/gtime"
)

type User struct {
    Id         int
    Passport   string
    Password   string
    Nickname   string
    CreateTime *gtime.Time
}

func initUser(ctx context.Context) error {
    _, err := g.Model("user").Ctx(ctx).Data(User{
        Id:       1,
        Passport: "john",
        Password: "12345678",
        Nickname: "John",
    }).Insert()
    return err
}

func main() {
    var ctx = gctx.New()
    sqlArray, err := gdb.CatchSQL(ctx, func(ctx context.Context) error {
        return initUser(ctx)
    })
    if err != nil {
        panic(err)
    }
    g.Dump(sqlArray)
}
```

执行后，终端输出：

```
[
    "SHOW FULL COLUMNS FROM `user`",
    "INSERT INTO `user`(`id`,`passport`,`password`,`nickname`,`created_at`,`updated_at`) VALUES(1,'john','12345678','John','2023-12-19 21:43:57','2023-12-19 21:43:57') ",
]
```

## `ToSQL`

我们可以通过 `gdb.ToSQL` 来将给定的 `SQL` 操作转换为 `SQL` 语句，并不真正提交执行。该方法的定义如下：

```go
// ToSQL formats and returns the last one of sql statements in given closure function
// WITHOUT TRULY EXECUTING IT.
// Be caution that, all the following sql statements should use the context object passing by function `f`.
func ToSQL(ctx context.Context, f func(ctx context.Context) error) (sql string, err error)
```

可以看到，该方法通过一个闭包函数来预估 `SQL` 语句，在闭包函数中的所有 `SQL` 操作都将被预估，但只会返回最后一条 `SQL` 语句作为 `string` 类型返回。这里需要注意的是，闭包中的 `SQL` 操作都应当传递 `ctx` 上下文对象，否则 `SQL` 操作对应的语句无法记录。使用示例：

`user.sql`

```sql
CREATE TABLE `user` (
    `id`          int(10) unsigned NOT NULL AUTO_INCREMENT,
    `passport`    varchar(45) NULL,
    `password`    char(32) NULL,
    `nickname`    varchar(45) NULL,
    `create_time` timestamp(6) NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

`main.go`

```go
package main

import (
    "context"

    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/os/gtime"
)

type User struct {
    Id         int
    Passport   string
    Password   string
    Nickname   string
    CreateTime *gtime.Time
}

func initUser(ctx context.Context) error {
    _, err := g.Model("user").Ctx(ctx).Data(User{
        Id:       1,
        Passport: "john",
        Password: "12345678",
        Nickname: "John",
    }).Insert()
    return err
}

func main() {
    var ctx = gctx.New()
    sql, err := gdb.ToSQL(ctx, func(ctx context.Context) error {
        return initUser(ctx)
    })
    if err != nil {
        panic(err)
    }
    g.Dump(sql)
}
```

执行后，终端输出：

```
"INSERT INTO `user`(`id`,`passport`,`password`,`nickname`,`created_at`,`updated_at`) VALUES(1,'john','12345678','John','2023-12-19 21:49:21','2023-12-19 21:49:21') "
```