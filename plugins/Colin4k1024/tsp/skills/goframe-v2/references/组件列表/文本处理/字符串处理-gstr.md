`gstr` 提供了强大便捷的文本处理组件，组件内置了大量常用的字符串处理方法，比较于 `Golang` 标准库更加全面丰富，可应对绝大部分业务场景。

**使用方式**：

```go
import "github.com/gogf/gf/v2/text/gstr"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/text/gstr](https://pkg.go.dev/github.com/gogf/gf/v2/text/gstr)
:::tip
以下常用方法列表，文档更新可能滞后于代码新特性，更多的方法及示例请参考代码文档： [https://pkg.go.dev/github.com/gogf/gf/v2/text/gstr](https://pkg.go.dev/github.com/gogf/gf/v2/text/gstr)
:::
## 字符串判断

### `IsNumeric`

- 说明：`IsNumeric` 验证字符串 `s` 是否为数字。

- 格式：

```go
IsNumeric(s string) bool
```

- 示例：

```go
func ExampleIsNumeric() {
      fmt.Println(gstr.IsNumeric("88"))
      fmt.Println(gstr.IsNumeric("3.1415926"))
      fmt.Println(gstr.IsNumeric("abc"))
      // Output:
      // true
      // true
      // false
}
```

## 字符串长度

### `LenRune`

- 说明：`LenRune` 返回 `unicode` 字符串长度。

- 格式：

```go
LenRune(str string) int
```

- 示例：

```go
func ExampleLenRune() {
      var (
          str    = `GoFrame框架`
          result = gstr.LenRune(str)
      )
      fmt.Println(result)

      // Output:
      // 9
}
```

## 字符串创建

### `Repeat`

- 说明：`Repeat` 返回一个由 `input` 重复 `multiplier` 次后组成的新字符串。

- 格式：

```go
Repeat(input string, multiplier int) string
```

- 示例：

```go
func ExampleRepeat() {
      var (
          input      = `goframe `
          multiplier = 3
          result     = gstr.Repeat(input, multiplier)
      )
      fmt.Println(result)

      // Output:
      // goframe goframe goframe
}
```

## 大小写转换

### `ToLower`

- 说明：`ToLower` 将 `s` 中所有 `Unicode` 字符都变为小写并返回其副本。

- 格式：

```go
ToLower(s string) string
```

- 示例：

```go
func ExampleToLower() {
      var (
          s      = `GOFRAME`
          result = gstr.ToLower(s)
      )
      fmt.Println(result)

      // Output:
      // goframe
}
```

### `ToUpper`

- 说明：`ToUpper` 将 `s` 中所有 `Unicode` 字符都变为大写并返回其副本。

- 格式：

```go
ToUpper(s string) string
```

- 示例：

```go
func ExampleToUpper() {
      var (
          s      = `goframe`
          result = gstr.ToUpper(s)
      )
      fmt.Println(result)

      // Output:
      // GOFRAME
}
```

### `UcFirst`

- 说明：`UcFirst` 将 `s` 中首字符变为大写并返回其副本。

- 格式：

```go
UcFirst(s string) string
```

- 示例：

```go
func ExampleUcFirst() {
      var (
          s      = `hello`
          result = gstr.UcFirst(s)
      )
      fmt.Println(result)

      // Output:
      // Hello
}
```

### `LcFirst`

- 说明： `LcFirst` 将 `s` 中首字符变为小写并返回其副本。

- 格式：

```go
LcFirst(s string) string
```

- 示例：

```go
func ExampleLcFirst() {
      var (
          str    = `Goframe`
          result = gstr.LcFirst(str)
      )
      fmt.Println(result)

      // Output:
      // goframe
}
```

### `UcWords`

- 说明： `UcWords` 将字符串 `str` 中每个单词的第一个字符变为大写。

- 格式：

```go
UcWords(str string) string
```

- 示例：

```go
func ExampleUcWords() {
      var (
          str    = `hello world`
          result = gstr.UcWords(str)
      )
      fmt.Println(result)

      // Output:
      // Hello World
}
```

### `IsLetterLower`

- 说明：`IsLetterLower` 验证给定的字符 `b` 是否是小写字符。

- 格式：

```go
IsLetterLower(b byte) bool
```

- 示例：

```go
func ExampleIsLetterLower() {
      fmt.Println(gstr.IsLetterLower('a'))
      fmt.Println(gstr.IsLetterLower('A'))

      // Output:
      // true
      // false
}
```

### `IsLetterUpper`

- 说明：`IsLetterUpper` 验证字符 `b` 是否是大写字符。

- 格式：

```go
IsLetterUpper(b byte) bool
```

- 示例：

```go
func ExampleIsLetterUpper() {
      fmt.Println(gstr.IsLetterUpper('A'))
      fmt.Println(gstr.IsLetterUpper('a'))

      // Output:
      // true
      // false
}
```

## 字符串比较

### `Compare`

- 说明：`Compare` 返回一个按字典顺序比较两个字符串的整数。 如果 `a == b`，结果为 `0`，如果 `a < b`，结果为 `-1`，如果 `a > b`，结果为 `+1`。

- 格式：

```go
Compare(a, b string) int
```

- 示例：

```go
func ExampleCompare() {
      fmt.Println(gstr.Compare("c", "c"))
      fmt.Println(gstr.Compare("a", "b"))
      fmt.Println(gstr.Compare("c", "b"))

      // Output:
      // 0
      // -1
      // 1
}
```

### `Equal`

- 说明： `Equal` 返回 `a` 和 `b` 在不区分大小写的情况下是否相等。

- 格式：

```go
Equal(a, b string) bool
```

- 示例：

```go
func ExampleEqual() {
      fmt.Println(gstr.Equal(`A`, `a`))
      fmt.Println(gstr.Equal(`A`, `A`))
      fmt.Println(gstr.Equal(`A`, `B`))

      // Output:
      // true
      // true
      // false
}
```

## 切分组合

### `Split`

- 说明：`Split` 用 `delimiter` 将 `str` 拆分为 `[]string`。

- 格式：

```go
Split(str, delimiter string) []string
```

- 示例：

```go
func ExampleSplit() {
      var (
          str       = `a|b|c|d`
          delimiter = `|`
          result    = gstr.Split(str, delimiter)
      )
      fmt.Printf(`%#v`, result)

      // Output:
      // []string{"a", "b", "c", "d"}
}
```

### `SplitAndTrim`

- 说明：`SplitAndTrim` 使用 `delimiter` 将 `str` 拆分为 `[]string`，并对 `[]string` 的每个元素调用 `Trim`，并忽略在 `Trim` 之后为空的元素。

- 格式：

```go
SplitAndTrim(str, delimiter string, characterMask ...string) []string
```

- 示例：

```go
func ExampleSplitAndTrim() {
      var (
          str       = `a|b|||||c|d`
          delimiter = `|`
          result    = gstr.SplitAndTrim(str, delimiter)
      )
      fmt.Printf(`%#v`, result)

      // Output:
      // []string{"a", "b", "c", "d"}
}
```

### `Join`

- 说明： `Join` 将 `array` 中的每一个元素连接并生成一个新的字符串。参数 `sep` 会作为新字符串的分隔符。

- 格式：

```go
Join(array []string, sep string) string
```

- 示例：

```go
func ExampleJoin() {
      var (
          array  = []string{"goframe", "is", "very", "easy", "to", "use"}
          sep    = ` `
          result = gstr.Join(array, sep)
      )
      fmt.Println(result)

      // Output:
      // goframe is very easy to use
}
```

### `JoinAny`

- 说明： `JoinAny` 将 `array` 中的每一个元素连接并生成一个新的字符串。参数 `sep` 会作为新字符串的分隔符。参数 `array` 可以是任意的类型。

- 格式：

```go
JoinAny(array interface{}, sep string) string
```

- 示例：

```go
func ExampleJoinAny() {
      var (
          sep    = `,`
          arr2   = []int{99, 73, 85, 66}
          result = gstr.JoinAny(arr2, sep)
      )
      fmt.Println(result)

      // Output:
      // 99,73,85,66
}
```

### `Explode`

- 说明： `Explode` 使用分隔符 `delimiter` 字符串 `str` 拆分成 `[]string`

- 格式：

```go
Explode(delimiter, str string) []string
```

- 示例：

```go
func ExampleExplode() {
      var (
          str       = `Hello World`
          delimiter = " "
          result    = gstr.Explode(delimiter, str)
      )
      fmt.Printf(`%#v`, result)

      // Output:
      // []string{"Hello", "World"}
}
```

### `Implode`

- 说明： `Implode` 使用 `glue` 连接 `pieces` 字符串数组的每一个元素。

- 格式：

```go
Implode(glue string, pieces []string) string
```

- 示例：

```go
func ExampleImplode() {
      var (
          pieces = []string{"goframe", "is", "very", "easy", "to", "use"}
          glue   = " "
          result = gstr.Implode(glue, pieces)
      )
      fmt.Println(result)

      // Output:
      // goframe is very easy to use
}
```

### `ChunkSplit`

- 说明：`ChunkSplit` 将字符串拆分为单位为 `chunkLen` 长度更小的每一份，并用 `end` 连接每一份拆分出的字符串。

- 格式：

```go
ChunkSplit(body string, chunkLen int, end string) string
```

- 示例：

```go
func ExampleChunkSplit() {
      var (
          body     = `1234567890`
          chunkLen = 2
          end      = "#"
          result   = gstr.ChunkSplit(body, chunkLen, end)
      )
      fmt.Println(result)

      // Output:
      // 12#34#56#78#90#
}
```

### `Fields`

- 说明： `Fields` 以 `[]string` 的形式返回字符串中的每个单词。

- 格式：

```go
Fields(str string) []string
```

- 示例：

```go
func ExampleFields() {
      var (
          str    = `Hello World`
          result = gstr.Fields(str)
      )
      fmt.Printf(`%#v`, result)

      // Output:
      // []string{"Hello", "World"}
}
```

## 转义处理

### `AddSlashes`

- 说明： `AddSlashes` 将字符串中的符号前添加转义字符 `'\'`

