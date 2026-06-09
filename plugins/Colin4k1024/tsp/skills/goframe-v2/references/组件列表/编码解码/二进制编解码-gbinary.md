## 基本介绍

`GoFrame`框架提供了独立的二进制数据操作包`gbinary`，主要用于各种数据类型与`[]byte`二进制类型之间的相互转换；以及针对于整型数据进行精准按位处理的功能。常用于网络通信时数据编码/解码，以及数据文件操作时的编码/解码。

**使用方式**：

```go
import "github.com/gogf/gf/v2/encoding/gbinary"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/encoding/gbinary](https://pkg.go.dev/github.com/gogf/gf/v2/encoding/gbinary)

用于二进制数据结构转换处理的接口文档如下：

```go
func Encode(vs ...interface{}) ([]byte, error)
func EncodeInt(i int) []byte
func EncodeInt8(i int8) []byte
func EncodeInt16(i int16) []byte
func EncodeInt32(i int32) []byte
func EncodeInt64(i int64) []byte
func EncodeUint(i uint) []byte
func EncodeUint8(i uint8) []byte
func EncodeUint16(i uint16) []byte
func EncodeUint32(i uint32) []byte
func EncodeUint64(i uint64) []byte
func EncodeBool(b bool) []byte
func EncodeFloat32(f float32) []byte
func EncodeFloat64(f float64) []byte
func EncodeString(s string) []byte

func Decode(b []byte, vs ...interface{}) error
func DecodeToInt(b []byte) int
func DecodeToInt8(b []byte) int8
func DecodeToInt16(b []byte) int16
func DecodeToInt32(b []byte) int32
func DecodeToInt64(b []byte) int64
func DecodeToUint(b []byte) uint
func DecodeToUint8(b []byte) uint8
func DecodeToUint16(b []byte) uint16
func DecodeToUint32(b []byte) uint32
func DecodeToUint64(b []byte) uint64
func DecodeToBool(b []byte) bool
func DecodeToFloat32(b []byte) float32
func DecodeToFloat64(b []byte) float64
func DecodeToString(b []byte) string
```

支持按位处理的接口文档如下：

```go
func EncodeBits(bits []Bit, i int, l int) []Bit
func EncodeBitsWithUint(bits []Bit, ui uint, l int) []Bit
func EncodeBitsToBytes(bits []Bit) []byte
func DecodeBits(bits []Bit) uint
func DecodeBitsToUint(bits []Bit) uint
func DecodeBytesToBits(bs []byte) []Bit
```

其中的`Bit`类型表示一个二进制数字(0或1)，其定义如下：

```go
type Bit int8
```

## 使用示例

我们来看一个比较完整的二进制操作示例，基本演示了绝大部分的二进制转换操作。

```go
package main

import (
    "fmt"
    "github.com/gogf/gf/v2/encoding/gbinary"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/os/glog"
)

