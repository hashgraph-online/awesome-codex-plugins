## 常用方法

### `Insert/Replace/Save`

这几个链式操作方法用于数据的写入，并且支持自动的单条或者批量的数据写入，区别如下：

1. `Insert`
   
    使用 `INSERT INTO` 语句进行数据库写入，如果写入的数据中存在主键或者唯一索引时，返回失败，否则写入一条新数据。

2. `Replace`

    使用 `REPLACE INTO` 语句进行数据库写入，如果写入的数据中存在主键或者唯一索引时，会删除原有的记录，必定会写入一条新记录。

3. `Save`

    使用 `INSERT INTO` 语句进行数据库写入，如果写入的数据中存在主键或者唯一索引时，更新原有数据，否则写入一条新数据。对于部分数据库，例如 `PgSQL, SQL server, Oracle` 可以使用 `OnConflict` 方法指定冲突键。

    ```go
    db.Model(table).Data(g.Map{
        "id":          1,
        "passport":    "p1",
        "password":    "pw1",
    }).OnConflict("id").Save()
    ```

> 在部分数据库类型中，并不支持 `Replace/Save` 方法，具体请参考 [链式操作](../ORM链式操作/ORM链式操作.md) 介绍章节。

这几个方法需要结合 `Data` 方法使用，该方法用于传递数据参数，用于数据写入/更新等写操作。

### `InsertIgnore`

用于写入数据时如果写入的数据中存在主键或者唯一索引时，忽略错误继续执行写入。该方法定义如下：

```go
func (m *Model) InsertIgnore(data ...interface{}) (result sql.Result, err error)
```

### `InsertAndGetId`

用于写入数据时并直接返回自增字段的 `ID`。该方法定义如下：

```go
func (m *Model) InsertAndGetId(data ...interface{}) (lastInsertId int64, err error)
```

### `OnDuplicate/OnDuplicateEx`

`OnDuplicate/OnDuplicateEx` 方法需要结合 `Save` 方法一起使用，用于指定 `Save` 方法的更新/不更新字段，参数为字符串、字符串数组、 `Map`。例如：

```go
OnDuplicate("nickname, age")
OnDuplicate("nickname", "age")
OnDuplicate(g.Map{
    "nickname": gdb.Raw("CONCAT('name_', VALUES(`nickname`))"),
})
OnDuplicate(g.Map{
    "nickname": "passport",
})
```

其中 `OnDuplicateEx` 用于排除指定忽略更新的字段，排除的字段需要在写入的数据集合中。

#### 使用 `gdb.Counter` 实现字段自增

在使用 `OnDuplicate` 方法时，可以结合 `gdb.Counter` 类型来实现字段的自增操作。`gdb.Counter` 类型包含两个属性：`Field` 和 `Value`，分别表示要自增的字段名和自增的值。

```go
_, err := db.Model("user").OnConflict("id").OnDuplicate(g.Map{
    "count": gdb.Counter{Field: "count", Value: 1},       // count = count + 1
    "amount": gdb.Counter{Field: "amount", Value: 9.99}, // amount = amount + 9.99
}).Data(g.Map{
    "id":       1,
    "name":     "john",
    "count":    0,
    "amount":   0,
}).Save()
```

上述示例中，当插入数据时遇到 `id` 冲突，会将现有记录的 `count` 字段值增加 `1`，将 `amount` 字段值增加 `9.99`。这在需要统计计数或累加金额等场景中非常有用。

## 使用示例

### 示例1，基本使用

数据写入/保存方法需要结合 `Data` 方法使用，方法的参数类型可以为 `Map/Struct/Slice`：

```go
// INSERT INTO `user`(`name`) VALUES('john')
g.Model("user").Data(g.Map{"name": "john"}).Insert()

// INSERT IGNORE INTO `user`(`uid`,`name`) VALUES(10000,'john')
g.Model("user").Data(g.Map{"uid": 10000, "name": "john"}).InsertIgnore()

// REPLACE INTO `user`(`uid`,`name`) VALUES(10000,'john')
g.Model("user").Data(g.Map{"uid": 10000, "name": "john"}).Replace()

// INSERT INTO `user`(`uid`,`name`) VALUES(10001,'john') ON DUPLICATE KEY UPDATE `uid`=VALUES(`uid`),`name`=VALUES(`name`)
g.Model("user").Data(g.Map{"uid": 10001, "name": "john"}).Save()
```

