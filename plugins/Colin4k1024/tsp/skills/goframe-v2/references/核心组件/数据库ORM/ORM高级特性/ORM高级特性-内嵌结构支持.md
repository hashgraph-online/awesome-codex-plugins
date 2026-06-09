`GoFrame ORM` 组件针对于 `struct` 内嵌结构提供了良好的支持，包括参数传递、结果处理。例如：

```go
type Base struct {
    Uid        int         `orm:"uid"`
    CreateAt   *gtime.Time `orm:"create_at"`
    UpdateAt   *gtime.Time `orm:"update_at"`
    DeleteAt   *gtime.Time `orm:"delete_at"`
}
type User struct {
    Base
    Passport   string `orm:"passport"`
    Password   string `orm:"password"`
    Nickname   string `orm:"nickname"`
}
```

并且，无论多少层级的 `struct` 嵌套， `ORM` 的参数传递和结果处理都支持。