- 格式：

```go
AddSlashes(str string) string
```

- 示例：

```go
func ExampleAddSlashes() {
      var (
          str    = `'aa'"bb"cc\r\n\d\t`
          result = gstr.AddSlashes(str)
      )

      fmt.Println(result)

      // Output:
      // \'aa\'\"bb\"cc\\r\\n\\d\\t
}
```

### `StripSlashes`

- 说明： `StripSlashes` 去掉字符串 `str` 中的转义字符 `'\'`。

- 格式：

```go
StripSlashes(str string) string
```

- 示例：

```go
func ExampleStripSlashes() {
      var (
          str    = `C:\\windows\\GoFrame\\test`
          result = gstr.StripSlashes(str)
      )
      fmt.Println(result)

      // Output:
      // C:\windows\GoFrame\test
}
```

### `QuoteMeta`

- 说明：`QuoteMeta` 为str中' `. \ + * ? [ ^ ] ( $ )` 中的每个字符前添加一个转义字符 `'\'。`

- 格式：

```go
QuoteMeta(str string, chars ...string) string
```

- 示例：

```go
func ExampleQuoteMeta() {
      {
          var (
              str    = `.\+?[^]()`
              result = gstr.QuoteMeta(str)
          )
          fmt.Println(result)
      }
      {
          var (
              str    = `https://goframe.org/pages/viewpage.action?pageId=1114327`
              result = gstr.QuoteMeta(str)
          )
          fmt.Println(result)
      }

      // Output:
      // \.\\\+\?\[\^\]\(\)
      // https://goframe\.org/pages/viewpage\.action\?pageId=1114327

}
```

## 统计计数

### `Count`

- 说明：`Count` 计算 `substr` 在 `s` 中出现的次数。  如果在 `s` 中没有找到 `substr`，则返回 `0`。

- 格式：

```go
Count(s, substr string) int
```

- 示例：

```go
func ExampleCount() {
      var (
          str     = `goframe is very, very easy to use`
          substr1 = "goframe"
          substr2 = "very"
          result1 = gstr.Count(str, substr1)
          result2 = gstr.Count(str, substr2)
      )
      fmt.Println(result1)
      fmt.Println(result2)

      // Output:
      // 1
      // 2
}
```

### `CountI`

- 说明：`Count` 计算 `substr` 在 `s` 中出现的次数，不区分大小写。  如果在 `s` 中没有找到 `substr`，则返回 `0`。

- 格式：

```go
CountI(s, substr string) int
```

- 示例：

```go
func ExampleCountI() {
      var (
          str     = `goframe is very, very easy to use`
          substr1 = "GOFRAME"
          substr2 = "VERY"
          result1 = gstr.CountI(str, substr1)
          result2 = gstr.CountI(str, substr2)
      )
      fmt.Println(result1)
      fmt.Println(result2)

      // Output:
      // 1
      // 2
}
```

### `CountWords`

- 说明：`CountWords` 以 `map[string]int` 的形式返回 `str` 中使用的单词的统计信息。

- 格式：

```go
CountWords(str string) map[string]int
```

- 示例：

```go
func ExampleCountWords() {
      var (
          str    = `goframe is very, very easy to use!`
          result = gstr.CountWords(str)
      )
      fmt.Printf(`%#v`, result)

      // Output:
      // map[string]int{"easy":1, "goframe":1, "is":1, "to":1, "use!":1, "very":1, "very,":1}
}
```

### `CountChars`

- 说明：`CountChars` 以 `map[string]int` 的形式返回 `str` 中使用的字符的统计信息。 `noSpace` 参数可以控制是否计算空格。

- 格式：

```go
CountChars(str string, noSpace ...bool) map[string]int
```

- 示例：

```go
func ExampleCountChars() {
      var (
          str    = `goframe`
          result = gstr.CountChars(str)
      )
      fmt.Println(result)

      // May Output:
      // map[a:1 e:1 f:1 g:1 m:1 o:1 r:1]
}
```

## 数组处理

### `SearchArray`

- 说明：`SearchArray` 在 `[]string 'a'` 中区分大小写地搜索字符串 `'s'`，返回其在 `'a'` 中的索引。 如果在 `'a'` 中没有找到 `'s'`，则返回 `-1`。

- 格式：

```go
SearchArray(a []string, s string) int
```

- 示例：

```go
func ExampleSearchArray() {
      var (
          array  = []string{"goframe", "is", "very", "nice"}
          str    = `goframe`
          result = gstr.SearchArray(array, str)
      )
      fmt.Println(result)

      // Output:
      // 0
}
```

### `InArray`

- 说明：`InArray校验` `[]string 'a'` 中是否有字符串 `' s '`。

- 格式：

```go
InArray(a []string, s string) bool
```

- 示例：

```go
func ExampleInArray() {
      var (
          a      = []string{"goframe", "is", "very", "easy", "to", "use"}
          s      = "goframe"
          result = gstr.InArray(a, s)
      )
      fmt.Println(result)

      // Output:
      // true
}
```

### `PrefixArray`

- 说明： `PrefixArray` 位 `[]string array` 的每一个字符串添加 `'prefix'` 的前缀。

- 格式：

```go
PrefixArray(array []string, prefix string)
```

- 示例：

```go
func ExamplePrefixArray() {
      var (
          strArray = []string{"tom", "lily", "john"}
      )

      gstr.PrefixArray(strArray, "classA_")

      fmt.Println(strArray)

      // Output:
      // [classA_tom classA_lily classA_john]
}
```

## 命名转换

### `CaseCamel`

- 说明： `CaseCamel` 将字符串转换为大驼峰形式(首字母大写)。

- 格式：

```go
CaseCamel(s string) string
```

- 示例：

```go
func ExampleCaseCamel() {
      var (
          str    = `hello world`
          result = gstr.CaseCamel(str)
      )
      fmt.Println(result)

      // Output:
      // HelloWorld
}
```

### `CaseCamelLower`

- 说明： `CaseCamelLower` 将字符串转换为小驼峰形式(首字母小写)。

- 格式：

```go
CaseCamelLower(s string) string
```

- 示例：

```go
func ExampleCaseCamelLower() {
      var (
          str    = `hello world`
          result = gstr.CaseCamelLower(str)
      )
      fmt.Println(result)

      // Output:
      // helloWorld
}
```

### `CaseSnake`

- 说明： `CaseSnake` 将字符串转换中的符号(下划线,空格,点,中横线)用下划线( `_` )替换,并全部转换为小写字母。

- 格式：

```go
CaseSnake(s string) string
```

- 示例：

```go
func ExampleCaseSnake() {
      var (
          str    = `hello world`
          result = gstr.CaseSnake(str)
      )
      fmt.Println(result)

      // Output:
      // hello_world
}
```

### `CaseSnakeScreaming`

- 说明： `CaseSnakeScreaming` 把字符串中的符号(下划线,空格,点,中横线),全部替换为下划线 `'_'`,并将所有英文字母转为大写。

- 格式：

```go
CaseSnakeScreaming(s string) string
```

- 示例：

```go
func ExampleCaseSnakeScreaming() {
      var (
          str    = `hello world`
          result = gstr.CaseSnakeScreaming(str)
      )
      fmt.Println(result)

      // Output:
      // HELLO_WORLD
}
```

### `CaseSnakeFirstUpper`

- 说明： `CaseSnakeFirstUpper` 将字符串中的字母为大写时,将大写字母转换为小写字母并在其前面增加一个下划线 `'_'`,首字母大写时,只转换为小写,前面不增加下划线 `'_'`。

- 格式：

```go
CaseSnakeFirstUpper(word string, underscore ...string) string
```

- 示例：

```go
func ExampleCaseSnakeFirstUpper() {
      var (
          str    = `RGBCodeMd5`
          result = gstr.CaseSnakeFirstUpper(str)
      )
      fmt.Println(result)

      // Output:
      // rgb_code_md5
}
```

### `CaseKebab`

- 说明： `CaseKebab` 将字符串转换中的符号(下划线,空格,点,)用中横线 `'-'` 替换,并全部转换为小写字母。

- 格式：

```go
CaseKebab(s string) string
```

- 示例：

```go
func ExampleCaseKebab() {
      var (
          str    = `hello world`
          result = gstr.CaseKebab(str)
      )
      fmt.Println(result)

      // Output:
      // hello-world
}
```

### `CaseKebabScreaming`

- 说明： `CaseKebabScreaming` 将字符串转换中的符号(下划线,空格,点,中横线)用中横线 `'-'` 替换,并全部转换为大写字母。

- 格式：

```go
CaseKebabScreaming(s string) string
```

- 示例：

```go
func ExampleCaseKebabScreaming() {
      var (
          str    = `hello world`
          result = gstr.CaseKebabScreaming(str)
      )
      fmt.Println(result)

      // Output:
      // HELLO-WORLD
}
```

### `CaseDelimited`

- 说明： `CaseDelimited` 将字符串转换中的符号进行替换。

- 格式：

```go
CaseDelimited(s string, del byte) string
```

- 示例：

```go
func ExampleCaseDelimited() {
      var (
          str    = `hello world`
          del    = byte('-')
          result = gstr.CaseDelimited(str, del)
      )
      fmt.Println(result)

      // Output:
      // hello-world
}
```

### `CaseDelimitedScreaming`

- 说明： `CaseDelimitedScreaming` 将字符串中的符号(空格,下划线,点,中横线)用第二个参数进行替换,该函数第二个参数为替换的字符,第三个参数为大小写转换, `true` 为全部转换大写字母, `false` 为全部转为小写字母。

- 格式：

```go
CaseDelimitedScreaming(s string, del uint8, screaming bool) string
```

- 示例：

```go
func ExampleCaseDelimitedScreaming() {
      {
          var (
              str    = `hello world`
              del    = byte('-')
              result = gstr.CaseDelimitedScreaming(str, del, true)
          )
          fmt.Println(result)
      }
      {
          var (
              str    = `hello world`
              del    = byte('-')
              result = gstr.CaseDelimitedScreaming(str, del, false)
          )
          fmt.Println(result)
      }

      // Output:
      // HELLO-WORLD
      // hello-world
}
```

## 包含判断

### `Contains`

- 说明： `Contains` 返回字符串 `str` 是否包含子字符串 `substr`，区分大小写。

- 格式：

```go
Contains(str, substr string) bool
```

- 示例：

```go
func ExampleContains() {
      {
          var (
              str    = `Hello World`
              substr = `Hello`
              result = gstr.Contains(str, substr)
          )
          fmt.Println(result)
      }
      {
          var (
              str    = `Hello World`
              substr = `hello`
              result = gstr.Contains(str, substr)
          )
          fmt.Println(result)
      }

      // Output:
      // true
      // false
}
```

### `ContainsI`

- 说明：`ContainsI` 校验 `substr` 是否在 `str` 中，不区分大小写。

- 格式：

```go
ContainsI(str, substr string) bool
```

- 示例：

```go
func ExampleContainsI() {
      var (
          str     = `Hello World`
          substr  = "hello"
          result1 = gstr.Contains(str, substr)
          result2 = gstr.ContainsI(str, substr)
      )
      fmt.Println(result1)
      fmt.Println(result2)

      // Output:
      // false
      // true
}
```

### `ContainsAny`

- 说明：`ContainsAny` 校验 `s` 中是否包含 `chars`。

- 格式：

```go
ContainsAny(s, chars string) bool
```

- 示例：

```go
func ExampleContainsAny() {
      {
          var (
              s      = `goframe`
              chars  = "g"
              result = gstr.ContainsAny(s, chars)
          )
          fmt.Println(result)
      }
      {
          var (
              s      = `goframe`
              chars  = "G"
              result = gstr.ContainsAny(s, chars)
          )
          fmt.Println(result)
      }

      // Output:
      // true
      // false
}
```

## 字符串转换

### `Chr`

- 说明：`Chr` 返回一个数字 `0-255` 对应的 `ascii` 字符串。

- 格式：

```go
Chr(ascii int) string
```

- 示例：

```go
func ExampleChr() {
      var (
          ascii  = 65 // A
          result = gstr.Chr(ascii)
      )
      fmt.Println(result)

      // Output:
      // A
}
```

### `Ord`

- 说明：`Ord` 将字符串的第一个字节转换为 `0-255` 之间的值。

- 格式：

```go
Ord(char string) int
```

- 示例：

```go
func ExampleOrd() {
      var (
          str    = `goframe`
          result = gstr.Ord(str)
      )

      fmt.Println(result)

      // Output:
      // 103
}
```

### `OctStr`

- 说明：`OctStr` 将字符串 `str` 中的八进制字符串转换为其原始字符串。

- 格式：

```go
OctStr(str string) string
```

- 示例：

```go
func ExampleOctStr() {
      var (
          str    = `\346\200\241`
          result = gstr.OctStr(str)
      )
      fmt.Println(result)

      // Output:
      // 怡
}
```

### `Reverse`

- 说明：`Reverse` 返回 `str` 的反转字符串。

- 格式：

```go
Reverse(str string) string
```

- 示例：

```go
func ExampleReverse() {
      var (
          str    = `123456`
          result = gstr.Reverse(str)
      )
      fmt.Println(result)

      // Output:
      // 654321
}
```

### `NumberFormat`

- 说明：`NumberFormat` 以千位分组来格式化数字。

  - 参数 `decimal` 设置小数点的个数。
  - 参数 `decPoint` 设置小数点的分隔符。
  - 参数 `thousand` 设置千位分隔符。
- 格式：

```go
NumberFormat(number float64, decimals int, decPoint, thousandsSep string) string
```

- 示例：

```go
func ExampleNumberFormat() {
      var (
          number       float64 = 123456
          decimals             = 2
          decPoint             = "."
          thousandsSep         = ","
          result               = gstr.NumberFormat(number, decimals, decPoint, thousandsSep)
      )
      fmt.Println(result)

      // Output:
      // 123,456.00
}
```

### `Shuffle`

- 说明：`Shuffle` 返回将 `str` 随机打散后的字符串。

- 格式：

```go
Shuffle(str string) string
```

- 示例：

```go
func ExampleShuffle() {
      var (
          str    = `123456`
          result = gstr.Shuffle(str)
      )
      fmt.Println(result)

      // May Output:
      // 563214
}
```

### `HideStr`

- 说明： `HideStr` 将字符串 `str` 从中间字符开始，百分比 `percent` 的字符转换成 `hide` 字符串。

- 格式：

```go
HideStr(str string, percent int, hide string) string
```

- 示例：

```go
func ExampleHideStr() {
      var (
          str     = `13800138000`
          percent = 40
          hide    = `*`
          result  = gstr.HideStr(str, percent, hide)
      )
      fmt.Println(result)

      // Output:
      // 138****8000
}
```

### `Nl2Br`

- 说明：`Nl2Br` 在字符串中的所有换行符之前插入 `HTML` 换行符 `(' br ' |<br />): \n\r， \r\n， \r， \n`。

- 格式：

```go
Nl2Br(str string, isXhtml ...bool) string
```

- 示例：

```go
func ExampleNl2Br() {
      var (
          str = `goframe
is
very
easy
to
use`
          result = gstr.Nl2Br(str)
      )

      fmt.Println(result)

      // Output:
      // goframe<br>is<br>very<br>easy<br>to<br>use
}
```

### `WordWrap`

- 说明： `WordWrap` 使用换行符将 `str` 换行到给定字符数（不会切分单词）。

- 格式：

```go
WordWrap(str string, width int, br string) string
```

- 示例：

```go
func ExampleWordWrap() {
      {
          var (
              str    = `A very long woooooooooooooooooord. and something`
              width  = 8
              br     = "\n"
              result = gstr.WordWrap(str, width, br)
          )
          fmt.Println(result)
      }
      {
          var (
              str    = `The quick brown fox jumped over the lazy dog.`
              width  = 20
              br     = "<br />\n"
              result = gstr.WordWrap(str, width, br)
          )
          fmt.Printf("%v", result)
      }

      // Output:
      // A very
      // long
      // woooooooooooooooooord.
      // and
      // something
      // The quick brown fox<br />
      // jumped over the lazy<br />
      // dog.
}
```

## 域名处理

### `IsSubDomain`

- 说明：`IsSubDomain` 校验 `subDomain` 是否为 `mainDomain` 的子域名。 支持 `mainDomain` 中的 `'*'`。

- 格式：

```go
IsSubDomain(subDomain string, mainDomain string) bool
```

- 示例：

```go
func ExampleIsSubDomain() {
      var (
          subDomain  = `s.goframe.org`
          mainDomain = `goframe.org`
          result     = gstr.IsSubDomain(subDomain, mainDomain)
      )
      fmt.Println(result)

      // Output:
      // true
}

