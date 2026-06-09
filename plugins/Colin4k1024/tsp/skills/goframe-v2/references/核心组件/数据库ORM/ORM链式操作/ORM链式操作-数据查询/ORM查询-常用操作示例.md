## `in` 查询

使用字符串、 `slice` 参数类型。当使用 `slice` 参数类型时，预处理占位符只需要一个 `?` 即可。

```go
// SELECT * FROM user WHERE uid IN(100,10000,90000)
g.Model("user").Where("uid IN(?,?,?)", 100, 10000, 90000).All()
g.Model("user").Where("uid", g.Slice{100, 10000, 90000}).All()

// SELECT * FROM user WHERE gender=1 AND uid IN(100,10000,90000)
g.Model("user").Where("gender=? AND uid IN(?)", 1, g.Slice{100, 10000, 90000}).All()

// SELECT COUNT(*) FROM user WHERE age in(18,50)
g.Model("user").Where("age IN(?,?)", 18, 50).Count()
g.Model("user").Where("age", g.Slice{18, 50}).Count()
```

使用任意 `map` 参数类型。

```go
// SELECT * FROM user WHERE gender=1 AND uid IN(100,10000,90000)
g.Model("user").Where(g.Map{
    "gender" : 1,
    "uid"    : g.Slice{100,10000,90000},
}).All()
```

使用 `struct` 参数类型，注意查询条件的顺序和 `struct` 的属性定义顺序有关。

```go
type User struct {
    Id     []int  `orm:"uid"`
    Gender int    `orm:"gender"`
}
// SELECT * FROM `user` WHERE uid IN(100,10000,90000) AND gender=1
g.Model("user").Where(User{
    Gender: 1,
    Id:     []int{100, 10000, 90000},
}).All()

```

为提高易用性，当传递的 `slice` 参数为空或 `nil` 时，查询并不会报错，而是转换为一个 `false` 条件语句。

```go
// SELECT * FROM `user` WHERE 0=1
g.Model("user").Where("uid", g.Slice{}).All()
// SELECT * FROM `user` WHERE `uid` IS NULL
g.Model("user").Where("uid", nil).All()
```

`ORM` 同时也提供了常用条件方法 `WhereIn/WhereNotIn/WhereOrIn/WhereOrNotIn` 方法，用于常用的 `In` 查询条件过滤。方法定义如下：

```go
func (m *Model) WhereIn(column string, in interface{}) *Model
func (m *Model) WhereNotIn(column string, in interface{}) *Model
func (m *Model) WhereOrIn(column string, in interface{}) *Model
func (m *Model) WhereOrNotIn(column string, in interface{}) *Model
```

使用示例：

```go
// SELECT * FROM `user` WHERE (`gender`=1) AND (`type` IN(1,2,3))
g.Model("user").Where("gender", 1).WhereIn("type", g.Slice{1,2,3}).All()

// SELECT * FROM `user` WHERE (`gender`=1) AND (`type` NOT IN(1,2,3))
g.Model("user").Where("gender", 1).WhereNotIn("type", g.Slice{1,2,3}).All()

// SELECT * FROM `user` WHERE (`gender`=1) OR (`type` IN(1,2,3))
g.Model("user").Where("gender", 1).WhereOrIn("type", g.Slice{1,2,3}).All()

// SELECT * FROM `user` WHERE (`gender`=1) OR (`type` NOT IN(1,2,3))
g.Model("user").Where("gender", 1).WhereOrNotIn("type", g.Slice{1,2,3}).All()
```

## `like         ` 查询

```go
// SELECT * FROM `user` WHERE name like '%john%'
g.Model("user").Where("name like ?", "%john%").All()
// SELECT * FROM `user` WHERE birthday like '1990-%'
g.Model("user").Where("birthday like ?", "1990-%").All()

```

