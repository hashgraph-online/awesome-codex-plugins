## 方法操作

方法操作用于原生 `SQL` 执行，相对链式操作更偏底层操作一些，在 `ORM` 链式操作执行不了太过于复杂的 `SQL` 操作时，可以交给方法操作来处理。

**接口文档：** 

[https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#DB](https://pkg.go.dev/github.com/gogf/gf/v2/database/gdb#DB)

**常用方法：**

本文档的方法列表可能滞后于于代码，详细的方法列表请查看接口文档，以下方法仅供参考。

```go
// SQL操作方法，返回原生的标准库sql对象
Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error)
Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error)
Prepare(ctx context.Context, query string) (*sql.Stmt, error)

// 数据表记录查询：
// 查询单条记录、查询多条记录、获取记录对象、查询单个字段值(链式操作同理)
GetAll(ctx context.Context, sql string, args ...interface{}) (Result, error)
GetOne(ctx context.Context, sql string, args ...interface{}) (Record, error)
GetValue(ctx context.Context, sql string, args ...interface{}) (Value, error)
GetArray(ctx context.Context, sql string, args ...interface{}) ([]Value, error)
GetCount(ctx context.Context, sql string, args ...interface{}) (int, error)
GetScan(ctx context.Context, objPointer interface{}, sql string, args ...interface{}) error

// 数据单条操作
Insert(ctx context.Context, table string, data interface{}, batch...int) (sql.Result, error)
Replace(ctx context.Context, table string, data interface{}, batch...int) (sql.Result, error)
Save(ctx context.Context, table string, data interface{}, batch...int) (sql.Result, error)

// 数据修改/删除
Update(ctx context.Context, table string, data interface{}, condition interface{}, args ...interface{}) (sql.Result, error)
Delete(ctx context.Context, table string, condition interface{}, args ...interface{}) (sql.Result, error)
```

**简要说明：**

1. `Query` 是原始的数据查询方法，返回的是原生的标准库的结果集对象，需要自行解析。推荐使用 `Get*` 方法，会对结果自动做解析。
2. `Exec` 方法用于写入/更新的 `SQL` 的操作。
3.  在执行数据查询时推荐使用 `Get*` 系列查询方法。
4. `Insert`/ `Replace`/ `Save` 方法中的 `data` 参数支持的数据类型为： `string/map/slice/struct/*struct`，当传递为 `slice` 类型时，自动识别为批量操作，此时 `batch` 参数有效。

## 操作示例

### 1\. `ORM` 对象

```go
// 获取默认配置的数据库对象(配置名称为"default")
db := g.DB()

// 获取配置分组名称为"user-center"的数据库对象
db := g.DB("user-center")

// 使用原生单例管理方法获取数据库对象单例
db, err := gdb.Instance()
db, err := gdb.Instance("user-center")

// 注意不用的时候不需要使用Close方法关闭数据库连接(并且gdb也没有提供Close方法)，
// 数据库引擎底层采用了链接池设计，当链接不再使用时会自动关闭
```

### 2\. 数据写入

```go
r, err := db.Insert(ctx, "user", gdb.Map {
    "name": "john",
})
```

### 3\. 数据查询(列表)

```go
list, err := db.GetAll(ctx, "select * from user limit 2")
list, err := db.GetAll(ctx, "select * from user where age > ? and name like ?", g.Slice{18, "%john%"})
list, err := db.GetAll(ctx, "select * from user where status=?", g.Slice{1})
```

### 4\. 数据查询(单条)

```go
one, err := db.GetOne(ctx, "select * from user limit 2")
one, err := db.GetOne(ctx, "select * from user where uid=1000")
one, err := db.GetOne(ctx, "select * from user where uid=?", 1000)
one, err := db.GetOne(ctx, "select * from user where uid=?", g.Slice{1000})
```

### 5\. 数据保存

```go
r, err := db.Save(ctx, "user", gdb.Map {
    "uid"  :  1,
    "name" : "john",
})
```

### 6\. 批量操作

其中 `batch` 参数用于指定批量操作中分批写入条数数量（默认是 `10`）。

```go
_, err := db.Insert(ctx, "user", gdb.List {
    {"name": "john_1"},
    {"name": "john_2"},
    {"name": "john_3"},
    {"name": "john_4"},
}, 10)
```

### 7\. 数据更新/删除

```go
// db.Update/db.Delete 同理
// UPDATE `user` SET `name`='john' WHERE `uid`=10000
r, err := db.Update(ctx, "user", gdb.Map {"name": "john"}, "uid=?", 10000)
// UPDATE `user` SET `name`='john' WHERE `uid`=10000
r, err := db.Update(ctx, "user", "name='john'", "uid=10000")
// UPDATE `user` SET `name`='john' WHERE `uid`=10000
r, err := db.Update(ctx, "user", "name=?", "uid=?", "john", 10000)
```

注意，参数域支持并建议使用预处理模式（使用 `?` 占位符）进行输入，避免 `SQL` 注入风险。