## `Fields/FieldsEx` 字段过滤

1. `Fields` 用于指定需要操作的表字段，包括查询字段、写入字段、更新字段等过滤；
2. `FieldsEx` 用于例外的字段指定，可用于查询字段、写入字段、更新字段等过滤；

### `Fields` 示例

1. 假如 `user` 表有4个字段 `uid`, `nickname`, `passport`, `password`。
2. 查询字段过滤
    ```go
    // SELECT `uid`,`nickname` FROM `user` ORDER BY `uid` asc
    g.Model("user").Fields("uid, nickname").Order("uid asc").All()
    ```

3. 写入字段过滤
    ```go
    m := g.Map{
        "uid"      : 10000,
        "nickname" : "John Guo",
        "passport" : "john",
        "password" : "123456",
    }
    g.Model(table).Fields("nickname,passport,password").Data(m).Insert()
    // INSERT INTO `user`(`nickname`,`passport`,`password`) VALUES('John Guo','john','123456')
    ```
4. 支持`gdb.Raw`输入
    ```go
    // SELECT 1 FROM `user` WHERE `id`=10
    g.Model("user").Fields(gdb.Raw("1")).Where("id", 10).Value()
    ```

### `FieldsEx` 示例

1. 假如 `user` 表有4个字段 `uid`, `nickname`, `passport`, `password`。
2. 查询字段排除

    ```go
    // SELECT `uid`,`nickname` FROM `user`
    g.Model("user").FieldsEx("passport, password").All()
    ```

1. 写入字段排除
    ```go
    m := g.Map{
        "uid"      : 10000,
        "nickname" : "John Guo",
        "passport" : "john",
        "password" : "123456",
    }
    g.Model(table).FieldsEx("uid").Data(m).Insert()
    // INSERT INTO `user`(`nickname`,`passport`,`password`) VALUES('John Guo','john','123456')
    ```

## `OmitEmpty` 空值过滤

当 `map`/ `struct` 中存在空值如 `nil`, `""`, `0` 时，默认情况下， `gdb` 将会将其当做正常的输入参数，因此这些参数也会被更新到数据表。 `OmitEmpty` 特性可以在将数据写入到数据库之前过滤空值数据的字段。

相关方法：

```go
func (m *Model) OmitEmpty() *Model
func (m *Model) OmitEmptyWhere() *Model
func (m *Model) OmitEmptyData() *Model
```

`OmitEmpty` 方法会同时过滤 `Where` 及 `Data` 中的空值数据，而通过 `OmitEmptyWhere/OmitEmptyData` 方法可以执行特定的字段过滤。

### 写入/更新操作

空值会影响于写入/更新操作方法，如 `Insert`, `Replace`, `Update`, `Save` 操作。如以下操作（以 `map` 为例， `struct` 同理）：

```go
// UPDATE `user` SET `name`='john',update_time=null WHERE `id`=1
g.Model("user").Data(g.Map{
    "name"        : "john",
    "update_time" : nil,
}).Where("id", 1).Update()
```

针对空值情况，我们可以通过 `OmitEmpty` 方法来过滤掉这些空值。例如，以上示例可以修改为：

```go
// UPDATE `user` SET `name`='john' WHERE `id`=1
g.Model("user").OmitEmpty().Data(g.Map{
    "name"        : "john",
    "update_time" : nil,
}).Where("id", 1).Update()
```

对于 `struct` 数据参数，我们也可以进行空值过滤。操作示例：

```go
type User struct {
    Id         int    `orm:"id"`
    Passport   string `orm:"passport"`
    Password   string `orm:"password"`
    NickName   string `orm:"nickname"`
    CreateTime string `orm:"create_time"`
    UpdateTime string `orm:"update_time"`
}
user := User{
    Id        : 1,
    NickName  : "john",
    UpdateTime: gtime.Now().String(),
}
g.Model("user").OmitEmpty().Data(user).Insert()
// INSERT INTO `user`(`id`,`nickname`,`update_time`) VALUES(1,'john','2019-10-01 12:00:00')
```
:::warning
注意哟，批量写入/更新操作中 `OmitEmpty` 方法将会失效，因为在批量操作中，必须保证每个写入记录的字段是统一的。
:::
关于 `omitempty` 标签与 `OmitEmpty` 方法：

1. 针对于 `struct` 的空值过滤大家会想到 `omitempty` 的标签。该标签常用于 `json` 转换的空值过滤，也在某一些第三方的 `ORM` 库中用作 `struct` 到数据表字段的空值过滤，即当属性为空值时不做转换。
2. `omitempty` 标签与 `OmitEmpty` 方法所达到的效果是一样的。在 `ORM` 操作中，我们不建议对 `struct` 使用 `omitempty` 的标签来控制字段的空值过滤，而建议使用 `OmitEmpty` 方法来做控制。因为该标签一旦加上之后便绑定到了 `struct` 上，没有办法做灵活控制；而通过 `OmitEmpty` 方法使得开发者可以选择性地、根据业务场景对 `struct` 做空值过滤，操作更加灵活。