从 `goframe v1.16` 版本开始， `goframe` 的 `ORM` 同时也提供了常用条件方法 `WhereLike/WhereNotLike/WhereOrLike/WhereOrNotLike` 方法，用于常用的 `Like` 查询条件过滤。方法定义如下：

```go
func (m *Model) WhereLike(column string, like interface{}) *Model
func (m *Model) WhereNotLike(column string, like interface{}) *Model
func (m *Model) WhereOrLike(column string, like interface{}) *Model
func (m *Model) WhereOrNotLike(column string, like interface{}) *Model
```

使用示例：

```go
// SELECT * FROM `user` WHERE (`gender`=1) AND (`name` LIKE 'john%')
g.Model("user").Where("gender", 1).WhereLike("name", "john%").All()

// SELECT * FROM `user` WHERE (`gender`=1) AND (`name` NOT LIKE 'john%')
g.Model("user").Where("gender", 1).WhereNotLike("name", "john%").All()

// SELECT * FROM `user` WHERE (`gender`=1) OR (`name` LIKE 'john%')
g.Model("user").Where("gender", 1).WhereOrLike("name", "john%").All()

// SELECT * FROM `user` WHERE (`gender`=1) OR (`name` NOT LIKE 'john%')
g.Model("user").Where("gender", 1).WhereOrNotLike("name", "john%").All()
```

## `min/max/avg/sum`

我们直接将统计方法使用在 `Fields` 方法上，例如：

```go
// SELECT MIN(score) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Fields("MIN(score)").Where("uid", 1).Value()

// SELECT MAX(score) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Fields("MAX(score)").Where("uid", 1).Value()

// SELECT AVG(score) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Fields("AVG(score)").Where("uid", 1).Value()

// SELECT SUM(score) FROM `user` WHERE `uid`=1  LIMIT 1
g.Model("user").Fields("SUM(score)").Where("uid", 1).Value()
```

从 `goframe v1.16` 版本开始， `goframe` 的 `ORM` 同时也提供了常用统计方法 `Min/Max/Avg/Sum` 方法，用于常用的字段统计查询。方法定义如下：

```go
func (m *Model) Min(column string) (float64, error)
func (m *Model) Max(column string) (float64, error)
func (m *Model) Avg(column string) (float64, error)
func (m *Model) Sum(column string) (float64, error)
```

上面的示例使用快捷统计方法改造后：

```go
// SELECT MIN(`score`) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Where("uid", 1).Min("score")

// SELECT MAX(`score`) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Where("uid", 1).Max("score")

// SELECT AVG(`score`) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Where("uid", 1).Avg("score")

// SELECT SUM(`score`) FROM `user` WHERE `uid`=1 LIMIT 1
g.Model("user").Where("uid", 1).Sum("score")
```

## `count` 查询

```go
// SELECT COUNT(1) FROM `user` WHERE `birthday`='1990-10-01'
g.Model("user").Where("birthday", "1990-10-01").Count()
// SELECT COUNT(uid) FROM `user` WHERE `birthday`='1990-10-01'
g.Model("user").Fields("uid").Where("birthday", "1990-10-01").Count()

```

从 `goframe v1.16` 版本开始， `goframe` 的 `ORM` 同时也提供了一个按照字段进行 `Count` 的常用方法 `CountColumn`。方法定义如下：

```go
func (m *Model) CountColumn(column string) (int, error)
```

使用示例：

```go
g.Model("user").Where("birthday", "1990-10-01").CountColumn("uid")
```

## `distinct` 查询

```go
// SELECT DISTINCT uid,name FROM `user`
g.Model("user").Fields("DISTINCT uid,name").All()
// SELECT COUNT(DISTINCT uid,name) FROM `user`
g.Model("user").Fields("DISTINCT uid,name").Count()

```

从 `goframe v1.16` 版本开始， `goframe` 的 `ORM` 同时也提供了一个字段唯一性过滤标记方法 `Distinct`。方法定义如下：

```go
func (m *Model) Distinct() *Model
```

