`gdb` 模块使用了非常灵活且扩展性强的接口设计，接口设计允许开发者可以非常方便地自定义实现和替换接口定义中的任何方法。

## `DB` 接口

接口文档： [https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#DB](https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#DB)

`DB` 接口是数据库操作的核心接口，也是我们通过 `ORM` 操作数据库时最常用的接口，这里主要对接口的几个重要方法做说明：

1. `Open` 方法用于创建特定的数据库连接对象，返回的是标准库的 `*sql.DB` 通用数据库对象。
2. `Do*` 系列方法的第一个参数 `link` 为 `Link` 接口对象，该对象在 `master-slave` 模式下可能是一个主节点对象，也可能是从节点对象，因此如果在继承的驱动对象实现中使用该 `link` 参数时，注意当前的运行模式。 `slave` 节点在大部分的数据库主从模式中往往是不可写的。
3. `HandleSqlBeforeCommit` 方法将会在每一条 `SQL` 提交给数据库服务端执行时被调用做一些提交前的回调处理。
4. 其他接口方法详见接口文档或者源码文件。

## `DB` 接口关系

`GoFrame ORM Relations`

## `Driver` 接口

接口文档： [https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#Driver](https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#Driver)

开发者自定义的驱动需要实现以下接口：

```go
// Driver is the interface for integrating sql drivers into package gdb.
type Driver interface {
    // New creates and returns a database object for specified database server.
    New(core *Core, node *ConfigNode) (DB, error)
}
```

其中的 `New` 方法用于根据 `Core` 数据库基础对象以及 `ConfigNode` 配置对象创建驱动对应的数据库操作对象，需要注意的是，返回的数据库对象需要实现 `DB` 接口。而数据库基础对象 `Core` 已经实现了 `DB` 接口，因此开发者只需要”继承” `Core` 对象，然后根据需要覆盖对应的接口实现方法即可。

## 相关文档