### 数据查询操作

空值也会影响数据查询操作，主要是影响 `where` 条件参数。我们可以通过 `OmitEmpty` 方法过滤条件参数中的空值。

使用示例：

```go
// SELECT * FROM `user` WHERE `passport`='john' LIMIT 1
r, err := g.Model("user").Where(g.Map{
    "nickname" : "",
    "passport" : "john",
}).OmitEmpty().One()
```

```go
type User struct {
    Id         int    `orm:"id"`
    Passport   string `orm:"passport"`
    Password   string `orm:"password"`
    NickName   string `orm:"nickname"`
    CreateTime string `orm:"create_time"`
    UpdateTime string `orm:"update_time"`
}
user := User{
    Passport : "john",
}
r, err := g.Model("user").OmitEmpty().Where(user).One()
// SELECT * FROM `user` WHERE `passport`='john' LIMIT 1
```

## `OmitNil` 空值过滤

### 基本介绍

当 `map`/ `struct` 中存在空值如 `nil` 时，默认情况下， `gdb` 将会将其当做正常的输入参数，因此这些参数也会被更新到数据表。 `OmitNil` 特性可以在将数据写入到数据库之前过滤空值数据的字段。与 `OmitEmpty` 特性的区别在于， `OmitNil` 只会过滤值为 `nil` 的空值字段，其他空值如 `""`, `0` 并不会被过滤。

相关方法：

```go
func (m *Model) OmitNil() *Model
func (m *Model) OmitNilWhere() *Model
func (m *Model) OmitNilData() *Model
```

`OmitEmpty` 方法会同时过滤 `Where` 及 `Data` 中的空值数据，而通过 `OmitEmptyWhere/OmitEmptyData` 方法可以执行特定的字段过滤。

### 使用 `do` 对象进行字段过滤

如果使用 `GoFrame` 工程目录，通过 `gf gen dao` 或者 `make dao` 指令会自动根据配置的数据库生成对应的数据表 `dao/entity/do` 文件，如果在数据库操作中使用 `do` 对象，那么将会自动过滤未赋值的字段。例如：

生成的 `do` 对象结构体定义

```go
// User is the golang structure of table user for DAO operations like Where/Data.
type User struct {
    g.Meta   `orm:"table:user, do:true"`
    Id       interface{} // User ID
    Passport interface{} // User Passport
    Password interface{} // User Password
    Nickname interface{} // User Nickname
    CreateAt *gtime.Time // Created Time
    UpdateAt *gtime.Time // Updated Time
}
```

数据写入：

```go
dao.User.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
    _, err = dao.User.Ctx(ctx).Data(do.User{
        Passport: in.Passport,
        Password: in.Password,
        Nickname: in.Nickname,
    }).Insert()
    return err
})
```

数据查询：

```go
var user *entity.User
err = dao.User.Ctx(ctx).Where(do.User{
    Passport: in.Passport,
    Password: in.Password,
}).Scan(&user)
```

## `Filter` 字段过滤(已内置)

~~`gdb` 可以自动同步 **数据表结构** 到程序缓存中(缓存不过期，直至程序重启/重新部署)，并且可以过滤提交参数中不符合表结构的数据项，该特性可以使用 `Filter` 方法实现。常用于新增/删除操作中输入 `map/struct/[]map/[]string` 参数类型的场景。~~

~~使用示例，假如 `user` 表有4个字段 `uid`, `nickname`, `passport`, `password`：~~

```go
r, err := g.Model("user").Filter().Data(g.Map{
    "id"          : 1,
    "uid"         : 1,
    "passport"    : "john",
    "password"    : "123456",
}).Insert()
// INSERT INTO user(uid,passport,password) VALUES(1, "john", "123456")
```

~~其中 `id` 为不存在的字段，在写入数据时将会被过滤掉，不至于被构造成写入SQL中产生执行错误。~~
:::tip
~~数据库没有设计为 `Data` 方法做自动过滤，而是需要开发者调用 `Filter` 方法来手动指定过滤，目的是友好地提醒开发者可能误写/传递错误了字段名称。如果强制性的自动过滤可能会引起难以预料的业务逻辑异常，例如，由于字段名称拼写错误导致自动过滤了本来需要输入的字段，导致写入数据库的数据不完整。~~
:::
:::warning
从 `GoFrame v1.15.7` 版本开始，根据社区整体反馈，为提高组件易用性， `filter` 特性被设置为默认开启，不再需要显示调用， `Filter` 方法已被标记废弃。
:::