也可以不使用 `Data` 方法，而给写入/保存方法直接传递数据参数：

```go
g.Model("user").Insert(g.Map{"name": "john"})
g.Model("user").Replace(g.Map{"uid": 10000, "name": "john"})
g.Model("user").Save(g.Map{"uid": 10001, "name": "john"})
```

数据参数也常用 `struct` 类型，例如当表字段为 `uid/name/site` 时：

```go
type User struct {
    Uid  int    `orm:"uid"`
    Name string `orm:"name"`
    Site string `orm:"site"`
}
user := &User{
    Uid:  1,
    Name: "john",
    Site: "https://goframe.org",
}
// INSERT INTO `user`(`uid`,`name`,`site`) VALUES(1,'john','https://goframe.org')
g.Model("user").Data(user).Insert()
```

### 示例2，数据批量写入

通过给 `Data` 方法输入 `Slice` 数组类型的参数，用以实现批量写入。数组元素需要为 `Map` 或者 `Struct` 类型，以便于数据库组件自动获取字段信息并生成批量操作 `SQL`。

```go
// INSERT INTO `user`(`name`) VALUES('john_1'),('john_2'),('john_3')
g.Model("user").Data(g.List{
    {"name": "john_1"},
    {"name": "john_2"},
    {"name": "john_3"},
}).Insert()
```

可以通过 `Batch` 方法指定批量操作中分批写入条数数量（默认是 `10`），以下示例将会被拆分为两条写入请求：

```go
// INSERT INTO `user`(`name`) VALUES('john_1'),('john_2')
// INSERT INTO `user`(`name`) VALUES('john_3')
g.Model("user").Data(g.List{
    {"name": "john_1"},
    {"name": "john_2"},
    {"name": "john_3"},
}).Batch(2).Insert()
```

### 示例3，数据批量保存

批量保存操作与单条保存操作原理是一样的，当写入的数据中存在主键或者唯一索引时将会更新原有记录值，否则新写入一条记录。

> `oracle, dm, mssql` 不支持批量保存。

```go
// INSERT INTO `user`(`uid`,`name`) VALUES(10000,'john_1'),(10001,'john_2'),(10002,'john_3')
// ON DUPLICATE KEY UPDATE `uid`=VALUES(`uid`),`name`=VALUES(`name`)
g.Model("user").Data(g.List{
    {"uid":10000, "name": "john_1"},
    {"uid":10001, "name": "john_2"},
    {"uid":10002, "name": "john_3"},
}).Save()
```

## `RawSQL` 语句嵌入

`gdb.Raw` 是字符串类型，该类型的参数将会直接作为 `SQL` 片段嵌入到提交到底层的 `SQL` 语句中，不会被自动转换为字符串参数类型、也不会被当做预处理参数。更详细的介绍请参考章节： [ORM高级特性-RawSQL](../ORM高级特性/ORM高级特性-RawSQL.md)。例如：

```go
// INSERT INTO `user`(`id`,`passport`,`password`,`nickname`,`create_time`) VALUES('id+2','john','123456','now()')
g.Model("user").Data(g.Map{
    "id":          "id+2",
    "passport":    "john",
    "password":    "123456",
    "nickname":    "JohnGuo",
    "create_time": "now()",
}).Insert()
// 执行报错：Error Code: 1136. Column count doesn't match value count at row 1
```

使用 `gdb.Raw` 改造后：

```go
// INSERT INTO `user`(`id`,`passport`,`password`,`nickname`,`create_time`) VALUES(id+2,'john','123456',now())
g.Model("user").Data(g.Map{
    "id":          gdb.Raw("id+2"),
    "passport":    "john",
    "password":    "123456",
    "nickname":    "JohnGuo",
    "create_time": gdb.Raw("now()"),
}).Insert()
```