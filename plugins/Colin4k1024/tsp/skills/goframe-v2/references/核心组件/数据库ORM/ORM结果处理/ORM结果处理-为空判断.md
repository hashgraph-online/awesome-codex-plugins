使用 `GoFrame ORM` 对返回结果为空判断非常简便，大部分场景下直接判断返回的数据是否为 `nil` 或者长度为 `0`，或者使用 `IsEmpty/IsNil` 方法。

## 一、数据集合（多条）

```go
r, err := g.Model("order").Where("status", 1).All()
if err != nil {
    return err
}
if len(r) == 0 {
    // 结果为空
}
```

也可以使用 `IsEmpty` 方法：

```go
r, err := g.Model("order").Where("status", 1).All()
if err != nil {
    return err
}
if r.IsEmpty() {
    // 结果为空
}
```

## 二、数据记录（单条）

```go
r, err := g.Model("order").Where("status", 1).One()
if err != nil {
    return err
}
if len(r) == 0 {
    // 结果为空
}
```

也可以使用 `IsEmpty` 方法：

```go
r, err := g.Model("order").Where("status", 1).One()
if err != nil {
    return err
}
if r.IsEmpty() {
    // 结果为空
}
```

## 三、数据字段值

返回的是一个"泛型"变量，这个只能使用 `IsEmpty` 来判断是否为空了。

```go
r, err := g.Model("order").Where("status", 1).Value()
if err != nil {
    return err
}
if r.IsEmpty() {
    // 结果为空
}
```

## 四、字段值数组

查询返回字段值数组本身类型为 `[]gdb.Value` 类型，因此直接判断长度是否为 `0` 即可。

```go
// Array/FindArray
r, err := g.Model("order").Fields("id").Where("status", 1).Array()
if err != nil {
    return err
}
if len(r) == 0 {
    // 结果为空
}
```

## 五、 `Struct` 对象（🔥注意🔥）

关于 `Struct` 转换对象来说 **会有一点不一样**，我们直接看例子吧。

当传递的对象 **本身就是一个空指针时**，如果查询到数据，那么会在内部 **自动创建这个对象**；如果没有查询到数据，那么这个空指针仍旧是一个空指针，内部并不会做任何处理。

```go
var user *User
err := g.Model("order").Where("status", 1).Scan(&user)
if err != nil {
    return err
}
if user == nil {
    // 结果为空
}
```

当传递的对象 **本身已经是一个初始化的对象**，如果查询到数据，那么会在内部将数据赋值给这个对象； **如果没有查询到数据，那么此时就没办法将对象做 `nil` 判断空结果**。因此 `ORM` 会返回一个 `sql.ErrNoRows` 错误，提醒开发者没有查询到任何数据并且对象没有做任何赋值，对象的所有属性还是给定的初始化数值，以便开发者可以做进一步的空结果判断。

```go
var user = new(User)
err := g.Model("order").Where("status", 1).Scan(&user)
if err != nil && err != sql.ErrNoRows {
    return err
}
if err == sql.ErrNoRows {
    // 结果为空
}
```
:::tip
所以我们推荐开发者不要传递一个初始化过后的对象给 `ORM`，而是直接传递一个对象的指针的指针类型（ `**struct` 类型）， `ORM` 内部会根据查询结果智能地做自动初始化。
:::
## 六、 `Struct` 数组

当传递的对象数组本身是一个空数组（长度为 `0`），如果查询到数据，那么会在内部自动赋值给数组；如果没有查询到数据，那么这个空数组仍旧是一个空数组，内部并不会做任何处理。

```go
var users []*User
err := g.Model("order").Where("status", 1).Scan(&users)
if err != nil {
    return err
}
if len(users) == 0 {
    // 结果为空
}
```

当传递的对象数组本身不是空数组，如果查询到数据，那么会在内部自动从索引 `0` 位置覆盖到数组上；如果没有查询到数据，那么此时就没办法将数组做长度为 `0` 判断空结果。因此 `ORM` 会返回一个 `sql.ErrNoRows` 错误，提醒开发者没有查询到任何数据并且数组没有做任何赋值，以便开发者可以做进一步的空结果判断。

```go
var users = make([]*User, 100)
err := g.Model("order").Where("status", 1).Scan(&users)
if err != nil {
    return err
}
if err == sql.ErrNoRows {
    // 结果为空
}
```
:::warning
由于 `struct` 转换利用了 `Golang` 反射特性，执行性能会有一定的损耗。如果您涉及到大量查询结果数据的 `struct` 数组对象转换，并且需要提高转换性能，请参考自定义实现对应 `struct` 的 `UnmarshalValue` 方法：
[类型转换-UnmarshalValue](../../类型转换/类型转换-UnmarshalValue.md)
:::