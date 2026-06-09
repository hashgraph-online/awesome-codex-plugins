`Scan` 方法支持将查询结果转换为结构体或者结构体数组， `Scan` 方法将会根据给定的参数类型自动识别执行的转换类型。

## `struct` 对象

`Scan` 支持将查询结果转换为一个 `struct` 对象，查询结果应当是特定的一条记录，并且 `pointer` 参数应当为 `struct` 对象的指针地址（ `*struct` 或者 `**struct`），使用方式例如：

```go
type User struct {
    Id         int
    Passport   string
    Password   string
    NickName   string
    CreateTime *gtime.Time
}
user := User{}
g.Model("user").Where("id", 1).Scan(&user)
```

或者

```go
var user = User{}
g.Model("user").Where("id", 1).Scan(&user)
```

前两种方式都是预先初始化对象（提前分配内存），推荐的方式：

```go
var user *User
g.Model("user").Where("id", 1).Scan(&user)
```

这种方式只有在查询到数据的时候才会执行初始化及内存分配。注意在用法上的区别，特别是传递参数类型的差别（前两种方式传递的参数类型是 `*User`，这里传递的参数类型其实是 `**User`）。

## `struct` 数组

`Scan` 支持将多条查询结果集转换为一个 `[]struct/[]*struct` 数组，查询结果应当是多条记录组成的结果集，并且 `pointer` 应当为数组的指针地址，使用方式例如：

```go
var users []User
g.Model("user").Scan(&users)
```

或者

```go
var users []*User
g.Model("user").Scan(&users)
```