```

## 参数解析

### `Parse`

- 说明： `Parse` 解析字符串并以 `map[string]interface{}` 类型返回。

- 格式：

```go
Parse(s string) (result map[string]interface{}, err error)
```

- 示例：

```go
func ExampleParse() {
      {
          var (
              str       = `v1=m&v2=n`
              result, _ = gstr.Parse(str)
          )
          fmt.Println(result)
      }
      {
          var (
              str       = `v[a][a]=m&v[a][b]=n`
              result, _ = gstr.Parse(str)
          )
          fmt.Println(result)
      }
      {
          // The form of nested Slice is not yet supported.
          var str = `v[][]=m&v[][]=n`
          result, err := gstr.Parse(str)
          if err != nil {
              panic(err)
          }
          fmt.Println(result)
      }
      {
          // This will produce an error.
          var str = `v=m&v[a]=n`
          result, err := gstr.Parse(str)
          if err != nil {
              println(err)
          }
          fmt.Println(result)
      }
      {
          var (
              str       = `a .[[b=c`
              result, _ = gstr.Parse(str)
          )
          fmt.Println(result)
      }

      // May Output:
      // map[v1:m v2:n]
      // map[v:map[a:map[a:m b:n]]]
      // map[v:map[]]
      // Error: expected type 'map[string]interface{}' for key 'v', but got 'string'
      // map[]
      // map[a___[b:c]
}
```

## 位置查找

### `Pos`

- 说明：`Pos` 返回 `needle` 在 `haystack` 中第一次出现的位置，区分大小写。 如果没有找到，则返回-1。

- 格式：

```go
Pos(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePos() {
      var (
          haystack = `Hello World`
          needle   = `World`
          result   = gstr.Pos(haystack, needle)
      )
      fmt.Println(result)

      // Output:
      // 6
}
```

### `PosRune`

- 说明： `PosRune` 的作用于函数 `Pos` 相似，但支持 `haystack` 和 `needle` 为 `unicode` 字符串。

- 格式：

```go
PosRune(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosRune() {
      var (
          haystack = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架`
          needle   = `Go`
          posI     = gstr.PosRune(haystack, needle)
          posR     = gstr.PosRRune(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 0
      // 22
}
```

### `PosI`

- 说明：`PosI` 返回 `needle` 在 `haystack` 中第一次出现的位置，不区分大小写。 如果没有找到，则返回-1。

- 格式：

```go
PosI(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosI() {
      var (
          haystack = `goframe is very, very easy to use`
          needle   = `very`
          posI     = gstr.PosI(haystack, needle)
          posR     = gstr.PosR(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 11
      // 17
}
```

### `PosRuneI`

- 说明： `PosRuneI` 的作用于函数 `PosI` 相似，但支持 `haystack` 和 `needle` 为 `unicode` 字符串。

- 格式：

```go
PosIRune(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosIRune() {
      {
          var (
              haystack    = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架`
              needle      = `高性能`
              startOffset = 10
              result      = gstr.PosIRune(haystack, needle, startOffset)
          )
          fmt.Println(result)
      }
      {
          var (
              haystack    = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架`
              needle      = `高性能`
              startOffset = 30
              result      = gstr.PosIRune(haystack, needle, startOffset)
          )
          fmt.Println(result)
      }

      // Output:
      // 14
      // -1
}
```

### `PosR`

- 说明：`PosR` 返回 `needle` 在 `haystack` 中最后一次出现的位置，区分大小写。 如果没有找到，则返回-1。

- 格式：

```go
PosR(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosR() {
      var (
          haystack = `goframe is very, very easy to use`
          needle   = `very`
          posI     = gstr.PosI(haystack, needle)
          posR     = gstr.PosR(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 11
      // 17
}
```

### `PosRuneR`

- 说明： `PosRuneR` 的作用于函数 `PosR` 相似，但支持 `haystack` 和 `needle` 为 `unicode` 字符串。

- 格式：

```go
PosRRune(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosRRune() {
      var (
          haystack = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架`
          needle   = `Go`
          posI     = gstr.PosIRune(haystack, needle)
          posR     = gstr.PosRRune(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 0
      // 22
}
```

### `PosRI`

- 说明：`PosRI` 返回 `needle` 在 `haystack` 中最后一次出现的位置，不区分大小写。 如果没有找到，则返回-1。

- 格式：

```go
PosRI(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosRI() {
      var (
          haystack = `goframe is very, very easy to use`
          needle   = `VERY`
          posI     = gstr.PosI(haystack, needle)
          posR     = gstr.PosRI(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 11
      // 17
}
```

### `PosRIRune`

- 说明：`PosRIRune`的作用于函数`PosRI`相似，但支持 `haystack` 和 `needle` 为 `unicode` 字符串。

- 格式：

```go
PosRIRune(haystack, needle string, startOffset ...int) int
```

- 示例：

```go
func ExamplePosRIRune() {
      var (
          haystack = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架`
          needle   = `GO`
          posI     = gstr.PosIRune(haystack, needle)
          posR     = gstr.PosRIRune(haystack, needle)
      )
      fmt.Println(posI)
      fmt.Println(posR)

      // Output:
      // 0
      // 22
}
```

## 查找替换

### `Replace`

- 说明： `Replace` 返回 `origin` 字符串中, `search` 被 `replace` 替换后的新字符串。 `search` 区分大小写。

- 格式：

```go
Replace(origin, search, replace string, count ...int) string
```

- 示例：

```go
func ExampleReplace() {
      var (
          origin  = `golang is very nice!`
          search  = `golang`
          replace = `goframe`
          result  = gstr.Replace(origin, search, replace)
      )
      fmt.Println(result)

      // Output:
      // goframe is very nice!
}
```

### `ReplaceI`

- 说明： `ReplaceI` 返回 `origin` 字符串中, `search` 被 `replace` 替换后的新字符串。 `search` 不区分大小写。

- 格式：

```go
ReplaceI(origin, search, replace string, count ...int) string
```

- 示例：

```go
func ExampleReplaceI() {
      var (
          origin  = `golang is very nice!`
          search  = `GOLANG`
          replace = `goframe`
          result  = gstr.ReplaceI(origin, search, replace)
      )
      fmt.Println(result)

      // Output:
      // goframe is very nice!
}
```

### `ReplaceByArray`

- 说明：`ReplaceByArray` 返回 `origin` 被一个切片按两个一组 `(search, replace)` 顺序替换的新字符串，区分大小写。

- 格式：

```go
ReplaceByArray(origin string, array []string) string
```

- 示例：

```go
func ExampleReplaceByArray() {
      {
          var (
              origin = `golang is very nice`
              array  = []string{"lang", "frame"}
              result = gstr.ReplaceByArray(origin, array)
          )
          fmt.Println(result)
      }
      {
          var (
              origin = `golang is very good`
              array  = []string{"golang", "goframe", "good", "nice"}
              result = gstr.ReplaceByArray(origin, array)
          )
          fmt.Println(result)
      }

      // Output:
      // goframe is very nice
      // goframe is very nice
}
```

### `ReplaceIByArray`

- 说明：`ReplaceIByArray` 返回 `origin` 被一个切片按两个一组 `(search, replace)` 顺序替换的新字符串，不区分大小写。

- 格式：

```go
ReplaceIByArray(origin string, array []string) string
```

- 示例：

```go
func ExampleReplaceIByArray() {
      var (
          origin = `golang is very Good`
          array  = []string{"Golang", "goframe", "GOOD", "nice"}
          result = gstr.ReplaceIByArray(origin, array)
      )

      fmt.Println(result)

      // Output:
      // goframe is very nice
}
```

### `ReplaceByMap`

- 说明：`ReplaceByMap` 返回 `origin` 中 `map` 的 `key` 替换为 `value` 的新字符串，区分大小写。

- 格式：

```go
ReplaceByMap(origin string, replaces map[string]string) string
```

- 示例：

```go
func ExampleReplaceByMap() {
      {
          var (
              origin   = `golang is very nice`
              replaces = map[string]string{
                  "lang": "frame",
              }
              result = gstr.ReplaceByMap(origin, replaces)
          )
          fmt.Println(result)
      }
      {
          var (
              origin   = `golang is very good`
              replaces = map[string]string{
                  "golang": "goframe",
                  "good":   "nice",
              }
              result = gstr.ReplaceByMap(origin, replaces)
          )
          fmt.Println(result)
      }

      // Output:
      // goframe is very nice
      // goframe is very nice
}
```

### `ReplaceIByMap`

- 说明：`ReplaceIByMap` 返回 `origin` 中 `map` 的 `key` 替换为 `value` 的新字符串，不区分大小写。

- 格式：

```go
ReplaceIByMap(origin string, replaces map[string]string) string
```

- 示例：

```go
func ExampleReplaceIByMap() {
      var (
          origin   = `golang is very nice`
          replaces = map[string]string{
              "Lang": "frame",
          }
          result = gstr.ReplaceIByMap(origin, replaces)
      )
      fmt.Println(result)

      // Output:
      // goframe is very nice
}
```

## 子串截取

### `Str`

- 说明： `Str` 返回从 `needle` 第一次出现的位置开始，到 `haystack` 结尾的字符串（包含 `needle` 本身）。

- 格式：

```go
Str(haystack string, needle string) string
```

- 示例：

```go
func ExampleStr() {
      var (
          haystack = `xxx.jpg`
          needle   = `.`
          result   = gstr.Str(haystack, needle)
      )
      fmt.Println(result)

      // Output:
      // .jpg
}
```

### `StrEx`

- 说明： `StrEx` 返回从 `needle` 第一次出现的位置开始，到 `haystack` 结尾的字符串（不包含 `needle` 本身）。

- 格式：

```go
StrEx(haystack string, needle string) string
```

- 示例：

```go
func ExampleStrEx() {
      var (
          haystack = `https://goframe.org/index.html?a=1&b=2`
          needle   = `?`
          result   = gstr.StrEx(haystack, needle)
      )
      fmt.Println(result)

      // Output:
      // a=1&b=2
}
```

### `StrTill`

- 说明： `StrTill` 返回从 `haystack` 字符串开始到 `needle` 第一次出现的位置的字符串（包含 `needle` 本身）。

- 格式：

```go
StrTill(haystack string, needle string) string
```

- 示例：

```go
func ExampleStrTill() {
      var (
          haystack = `https://goframe.org/index.html?test=123456`
          needle   = `?`
          result   = gstr.StrTill(haystack, needle)
      )
      fmt.Println(result)

      // Output:
      // https://goframe.org/index.html?
}
```

### `StrTillEx`

- 说明： `StrTillEx` 返回从 `haystack` 字符串开始到 `needle` 第一次出现的位置的字符串（不包含 `needle` 本身）。

- 格式：

```go
StrTillEx(haystack string, needle string) string
```

- 示例：

```go
func ExampleStrTillEx() {
      var (
          haystack = `https://goframe.org/index.html?test=123456`
          needle   = `?`
          result   = gstr.StrTillEx(haystack, needle)
      )
      fmt.Println(result)

      // Output:
      // https://goframe.org/index.html
}
```

### `SubStr`

- 说明：`SubStr` 返回字符串 `str` 从 `start` 开始，长度为 `length` 的新字符串。 参数 `length` 是可选的，它默认使用 `str` 的长度。

- 格式：

```go
SubStr(str string, start int, length ...int) (substr string)
```

- 示例：

```go
func ExampleSubStr() {
      var (
          str    = `1234567890`
          start  = 0
          length = 4
          subStr = gstr.SubStr(str, start, length)
      )
      fmt.Println(subStr)

      // Output:
      // 1234
}
```

### `SubStrRune`

- 说明：`SubStrRune` 返回 `unicode` 字符串 `str` 从 `start` 开始，长度为 `length` 的新字符串。 参数 `length` 是可选的，它默认使用 `str` 的长度。

- 格式：

```go
SubStrRune(str string, start int, length ...int) (substr string)
```

- 示例：

```go
func ExampleSubStrRune() {
      var (
          str    = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架。`
          start  = 14
          length = 3
          subStr = gstr.SubStrRune(str, start, length)
      )
      fmt.Println(subStr)

      // Output:
      // 高性能
}
```

### `StrLimit`

- 说明： `StrLimit` 取 `str` 字符串开始，长度为 `length` 的字符串，加上 `suffix...` 后返回新的字符串。

- 格式：

```go
StrLimit(str string, length int, suffix ...string) string
```

- 示例：

```go
func ExampleStrLimit() {
      var (
          str    = `123456789`
          length = 3
          suffix = `...`
          result = gstr.StrLimit(str, length, suffix)
      )
      fmt.Println(result)

      // Output:
      // 123...
}
```

### `StrLimitRune`

- 说明： `StrLimitRune` 取 `unicode` 字符串 `str` 开始，长度为 `length` 的字符串，加上 `suffix...` 后返回新的字符串。

- 格式：

```go
StrLimitRune(str string, length int, suffix ...string) string
```

- 示例：

```go
func ExampleStrLimitRune() {
      var (
          str    = `GoFrame是一款模块化、高性能、企业级的Go基础开发框架。`
          length = 17
          suffix = "..."
          result = gstr.StrLimitRune(str, length, suffix)
      )
      fmt.Println(result)

      // Output:
      // GoFrame是一款模块化、高性能...
}
```

### `SubStrFrom`

- 说明：`SubStrFrom` 返回字符串 `str` 从第一次出现 `need` 到 `str` 的结尾的字符串（包含 `need`）。

- 格式：

```go
SubStrFrom(str string, need string) (substr string)
```

- 示例：

```go
func ExampleSubStrFrom() {
      var (
          str  = "我爱GoFrameGood"
          need = `爱`
      )

      fmt.Println(gstr.SubStrFrom(str, need))

      // Output:
      // 爱GoFrameGood
}
```

### `SubStrFromEx`

- 说明：`SubStrFromEx` 返回字符串 `str` 从第一次出现 `need` 到 `str` 的结尾的字符串（不包含 `need`）。

- 格式：

```go
SubStrFromEx(str string, need string) (substr string)
```

- 示例：

```go
func ExampleSubStrFromEx() {
      var (
          str  = "我爱GoFrameGood"
          need = `爱`
      )

      fmt.Println(gstr.SubStrFromEx(str, need))

      // Output:
      // GoFrameGood
}
```

### `SubStrFromR`

- 说明：`SubStrFromR` 返回字符串 `str` 从最后一次出现 `need` 到 `str` 的结尾的字符串（包含 `need`）。

- 格式：

```go
SubStrFromR(str string, need string) (substr string)
```

- 示例：

```go
func ExampleSubStrFromR() {
      var (
          str  = "我爱GoFrameGood"
          need = `Go`
      )

      fmt.Println(gstr.SubStrFromR(str, need))

      // Output:
      // Good
}
```

### `SubStrFromREx`

- 说明：`SubStrFromREx` 返回字符串 `str` 从最后一次出现 `need` 到 `str` 的结尾的字符串（不包含 `need`）。

- 格式：

```go
SubStrFromREx(str string, need string) (substr string)
```

- 示例：

```go
func ExampleSubStrFromREx() {
      var (
          str  = "我爱GoFrameGood"
          need = `Go`
      )

      fmt.Println(gstr.SubStrFromREx(str, need))

      // Output:
      // od
}
```

## 字符/子串过滤

### `Trim`

- 说明： `Trim` 从字符串的开头和结尾剪切空白(或其他字符)。 可选参数 `characterMask` 指定额外剥离的字符。

- 格式：

```go
Trim(str string, characterMask ...string) string
```

- 示例：

```go
func ExampleTrim() {
      var (
          str           = `*Hello World*`
          characterMask = "*d"
          result        = gstr.Trim(str, characterMask)
      )
      fmt.Println(result)

      // Output:
      // Hello Worl
}
```

### `TrimStr`

- 说明：`TrimStr` 从字符串的开头和结尾去掉所有 `cut` 字符串（不会删除开头或结尾的空白）。

- 格式：

```go
TrimStr(str string, cut string, count ...int) string
```

- 示例：

```go
func ExampleTrimStr() {
      var (
          str    = `Hello World`
          cut    = "World"
          count  = -1
          result = gstr.TrimStr(str, cut, count)
      )
      fmt.Println(result)

      // Output:
      // Hello
}
```

### `TrimLeft`

- 说明：`TrimLeft` 将字符串开头的空格(或其他字符)删除。

- 格式：

```go
TrimLeft(str string, characterMask ...string) string
```

- 示例：

```go
func ExampleTrimLeft() {
      var (
          str           = `*Hello World*`
          characterMask = "*"
          result        = gstr.TrimLeft(str, characterMask)
      )
      fmt.Println(result)

      // Output:
      // Hello World*
}
```

### `TrimLeftStr`

- 说明：`TrimLeftStr` 从字符串的开头删除 `count` 个 `cut` 字符串（不会删除开头的空格）。

- 格式：

```go
TrimLeftStr(str string, cut string, count ...int) string
```

- 示例：

```go
func ExampleTrimLeftStr() {
      var (
          str    = `**Hello World**`
          cut    = "*"
          count  = 1
          result = gstr.TrimLeftStr(str, cut, count)
      )
      fmt.Println(result)

      // Output:
      // *Hello World**
}
```

### `TrimRight`

- 说明： `TrimRight` 从字符串的末尾去掉空白(或其他字符)。

- 格式：

```go
TrimRight(str string, characterMask ...string) string
```

- 示例：

```go
func ExampleTrimRight() {
      var (
          str           = `**Hello World**`
          characterMask = "*def" // []byte{"*", "d", "e", "f"}
          result        = gstr.TrimRight(str, characterMask)
      )
      fmt.Println(result)

      // Output:
      // **Hello Worl
}
```

### `TrimRightStr`

- 说明：`TrimRightStr` 从字符串的尾部删除 `count` 个 `cut` 字符串（不会删除尾部的空格）。

- 格式：

```go
TrimRightStr(str string, cut string, count ...int) string
```

- 示例：

```go
func ExampleTrimRightStr() {
      var (
          str    = `Hello World!`
          cut    = "!"
          count  = -1
          result = gstr.TrimRightStr(str, cut, count)
      )
      fmt.Println(result)

      // Output:
      // Hello World
}
```

### `TrimAll`

- 说明： `TrimAll` 删除字符串 `str` 中的所有空格(或其他字符)以及 `characterMask` 字符。

- 格式：

```go
TrimAll(str string, characterMask ...string) string
```

- 示例：

```go
func ExampleTrimAll() {
      var (
          str           = `*Hello World*`
          characterMask = "*"
          result        = gstr.TrimAll(str, characterMask)
      )
      fmt.Println(result)

      // Output:
      // HelloWorld
}
```

### `HasPrefix`

- 说明： `HasPrefix` 返回 `s` 是否以 `prefix` 开头。

- 格式：

```go
HasPrefix(s, prefix string) bool
```

- 示例：

```go
func ExampleHasPrefix() {
      var (
          s      = `Hello World`
          prefix = "Hello"
          result = gstr.HasPrefix(s, prefix)
      )
      fmt.Println(result)

      // Output:
      // true
}
```

### `HasSuffix`

- 说明： `HasSuffix` 返回 `s` 是否以 `suffix` 结束。

- 格式：

```go
HasSuffix(s, suffix string) bool
```

- 示例：

```go
func ExampleHasSuffix() {
      var (
          s      = `my best love is goframe`
          prefix = "goframe"
          result = gstr.HasSuffix(s, prefix)
      )
      fmt.Println(result)

      // Output:
      // true
}
```

## 版本比较

### `CompareVersion`

- 说明：`CompareVersion` 将 `a` 和 `b` 作为标准 `GNU` 版本进行比较。

- 格式：

```go
CompareVersion(a, b string) int
```

- 示例：

```go
func ExampleCompareVersion() {
      fmt.Println(gstr.CompareVersion("v2.11.9", "v2.10.8"))
      fmt.Println(gstr.CompareVersion("1.10.8", "1.19.7"))
      fmt.Println(gstr.CompareVersion("2.8.beta", "2.8"))

      // Output:
      // 1
      // -1
      // 0
}
```

### `CompareVersionGo`

- 说明： `CompareVersionGo` 将 `a` 和 `b` 作为标准的 `Golang` 版本进行比较。

- 格式：

```go
CompareVersionGo(a, b string) int
```

- 示例：

```go
func ExampleCompareVersionGo() {
      fmt.Println(gstr.CompareVersionGo("v2.11.9", "v2.10.8"))
      fmt.Println(gstr.CompareVersionGo("v4.20.1", "v4.20.1+incompatible"))
      fmt.Println(gstr.CompareVersionGo(
          "v0.0.2-20180626092158-b2ccc119800e",
          "v1.0.1-20190626092158-b2ccc519800e",
      ))

      // Output:
      // 1
      // 1
      // -1
}
```

## 相似计算

### `Levenshtein`

- 说明： `Levenshtein` 计算两个字符串之间的 `Levenshtein` 距离。

- 格式：

```go
Levenshtein(str1, str2 string, costIns, costRep, costDel int) int
```

- 示例：

```go
func ExampleLevenshtein() {
      var (
          str1    = "Hello World"
          str2    = "hallo World"
          costIns = 1
          costRep = 1
          costDel = 1
          result  = gstr.Levenshtein(str1, str2, costIns, costRep, costDel)
      )
      fmt.Println(result)

      // Output:
      // 2
}
```

### `SimilarText`

- 说明： `SimilarText` 计算两个字符串之间的相似度。

- 格式：

```go
SimilarText(first, second string, percent *float64) int
```

- 示例：

```go
func ExampleSimilarText() {
      var (
          first   = `AaBbCcDd`
          second  = `ad`
          percent = 0.80
          result  = gstr.SimilarText(first, second, &percent)
      )
      fmt.Println(result)

      // Output:
      // 2
}
```

### `Soundex`

- 说明： `Soundex` 用于计算字符串的 `Soundex` 键。

- 格式：

```go
Soundex(str string) string
```

- 示例：

```go
func ExampleSoundex() {
      var (
          str1    = `Hello`
          str2    = `Hallo`
          result1 = gstr.Soundex(str1)
          result2 = gstr.Soundex(str2)
      )
      fmt.Println(result1, result2)

      // Output:
      // H400 H400
}
```