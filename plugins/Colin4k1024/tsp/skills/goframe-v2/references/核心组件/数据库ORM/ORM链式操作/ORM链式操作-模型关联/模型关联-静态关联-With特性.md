## 一、设计背景

大家都知道易用性和易维护性一直是 `goframe` 一直努力建设的，也是 `goframe` 有别其他框架和组件比较大的一点差异。 `goframe` 没有采用其他 `ORM` 常见的 `BelongsTo`,`HasOne`,`HasMany`,`ManyToMany` 这样的模型关联设计，这样的关联关系维护较繁琐，例如外键约束、额外的标签备注等，对开发者有一定的心智负担。因此框架不倾向于通过向模型结构体中注入过多复杂的标签内容、关联属性或方法，并一如既往地尝试着简化设计，目标是使得模型关联查询尽可能得易于理解、使用便捷。因此在之前推出了 `ScanList` 方案，建议大家在继续了解 `With` 特性之前先了解一下 [模型关联-动态关联-ScanList](模型关联-动态关联-ScanList.md) 。

经过一系列的项目实践，我们发现 `ScanList` 虽然从运行时业务逻辑的角度来维护了模型关联关系，但是这种关联关系维护也不如期望的简便。因此，我们继续改进推出了可以通过模型简单维护关联关系的 `With` 模型关联特性，当然，这种特性仍然致力于提升整体框架的易用性和维护性，可以把 `With` 特性看做 `ScanList` 与模型关联关系维护的一种结合和改进。

:::warning
`With` 特性目前属于实验性特性。
:::
## 二、举个例子

我们先来一个简单的示例，便于大家更好理解 `With` 特性，该示例来自于之前的 `ScanList` 章节的相同示例，改进版。

### 1、数据结构

```sql
# 用户表
CREATE TABLE `user` (
  id int(10) unsigned NOT NULL AUTO_INCREMENT,
  name varchar(45) NOT NULL,
  PRIMARY KEY (id)
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
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

### 2、数据结构

根据表定义，我们可以得知：

1. 用户表与用户详情是 `1:1` 关系。
2. 用户表与用户学分是 `1:N` 关系。
3. 这里并没有演示 `N:N` 的关系，因为相比较于 `1:N` 的查询只是多了一次关联、或者一次查询，最终处理方式和 `1:N` 类似。

那么 `Golang` 的模型可定义如下：

```go
// 用户详情
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}
// 用户学分
type UserScores struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}
// 用户信息
type User struct {
    g.Meta `orm:"table:user"`
    Id         int           `json:"id"`
    Name       string        `json:"name"`
    UserDetail *UserDetail   `orm:"with:uid=id"`
    UserScores []*UserScores `orm:"with:uid=id"`
}
```

### 3、数据写入

为简化示例，我们这里创建 `5` 条用户数据，采用事务操作方式写入：

- 用户信息， `id` 为 `1-5`， `name` 为 `name_1` 到 `name_5`。
- 同时创建 `5` 条用户详情数据， `address` 数据为 `address_1` 到 `address_5`。
- 每个用户创建 `5` 条学分信息，学分为 `1-5`。

```go
g.DB().Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
    for i := 1; i <= 5; i++ {
        // User.
        user := User{
            Name: fmt.Sprintf(`name_%d`, i),
        }
        lastInsertId, err := g.Model(user).Data(user).OmitEmpty().InsertAndGetId()
        if err != nil {
            return err
        }
        // Detail.
        userDetail := UserDetail{
            Uid:     int(lastInsertId),
            Address: fmt.Sprintf(`address_%d`, lastInsertId),
        }
        _, err = g.Model(userDetail).Data(userDetail).OmitEmpty().Insert()
        if err != nil {
            return err
        }
        // Scores.
        for j := 1; j <= 5; j++ {
            userScore := UserScores{
                Uid:   int(lastInsertId),
                Score: j,
            }
            _, err = g.Model(userScore).Data(userScore).OmitEmpty().Insert()
            if err != nil {
                return err
            }
        }
    }
    return nil
})
```

执行成功后，数据库数据如下：

```text
mysql> show tables;
+----------------+
| Tables_in_test |
+----------------+
| user           |
| user_detail    |
| user_score     |
+----------------+
3 rows in set (0.01 sec)

mysql> select * from `user`;
+----+--------+
| id | name   |
+----+--------+
|  1 | name_1 |
|  2 | name_2 |
|  3 | name_3 |
|  4 | name_4 |
|  5 | name_5 |
+----+--------+
5 rows in set (0.01 sec)

