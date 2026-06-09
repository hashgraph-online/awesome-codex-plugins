`gf` 的 `ORM` 没有采用其他 `ORM` 常见的 `BelongsTo`, `HasOne`, `HasMany`, `ManyToMany` 这样的模型关联设计，这样的关联关系维护较繁琐，例如外键约束、额外的标签备注等，对开发者有一定的心智负担。因此 `gf` 框架不倾向于通过向模型结构体中注入过多复杂的标签内容、关联属性或方法，并一如既往地尝试着简化设计，目标是使得模型关联查询尽可能得易于理解、使用便捷。
:::warning
接下来关于 `gf ORM` 提供的模型关联实现，从 `GoFrame v1.13.6` 版本开始提供，目前属于实验性特性。
:::
那么我们就使用一个例子来介绍 `gf ORM` 提供的模型关联吧。

### 数据结构

为简化示例，我们这里设计得表都尽可能简单，每张表仅包含3-4个字段，方便阐述关联关系即可。

```
# 用户表
CREATE TABLE `user` (
  uid int(10) unsigned NOT NULL AUTO_INCREMENT,
  name varchar(45) NOT NULL,
  PRIMARY KEY (uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 用户详情
CREATE TABLE `user_detail` (
  uid  int(10) unsigned NOT NULL AUTO_INCREMENT,
  address varchar(45) NOT NULL,
  PRIMARY KEY (uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# 用户学分
CREATE TABLE `user_scores` (
  id int(10) unsigned NOT NULL AUTO_INCREMENT,
  uid int(10) unsigned NOT NULL,
  score int(10) unsigned NOT NULL,
  course varchar(45) NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

```

### 数据模型

根据表定义，我们可以得知：

1. 用户表与用户详情是 `1:1` 关系。
2. 用户表与用户学分是 `1:N` 关系。
3. 这里并没有演示 `N:N` 的关系，因为相比较于 `1:N` 的查询只是多了一次关联、或者一次查询，最终处理方式和 `1:N` 类似。

那么 `Golang` 的模型可定义如下：

```go
// 用户表
type EntityUser struct {
    Uid  int    `orm:"uid"`
    Name string `orm:"name"`
}
// 用户详情
type EntityUserDetail struct {
    Uid     int    `orm:"uid"`
    Address string `orm:"address"`
}
// 用户学分
type EntityUserScores struct {
    Id     int    `orm:"id"`
    Uid    int    `orm:"uid"`
    Score  int    `orm:"score"`
    Course string `orm:"course"`
}
// 组合模型，用户信息
type Entity struct {
    User       *EntityUser
    UserDetail *EntityUserDetail
    UserScores []*EntityUserScores
}
```

其中， `EntityUser`, `EntityUserDetail`, `EntityUserScores` 分别对应的是用户表、用户详情、用户学分数据表的数据模型。 `Entity` 是一个组合模型，对应的是一个用户的所有详细信息。

### 数据写入

写入数据时涉及到简单的数据库事务即可。

```go
    err := g.DB().Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
            r, err := tx.Model("user").Save(EntityUser{
            Name: "john",
        })
        if err != nil {
            return err
        }
        uid, err := r.LastInsertId()
        if err != nil {
            return err
        }
        _, err = tx.Model("user_detail").Save(EntityUserDetail{
            Uid:     int(uid),
            Address: "Beijing DongZhiMen #66",
        })
        if err != nil {
            return err
        }
        _, err = tx.Model("user_scores").Save(g.Slice{
            EntityUserScores{Uid: int(uid), Score: 100, Course: "math"},
            EntityUserScores{Uid: int(uid), Score: 99, Course: "physics"},
        })
        return err
    })
```

### 数据查询

#### 单条数据记录

查询单条模型数据比较简单，直接使用 `Scan` 方法即可，该方法会自动识别绑定查询结果到单个对象属性还是数组对象属性中。例如：

```go
// 定义用户列表
var user Entity
// 查询用户基础数据
// SELECT * FROM `user` WHERE `name`='john'
err := g.Model("user").Scan(&user.User, "name", "john")
if err != nil {
    return err
}
// 查询用户详情数据
// SELECT * FROM `user_detail` WHERE `uid`=1
err := g.Model("user_detail").Scan(&user.UserDetail, "uid", user.User.Uid)
// 查询用户学分数据
// SELECT * FROM `user_scores` WHERE `uid`=1
err := g.Model("user_scores").Scan(&user.UserScores, "uid", user.User.Uid)
```

该方法在之前的章节中已经有介绍，因此这里不再赘述。

#### 多条数据记录

查询多条数据记录并绑定数据到数据模型数组中，需要使用到 `ScanList` 方法，该方法会需要用户指定结果字段与模型属性的关系，随后底层会遍历数组并自动执行数据绑定。例如：