func main() {
    // 使用gbinary.Encoded对基本数据类型进行二进制打包
    if buffer := gbinary.Encode(18, 300, 1.01); buffer != nil {
        // glog.Error(err)
    } else {
        fmt.Println(buffer)
    }

    // 使用gbinary.Decode对整形二进制解包，注意第二个及其后参数为字长确定的整形变量的指针地址，字长确定的类型，
    // 例如：int8/16/32/64、uint8/16/32/64、float32/64
    // 这里的1.01默认为float64类型(64位系统下)
    if buffer := gbinary.Encode(18, 300, 1.01); buffer != nil {
        //glog.Error(err)
    } else {
        var i1 int8
        var i2 int16
        var f3 float64
        if err := gbinary.Decode(buffer, &i1, &i2, &f3); err != nil {
            glog.Error(gctx.New(), err)
        } else {
            fmt.Println(i1, i2, f3)
        }
    }

    // 编码/解析 int，自动识别变量长度
    fmt.Println(gbinary.DecodeToInt(gbinary.EncodeInt(1)))
    fmt.Println(gbinary.DecodeToInt(gbinary.EncodeInt(300)))
    fmt.Println(gbinary.DecodeToInt(gbinary.EncodeInt(70000)))
    fmt.Println(gbinary.DecodeToInt(gbinary.EncodeInt(2000000000)))
    fmt.Println(gbinary.DecodeToInt(gbinary.EncodeInt(500000000000)))

    // 编码/解析 uint，自动识别变量长度
    fmt.Println(gbinary.DecodeToUint(gbinary.EncodeUint(1)))
    fmt.Println(gbinary.DecodeToUint(gbinary.EncodeUint(300)))
    fmt.Println(gbinary.DecodeToUint(gbinary.EncodeUint(70000)))
    fmt.Println(gbinary.DecodeToUint(gbinary.EncodeUint(2000000000)))
    fmt.Println(gbinary.DecodeToUint(gbinary.EncodeUint(500000000000)))

    // 编码/解析 int8/16/32/64
    fmt.Println(gbinary.DecodeToInt8(gbinary.EncodeInt8(int8(100))))
    fmt.Println(gbinary.DecodeToInt16(gbinary.EncodeInt16(int16(100))))
    fmt.Println(gbinary.DecodeToInt32(gbinary.EncodeInt32(int32(100))))
    fmt.Println(gbinary.DecodeToInt64(gbinary.EncodeInt64(int64(100))))

    // 编码/解析 uint8/16/32/64
    fmt.Println(gbinary.DecodeToUint8(gbinary.EncodeUint8(uint8(100))))
    fmt.Println(gbinary.DecodeToUint16(gbinary.EncodeUint16(uint16(100))))
    fmt.Println(gbinary.DecodeToUint32(gbinary.EncodeUint32(uint32(100))))
    fmt.Println(gbinary.DecodeToUint64(gbinary.EncodeUint64(uint64(100))))

    // 编码/解析 string
    fmt.Println(gbinary.DecodeToString(gbinary.EncodeString("I'm string!")))
}
```

以上程序执行结果为：

```
[18 44 1 41 92 143 194 245 40 240 63]
18 300 1.01
1
300
70000
2000000000
500000000000
1
300
70000
2000000000
500000000000
100
100
100
100
100
100
100
100
I'm string!
```

1. **编码**

`gbinary.Encode` 方法是一个非常强大灵活的方法，可以将所有的基本类型转换为二进制类型 `([ ]byte`)。在 `gbinary.Encode` 方法内部，会自动对变量进行长度计算，采用最小二进制长度来存放该变量的二进制值。例如，针对 `int` 类型值为 `1` 的变量， `gbinary.Encode` 将只会用 `1` 个 `byte` 来存储，而 `int` 类型值为 `300` 的变量，将会使用 `2` 个 `byte` 来存储，尽量减少二进制结果的存储空间。因此，在解析的时候要非常注意 `[ ]byte` 的长度，建议能够确定变量长度的地方，在进行二进制编码/解码时，尽量采用形如 `int8/16/32/64` 的定长基本类型来存储变量，这样解析的时候也能够采用对应的变量形式进行解析，不易产生错误。

`gbinary` 包也提供了一系列 `gbinary.Encode*` 的方法，用于将基本数据类型转换为二进制。其中， `gbinary.EncodeInt/gbinary.EncodeUint` 也是会在内部自动识别变量值大小，返回不定长度的 `[ ]byte` 值，长度范围 `1/2/4/8`。

2. **解码**

在二进制类型的解析操作中，二进制的长度( `[ ]byte` 的长度)是非常重要的，只有给定正确的长度才能执行正确的解析，因此 `gbinary.Decode` 方法给定的变量长度必须为确定长度类型的变量，例如： `int8/16/32/64`、 `uint8/16/32/64`、 `float32/64`，而如果给定的第二个变量地址对应的变量类型为 `int/uint`，无法确定长度，因此解析会失败。

此外， `gbinary` 包也提供了一系列 `gbinary.DecodeTo*` 的方法，用于将二进制转换为特定的数据类型。其中， `gbinary.DecodeToInt/gbinary.DecodeToUint` 方法会对二进制长度进行自动识别解析，支持的二进制参数长度范围 `1-8`。