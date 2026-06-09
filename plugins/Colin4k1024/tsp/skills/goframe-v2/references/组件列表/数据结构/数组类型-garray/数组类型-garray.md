## 基本介绍

数组容器，提供普通数组，及排序数组，支持数据项唯一性矫正，支持并发安全开关控制。

**使用场景**：

数组操作。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/garray"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/garray](https://pkg.go.dev/github.com/gogf/gf/v2/container/garray)

简要说明：

1. `garray`模块下的对象及方法较多，建议仔细看看接口文档。
2. `garray`支持`int`/`string`/`interface{}`三种常用的数据类型。
3. `garray`支持普通数组和排序数组，普通数组的结构体名称定义为`*Array`格式，排序数组的结构体名称定义为`Sorted*Array`格式，如下：
   - `Array`, `intArray`, `StrArray`
   - `SortedArray`, `SortedIntArray`, `SortedStrArray`
   - 其中排序数组`SortedArray`，需要给定排序比较方法，在工具包`gutil`中也定义了很多`Comparator*`比较方法
4. 从`v2.10`版本开始，`garray`提供了泛型数组类型：
   - `TArray[T]`：泛型普通数组，提供类型安全的数组操作
   - `SortedTArray[T]`：泛型排序数组，支持自定义比较函数
   - 推荐在新项目中使用泛型数组，享受编译时类型检查带来的安全性和更好的IDE支持

## 相关文档