```go
// 定义用户列表
var users []Entity
// 查询用户基础数据
// SELECT * FROM `user`
err := g.Model("user").ScanList(&users, "User")
// 查询用户详情数据
// SELECT * FROM `user_detail` WHERE `uid` IN(1,2)
err := g.Model("user_detail").
       WhereIn("uid", gdb.ListItemValuesUnique(users, "User", "Uid")).
       ScanList(&users, "UserDetail", "User", "uid:Uid")
// 查询用户学分数据
// SELECT * FROM `user_scores` WHERE `uid` IN(1,2)
err := g.Model("user_scores").
       WhereIn("uid", gdb.ListItemValuesUnique(users, "User", "Uid")).
       ScanList(&users, "UserScores", "User", "uid:Uid")
```

这其中涉及到两个比较重要的方法：

**1\. `ScanList`**

方法定义：

```go
// ScanList converts <r> to struct slice which contains other complex struct attributes.
// Note that the parameter <listPointer> should be type of *[]struct/*[]*struct.
// Usage example:
//
// type Entity struct {
//        User       *EntityUser
//        UserDetail *EntityUserDetail
//       UserScores []*EntityUserScores
// }
// var users []*Entity
// or
// var users []Entity
//
// ScanList(&users, "User")
// ScanList(&users, "UserDetail", "User", "uid:Uid")
// ScanList(&users, "UserScores", "User", "uid:Uid")
// The parameters "User"/"UserDetail"/"UserScores" in the example codes specify the target attribute struct
// that current result will be bound to.
// The "uid" in the example codes is the table field name of the result, and the "Uid" is the relational
// struct attribute name. It automatically calculates the HasOne/HasMany relationship with given <relation>
// parameter.
// See the example or unit testing cases for clear understanding for this function.
func (m *Model) ScanList(listPointer interface{}, attributeName string, relation ...string) (err error)
```

该方法用于将查询到的数组数据绑定到指定的列表上，例如：

- `ScanList(&users, "User")`

表示将查询到的用户信息数组数据绑定到 `users` 列表中每一项的 `User` 属性上。

- `ScanList(&users, "UserDetail", "User", "uid:Uid")`

表示将查询到用户详情数组数据绑定到 `users` 列表中每一项的 `UserDetail` 属性上，并且和另一个 `User` 对象属性通过 `uid:Uid` 的 `字段:属性` 关联，内部将会根据这一关联关系自动进行数据绑定。其中 `uid:Uid` 前面的 `uid` 表示查询结果字段中的 `uid` 字段，后面的 `Uid` 表示目标关联对象中的 `Uid` 属性。

- `ScanList(&users, "UserScores", "User", "uid:Uid")`

表示将查询到用户详情数组数据绑定到 `users` 列表中每一项的 `UserScores` 属性上，并且和另一个 `User` 对象属性通过 `uid:Uid` 的 `字段:属性` 关联，内部将会根据这一关联关系自动进行数据绑定。由于 `UserScores` 是一个数组类型 `[]*EntityUserScores`，因此该方法内部可以自动识别到 `User` 到 `UserScores` 其实是 `1:N` 的关系，自动完成数据绑定。

需要提醒的是，如果关联数据中对应的关联属性数据不存在，那么该属性不会被初始化并将保持 `nil`。

**2\. `ListItemValues/ListItemValuesUnique`**

方法定义：

```go
// ListItemValues retrieves and returns the elements of all item struct/map with key <key>.
// Note that the parameter <list> should be type of slice which contains elements of map or struct,
// or else it returns an empty slice.
//
// The parameter <list> supports types like:
// []map[string]interface{}
// []map[string]sub-map
// []struct
// []struct:sub-struct
// Note that the sub-map/sub-struct makes sense only if the optional parameter <subKey> is given.
func ListItemValues(list interface{}, key interface{}, subKey ...interface{}) (values []interface{})

// ListItemValuesUnique retrieves and returns the unique elements of all struct/map with key <key>.
// Note that the parameter <list> should be type of slice which contains elements of map or struct,
// or else it returns an empty slice.
// See gutil.ListItemValuesUnique.
func ListItemValuesUnique(list interface{}, key string, subKey ...interface{}) []interface{}
```

`ListItemValuesUnique` 与 `ListItemValues` 方法的区别在于过滤重复的返回值，保证返回的列表数据中不带有重复值。这两个方法都会在当给定的列表中包含 `struct`/ `map` 数据项时，用于获取指定属性/键名的数据值，构造成数组 `[]interface{}` 返回。示例：

- `gdb.ListItemValuesUnique(users, "Uid")` 用于获取 `users` 数组中，每一个 `Uid` 属性，构造成 `[]interface{}` 数组返回。这里以便根据 `uid` 构造成 `SELECT...IN...` 查询。
- `gdb.ListItemValuesUnique(users, "User", "Uid")` 用于获取 `users` 数组中，每一个 `User` 属性项中的 `Uid` 属性，构造成 `[]interface{}` 数组返回。这里以便根据 `uid` 构造成 `SELECT...IN...` 查询。