mysql> select * from `user_detail`;
+-----+-----------+
| uid | address   |
+-----+-----------+
|   1 | address_1 |
|   2 | address_2 |
|   3 | address_3 |
|   4 | address_4 |
|   5 | address_5 |
+-----+-----------+
5 rows in set (0.00 sec)

mysql> select * from `user_score`;
+----+-----+-------+
| id | uid | score |
+----+-----+-------+
|  1 |   1 |     1 |
|  2 |   1 |     2 |
|  3 |   1 |     3 |
|  4 |   1 |     4 |
|  5 |   1 |     5 |
|  6 |   2 |     1 |
|  7 |   2 |     2 |
|  8 |   2 |     3 |
|  9 |   2 |     4 |
| 10 |   2 |     5 |
| 11 |   3 |     1 |
| 12 |   3 |     2 |
| 13 |   3 |     3 |
| 14 |   3 |     4 |
| 15 |   3 |     5 |
| 16 |   4 |     1 |
| 17 |   4 |     2 |
| 18 |   4 |     3 |
| 19 |   4 |     4 |
| 20 |   4 |     5 |
| 21 |   5 |     1 |
| 22 |   5 |     2 |
| 23 |   5 |     3 |
| 24 |   5 |     4 |
| 25 |   5 |     5 |
+----+-----+-------+
25 rows in set (0.00 sec)
```

### 4、数据查询

新的 `With` 特性下，数据查询相当简便，例如，我们查询一条数据：

```go
// 重新声明一下，防止大家上下来回拉动
// 用户详情
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}
// 用户学分
type UserScores struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}
// 用户信息
type User struct {
    g.Meta `orm:"table:user"`
    Id         int           `json:"id"`
    Name       string        `json:"name"`
    UserDetail *UserDetail   `orm:"with:uid=id"`
    UserScores []*UserScores `orm:"with:uid=id"`
}

