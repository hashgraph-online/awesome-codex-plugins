:::warning
为安全性保证、防止误操作， `Update` 及 `Delete` 方法必须带有 `Where` 条件才能提交执行，否则将会错误返回，错误信息如： `there should be WHERE condition statement for XXX operation`。 `goframe` 是一款用于企业生产级别的框架，各个模块设计严谨，工程实践的细节处理得比较好。
:::
## `Update` 更新方法

`Update` 用于数据的更新，往往需要结合 `Data` 及 `Where` 方法共同使用。 `Data` 方法用于指定需要更新的数据， `Where` 方法用于指定更新的条件范围。同时， `Update` 方法也支持直接给定数据和条件参数。

使用示例：

```go
// UPDATE `user` SET `name`='john guo' WHERE name='john'
g.Model("user").Data(g.Map{"name" : "john guo"}).Where("name", "john").Update()
g.Model("user").Data("name='john guo'").Where("name", "john").Update()

// UPDATE `user` SET `status`=1 WHERE `status`=0 ORDER BY `login_time` asc LIMIT 10
g.Model("user").Data("status", 1).Order("login_time asc").Where("status", 0).Limit(10).Update()

// UPDATE `user` SET `status`=1 WHERE 1
g.Model("user").Data("status=1").Where(1).Update()
g.Model("user").Data("status", 1).Where(1).Update()
g.Model("user").Data(g.Map{"status" : 1}).Where(1).Update()
```

也可以直接给 `Update` 方法传递 `data` 及 `where` 参数：

```go
// UPDATE `user` SET `name`='john guo' WHERE name='john'
g.Model("user").Update(g.Map{"name" : "john guo"}, "name", "john")
g.Model("user").Update("name='john guo'", "name", "john")

// UPDATE `user` SET `status`=1 WHERE 1
g.Model("user").Update("status=1", 1)
g.Model("user").Update(g.Map{"status" : 1}, 1)
```

## `Counter` 更新特性

可以使用 `Counter` 类型参数对特定的字段进行数值操作，例如：增加、减少操作。

`Counter` 数据结构定义：

```go
// Counter  is the type for update count.
type Counter struct {
    Field string
    Value float64
}
```

`Counter` 使用示例，字段自增：

```go
updateData := g.Map{
    "views": &gdb.Counter{
        Field: "views",
        Value: 1,
    },
}
// UPDATE `article` SET `views`=`views`+1 WHERE `id`=1
result, err := db.Update("article", updateData, "id", 1)
```

`Counter` 也可以实现非自身字段的自增，例如：

```go
updateData := g.Map{
    "views": &gdb.Counter{
        Field: "clicks",
        Value: 1,
    },
}
// UPDATE `article` SET `views`=`clicks`+1 WHERE `id`=1
result, err := db.Update("article", updateData, "id", 1)
```

## `Increment/Decrement` 自增/减

我们可以通过 `Increment` 和 `Decrement` 方法实现对指定字段的自增/自减常用操作。两个方法的定义如下：

```go
// Increment increments a column's value by a given amount.
func (m *Model) Increment(column string, amount float64) (sql.Result, error)

// Decrement decrements a column's value by a given amount.
func (m *Model) Decrement(column string, amount float64) (sql.Result, error)
```

使用示例：

```go
// UPDATE `article` SET `views`=`views`+10000 WHERE `id`=1
g.Model("article").Where("id", 1).Increment("views", 10000)
// UPDATE `article` SET `views`=`views`-10000 WHERE `id`=1
g.Model("article").Where("id", 1).Decrement("views", 10000)
```

## `RawSQL` 语句嵌入

`gdb.Raw` 是字符串类型，该类型的参数将会直接作为 `SQL` 片段嵌入到提交到底层的 `SQL` 语句中，不会被自动转换为字符串参数类型、也不会被当做预处理参数。更详细的介绍请参考章节： [ORM高级特性-RawSQL](../ORM高级特性/ORM高级特性-RawSQL.md)。例如：

```go
// UPDATE `user` SET login_count='login_count+1',update_time='now()' WHERE id=1
g.Model("user").Data(g.Map{
    "login_count": "login_count+1",
    "update_time": "now()",
}).Where("id", 1).Update()
// 执行报错：Error Code: 1136. Column count doesn't match value count at row 1
```

使用 `gdb.Raw` 改造后：

```go
// UPDATE `user` SET login_count=login_count+1,update_time=now() WHERE id=1
g.Model("user").Data(g.Map{
    "login_count": gdb.Raw("login_count+1"),
    "update_time": gdb.Raw("now()"),
}).Where("id", 1).Update()
```

## `Delete` 删除方法

`Delete` 方法用于数据的删除。

使用示例：

```go
// DELETE FROM `user` WHERE uid=10
g.Model("user").Where("uid", 10).Delete()
// DELETE FROM `user` ORDER BY `login_time` asc LIMIT 10
g.Model("user").Order("login_time asc").Limit(10).Delete()
```

也可以直接给 `Delete` 方法传递 `where` 参数：

```go
// DELETE FROM `user` WHERE `uid`=10
g.Model("user").Delete("uid", 10)
// DELETE FROM `user` WHERE `score`<60
g.Model("user").Delete("score < ", 60)
```

## 软删除特性

软删除特性请查看章节： [ORM链式操作-时间维护](ORM链式操作-时间维护/ORM链式操作-时间维护.md)