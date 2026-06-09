## 基本介绍

这个问题由于大家问得比较多，因此单独开了一个章节详细介绍一下 `ORM` 中的时区处理是怎么一回事。我们这里以 `MySQL` 数据库为例来介绍时区转换的事情，本地时区我们设定为 `+8` 时区，数据库时区也是 `+8` 时区。

`MySQL` 数据库驱动用得最多的是这个第三方包： [https://github.com/go-sql-driver/mysql](https://github.com/go-sql-driver/mysql) ，在这个第三方包中有这么一个参数:

大概的意思是，当你提交的时间参数为 `time.Time` 时，该参数用来转换参数时区的。当你在连接数据库时，该参数传递 `loc=Local`，那么该 `driver` 将会自动将你提交的 `time.Time` 参数转换为本地程序设置的时区，没有手动设置时，那么该时区为 `UTC` 时区。那么我们来看两个例子。

## 转换示例

### 示例1，设置 `loc=Local`

**配置文件**

```yaml
database:
  link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test?loc=Local"
```

**代码示例**

```go
t1, _ := time.Parse("2006-01-02 15:04:05", "2020-10-27 10:00:00")
t2, _ := time.Parse("2006-01-02 15:04:05", "2020-10-27 11:00:00")
db.Model("user").Ctx(ctx).Where("create_time>? and create_time<?", t1, t2).One()
// SELECT * FROM `user` WHERE create_time>'2020-10-27 18:00:00' AND create_time<'2020-10-27 19:00:00'
```

这里由于通过 `time.Parse` 创建的 `time.Time` 时间对象是 `UTC` 时区，那么提交到数据库执行时将会被底层的 `driver` 修改为 `+8` 时区。

```go
t1, _ := time.ParseInLocation("2006-01-02 15:04:05", "2020-10-27 10:00:00", time.Local)
t2, _ := time.ParseInLocation("2006-01-02 15:04:05", "2020-10-27 11:00:00", time.Local)
db.Model("user").Ctx(ctx).Where("create_time>? and create_time<?", t1, t2).One()
// SELECT * FROM `user` WHERE create_time>'2020-10-27 10:00:00' AND create_time<'2020-10-27 11:00:00'
```

这里由于通过 `time.ParseInLocation` 创建的 `time.Time` 时间对象是 `+8` 时区，和 `loc=Local` 的时区一致，那么提交到数据库执行时不会被底层的 `driver` 修改。
:::warning
注意在写入数据中包含 `time.Time` 参数时，也需要注意时区转换的问题。
:::
### 示例2，不设置 `loc` 参数

**配置文件**

```yaml
database:
  link: "mysql:root:12345678@tcp(127.0.0.1:3306)/test"
```

**代码示例**

```go
t1, _ := time.Parse("2006-01-02 15:04:05", "2020-10-27 10:00:00")
t2, _ := time.Parse("2006-01-02 15:04:05", "2020-10-27 11:00:00")
db.Model("user").Ctx(ctx).Where("create_time>? and create_time<?", t1, t2).One()
// SELECT * FROM `user` WHERE create_time>'2020-10-27 10:00:00' AND create_time<'2020-10-27 11:00:00'
```

这里由于通过 `time.Parse` 创建的 `time.Time` 时间对象是 `UTC` 时区，那么提交到数据库执行时将不会被底层的 `driver` 修改。

```go
t1, _ := time.ParseInLocation("2006-01-02 15:04:05", "2020-10-27 10:00:00", time.Local)
t2, _ := time.ParseInLocation("2006-01-02 15:04:05", "2020-10-27 11:00:00", time.Local)
db.Model("user").Ctx(ctx).Where("create_time>? and create_time<?", t1, t2).One()
// SELECT * FROM `user` WHERE create_time>'2020-10-27 02:00:00' AND create_time<'2020-10-27 03:00:00'
```

这里由于通过 `time.ParseInLocation` 创建的 `time.Time` 时间对象是 `+8` 时区，那么提交到数据库执行时会被底层的 `driver` 修改为 `UTC` 时区。
:::warning
注意在写入数据中包含 `time.Time` 参数时，也需要注意时区转换的问题。
:::
## 改进建议

建议在配置中统一加上 `locl` 配置，例如（MySQL）： `loc=Local&parseTime=true`。以下是一个可供参考的配置：

```yaml
database:
  logger:
    level:  "all"
    stdout: true
  default:
    link:  "mysql:root:12345678@tcp(192.168.1.10:3306)/mydb?loc=Local&parseTime=true"
    debug: true
  order:
    link:  "mysql:root:12345678@tcp(192.168.1.20:3306)/order?loc=Local&parseTime=true"
    debug: true
```