`GoFrame ORM` 组件支持 `Union/UnionAll` 操作， `Union/UnionAll` 操作符用于连接两个以上的 `SELECT` 语句的结果组合到一个结果集合中，关于 `Union/UnionAll` 组合查询的相关介绍可以参考MySQL的官方文档介绍 [https://dev.mysql.com/doc/refman/8.0/en/union.html](https://dev.mysql.com/doc/refman/8.0/en/union.html) 。我们可以通过链式操作或者方法操作来实现 `Union/UnionAll` 操作。

## 方法定义

```go
// Union does "(SELECT xxx FROM xxx) UNION (SELECT xxx FROM xxx) ..." statement.
func (c *Core) Union(unions ...*Model) *Model

// UnionAll does "(SELECT xxx FROM xxx) UNION ALL (SELECT xxx FROM xxx) ..." statement.
func (c *Core) UnionAll(unions ...*Model) *Model
```

## `Union`

使用 `Union` 操作符，多个 `SELECT` 语句会删除重复的数据。

```go
// 获取默认配置的数据库对象(配置名称为"default")
db := g.DB()

db.Union(
    db.Model("user").Where("id", 1),
    db.Model("user").Where("id", 2),
    db.Model("user").WhereIn("id", g.Slice{1, 2, 3}),
).OrderDesc("id").All()
// (SELECT * FROM `user` WHERE `id`=1)
// UNION
// (SELECT * FROM `user` WHERE `id`=2)
// UNION
// (SELECT * FROM `user` WHERE `id` IN (1,2,3)
// ORDER BY `id` DESC) ORDER BY `id` DESC
```

也可以通过 `dao` 链式操作实现：

```go
dao.User.Union(
    dao.User.Where(dao.User.Columns.Id, 1),
    dao.User.Where(dao.User.Columns.Id, 2),
    dao.User.WhereIn(dao.User.Columns.Id, g.Slice{1, 2, 3}),
).OrderDesc(dao.User.Columns.Id).All()
// (SELECT * FROM `user` WHERE `id`=1)
// UNION
// (SELECT * FROM `user` WHERE `id`=2)
// UNION
// (SELECT * FROM `user` WHERE `id` IN (1,2,3)
// ORDER BY `id` DESC) ORDER BY `id` DESC
```

## `UnionAll`

使用 `UnionAll` 操作符，多个 `SELECT` 语句不会删除重复的数据。

```go
db.UnionAll(
    db.Model("user").Where("id", 1),
    db.Model("user").Where("id", 2),
    db.Model(table).WhereIn("id", g.Slice{1, 2, 3}),
).OrderDesc("id").All()
// (SELECT * FROM `user` WHERE `id`=1)
// UNION ALL
// (SELECT * FROM `user` WHERE `id`=2)
// UNION ALL
// (SELECT * FROM `user` WHERE `id` IN (1,2,3)
// ORDER BY `id` DESC) ORDER BY `id` DESC
```

也可以通过 `dao` 链式操作实现：

```go
dao.User.UnionAll(
    dao.User.Where(dao.User.Columns.Id, 1),
    dao.User.Where(dao.User.Columns.Id, 2),
    dao.User.WhereIn(dao.User.Columns.Id, g.Slice{1, 2, 3}),
).OrderDesc(dao.User.Columns.Id).All()
// (SELECT * FROM `user` WHERE `id`=1)
// UNION ALL
// (SELECT * FROM `user` WHERE `id`=2)
// UNION ALL
// (SELECT * FROM `user` WHERE `id` IN (1,2,3)
// ORDER BY `id` DESC) ORDER BY `id` DESC
```