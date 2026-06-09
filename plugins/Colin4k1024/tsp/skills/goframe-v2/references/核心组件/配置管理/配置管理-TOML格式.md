## 基本介绍

`Toml` 是一种易读、 `mini` 语言，由 `github` 前CEO `Tom` 创建。 `Tom's Obvious, Minimal Language`。

`TOML` 致力于配置文件的小型化和易读性。

1. WIKI介绍: [https://github.com/toml-lang/toml/wiki](https://github.com/toml-lang/toml/wiki)
2. 官方地址: [https://github.com/toml-lang/toml](https://github.com/toml-lang/toml)
3. 汉化版: [https://github.com/LongTengDao/TOML/blob/%E9%BE%99%E8%85%BE%E9%81%93-%E8%AF%91/toml-v1.0.0.md](https://github.com/LongTengDao/TOML/blob/%E9%BE%99%E8%85%BE%E9%81%93-%E8%AF%91/toml-v1.0.0.md)

## 与其他格式比较

`TOML` 与用于应用程序配置和数据序列化的其他文件格式(如 `YAML` 和 `JSON`)具有相同的特性。 `TOML` 和 `JSON` 都很简单，并且使用普遍存在的数据类型，这使得它们易于编写代码或使用机器进行解析。 `TOML` 和 `YAML` 都强调人的可读性，比如注释，它使理解给定行的目的变得更容易。 `TOML` 的不同之处在于，它支持注释(不像 `JSON`)，但保持了简单性(不像 `YAML`)。

由于 `TOML` 被显式地设计为一种配置文件格式，所以解析它很容易，但并不打算序列化任意的数据结构。 `TOML` 的文件顶层是一个哈希表，它很容易在键中嵌套数据，但是它不允许顶级数组或浮点数，所以它不能直接序列化一些数据。也没有标准来标识 `TOML` 文件的开始或结束，这会使通过流发送文件变得复杂。这些细节必须在应用层进行协商。

`INI` 文件经常与 `TOML` 进行比较，因为它们在语法和用作配置文件方面具有相似性。然而， `INI` 没有标准化的格式，它们不能优雅地处理超过一两个层次的嵌套。

## 基础语法

```toml
title = "TOML 例子"

[owner]
name = "Tom Preston-Werner"
organization = "GitHub"
bio = "GitHub Cofounder & CEO\nLikes tater tots and beer."
dob = 1979-05-27T07:32:00Z # 日期时间是一等公民。为什么不呢？

[database]
server = "192.168.1.1"
ports = [ 8001, 8001, 8002 ]
connection_max = 5000
enabled = true

[servers]
  # 你可以依照你的意愿缩进。使用空格或Tab。TOML不会在意。
  [servers.alpha]
  ip = "10.0.0.1"
  dc = "eqdc10"

  [servers.beta]
  ip = "10.0.0.2"
  dc = "eqdc10"

[clients]
data = [ ["gamma", "delta"], [1, 2] ]

#在数组里换行没有关系。
hosts = [
  "alpha",
  "omega"
]
```

特点：

- 大小写敏感，必须是 `UTF-8` 编码
- 注释： `#`
- 空白符： `tab(0x09)` 或 `space(0x20)`
- 换行符： `LF(0x0A)` 或 `CRLF(0x0D 0x0A)`
- 键值对：同一行，无值的键不可用，每行只能保存一个键值对

`TOML` 主要结构是键值对，与 `JSON` 类似。值必须是如下类型： `String`, `Integer`, `Float`, `Boolean`, `Datetime`, `Array`, `Table`

## 注释

使用 `#` 表示注释：

```toml
# I am a comment. Hear me roar. Roar.
key = "value" # Yeah, you can do this.
```

## 字符串

`TOML` 中有4种字符串表示方法：基本、多行-基本、字面量、多行-字面量

### 1\. 基本字符串

由双引号包裹，所有 `Unicode` 字符均可出现，除了双引号、反斜线、控制字符( `U+0000` to `U+001F`)需要转义。

### 2\. 多行-基本字符串

由三个双引号包裹，除了分隔符开始的换行外，字符串内的换行将被保留：

```toml
str1 = """
Roses are red
Violets are blue"""
```

### 3\. 字面量字符串

由单引号包裹，其内不允许转义，因此可以方便的表示基本字符串中需要转义的内容：

```toml
winpath = 'C:\Users\nodejs\templates'
```

### 4\. 多行-字面量字符串

与多行-基本字符串相似：

```toml
str1 = '''
Roses are red
Violets are blue'''
```

## 数值与BOOL值

```toml
int1  = +99
flt3  = -0.01
bool1 = true
```

## 日期时间

```toml
date = 1979-05-27T07:32:00Z
```

## 数组

数组使用方括号包裹。空格会被忽略。元素使用逗号分隔。

注意，同一个数组下不允许混用数据类型。

```toml
array1 = [ 1, 2, 3 ]
array2 = [ "red", "yellow", "green" ]
array3 = [ [ 1, 2 ], [3, 4, 5] ]
array4 = [ [ 1, 2 ], ["a", "b", "c"] ] # 这是可以的。
array5 = [ 1, 2.0 ] # 注意：这是不行的。
```

## 表格

表格（也叫哈希表或字典）是键值对的集合。它们在方括号内，自成一行。注意和数组相区分，数组只有值。

```toml
[table]
```

在此之下，直到下一个　`table` 或　`EOF` 之前，是这个表格的键值对。键在左，值在右，等号在中间。键以非空字符开始，以等号前的非空字符为结尾。键值对是无序的。

```toml
[table]
key = "value"
```

你可以随意缩进，使用 `Tab` 或 `空格`。为什么要缩进呢？因为你可以嵌套表格。

嵌套表格的表格名称中使用 `.` 符号。你可以任意命名你的表格，只是不要用点，点是保留的。

```toml
[dog.tater]
type = "pug"
```

以上等价于如下的 `JSON` 结构：

```
{ "dog": { "tater": { "type": "pug" } } }
```

如果你不想的话，你不用声明所有的父表。TOML　知道该如何处理。

```toml
# [x] 你
# [x.y] 不需要
# [x.y.z] 这些
[x.y.z.w] # 可以直接写
```

空表是允许的，其中没有键值对。

只要父表没有被直接定义，而且没有定义一个特定的键，你可以继续写入：

```toml
[a.b]
c = 1

[a]
d = 2
```

然而你不能多次定义键和表格。这么做是不合法的。

```toml
# 别这么干！

[a]
b = 1

[a]
c = 2
# 也别这个干

[a]
b = 1

[a.b]
c = 2
```

## 表格数组

最后要介绍的类型是表格数组。表格数组可以通过包裹在双方括号内的表格名来表达。使用相同的双方括号名称的表格是同一个数组的元素。表格按照书写的顺序插入。双方括号表格如果没有键值对，会被当成空表。

```toml
[[products]]
name = "Hammer"
sku = 738594937

[[products]]

[[products]]
name = "Nail"
sku = 284758393
color = "gray"
```

等价于以下的　`JSON` 结构：

```
{
  "products": [
    { "name": "Hammer", "sku": 738594937 },
    { },
    { "name": "Nail", "sku": 284758393, "color": "gray" }
  ]
}
```

表格数组同样可以嵌套。只需在子表格上使用相同的双方括号语法。每一个双方括号子表格从属于最近定义的上层表格元素。

```toml
[[fruit]]
  name = "apple"

  [fruit.physical]
    color = "red"
    shape = "round"

  [[fruit.variety]]
    name = "red delicious"

  [[fruit.variety]]
    name = "granny smith"

[[fruit]]
  name = "banana"

  [[fruit.variety]]
    name = "plantain"
```

等价于如下的　`JSON` 结构：

```
{
  "fruit": [
    {
      "name": "apple",
      "physical": {
        "color": "red",
        "shape": "round"
      },
      "variety": [
        { "name": "red delicious" },
        { "name": "granny smith" }
      ]
    },
    {
      "name": "banana",
      "variety": [
        { "name": "plantain" }
      ]
    }
  ]
}
```

尝试定义一个普通的表格，使用已经定义的数组的名称，将抛出一个解析错误：

```toml
# 不合法的　TOML

[[fruit]]
  name = "apple"

  [[fruit.variety]]
    name = "red delicious"

  # 和上面冲突了
  [fruit.variety]
    name = "granny smith"
```