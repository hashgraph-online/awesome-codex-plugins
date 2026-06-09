## 基本介绍

自定义回调处理是最常见的接口开发实现，开发中只需要对接口中的部分方法进行 **替换与修改**，在驱动默认实现逻辑中注入自定义逻辑。参考接口关系图（ [ORM接口开发](ORM接口开发.md)）我们可以知道，所有的 `SQL` 语句执行必定会通过 `DoQuery` 或者 `DoExec` 或者 `DoFilter` 接口，根据需求在自定义的驱动中 **实现并覆盖** 相关接口方法实现所需功能即可。

其中，最常见的使用场景是在 `ORM` 底层实现对 `SQL` 的 **日志记录或者鉴权等统一判断操作**。

## 使用示例

我们来看一个自定义回调处理的示例，现需要将所有执行的 `SQL` 语句记录到 `monitor` 表中，以方便于进行 `SQL` 审计。因此通过自定义 `Driver` 然后覆盖 `ORM` 的底层接口方法来实现是最简单的。为简化示例编写，以下代码实现了一个自定义的 `MySQL` 驱动，该驱动继承于 `drivers` 下 `mysql` 模块内已经实现的 `Driver`。

```go
package driver

import (
    "context"

    "github.com/gogf/gf/contrib/drivers/mysql/v2"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/os/gtime"
)

// MyDriver is a custom database driver, which is used for testing only.
// For simplifying the unit testing case purpose, MyDriver struct inherits the mysql driver
// gdb.Driver and overwrites its functions DoQuery and DoExec.
// So if there's any sql execution, it goes through MyDriver.DoQuery/MyDriver.DoExec firstly
// and then gdb.Driver.DoQuery/gdb.Driver.DoExec.
// You can call it sql "HOOK" or "HiJack" as your will.
type MyDriver struct {
    *mysql.Driver
}

var (
    // customDriverName is my driver name, which is used for registering.
    customDriverName = "MyDriver"
)

func init() {
    // It here registers my custom driver in package initialization function "init".
    // You can later use this type in the database configuration.
    if err := gdb.Register(customDriverName, &MyDriver{}); err != nil {
        panic(err)
    }
}

// New creates and returns a database object for mysql.
// It implements the interface of gdb.Driver for extra database driver installation.
func (d *MyDriver) New(core *gdb.Core, node *gdb.ConfigNode) (gdb.DB, error) {
    return &MyDriver{
        &mysql.Driver{
            Core: core,
        },
    }, nil
}

// DoCommit commits current sql and arguments to underlying sql driver.
func (d *MyDriver) DoCommit(ctx context.Context, in gdb.DoCommitInput) (out gdb.DoCommitOutput, err error) {
    tsMilliStart := gtime.TimestampMilli()
    out, err = d.Core.DoCommit(ctx, in)
    tsMilliFinished := gtime.TimestampMilli()
    _, _ = in.Link.ExecContext(ctx,
        "INSERT INTO `monitor`(`sql`,`cost`,`time`,`error`) VALUES(?,?,?,?)",
        gdb.FormatSqlWithArgs(in.Sql, in.Args),
        tsMilliFinished-tsMilliStart,
        gtime.Now(),
        err,
    )
    return
}
```

我们看到，这里在包初始化方法 `init` 中使用了 `gdb.Register("MyDriver", &MyDriver{})` 来注册了了一个自定义名称的驱动。我们也可以通过 `gdb.Register("mysql", &MyDriver{})` 来覆盖已有的框架 `mysql` 驱动为自己的驱动。
:::tip
驱动名称 `mysql` 为框架默认的 `DriverMysql` 驱动的名称。
:::
由于这里我们使用了一个新的驱动名称 `MyDriver`，因此在 `gdb` 配置中的 `type` 数据库类型时，需要填写该驱动名称。以下是一个使用配置的示例：

```yaml
database:
  default:
  - link: "MyDriver:root:12345678@tcp(127.0.0.1:3306)/user"
```

## 注意事项

在接口方法实现中，需要使用接口的 `Link` 输入对象参数来操作数据库，如果使用 `g.DB` 方法获取数据库对象来操作可能会引起死锁问题。