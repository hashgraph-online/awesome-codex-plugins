当然，想必您已经猜到了，在对一些复杂类型（如 `struct`）的转换时， `gconv` 模块内部其实使用了反射的特性来实现的。这虽然为开发者提供了极大的便捷，但是这确实是以性能损耗为代价的。其实在对于 `struct` 转换时，如果开发者已经 **明确转换规则**，并且对于其中的性能损耗比较在意，那么可以对特定的 `struct` 实现 `UnmarshalValue` 接口来实现 **自定义转换**。当使用 `gconv` 模块对该 `struct` 进行转换时，无论该 `struct` 是直接作为转换对象或者作为转换对象的属性， `gconv` 都将会自动识别其实现的 `UnmarshalValue` 接口并直接调用该接口实现类型转换，而不会使用反射特性来实现转换。
:::tip
标准库的常用反序列化接口，如 `UnmarshalText(text []byte) error` 其实也是支持的哟，使用方式同 `UnmarshalValue`，只是参数不同。
:::
## 接口定义

```go
// apiUnmarshalValue is the interface for custom defined types customizing value assignment.
// Note that only pointer can implement interface apiUnmarshalValue.
type apiUnmarshalValue interface {
    UnmarshalValue(interface{}) error
}
```

可以看到，自定义的类型可以通过定义 `UnmarshalValue` 方法来实现自定义的类型转换。这里的输入参数为 `interface{}` 类型，开发者可以在实际使用场景中通过 类型断言 或者其他方式进行类型转换。
:::warning
需要特别注意，由于 `UnmarshalValue` 类型转换会修改当前对象的属性值，因此需要保证该接口实现的接受者( `Receiver`)是指针类型。

正确的接口实现定义示例（使用指针接受）：

```go
func (c *Receiver) UnmarshalValue(interface{}) error
```

**错误的** 接口实现定义示例（使用了值传递）：

```go
func (c Receiver) UnmarshalValue(interface{}) error
```
:::
## 使用示例

### 1、自定义数据表查询结果 `struct` 转换

数据表结构：

```sql
CREATE TABLE `user` (
   id bigint unsigned NOT NULL AUTO_INCREMENT,
   passport varchar(45),
   password char(32) NOT NULL,
   nickname varchar(45) NOT NULL,
   create_time timestamp NOT NULL,
   PRIMARY KEY (id)
) ;
```

示例代码：

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/container/garray"
    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/errors/gerror"
    "github.com/gogf/gf/v2/frame/g"
    "github.com/gogf/gf/v2/os/gtime"
    "reflect"
)

type User struct {
    Id         int
    Passport   string
    Password   string
    Nickname   string
    CreateTime *gtime.Time
}

// 实现UnmarshalValue接口，用于自定义结构体转换
func (user *User) UnmarshalValue(value interface{}) error {
    if record, ok := value.(gdb.Record); ok {
        *user = User{
            Id:         record["id"].Int(),
            Passport:   record["passport"].String(),
            Password:   "",
            Nickname:   record["nickname"].String(),
            CreateTime: record["create_time"].GTime(),
        }
        return nil
    }
    return gerror.Newf(`unsupported value type for UnmarshalValue: %v`, reflect.TypeOf(value))
}

func main() {
    var (
        err   error
        users []*User
    )
    array := garray.New(true)
    for i := 1; i <= 10; i++ {
        array.Append(g.Map{
            "id":          i,
            "passport":    fmt.Sprintf(`user_%d`, i),
            "password":    fmt.Sprintf(`pass_%d`, i),
            "nickname":    fmt.Sprintf(`name_%d`, i),
            "create_time": gtime.NewFromStr("2018-10-24 10:00:00").String(),
        })
    }
    // 写入数据
    _, err = g.Model("user").Data(array).Insert()
    if err != nil {
        panic(err)
    }
    // 查询数据
    err = g.Model("user").Order("id asc").Scan(&users)
    if err != nil {
        panic(err)
    }
    g.Dump(users)
}
```

执行后，终端输出：

```
[
    {
        Id:         1,
        Passport:   "user_1",
        Password:   "",
        Nickname:   "name_1",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         2,
        Passport:   "user_2",
        Password:   "",
        Nickname:   "name_2",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         3,
        Passport:   "user_3",
        Password:   "",
        Nickname:   "name_3",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         4,
        Passport:   "user_4",
        Password:   "",
        Nickname:   "name_4",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         5,
        Passport:   "user_5",
        Password:   "",
        Nickname:   "name_5",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         6,
        Passport:   "user_6",
        Password:   "",
        Nickname:   "name_6",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         7,
        Passport:   "user_7",
        Password:   "",
        Nickname:   "name_7",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         8,
        Passport:   "user_8",
        Password:   "",
        Nickname:   "name_8",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         9,
        Passport:   "user_9",
        Password:   "",
        Nickname:   "name_9",
        CreateTime: "2018-10-24 10:00:00",
    },
    {
        Id:         10,
        Passport:   "user_10",
        Password:   "",
        Nickname:   "name_10",
        CreateTime: "2018-10-24 10:00:00",
    },
]
```
:::tip
可以看到自定义的 `UnmarshalValue` 类型转换方法中没有使用到反射特性，因此转换的性能会得到极大的提升。小伙伴们可以尝试着增加写入的数据量（例如 `100W`），同时对比一下去掉 `UnmarshalValue` 后的类型转换所开销的时间。
:::
### 2、自定义二进制TCP数据解包

一个TCP通信的数据包解包示例。

```go
package main

import (
    "errors"
    "fmt"
    "github.com/gogf/gf/v2/crypto/gcrc32"
    "github.com/gogf/gf/v2/encoding/gbinary"
    "github.com/gogf/gf/v2/util/gconv"
)

type Pkg struct {
    Length uint16 // Total length.
    Crc32  uint32 // CRC32.
    Data   []byte
}

// NewPkg creates and returns a package with given data.
func NewPkg(data []byte) *Pkg {
    return &Pkg{
        Length: uint16(len(data) + 6),
        Crc32:  gcrc32.Encrypt(data),
        Data:   data,
    }
}

// Marshal encodes the protocol struct to bytes.
func (p *Pkg) Marshal() []byte {
    b := make([]byte, 6+len(p.Data))
    copy(b, gbinary.EncodeUint16(p.Length))
    copy(b[2:], gbinary.EncodeUint32(p.Crc32))
    copy(b[6:], p.Data)
    return b
}

// UnmarshalValue decodes bytes to protocol struct.
func (p *Pkg) UnmarshalValue(v interface{}) error {
    b := gconv.Bytes(v)
    if len(b) < 6 {
        return errors.New("invalid package length")
    }
    p.Length = gbinary.DecodeToUint16(b[:2])
    if len(b) < int(p.Length) {
        return errors.New("invalid data length")
    }
    p.Crc32 = gbinary.DecodeToUint32(b[2:6])
    p.Data = b[6:]
    if gcrc32.Encrypt(p.Data) != p.Crc32 {
        return errors.New("crc32 validation failed")
    }
    return nil
}

func main() {
    var p1, p2 *Pkg

    // Create a demo pkg as p1.
    p1 = NewPkg([]byte("123"))
    fmt.Println(p1)

    // Convert bytes from p1 to p2 using gconv.Struct.
    err := gconv.Struct(p1.Marshal(), &p2)
    if err != nil {
        panic(err)
    }
    fmt.Println(p2)
}
```

执行后，终端输出：

```
&{9 2286445522 [49 50 51]}
&{9 2286445522 [49 50 51]}
```