使用示例：

```go
// SELECT COUNT(DISTINCT `name`) FROM `user`
g.Model("user").Distinct().CountColumn("name")

// SELECT COUNT(DISTINCT uid,name) FROM `user`
g.Model("user").Distinct().CountColumn("uid,name")

// SELECT DISTINCT group,age FROM `user`
g.Model("user").Fields("group, age").Distinct().All()
```

## `between` 查询

```go
// SELECT * FROM `user` WHERE age between 18 and 20
g.Model("user").Where("age between ? and ?", 18, 20).All()

```

从 `goframe v1.16` 版本开始， `goframe` 的 `ORM` 同时也提供了常用条件方法 `WhereBetween/WhereNotBetween/WhereOrBetween/WhereOrNotBetween` 方法，用于常用的 `Between` 查询条件过滤。方法定义如下：

```go
func (m *Model) WhereBetween(column string, min, max interface{}) *Model
func (m *Model) WhereNotBetween(column string, min, max interface{}) *Model
func (m *Model) WhereOrBetween(column string, min, max interface{}) *Model
func (m *Model) WhereOrNotBetween(column string, min, max interface{}) *Model
```

使用示例：

```go
// SELECT * FROM `user` WHERE (`gender`=0) AND (`age` BETWEEN 16 AND 20)
g.Model("user").Where("gender", 0).WhereBetween("age", 16, 20).All()

// SELECT * FROM `user` WHERE (`gender`=0) AND (`age` NOT BETWEEN 16 AND 20)
g.Model("user").Where("gender", 0).WhereNotBetween("age", 16, 20).All()

// SELECT * FROM `user` WHERE (`gender`=0) OR (`age` BETWEEN 16 AND 20)
g.Model("user").Where("gender", 0).WhereOrBetween("age", 16, 20).All()

// SELECT * FROM `user` WHERE (`gender`=0) OR (`age` NOT BETWEEN 16 AND 20)
g.Model("user").Where("gender", 0).WhereOrNotBetween("age", 16, 20).All()
```

## `null` 查询

`ORM` 提供了常用条件方法 `WhereNull/WhereNotNull/WhereOrNull/WhereOrNotNull` 方法，用于常用的 `Null` 查询条件过滤。方法定义如下：

```go
func (m *Model) WhereNull(columns ...string) *Model
func (m *Model) WhereNotNull(columns ...string) *Model
func (m *Model) WhereOrNull(columns ...string) *Model
func (m *Model) WhereOrNotNull(columns ...string) *Model
```

使用示例：

```go
// SELECT * FROM `user` WHERE (`created_at`>'2021-05-01 00:00:00') AND (`inviter` IS NULL)
g.Model("user").Where("created_at>?", gtime.New("2021-05-01")).WhereNull("inviter").All()

// SELECT * FROM `user` WHERE (`created_at`>'2021-05-01 00:00:00') AND (`inviter` IS NOT NULL)
g.Model("user").Where("created_at>?", gtime.New("2021-05-01")).WhereNotNull("inviter").All()

// SELECT * FROM `user` WHERE (`created_at`>'2021-05-01 00:00:00') OR (`inviter` IS NULL)
g.Model("user").Where("created_at>?", gtime.New("2021-05-01")).WhereOrNull("inviter").All()

// SELECT * FROM `user` WHERE (`created_at`>'2021-05-01 00:00:00') OR (`inviter` IS NOT NULL)
g.Model("user").Where("created_at>?", gtime.New("2021-05-01")).WhereOrNotNull("inviter").All()
```

同时，这几个方法的参数支持多个字段输入，例如：

```go
// SELECT * FROM `user` WHERE (`created_at`>'2021-05-01 00:00:00') AND (`inviter` IS NULL) AND (`creator` IS NULL)
g.Model("user").Where("created_at>?", gtime.New("2021-05-01")).WhereNull("inviter", "creator").All()
```