var user *User
// WithAll 会查询带有with tag的字段，这个例子中，将会查询 UserDetail结构体对应的表和 UserScores结构体对应的表
g.Model(tableUser).WithAll().Where("id", 3).Scan(&user)
```

以上语句您将会查询到用户ID为 `3` 的用户信息、用户详情以及用户学分信息，以上语句将会在数据库中自动执行以下 `SQL` 语句：

```text
2021-05-02 22:29:52.634 [DEBU] [  2 ms] [default] SHOW FULL COLUMNS FROM `user`
2021-05-02 22:29:52.635 [DEBU] [  1 ms] [default] SELECT * FROM `user` WHERE `id`=3 LIMIT 1
2021-05-02 22:29:52.636 [DEBU] [  1 ms] [default] SHOW FULL COLUMNS FROM `user_detail`
2021-05-02 22:29:52.637 [DEBU] [  1 ms] [default] SELECT `uid`,`address` FROM `user_detail` WHERE `uid`=3 LIMIT 1
2021-05-02 22:29:52.643 [DEBU] [  6 ms] [default] SHOW FULL COLUMNS FROM `user_score`
2021-05-02 22:29:52.644 [DEBU] [  0 ms] [default] SELECT `id`,`uid`,`score` FROM `user_score` WHERE `uid`=3
```

执行后，通过 `g.Dump(user)` 打印的用户信息如下：

```js
{
    Id:         3,
    Name:       "name_3",
    UserDetail: {
        Uid:     3,
        Address: "address_3",
    },
    UserScores: [
        {
            Id:    11,
            Uid:   3,
            Score: 1,
        },
        {
            Id:    12,
            Uid:   3,
            Score: 2,
        },
        {
            Id:    13,
            Uid:   3,
            Score: 3,
        },
        {
            Id:    14,
            Uid:   3,
            Score: 4,
        },
        {
            Id:    15,
            Uid:   3,
            Score: 5,
        },
    ],
}
```

### 5、列表查询

我们来一个通过 `With` 特性查询列表的示例：

```go
var users []*User
// With(UserDetail{}) 只查询User结构体中的UserDetail对应的表
g.Model(users).With(UserDetail{}).Where("id>?", 3).Scan(&users)
```

执行后，通过 `g.Dump(users)` 打印用户数据如下：

```js
[
    {
        Id:         4,
        Name:       "name_4",
        UserDetail: {
            Uid:     4,
            Address: "address_4",
        },
        UserScores: [],
    },
    {
        Id:         5,
        Name:       "name_5",
        UserDetail: {
            Uid:     5,
            Address: "address_5",
        },
        UserScores: [],
    },
]
```

### 6、条件与排序

通过 `With` 特性关联时可以指定关联的额外条件，以及在多数据结果下指定排序规则。例如：

```go
type User struct {
    g.Meta `orm:"table:user"`
    Id         int           `json:"id"`
    Name       string        `json:"name"`
    UserDetail *UserDetail   `orm:"with:uid=id, where:uid > 3"`
    UserScores []*UserScores `orm:"with:uid=id, where:score>1 and score<5, order:score desc"`
}
```

通过 `orm` 标签中的 `where` 子标签以及 `order` 子标签指定额外关联条件体积排序规则。

### 7、`unscoped`标签
在`with`结构体标签中，支持使用`unscoped`特性，例如：
```go
type User struct {
    g.Meta `orm:"table:user"`
    Id         int          `json:"id"`
    Name       string       `json:"name"`
    UserDetail *UserDetail  `orm:"with:uid=id, unscoped:true"`
    UserScores []*UserScore `orm:"with:uid=id, unscoped:true"`
}
```

## 三、详细说明

想必您一定对上面的某些使用比较好奇，比如 `gmeta` 包、比如 `WithAll` 方法、比如 `orm` 标签中的 `with` 语句、比如 `Model` 方法给定 `struct` 参数识别数据表名等等，那这就对啦，接下来，我们详细聊聊吧。

### 1、 `gmeta` 包

我们可以看到在上面的结构体数据结构中都使用 `embed` 方式嵌入了一个 `g.Meta` 结构体，例如：

```go
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}
```

其实在 `GoFrame` 框架中有很多这种小组件包用以实现特定的便捷功能。 `gmeta` 包的作用主要用于嵌入到用户自定义的结构体中，并且通过标签的形式给 `gmeta` 包的结构体（例如这里的 `g.Meta`）打上自定义的标签内容（列如这里的 `` `orm:"table:user_detail"` ``），并在运行时可以特定方法动态获取这些自定义的标签内容。详情请参考章节： [元数据-gmeta](../../../../组件列表/实用工具/元数据-gmeta.md)

因此，这里嵌入 `g.Meta` 的目的是为了标记该结构体关联的数据表名称。

### 2、模型关联指定

在如下结构体中：

```go
type User struct {
    g.Meta `orm:"table:user"`
    Id         int          `json:"id"`
    Name       string       `json:"name"`
    UserDetail *UserDetail  `orm:"with:uid=id"`
    UserScores []*UserScore `orm:"with:uid=id"`
}
```

我们通过给指定的结构体属性绑定 `orm` 标签，并在 `orm` 标签中通过 `with` 语句指定当前结构体（数据表）与目标结构体（数据表）的关联关系， `with` 语句的语法如下：

```text
with:当前属性对应表关联字段=当前结构体对应数据表关联字段
```

并且字段名称 **忽略大小写以及特殊字符匹配**，例如以下形式的关联关系都是能够自动识别的：

```text
with:UID=ID
with:Uid=Id
with:U_ID=id
```

如果两个表的关联字段都是同一个名称，那么也可以直接写一个即可，例如：

```text
with:uid
```

在本示例中， `UserDetail` 属性对应的数据表为 `user_detail`， `UserScores` 属性对应的数据表为 `user_score`，两者与当前 `User` 结构体对应的表 `user` 都是使用 `uid` 进行关联，并且目标关联的 `user` 表的对应字段为 `id`。

### 3、 `With/WithAll`

#### 1）基本介绍

默认情况下，即使我们的结构体属性中的 `orm` 标签带有 `with` 语句， `ORM` 组件并不会默认启用 `With` 特性进行关联查询，而是需要依靠 `With/WithAll` 方法启用该查询特性。

- `With`：指定启用关联查询的数据表，通过给定的属性对象指定。
- `WithAll`：启用操作对象中所有带有 `with` 语句的属性结构体关联查询。

在我们本示例中，使用的是 `WithAll` 方法，因此自动启用了 `User` 表中的所有属性的模型关联查询，只要属性结构体关联了数据表，并且 `orm` 标签中带有 `with` 语句，那么都将会自动查询数据并根据模型结构的关联关系进行数据绑定。假如我们只启用某部分关联查询，并不启用全部属性模型的关联查询，那么可以使用 `With` 方法来指定。并且 `With` 方法可以指定启用多个关联模型的自动查询，在本示例中的 `WithAll` 就相当于：

```go
var user *User
g.Model(tableUser).With(UserDetail{}, UserScore{}).Where("id", 3).Scan(&user)
```

也可以这样：

```go
var user *User
g.Model(tableUser).With(User{}.UserDetail, User{}.UserScore).Where("id", 3).Scan(&user)
```

#### 2）仅关联用户详情模型

假如我们只需要查询用户详情，并不需要查询用户学分，那么我们可以使用 `With` 方法来启用指定对象对应数据表的关联查询，例如：

```go
var user *User
g.Model(tableUser).With(UserDetail{}).Where("id", 3).Scan(&user)
```

也可以这样：

```go
var user *User
g.Model(tableUser).With(User{}.UserDetail).Where("id", 3).Scan(&user)
```

执行后，通过 `g.Dump(user)` 打印用户数据如下：

```js
{
        "id": 3,
        "name": "name_3",
        "UserDetail": {
                "uid": 3,
                "address": "address_3"
        },
        "UserScores": []
}
```

#### 3）仅关联用户学分模型

我们也可以只关联查询用户学分信息，例如：

```go
var user *User
g.Model(tableUser).With(UserScore{}).Where("id", 3).Scan(&user)
```

也可以这样：

```go
var user *User
g.Model(tableUser).With(User{}.UserScore).Where("id", 3).Scan(&user)
```

执行后，通过 `g.Dump(user)` 打印用户数据如下：

```js
{
        "id": 3,
        "name": "name_3",
        "UserDetail": null,
        "UserScores": [
                {
                        "id": 11,
                        "uid": 3,
                        "score": 1
                },
                {
                        "id": 12,
                        "uid": 3,
                        "score": 2
                },
                {
                        "id": 13,
                        "uid": 3,
                        "score": 3
                },
                {
                        "id": 14,
                        "uid": 3,
                        "score": 4
                },
                {
                        "id": 15,
                        "uid": 3,
                        "score": 5
                }
        ]
}
```

#### 4）不关联任何模型查询

假如，我们不需要关联查询，那么更简单，例如：

```go
var user *User
g.Model(tableUser).Where("id", 3).Scan(&user)
```

执行后，通过 `g.Dump(user)` 打印用户数据如下：

```js
{
        "id": 3,
        "name": "name_3",
        "UserDetail": null,
        "UserScores": []
}
```

## 四、使用限制

### 1、字段查询与过滤

可以看到，在我们上面的示例中，并没有指定查询的字段，但是在打印的 `SQL` 日志中可以看到查询语句不是简单的 `SELECT *` 而是执行了具体的字段查询。在 `With` 特性下，将会自动按照关联模型对象的属性进行查询，属性的名称将会与数据表的字段做自动映射，并且会自动过滤掉无法自动映射的字段查询。

所以，在 `With` 特性下，我们无法做到仅查询属性中对应的某几个字段。如果需要实现仅查询并赋值某几个字段，建议您对 `model` 数据结构按照业务场景进行裁剪，创建满足特定业务场景的数据结构，而不是使用一个数据结构满足不同的多个场景。

我们来一个示例更好说明。假如我们有一个实体对象数据结构 `Content`，一个常见的 `CMS` 系统的内容模型如下，该模型与数据表字段一一对应：

```go
type Content struct {
    Id             uint        `orm:"id,primary"       json:"id"`               // 自增ID
    Key            string      `orm:"key"              json:"key"`              // 唯一键名，用于程序硬编码，一般不常用
    Type           string      `orm:"type"             json:"type"`             // 内容模型: topic, ask, article等，具体由程序定义
    CategoryId     uint        `orm:"category_id"      json:"category_id"`      // 栏目ID
    UserId         uint        `orm:"user_id"          json:"user_id"`          // 用户ID
    Title          string      `orm:"title"            json:"title"`            // 标题
    Content        string      `orm:"content"          json:"content"`          // 内容
    Sort           uint        `orm:"sort"             json:"sort"`             // 排序，数值越低越靠前，默认为添加时的时间戳，可用于置顶
    Brief          string      `orm:"brief"            json:"brief"`            // 摘要
    Thumb          string      `orm:"thumb"            json:"thumb"`            // 缩略图
    Tags           string      `orm:"tags"             json:"tags"`             // 标签名称列表，以JSON存储
    Referer        string      `orm:"referer"          json:"referer"`          // 内容来源，例如github/gitee
    Status         uint        `orm:"status"           json:"status"`           // 状态 0: 正常, 1: 禁用
    ReplyCount     uint        `orm:"reply_count"      json:"reply_count"`      // 回复数量
    ViewCount      uint        `orm:"view_count"       json:"view_count"`       // 浏览数量
    ZanCount       uint        `orm:"zan_count"        json:"zan_count"`        // 赞
    CaiCount       uint        `orm:"cai_count"        json:"cai_count"`        // 踩
    CreatedAt      *gtime.Time `orm:"created_at"       json:"created_at"`       // 创建时间
    UpdatedAt      *gtime.Time `orm:"updated_at"       json:"updated_at"`       // 修改时间
}
```

内容的列表页又不需要展示这么详细的内容，特别是其中的 `Content` 字段非常大，我们列表页只需要查询几个字段而已。那么我们可以单独定义一个用于列表的返回数据结构（字段裁剪），而不是直接使用数据表实体对象数据结构。例如：

```go
type ContentListItem struct {
    Id         uint        `json:"id"`          // 自增ID
    CategoryId uint        `json:"category_id"` // 栏目ID
    UserId     uint        `json:"user_id"`     // 用户ID
    Title      string      `json:"title"`       // 标题
    CreatedAt  *gtime.Time `json:"created_at"`  // 创建时间
    UpdatedAt  *gtime.Time `json:"updated_at"`  // 修改时间
}
```

### 2、必须存在关联字段属性

由于 `With` 特性是通过识别数据结构关联关系，并自动执行多条SQL查询来实现的，因此关联的字段也必须作为对象的属性便于关联字段值得自动获取。简单地讲， `with` 标签中的字段必须存在于关联对象的属性上。

## 五、递归关联

如果关联的模型属性也带有 `with` 标签，那么将会递归执行关联查询。 `With` 特性支持无限层级的递归关联。以下示例，仅供参考：

```go
// 用户详情
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}

