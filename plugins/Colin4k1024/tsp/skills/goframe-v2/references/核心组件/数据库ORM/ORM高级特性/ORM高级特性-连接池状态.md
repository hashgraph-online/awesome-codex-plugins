我们可以通过 `DB.Stats` 方法获取 `orm` 对象的连接池状态。我们来看个示例：

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gctx"
)

func main() {
    var ctx = gctx.New()
    db, err := gdb.New(gdb.ConfigNode{
        Link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test",
    })
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    err = db.PingMaster()
    if err != nil {
        g.Log().Fatal(ctx, err)
    }
    stats := db.Stats(ctx)
    g.Dump(stats)
}
```

执行后，终端输出如下，可以看到每个链接的数据库节点以及对应的连接池状态信息。

```html
[
    {
        node:  {
            Host:                 "127.0.0.1",
            Port:                 "3306",
            User:                 "root",
            Pass:                 "12345678",
            Name:                 "test",
            Type:                 "mysql",
            Link:                 "",
            Extra:                "",
            Role:                 "",
            Debug:                false,
            Prefix:               "",
            DryRun:               false,
            Weight:               0,
            Charset:              "utf8",
            Protocol:             "tcp",
            Timezone:             "",
            Namespace:            "",
            MaxIdleConnCount:     0,
            MaxOpenConnCount:     0,
            MaxConnLifeTime:      0,
            QueryTimeout:         0,
            ExecTimeout:          0,
            TranTimeout:          0,
            PrepareTimeout:       0,
            CreatedAt:            "",
            UpdatedAt:            "",
            DeletedAt:            "",
            TimeMaintainDisabled: false,
        },
        stats: {
            MaxOpenConnections: 0,
            OpenConnections:    1,
            InUse:              0,
            Idle:               1,
            WaitCount:          0,
            WaitDuration:       0,
            MaxIdleClosed:      0,
            MaxIdleTimeClosed:  0,
            MaxLifetimeClosed:  0,
        },
    },
]
```