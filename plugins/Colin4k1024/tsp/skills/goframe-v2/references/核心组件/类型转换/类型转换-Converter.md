`gconv.Converter`是`GoFrame v2.9`版本新增的类型转换接口，通过创建转换对象的形式来使用类型转换能力，提供了一种更严谨、更灵活的类型转换机制。与传统的`gconv`包方法不同，`Converter`接口在转换失败时会返回错误，而不是默认返回零值或空值。

**功能特点**:

1. **严谨的错误处理**：转换失败时返回错误信息，避免静默失败导致的潜在问题
2. **类型安全**：提供更严格的类型检查，减少运行时错误
3. **可扩展性**：支持注册自定义类型转换函数，适应复杂业务场景
4. **一致的API**：所有转换方法遵循相同的模式，使用更加一致
5. **独立实例**：可以创建多个转换器实例，每个实例可以有不同的配置和注册的转换函数

## 基本介绍

`Converter`接口是一个组合接口，包含了多个子接口，提供了全面的类型转换能力：

```go
type Converter interface {
	ConverterForConvert
	ConverterForRegister
	ConverterForInt
	ConverterForUint
	ConverterForTime
	ConverterForFloat
	ConverterForMap
	ConverterForSlice
	ConverterForStruct
	ConverterForBasic
}
```

这些子接口分别提供了不同类型的转换功能，例如：

- `ConverterForBasic`：基本类型转换（字符串、布尔值等）
- `ConverterForInt`：整数类型转换
- `ConverterForUint`：无符号整数类型转换
- `ConverterForFloat`：浮点数类型转换
- `ConverterForTime`：时间类型转换
- `ConverterForMap`：`Map`类型转换
- `ConverterForSlice`：切片类型转换
- `ConverterForStruct`：结构体类型转换
- `ConverterForConvert`：自定义类型转换
- `ConverterForRegister`：注册自定义转换函数

## 创建`Converter`对象

使用`gconv.NewConverter()`函数可以创建一个新的`Converter`对象：

```go
converter := gconv.NewConverter()
```

## 基本用法

### 基本类型转换

```go
package main

import (
	"fmt"

	"github.com/gogf/gf/v2/util/gconv"
)

func main() {
	// 创建转换对象
	converter := gconv.NewConverter()

	// 整数转换
	intValue, err := converter.Int("123")
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Println("Int转换结果:", intValue) // 输出: 123
	}

	// 浮点数转换
	floatValue, err := converter.Float64("123.456")
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Println("Float64转换结果:", floatValue) // 输出: 123.456
	}

	// 布尔值转换
	boolValue, err := converter.Bool("true")
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Println("Bool转换结果:", boolValue) // 输出: true
	}

	// 字符串转换
	strValue, err := converter.String(123)
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Println("String转换结果:", strValue) // 输出: 123
	}
}
```

### 结构体转换

```go
package main

import (
	"fmt"
    
	"github.com/gogf/gf/v2/util/gconv"
)

type User struct {
	Id   int
	Name string
	Age  int
}

func main() {
	converter := gconv.NewConverter()

	// Map转结构体
	data := map[string]interface{}{
		"id":   1,
		"name": "John",
		"age":  30,
	}

	var user User
	err := converter.Struct(data, &user, gconv.StructOption{})
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Printf("结构体转换结果: %+v\n", user) // 输出: {Id:1 Name:John Age:30}
	}
}
```

### 自定义类型转换

> **注意**：自定义类型转换主要用于复杂类型（如结构体、切片、映射等）之间的转换，不支持基础类型的别名类型。这是为了提高转换效率，避免不必要的性能开销。

以下是一个使用复杂类型的自定义转换示例：

```go
package main

import (
	"fmt"
	"time"

	"github.com/gogf/gf/v2/util/gconv"
)

// UserInfo 自定义类型
type UserInfo struct {
	ID       int
	Name     string
	Birthday time.Time
}

type UserDTO struct {
	UserID   string
	UserName string
	Age      int
}

func userInfoT2UserDTO(in UserInfo) (*UserDTO, error) {
	if in.ID <= 0 {
		return nil, fmt.Errorf("invalid user ID: %d", in.ID)
	}
	// 计算年龄
	age := time.Now().Year() - in.Birthday.Year()
	return &UserDTO{
		UserID:   fmt.Sprintf("U%d", in.ID),
		UserName: in.Name,
		Age:      age,
	}, nil
}

func main() {
	converter := gconv.NewConverter()
	// 注册自定义类型转换函数 - 从UserInfo到UserDTO
	err := converter.RegisterTypeConverterFunc(userInfoT2UserDTO)
	if err != nil {
		fmt.Println("注册转换函数失败:", err)
		return
	}

	// 使用自定义类型转换
	userInfo := UserInfo{
		ID:       101,
		Name:     "张三",
		Birthday: time.Date(1990, 5, 15, 0, 0, 0, 0, time.Local),
	}

	var userDTO UserDTO
	err = converter.Scan(userInfo, &userDTO)
	if err != nil {
		fmt.Println("转换失败:", err)
	} else {
		fmt.Printf("自定义类型转换结果: %#v\n", userDTO)
		// 输出类似: 自定义类型转换结果: main.UserDTO{UserID:"U101", UserName:"张三", Age:35}
	}

	// 测试错误处理
	invalidUser := UserInfo{ID: -1, Name: "无效用户"}
	err = converter.Scan(invalidUser, &userDTO)
	if err != nil {
		fmt.Println("预期的错误:", err) // 输出错误信息: invalid user ID: -1
	}
}
```

在上面的示例中，我们定义了两个复杂类型：`UserInfo`（源类型）和`UserDTO`（目标类型），并注册了一个自定义转换函数，用于将`UserInfo`转换为`UserDTO`。这种转换不仅仅是简单的字段映射，还包含了业务逻辑（如计算年龄）。

更多关于自定义类型转换的介绍，请参考章节：[类型转换-自定义类型转换](./类型转换-自定义类型转换.md)

## 与传统`gconv`包方法的区别

### 错误处理

传统的`gconv`包方法在转换失败时会默认返回零值或空值，而不会返回错误信息：

```go
// 传统方法
value := gconv.Int("not-a-number") // 返回0，不返回错误

// Converter方法
converter := gconv.NewConverter()
value, err := converter.Int("not-a-number") // 返回0和错误信息
```

### 转换选项

`Converter`接口的方法支持更多的转换选项参数，可以更精细地控制转换行为：

```go
// 结构体转换选项
structOption := gconv.StructOption{
    Mapping:           map[string]string{"ID": "UserId"},
    RecursiveOption:   gconv.RecursiveOptionTrue,
    ContinueOnError:   false,
    PrivateAttribute:  true,
}

// 使用选项进行转换
converter.Struct(data, &user, structOption)
```