// 用户学分 - 必修课
type UserScoresRequired struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}

// 用户学分 - 选修课
type UserScoresOptional struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}

// 用户学分
type UserScores struct {
    g.Meta `orm:"table:user_scores"`
    Id         int                  `json:"id"`
    Uid        int                  `json:"uid"`
    Required   []UserScoresRequired `orm:"with:id, where:type=1"`
    Optional   []UserScoresOptional `orm:"with:id, where:type=2"`
}

// 用户信息
type User struct {
    g.Meta `orm:"table:user"`
    Id         int           `json:"id"`
    Name       string        `json:"name"`
    UserDetail *UserDetail   `orm:"with:uid=id"`
    UserScores []*UserScores `orm:"with:uid=id"`
}
```

## 六、模型示例

根据当前的数据表，这里给了更多的一些模型编写示例供大家参考。

### 1、关联模型嵌套

```go
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}

type UserScores struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}

type User struct {
    g.Meta  `orm:"table:user"`
    *UserDetail `orm:"with:uid=id"`
    Id          int           `json:"id"`
    Name        string        `json:"name"`
    UserScores  []*UserScores `orm:"with:uid=id"`
}
```

嵌套的模型也支持嵌套，只要是结构体嵌套的都支持自动数据赋值。例如：

```go
type UserDetail struct {
    Uid     int    `json:"uid"`
    Address string `json:"address"`
}

