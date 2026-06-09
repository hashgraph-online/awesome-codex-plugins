框架数据库组件的驱动意义在于，数据库上层业务使用的各种方法操作不用变化，只需要修改配置中的数据库类型即可切换支持到新的数据库。

我们可以通过数据库组件的接口设计实现：新增框架默认不支持的第三方数据库驱动、对已有支持的驱动进行定制化修改等。驱动的开发并不是完整地开发一类数据库的协议实现代码，而是使用第三方已有的数据库驱动，通过实现框架数据库组件的接口，将该第三方数据库驱动对接到框架数据库组件上来，保证上层操作的一致。

## 驱动注册

之前我们有提到 `Driver` 的驱动接口，在实现该接口之后，我们可以通过以下方法注册自定义驱动到 `gdb` 模块：

```go
// Register registers custom database driver to gdb.
func Register(name string, driver Driver) error
```

其中的驱动名称 `name` 可以是已有的驱动名称，例如 `mysql`, `mssql`, `pgsql` 等等，当出现同名的驱动注册时，新的驱动将会覆盖老的驱动。

## 驱动实现

开发一个自定义的驱动并注册到 `gdb` 模块中非常简单，可以参考 `gdb` 模块源码中已对接的数据库类型代码示例： [https://github.com/gogf/gf/tree/master/contrib/drivers](https://github.com/gogf/gf/tree/master/contrib/drivers)

需要说明的是，最常见的驱动开发或者修改方式是直接继承于现有 `*Core` 类型，因为在 `Driver` 接口中会传递该类型的对象，例如：

```go
// DriverMysql is the driver for mysql database.
type DriverMysql struct {
    *Core
}

// New creates and returns a database object for mysql.
// It implements the interface of gdb.Driver for extra database driver installation.
func (d *DriverMysql) New(core *Core, node *ConfigNode) (DB, error) {
    return &DriverMysql{
        Core: core,
    }, nil
}
```

## 注意事项

一个新的驱动至少应该实现以下接口方法：

| 接口方法 | 说明 |
| --- | --- |
| `Open` | 用于创建数据库连接。 |
| `GetChars` | 用于获取该数据库的安全/转义符号。 |
| `Tables` | 返回当前/指定数据库的数据表列表。 |
| `TableFields` | 返回指定数据表的字段列表信息。 |