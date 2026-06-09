## 基本介绍

支持并发安全开关特性的树形容器，树形数据结构的特点是支持有序遍历、内存占用低、复杂度稳定、适合大数据量存储。该模块包含多个数据结构的树形容器： `RedBlackTree`、 `AVLTree` 和 `BTree`。

| 类型 | 数据结构 | 平均复杂度 | 支持排序 | 有序遍历 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `RedBlackTree` | 红黑树 | `O(log N)` | 是 | 是 | 写入性能比较好 |
| `AVLTree` | 高度平衡树 | `O(log N)` | 是 | 是 | 查找性能比较好 |
| `BTree` | B树/B-树 | `O(log N)` | 是 | 是 | 常用于外部存储 |

> 参考连接： [https://en.wikipedia.org/wiki/Binary\_tree](https://en.wikipedia.org/wiki/Binary_tree)

**使用场景**：

关联数组场景、排序键值对场景、大数据量内存CRUD场景等等。

**使用方式**：

```go
import "github.com/gogf/gf/v2/container/gtree"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/container/gtree](https://pkg.go.dev/github.com/gogf/gf/v2/container/gtree)

几种容器的API方法都非常类似，特点是需要在初始化时提供用于排序的方法。

在 `gutil` 模块中提供了常用的一些基本类型比较方法，可以直接在程序中直接使用，后续也有示例。

```go
func ComparatorByte(a, b interface{}) int
func ComparatorFloat32(a, b interface{}) int
func ComparatorFloat64(a, b interface{}) int
func ComparatorInt(a, b interface{}) int
func ComparatorInt16(a, b interface{}) int
func ComparatorInt32(a, b interface{}) int
func ComparatorInt64(a, b interface{}) int
func ComparatorInt8(a, b interface{}) int
func ComparatorRune(a, b interface{}) int
func ComparatorString(a, b interface{}) int
func ComparatorTime(a, b interface{}) int
func ComparatorUint(a, b interface{}) int
func ComparatorUint16(a, b interface{}) int
func ComparatorUint32(a, b interface{}) int
func ComparatorUint64(a, b interface{}) int
func ComparatorUint8(a, b interface{}) int
```

## 泛型支持

:::tip
版本要求：`v2.10.0`
:::

从 `v2.10.0` 版本开始，`gtree` 提供了泛型版本的树形容器，包括 `RedBlackKVTree[K, V]`、`AVLKVTree[K, V]` 和 `BKVTree[K, V]`，提供类型安全的键值对操作。

### 基本使用

使用泛型版本创建树形容器：

```go
import (
    "github.com/gogf/gf/v2/container/gtree"
    "github.com/gogf/gf/v2/util/gutil"
)

// 创建泛型红黑树
tree := gtree.NewRedBlackKVTree[int, string](gutil.ComparatorInt)
tree.Set(1, "value1")
tree.Set(2, "value2")

// 无需类型断言，直接获取类型安全的值
value, found := tree.Get(1) // value 是 string 类型
if found {
    fmt.Println(value) // 直接使用，无需类型转换
}
```

### 类型安全的优势

泛型版本提供编译时类型检查：

```go
// 传统方式（需要类型断言）
tree := gtree.NewRedBlackTree(gutil.ComparatorInt)
tree.Set(1, "value")
value := tree.Get(1).(string) // 需要类型断言，运行时可能panic

// 泛型方式（类型安全）
tree := gtree.NewRedBlackKVTree[int, string](gutil.ComparatorInt)
tree.Set(1, "value")
value, _ := tree.Get(1) // value 直接是 string 类型，编译时检查
```

### NilChecker 支持

:::tip
`NilChecker` 是一个可选参数，并非必须提供。它主要用于解决`typed nil`问题，并提供更好的`nil`判断性能。在默认情况下，组件使用**反射**来判断数据是否为`nil`。
:::

对于指针、接口等类型，可以使用 `WithChecker` 方法自定义`nil`检查逻辑：

```go
type Student struct {
    ID   int
    Name string
}

// 使用自定义 nil 检查器
tree := gtree.NewRedBlackKVTreeWithChecker[int, *Student](
    gutil.ComparatorInt,
    func(s *Student) bool {
        return s == nil || s.ID == 0 // 自定义 nil 判断
    },
)

tree.Set(1, &Student{ID: 1, Name: "张三"})
tree.Set(2, &Student{ID: 0, Name: ""}) // 会被视为 nil

value, found := tree.Get(2)
fmt.Println(found) // false，因为被视为 nil
```

### 泛型树类型

三种泛型树容器的使用方式类似：

```go
// 红黑树（写入性能好）
rbTree := gtree.NewRedBlackKVTree[int, string](gutil.ComparatorInt)

// AVL树（查找性能好）
avlTree := gtree.NewAVLKVTree[int, string](gutil.ComparatorInt)

// B树（适合外部存储）
bTree := gtree.NewBKVTree[int, string](3, gutil.ComparatorInt) // 3 是阶数
```

## 相关文档