type UserDetailEmbedded struct {
    UserDetail
}

type UserScores struct {
    Id    int `json:"id"`
    Uid   int `json:"uid"`
    Score int `json:"score"`
}

type User struct {
    *UserDetailEmbedded `orm:"with:uid=id"`
    Id                  int           `json:"id"`
    Name                string        `json:"name"`
    UserScores          []*UserScores `orm:"with:uid=id"`
}
```

### 2、基础模型嵌套

```go
type UserDetail struct {
    g.Meta `orm:"table:user_detail"`
    Uid        int    `json:"uid"`
    Address    string `json:"address"`
}

type UserScores struct {
    g.Meta `orm:"table:user_scores"`
    Id         int `json:"id"`
    Uid        int `json:"uid"`
    Score      int `json:"score"`
}

type UserEmbedded struct {
    Id   int    `json:"id"`
    Name string `json:"name"`
}

type User struct {
    g.Meta `orm:"table:user"`
    UserEmbedded
    *UserDetail `orm:"with:uid=id"`
    UserScores  []*UserScores `orm:"with:uid=id"`
}
```

### 3、模型不带 `meta` 信息

模型中的 `meta` 结构重要的是指定数据表名称，当不存在 `meta` 信息时，查询的数据表将会自动以结构体名称的 `CaseSnake` 名称。例如， `UserDetail` 将会自动使用 `user_detail` 数据表名称， `UserScores` 将会自动使用 `user_scores` 数据表名称。

```go
type UserDetail struct {
    Uid     int    `json:"uid"`
    Address string `json:"address"`
}

type UserScores struct {
    Id    int `json:"id"`
    Uid   int `json:"uid"`
    Score int `json:"score"`
}

type User struct {
    *UserDetail `orm:"with:uid=id"`
    Id          int           `json:"id"`
    Name        string        `json:"name"`
    UserScores  []*UserScores `orm:"with:uid=id"`
}
```

## 七、后续改进

- 目前 `With` 特性仅实现了查询操作，还不支持写入更新等操作。