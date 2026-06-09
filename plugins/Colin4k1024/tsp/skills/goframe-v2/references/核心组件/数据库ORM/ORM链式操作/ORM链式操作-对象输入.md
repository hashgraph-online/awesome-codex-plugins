`Data/Where/WherePri/And/Or` 方法支持任意的 `string/map/slice/struct/*struct` 数据类型参数，该特性为 `gdb` 提供了很高的灵活性。当使用 `struct`/ `*struct` 对象作为输入参数时，将会被自动解析为 `map` 类型，只有 `struct` 的 **公开属性** 能够被转换，并且支持 `orm`/ `gconv`/ `json` 标签，用于定义转换后的键名，即与表字段的映射关系。

例如:

```go
type User struct {
    Uid      int    `orm:"user_id"`
    Name     string `orm:"user_name"`
    NickName string `orm:"nick_name"`
}
// 或者
type User struct {
    Uid      int    `gconv:"user_id"`
    Name     string `gconv:"user_name"`
    NickName string `gconv:"nick_name"`
}
// 或者
type User struct {
    Uid      int    `json:"user_id"`
    Name     string `json:"user_name"`
    NickName string `json:"nick_name"`
}
```

其中， `struct` 的属性应该是公开属性（首字母大写）， `orm` 标签对应的是数据表的字段名称。表字段的对应关系标签既可以使用 `orm`，也可以用 `gconv`，还可以使用传统的 `json` 标签，但是当三种标签都存在时， `orm` 标签的优先级更高。为避免将 `struct` 对象转换为 `JSON` 数据格式返回时与 `JSON` 编码标签冲突，推荐使用 `orm` 标签来实现数据库 `ORM` 的映射关系。更详细的转换规则请查看 [类型转换-Map转换](../../类型转换/类型转换-Map转换.md) 章节。