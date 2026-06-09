## 基本介绍

`gfile` 文件管理组件提供了更加丰富的文件/目录操作能力。

**使用方式**：

```go
import "github.com/gogf/gf/v2/os/gfile"
```

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/os/gfile](https://pkg.go.dev/github.com/gogf/gf/v2/os/gfile)
:::tip
以下常用方法列表，文档更新可能滞后于代码新特性，更多的方法及示例请参考代码文档： [https://pkg.go.dev/github.com/gogf/gf/v2/os/gfile](https://pkg.go.dev/github.com/gogf/gf/v2/os/gfile)
:::
## 内容管理

### `GetContents`

- 说明：读取指定路径文件内容，以字符串形式返回。
- 格式:

```go
func GetContents(path string) string
```

- 示例：

```go
func ExampleGetContents() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // It reads and returns the file content as string.
      // It returns empty string if it fails reading, for example, with permission or IO error.
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
}
```

### `GetContentsWithCache`

- 说明：带缓存获取文件内容，可设置缓存超时，文件发生变化自动清除缓存。
- 格式:

```go
func GetContentsWithCache(path string, duration ...time.Duration) string
```

- 示例：

```go
func ExampleGetContentsWithCache() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_cache")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // It reads the file content with cache duration of one minute,
      // which means it reads from cache after then without any IO operations within on minute.
      fmt.Println(gfile.GetContentsWithCache(tempFile, time.Minute))

      // write new contents will clear its cache
      gfile.PutContents(tempFile, "new goframe example content")

      // There's some delay for cache clearing after file content change.
      time.Sleep(time.Second * 1)

      // read contents
      fmt.Println(gfile.GetContentsWithCache(tempFile))

      // May Output:
      // goframe example content
      // new goframe example content
}
```

### `GetBytesWithCache`

- 说明：带缓存获取文件内容，可设置缓存超时，文件发生变化自动清除缓存，返回\[\]byte。
- 格式:

```go
func GetBytesWithCache(path string, duration ...time.Duration) []byte
```

- 示例：

```go
func ExampleGetBytesWithCache() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_cache")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // It reads the file content with cache duration of one minute,
      // which means it reads from cache after then without any IO operations within on minute.
      fmt.Println(gfile.GetBytesWithCache(tempFile, time.Minute))

      // write new contents will clear its cache
      gfile.PutContents(tempFile, "new goframe example content")

      // There's some delay for cache clearing after file content change.
      time.Sleep(time.Second * 1)

      // read contents
      fmt.Println(gfile.GetBytesWithCache(tempFile))

      // Output:
      // [103 111 102 114 97 109 101 32 101 120 97 109 112 108 101 32 99 111 110 116 101 110 116]
      // [110 101 119 32 103 111 102 114 97 109 101 32 101 120 97 109 112 108 101 32 99 111 110 116 101 110 116]
}
```

### `GetBytes`

- 说明：读取指定路径文件内容，以字节形式返回。
- 格式:

```go
func GetBytes(path string) []byte
```

- 示例：

```go
func ExampleGetBytes() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // It reads and returns the file content as []byte.
      // It returns nil if it fails reading, for example, with permission or IO error.
      fmt.Println(gfile.GetBytes(tempFile))

      // Output:
      // [103 111 102 114 97 109 101 32 101 120 97 109 112 108 101 32 99 111 110 116 101 110 116]
}
```

### `GetBytesTilChar`

- 说明：以某个字符定位截取指定长度的文件内容以字节形式返回
- 格式:

```go
func GetBytesTilChar(reader io.ReaderAt, char byte, start int64) ([]byte, int64)
```

- 示例：

```go
func ExampleGetBytesTilChar() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      f, _ := gfile.OpenWithFlagPerm(tempFile, os.O_RDONLY, gfile.DefaultPermOpen)

      // GetBytesTilChar returns the contents of the file as []byte
      // until the next specified byte `char` position.
      char, i := gfile.GetBytesTilChar(f, 'f', 0)
      fmt.Println(char)
      fmt.Println(i)

      // Output:
      // [103 111 102]
      // 2
}
```

### `GetBytesByTwoOffsets`

- 说明：以指定的区间读取文件内容
- 格式:

```go
func GetBytesByTwoOffsets(reader io.ReaderAt, start int64, end int64) []byte
```

- 示例：

```go
func ExampleGetBytesByTwoOffsets() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      f, _ := gfile.OpenWithFlagPerm(tempFile, os.O_RDONLY, gfile.DefaultPermOpen)

      // GetBytesTilChar returns the contents of the file as []byte
      // until the next specified byte `char` position.
      char := gfile.GetBytesByTwoOffsets(f, 0, 3)
      fmt.Println(char)

      // Output:
      // [103 111 102]
}
```

### `PutContents`

- 说明：往指定路径文件添加字符串内容。如果文件不存在将会递归的形式自动创建。
- 格式:

```go
func putContents(path string, data []byte, flag int, perm os.FileMode) error
```

- 示例：

```go
func ExamplePutContents() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // It creates and puts content string into specifies file path.
      // It automatically creates directory recursively if it does not exist.
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
}
```

### `PutBytes`

- 说明：以字节形式写入指定文件，如果文件不存在将会递归的形式自动创建
- 格式:

```go
func PutBytes(path string, content []byte) error
```

- 示例：

```go
func ExamplePutBytes() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutBytes(tempFile, []byte("goframe example content"))

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
}
```

### `PutContentsAppend`

- 说明：追加字符串内容到指定文件，如果文件不存在将会递归的形式自动创建。
- 格式:

```go
func PutContentsAppend(path string, content string) error
```

- 示例：

```go
func ExamplePutContentsAppend() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // It creates and append content string into specifies file path.
      // It automatically creates directory recursively if it does not exist.
      gfile.PutContentsAppend(tempFile, " append content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
      // goframe example content append content
}
```

### `PutBytesAppend`

- 说明：追加字节内容到指定文件。如果文件不存在将会递归的形式自动创建。
- 格式:

```go
func PutBytesAppend(path string, content []byte) error
```

- 示例：

```go
func ExamplePutBytesAppend() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // write contents
      gfile.PutBytesAppend(tempFile, []byte(" append"))

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
      // goframe example content append
}
```

### `GetNextCharOffset`

- 说明：从某个偏移量开始，获取文件中指定字符所在下标
- 格式:

```go
func GetNextCharOffset(reader io.ReaderAt, char byte, start int64) int64
```

- 示例：

```go
func ExampleGetNextCharOffset() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      f, err := gfile.OpenWithFlagPerm(tempFile, os.O_RDONLY, DefaultPermOpen)
      defer f.Close()

      // read contents
      index := gfile.GetNextCharOffset(f, 'f', 0)
      fmt.Println(index)

      // Output:
      // 2
}
```

### `GetNextCharOffsetByPath`

- 说明：从某个偏移量开始，获取文件中指定字符所在下标
- 格式:

```go
func GetNextCharOffsetByPath(path string, char byte, start int64) int64
```

- 示例：

```go
func ExampleGetNextCharOffsetByPath() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      index := gfile.GetNextCharOffsetByPath(tempFile, 'f', 0)
      fmt.Println(index)

      // Output:
      // 2
}
```

### `GetBytesTilCharByPath`

- 说明：以某个字符定位截取指定长度的文件内容以字节形式返回
- 格式:

```go
func GetBytesTilCharByPath(path string, char byte, start int64) ([]byte, int64)
```

- 示例：

```go
func ExampleGetBytesTilCharByPath() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetBytesTilCharByPath(tempFile, 'f', 0))

      // Output:
      // [103 111 102] 2
}
```

### `GetBytesByTwoOffsetsByPath`

- 说明：用两个偏移量截取指定文件的内容以字节形式返回
- 格式:

```go
func GetBytesByTwoOffsetsByPath(path string, start int64, end int64) []byte
```

- 示例：

```go
func ExampleGetBytesByTwoOffsetsByPath() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetBytesByTwoOffsetsByPath(tempFile, 0, 7))

      // Output:
      // [103 111 102 114 97 109 101]
}
```

### `ReadLines`

- 说明：以字符串形式逐行读取文件内容
- 格式:

```go
func ReadLines(file string, callback func(text string) error) error
```

- 示例：

```go
func ExampleReadLines() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "L1 goframe example content\nL2 goframe example content")

      // read contents
      gfile.ReadLines(tempFile, func(text string) error {
          // Process each line
          fmt.Println(text)
          return nil
      })

      // Output:
      // L1 goframe example content
      // L2 goframe example content
}
```

### `ReadLinesBytes`

- 说明：以字节形式逐行读取文件内容
- 格式:

```go
func ReadLinesBytes(file string, callback func(bytes []byte) error) error
```

- 示例：

```go
func ExampleReadLinesBytes() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_content")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "L1 goframe example content\nL2 goframe example content")

      // read contents
      gfile.ReadLinesBytes(tempFile, func(bytes []byte) error {
          // Process each line
          fmt.Println(bytes)
          return nil
      })

      // Output:
      // [76 49 32 103 111 102 114 97 109 101 32 101 120 97 109 112 108 101 32 99 111 110 116 101 110 116]
      // [76 50 32 103 111 102 114 97 109 101 32 101 120 97 109 112 108 101 32 99 111 110 116 101 110 116]
}
```

### `Truncate`

- 说明：裁剪文件为指定大小
- 注意：如果给定文件路径是软链，将会修改源文件
- 格式:

```go
func Truncate(path string, size int) error
```

- 示例：

```go
func ExampleTruncate(){
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Check whether the `path` size
      stat, _ := gfile.Stat(path)
      fmt.Println(stat.Size())

      // Truncate file
      gfile.Truncate(path, 0)

      // Check whether the `path` size
      stat, _ = gfile.Stat(path)
      fmt.Println(stat.Size())

      // Output:
      // 13
      // 0
}
```

## 内容替换

### `ReplaceFile`

- 说明：替换指定文件的指定内容为新内容
- 格式:

```go
func ReplaceFile(search, replace, path string) error
```

- 示例：

```go
func ExampleReplaceFile() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_replace")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // It replaces content directly by file path.
      gfile.ReplaceFile("content", "replace word", tempFile)

      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
      // goframe example replace word
}
```

### `ReplaceFileFunc`

- 说明：使用自定义函数替换指定文件内容
- 格式:

```go
func ReplaceFileFunc(f func(path, content string) string, path string) error
```

- 示例：

```go
func ExampleReplaceFileFunc() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_replace")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example 123")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // It replaces content directly by file path and callback function.
      gfile.ReplaceFileFunc(func(path, content string) string {
          // Replace with regular match
          reg, _ := regexp.Compile(`\d{3}`)
          return reg.ReplaceAllString(content, "[num]")
      }, tempFile)

      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example 123
      // goframe example [num]
}
```

### `ReplaceDir`

- 说明：扫描指定目录，替换符合条件的文件的指定内容为新内容
- 格式:

```go
func ReplaceDir(search, replace, path, pattern string, recursive ...bool) error
```

- 示例：

```go
func ExampleReplaceDir() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_replace")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // It replaces content of all files under specified directory recursively.
      gfile.ReplaceDir("content", "replace word", tempDir, "gfile_example.txt", true)

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example content
      // goframe example replace word
}
```

### `ReplaceDirFunc`

- 说明：扫描指定目录，使用自定义函数替换符合条件的文件的指定内容为新内容
- 格式:

```go
func ReplaceDirFunc(f func(path, content string) string, path, pattern string, recursive ...bool) error
```

- 示例：

```go
func ExampleReplaceDirFunc() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_replace")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example 123")

      // read contents
      fmt.Println(gfile.GetContents(tempFile))

      // It replaces content of all files under specified directory with custom callback function recursively.
      gfile.ReplaceDirFunc(func(path, content string) string {
          // Replace with regular match
          reg, _ := regexp.Compile(`\d{3}`)
          return reg.ReplaceAllString(content, "[num]")
      }, tempDir, "gfile_example.txt", true)

      fmt.Println(gfile.GetContents(tempFile))

      // Output:
      // goframe example 123
      // goframe example [num]

}
```

## 文件时间

### `MTime`

- 说明：获取路径修改时间
- 格式:

```go
func MTime(path string) time.Time
```

- 示例：

```go
func ExampleMTime() {
      t := gfile.MTime(gfile.TempDir())
      fmt.Println(t)

      // May Output:
      // 2021-11-02 15:18:43.901141 +0800 CST
}
```

### `MTimestamp`

- 说明：获取路径修改时间戳（秒）
- 格式:

```go
func MTimestamp(path string) int64
```

- 示例：

```go
func ExampleMTimestamp() {
      t := gfile.MTimestamp(gfile.TempDir())
      fmt.Println(t)

      // May Output:
      // 1635838398
}
```

### `MTimestampMilli`

- 说明：获取路径修改时间戳（毫秒）
- 格式:

```go
func MTimestampMilli(path string) int64
```

- 示例：

```go
func ExampleMTimestampMilli() {
      t := gfile.MTimestampMilli(gfile.TempDir())
      fmt.Println(t)

      // May Output:
      // 1635838529330
}
```

## 文件大小

### `Size`

- 说明：获取路径大小，不进行格式化
- 格式:

```go
func Size(path string) int64
```

- 示例：

```go
func ExampleSize() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_size")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "0123456789")
      fmt.Println(gfile.Size(tempFile))

      // Output:
      // 10
}
```

### `SizeFormat`

- 说明：获取路径大小，并格式化成硬盘容量
- 格式:

```go
func SizeFormat(path string) string
```

- 示例：

```go
func ExampleSizeFormat() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_size")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "0123456789")
      fmt.Println(gfile.SizeFormat(tempFile))

      // Output:
      // 10.00B
}
```

### `ReadableSize`

- 说明：获取给定路径容量大小，并格式化人类易读的硬盘容量格式
- 格式:

```go
func ReadableSize(path string) string
```

- 示例：

```go
func ExampleReadableSize() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_size")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "01234567899876543210")
      fmt.Println(gfile.ReadableSize(tempFile))

      // Output:
      // 20.00B
}
```

### `StrToSize`

- 说明：硬盘容量大小字符串转换为大小整形
- 格式:

```go
func StrToSize(sizeStr string) int64
```

- 示例：

```go
func ExampleStrToSize() {
      size := gfile.StrToSize("100MB")
      fmt.Println(size)

      // Output:
      // 104857600
}
```

### `FormatSize`

- 说明：大小整形转换为硬盘容量大小字符串\`K、m、g、t、p、e、b\`
- 格式:

```go
func FormatSize(raw int64) string
```

- 示例：

```go
func ExampleFormatSize() {
      sizeStr := gfile.FormatSize(104857600)
      fmt.Println(sizeStr)
      sizeStr0 := gfile.FormatSize(1024)
      fmt.Println(sizeStr0)
      sizeStr1 := gfile.FormatSize(999999999999999999)
      fmt.Println(sizeStr1)

      // Output:
      // 100.00M
      // 1.00K
      // 888.18P
}
```

## 文件排序

### `SortFiles`

- 说明：排序多个路径，按首字母进行排序，数字优先。
- 格式:

```go
func SortFiles(files []string) []string
```

- 示例：

```go
func ExampleSortFiles() {
      files := []string{
          "/aaa/bbb/ccc.txt",
          "/aaa/bbb/",
          "/aaa/",
          "/aaa",
          "/aaa/ccc/ddd.txt",
          "/bbb",
          "/0123",
          "/ddd",
          "/ccc",
      }
      sortOut := gfile.SortFiles(files)
      fmt.Println(sortOut)

      // Output:
      // [/0123 /aaa /aaa/ /aaa/bbb/ /aaa/bbb/ccc.txt /aaa/ccc/ddd.txt /bbb /ccc /ddd]
}
```

## 文件检索

### `Search`

- 说明：在指定目录（默认包含当前目录、运行目录、主函数目录；不会递归子目录）中搜索文件并返回真实路径。
- 格式:

```go
func Search(name string, prioritySearchPaths ...string) (realPath string, err error)
```

- 示例：

```go
func ExampleSearch() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_search")
          tempFile = gfile.Join(tempDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")

      // search file
      realPath, _ := gfile.Search(fileName, tempDir)
      fmt.Println(gfile.Basename(realPath))

      // Output:
      // gfile_example.txt
}
```

## 目录扫描

### `ScanDir`

- 说明：扫描指定目录，可扫描文件或目录，支持递归扫描。
- 格式:

```go
func ScanDir(path string, pattern string, recursive ...bool) ([]string, error)
```

- 示例：

```go
func ExampleScanDir() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_scan_dir")
          tempFile = gfile.Join(tempDir, fileName)

          tempSubDir  = gfile.Join(tempDir, "sub_dir")
          tempSubFile = gfile.Join(tempSubDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")
      gfile.PutContents(tempSubFile, "goframe example content")

      // scans directory recursively
      list, _ := gfile.ScanDir(tempDir, "*", true)
      for _, v := range list {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // gfile_example.txt
      // sub_dir
      // gfile_example.txt
}
```

### `ScanDirFile`

- 说明：扫描指定目录的文件，支持递归扫描
- 格式:

```go
func ScanDirFile(path string, pattern string, recursive ...bool) ([]string, error)
```

- 示例：

```go
func ExampleScanDirFile() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_scan_dir_file")
          tempFile = gfile.Join(tempDir, fileName)

          tempSubDir  = gfile.Join(tempDir, "sub_dir")
          tempSubFile = gfile.Join(tempSubDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")
      gfile.PutContents(tempSubFile, "goframe example content")

      // scans directory recursively exclusive of directories
      list, _ := gfile.ScanDirFile(tempDir, "*.txt", true)
      for _, v := range list {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // gfile_example.txt
      // gfile_example.txt
}
```

### `ScanDirFunc`

- 说明：扫描指定目录（自定义过滤方法），可扫描文件或目录，支持递归扫描
- 格式:

```go
func ScanDirFunc(path string, pattern string, recursive bool, handler func(path string) string) ([]string, error)
```

- 示例：

```go
func ExampleScanDirFunc() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_scan_dir_func")
          tempFile = gfile.Join(tempDir, fileName)

          tempSubDir  = gfile.Join(tempDir, "sub_dir")
          tempSubFile = gfile.Join(tempSubDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")
      gfile.PutContents(tempSubFile, "goframe example content")

      // scans directory recursively
      list, _ := gfile.ScanDirFunc(tempDir, "*", true, func(path string) string {
          // ignores some files
          if gfile.Basename(path) == "gfile_example.txt" {
              return ""
          }
          return path
      })
      for _, v := range list {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // sub_dir
}
```

### `ScanDirFileFunc`

- 说明：扫描指定目录的文件（自定义过滤方法），支持递归扫描。
- 格式:

```go
func ScanDirFileFunc(path string, pattern string, recursive bool, handler func(path string) string) ([]string, error)
```

- 示例：

```go
func ExampleScanDirFileFunc() {
      // init
      var (
          fileName = "gfile_example.txt"
          tempDir  = gfile.TempDir("gfile_example_scan_dir_file_func")
          tempFile = gfile.Join(tempDir, fileName)

          fileName1 = "gfile_example_ignores.txt"
          tempFile1 = gfile.Join(tempDir, fileName1)

          tempSubDir  = gfile.Join(tempDir, "sub_dir")
          tempSubFile = gfile.Join(tempSubDir, fileName)
      )

      // write contents
      gfile.PutContents(tempFile, "goframe example content")
      gfile.PutContents(tempFile1, "goframe example content")
      gfile.PutContents(tempSubFile, "goframe example content")

      // scans directory recursively exclusive of directories
      list, _ := gfile.ScanDirFileFunc(tempDir, "*.txt", true, func(path string) string {
          // ignores some files
          if gfile.Basename(path) == "gfile_example_ignores.txt" {
              return ""
          }
          return path
      })
      for _, v := range list {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // gfile_example.txt
      // gfile_example.txt
}
```

## 常用目录

### `Pwd`

- 说明：获取当前工作路径。
- 格式:

```go
func Pwd() string
```

- 示例：

```go
func ExamplePwd() {
      // Get absolute path of current working directory.
      fmt.Println(gfile.Pwd())

      // May Output:
      // xxx/gf/os/gfile
}
```

### `Home`

- 说明：获取运行用户的主目录
- 格式:

```go
func Home(names ...string) (string, error)
```

- 示例：

```go
func ExampleHome() {
      // user's home directory
      homePath, _ := gfile.Home()
      fmt.Println(homePath)

      // May Output:
      // C:\Users\hailaz
}
```

### `Temp`

- 说明：获取拼接系统临时路径后的绝对地址。

- 格式:

```go
func Temp(names ...string) string
```

- 示例：

```go
func ExampleTempDir() {
      // init
      var (
          fileName = "gfile_example_basic_dir"
      )

      // fetch an absolute representation of path.
      path := gfile.Temp(fileName)

      fmt.Println(path)

      // Output:
      // /tmp/gfile_example_basic_dir
}
```

### `SelfPath`

- 说明：获取当前运行程序的绝对路径。

- 格式:

```go
func SelfPath() string
```

- 示例：

```go
func ExampleSelfPath() {

      // Get absolute file path of current running process
      fmt.Println(gfile.SelfPath())

      // May Output:
      // xxx/___github_com_gogf_gf_v2_os_gfile__ExampleSelfPath
}
```

## 类型判断

### `IsDir`

- 说明：检查给定的路径是否是文件夹。
- 格式:

```go
func IsDir(path string) bool
```

- 示例：

```go
func ExampleIsDir() {
      // init
      var (
          path     = gfile.TempDir("gfile_example_basic_dir")
          filePath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )
      // Checks whether given `path` a directory.
      fmt.Println(gfile.IsDir(path))
      fmt.Println(gfile.IsDir(filePath))

      // Output:
      // true
      // false
}
```

### `IsFile`

- 说明：检查给定的路径是否是文件。
- 格式:

```go
func IsFile(path string) bool
```

- 示例：

```go
func ExampleIsFile() {
      // init
      var (
          filePath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dirPath  = gfile.TempDir("gfile_example_basic_dir")
      )
      // Checks whether given `path` a file, which means it's not a directory.
      fmt.Println(gfile.IsFile(filePath))
      fmt.Println(gfile.IsFile(dirPath))

      // Output:
      // true
      // false
}
```

## 权限操作

### `IsReadable`

- 说明：检查给定的路径是否可读。

- 格式:

```go
func IsReadable(path string) bool
```

- 示例：

```go
func ExampleIsReadable() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Checks whether given `path` is readable.
      fmt.Println(gfile.IsReadable(path))

      // Output:
      // true
}
```

### `IsWritable`

- 说明：检查指定路径是否可写，如果路径是目录，则会创建临时文件检查是否可写，如果是文件则判断是否可以打开

- 格式:

```go
func IsWritable(path string) bool
```

- 示例：

```go
func ExampleIsWritable() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Checks whether given `path` is writable.
      fmt.Println(gfile.IsWritable(path))

      // Output:
      // true
}
```

### `Chmod`

- 说明：使用指定的权限，更改指定路径的文件权限。

- 格式:

```go
func Chmod(path string, mode os.FileMode) error
```

- 示例：

```go
func ExampleChmod() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Get a FileInfo describing the named file.
      stat, err := gfile.Stat(path)
      if err != nil {
          fmt.Println(err.Error())
      }
      // Show original mode
      fmt.Println(stat.Mode())

      // Change file model
      gfile.Chmod(path, gfile.DefaultPermCopy)

      // Get a FileInfo describing the named file.
      stat, _ = gfile.Stat(path)
      // Show the modified mode
      fmt.Println(stat.Mode())

      // Output:
      // -rw-r--r--
      // -rwxrwxrwx
}
```

## 文件/目录操作

### `Mkdir`

- 说明：创建文件夹，支持递归创建（建议采用绝对路径）,创建后的文件夹权限为： `drwxr-xr-x`。
- 格式:

```go
func Mkdir(path string) error
```

- 示例：

```go
func ExampleMkdir() {
      // init
      var (
          path = gfile.TempDir("gfile_example_basic_dir")
      )

      // Creates directory
      gfile.Mkdir(path)

      // Check if directory exists
      fmt.Println(gfile.IsDir(path))

      // Output:
      // true
}
```

### `Create`

- 说明：创建文件/文件夹,如果传入的路径中的文件夹不存在，则会自动创建文件夹以及文件，其中创建的文件权限为 `-rw-r–r–`。
- 注意：如果需要创建文件的已存在，则会清空该文件的内容！
- 格式:

```go
func Create(path string) (*os.File, error)
```

- 示例：

```go
func ExampleCreate() {
      // init
      var (
          path     = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dataByte = make([]byte, 50)
      )
      // Check whether the file exists
      isFile := gfile.IsFile(path)

      fmt.Println(isFile)

      // Creates file with given `path` recursively
      fileHandle, _ := gfile.Create(path)
      defer fileHandle.Close()

      // Write some content to file
      n, _ := fileHandle.WriteString("hello goframe")

      // Check whether the file exists
      isFile = gfile.IsFile(path)

      fmt.Println(isFile)

      // Reset file uintptr
      unix.Seek(int(fileHandle.Fd()), 0, 0)
      // Reads len(b) bytes from the File
      fileHandle.Read(dataByte)

      fmt.Println(string(dataByte[:n]))

      // Output:
      // false
      // true
      // hello goframe
}
```

### `Open`

- 说明：以只读的方式打开文件/文件夹。
- 格式:

```go
func Open(path string) (*os.File, error)
```

- 示例：

```go
func ExampleOpen() {
      // init
      var (
          path     = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dataByte = make([]byte, 4096)
      )
      // Open file or directory with READONLY model
      file, _ := gfile.Open(path)
      defer file.Close()

      // Read data
      n, _ := file.Read(dataByte)

      fmt.Println(string(dataByte[:n]))

      // Output:
      // hello goframe
}
```

### `OpenFile`

- 说明：以指定\`flag\`以及\`perm\`的方式打开文件/文件夹。
- 格式:

```go
func OpenFile(path string, flag int, perm os.FileMode) (*os.File, error)
```

- 示例：

```go
func ExampleOpenFile() {
      // init
      var (
          path     = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dataByte = make([]byte, 4096)
      )
      // Opens file/directory with custom `flag` and `perm`
      // Create if file does not exist,it is created in a readable and writable mode,prem 0777
      openFile, _ := gfile.OpenFile(path, os.O_CREATE|os.O_RDWR, gfile.DefaultPermCopy)
      defer openFile.Close()

      // Write some content to file
      writeLength, _ := openFile.WriteString("hello goframe test open file")

      fmt.Println(writeLength)

      // Read data
      unix.Seek(int(openFile.Fd()), 0, 0)
      n, _ := openFile.Read(dataByte)

      fmt.Println(string(dataByte[:n]))

      // Output:
      // 28
      // hello goframe test open file
}
```

### `OpenWithFalg`

- 说明：以指定\`flag\`的方式打开文件/文件夹。
- 格式:

```go
func OpenWithFlag(path string, flag int) (*os.File, error)
```

- 示例：

```go
func ExampleOpenWithFlag() {
      // init
      var (
          path     = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dataByte = make([]byte, 4096)
      )

      // Opens file/directory with custom `flag`
      // Create if file does not exist,it is created in a readable and writable mode with default `perm` is 0666
      openFile, _ := gfile.OpenWithFlag(path, os.O_CREATE|os.O_RDWR)
      defer openFile.Close()

      // Write some content to file
      writeLength, _ := openFile.WriteString("hello goframe test open file with flag")

      fmt.Println(writeLength)

      // Read data
      unix.Seek(int(openFile.Fd()), 0, 0)
      n, _ := openFile.Read(dataByte)

      fmt.Println(string(dataByte[:n]))

      // Output:
      // 38
      // hello goframe test open file with flag
}
```

### `OpenWithFalgPerm`

- 说明：以指定\`flag\`以及\`perm\`的方式打开文件/文件夹。
- 格式:

```go
func OpenWithFlagPerm(path string, flag int, perm os.FileMode) (*os.File, error)
```

- 示例：

```go
func ExampleOpenWithFlagPerm() {
      // init
      var (
          path     = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dataByte = make([]byte, 4096)
      )

      // Opens file/directory with custom `flag` and `perm`
      // Create if file does not exist,it is created in a readable and writable mode with  `perm` is 0777
      openFile, _ := gfile.OpenWithFlagPerm(path, os.O_CREATE|os.O_RDWR, gfile.DefaultPermCopy)
      defer openFile.Close()

      // Write some content to file
      writeLength, _ := openFile.WriteString("hello goframe test open file with flag and perm")

      fmt.Println(writeLength)

      // Read data
      unix.Seek(int(openFile.Fd()), 0, 0)
      n, _ := openFile.Read(dataByte)

      fmt.Println(string(dataByte[:n]))

      // Output:
      // 38
      // hello goframe test open file with flag
}
```

### `Stat`

- 说明：获取给定路径的文件详情。
- 格式:

```go
func Stat(path string) (os.FileInfo, error)
```

- 示例：

```go
func ExampleStat() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )
      // Get a FileInfo describing the named file.
      stat, _ := gfile.Stat(path)

      fmt.Println(stat.Name())
      fmt.Println(stat.IsDir())
      fmt.Println(stat.Mode())
      fmt.Println(stat.ModTime())
      fmt.Println(stat.Size())
      fmt.Println(stat.Sys())

      // May Output:
      // file1
      // false
      // -rwxr-xr-x
      // 2021-12-02 11:01:27.261441694 +0800 CST
      // &{16777220 33261 1 8597857090 501 20 0 [0 0 0 0] {1638414088 192363490} {1638414087 261441694} {1638414087 261441694} {1638413480 485068275} 38 8 4096 0 0 0 [0 0]}
}
```

### `Copy`

- 说明：支持复制文件或目录
- 格式:

```go
func Copy(src string, dst string) error
```

- 示例：

```go
func ExampleCopy() {
      // init
      var (
          srcFileName = "gfile_example.txt"
          srcTempDir  = gfile.TempDir("gfile_example_copy_src")
          srcTempFile = gfile.Join(srcTempDir, srcFileName)

          // copy file
          dstFileName = "gfile_example_copy.txt"
          dstTempFile = gfile.Join(srcTempDir, dstFileName)

          // copy dir
          dstTempDir = gfile.TempDir("gfile_example_copy_dst")
      )

      // write contents
      gfile.PutContents(srcTempFile, "goframe example copy")

      // copy file
      gfile.Copy(srcTempFile, dstTempFile)

      // read contents after copy file
      fmt.Println(gfile.GetContents(dstTempFile))

      // copy dir
      gfile.Copy(srcTempDir, dstTempDir)

      // list copy dir file
      fList, _ := gfile.ScanDir(dstTempDir, "*", false)
      for _, v := range fList {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // goframe example copy
      // gfile_example.txt
      // gfile_example_copy.txt
}
```

### `CopyFile`

- 说明：复制文件
- 格式:

```go
func CopyFile(src, dst string) (err error)
```

- 示例：

```go
func ExampleCopyFile() {
      // init
      var (
          srcFileName = "gfile_example.txt"
          srcTempDir  = gfile.TempDir("gfile_example_copy_src")
          srcTempFile = gfile.Join(srcTempDir, srcFileName)

          // copy file
          dstFileName = "gfile_example_copy.txt"
          dstTempFile = gfile.Join(srcTempDir, dstFileName)
      )

      // write contents
      gfile.PutContents(srcTempFile, "goframe example copy")

      // copy file
      gfile.CopyFile(srcTempFile, dstTempFile)

      // read contents after copy file
      fmt.Println(gfile.GetContents(dstTempFile))

      // Output:
      // goframe example copy
}
```

### `CopyDir`

- 说明：支持复制文件或目录
- 格式:

```go
func CopyDir(src string, dst string) error
```

- 示例：

```go
func ExampleCopyDir() {
      // init
      var (
          srcTempDir  = gfile.TempDir("gfile_example_copy_src")

          // copy file
          dstFileName = "gfile_example_copy.txt"
          dstTempFile = gfile.Join(srcTempDir, dstFileName)

          // copy dir
          dstTempDir = gfile.TempDir("gfile_example_copy_dst")
      )
      // read contents after copy file
      fmt.Println(gfile.GetContents(dstTempFile))

      // copy dir
      gfile.CopyDir(srcTempDir, dstTempDir)

      // list copy dir file
      fList, _ := gfile.ScanDir(dstTempDir, "*", false)
      for _, v := range fList {
          fmt.Println(gfile.Basename(v))
      }

      // Output:
      // gfile_example.txt
      // gfile_example_copy.txt
}
```

### `Move`

- 说明：将 `src` 重命名为 `dst`。

- 注意：如果 `dst` 已经存在并且是文件，将会被替换造成数据丢失！
- 格式:

```go
func Move(src string, dst string) error
```

- 示例：

```go
func ExampleMove() {
      // init
      var (
          srcPath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          dstPath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file2")
      )
      // Check is file
      fmt.Println(gfile.IsFile(dstPath))

      //  Moves `src` to `dst` path.
      // If `dst` already exists and is not a directory, it'll be replaced.
      gfile.Move(srcPath, dstPath)

      fmt.Println(gfile.IsFile(srcPath))
      fmt.Println(gfile.IsFile(dstPath))

      // Output:
      // false
      // false
      // true
}
```

### `Rename`

- 说明： `Move` 的别名，将 `src` 重命名为 `dst`。

- 注意：如果 `dst` 已经存在并且是文件，将会被替换造成数据丢失！
- 格式:

```go
func Rename(src string, dst string) error
```

- 示例：

```go
func ExampleRename() {
      // init
      var (
          srcPath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file2")
          dstPath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )
      // Check is file
      fmt.Println(gfile.IsFile(dstPath))

      //  renames (moves) `src` to `dst` path.
      // If `dst` already exists and is not a directory, it'll be replaced.
      gfile.Rename(srcPath, dstPath)

      fmt.Println(gfile.IsFile(srcPath))
      fmt.Println(gfile.IsFile(dstPath))

      // Output:
      // false
      // false
      // true
}
```

### `Remove`

- 说明：删除给定路径的文件或文件夹。

- 格式:

```go
func Remove(path string) error
```

- 示例：

```go
func ExampleRemove() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Checks whether given `path` a file, which means it's not a directory.
      fmt.Println(gfile.IsFile(path))

      // deletes all file/directory with `path` parameter.
      gfile.Remove(path)

      // Check again
      fmt.Println(gfile.IsFile(path))

      // Output:
      // true
      // false
}
```

### `IsEmpty`

- 说明：检查给定的路径，如果是文件夹则检查是否包含文件，如果是文件则检查文件大小是否为空。

- 格式:

```go
func IsEmpty(path string) bool
```

- 示例：

```go
func ExampleIsEmpty() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Check whether the `path` is empty
      fmt.Println(gfile.IsEmpty(path))

      // Truncate file
      gfile.Truncate(path, 0)

      // Check whether the `path` is empty
      fmt.Println(gfile.IsEmpty(path))

      // Output:
      // false
      // true
}
```

### `DirNames`

- 说明：获取给定路径下的文件列表，返回的是一个切片。

- 格式:

```go
func DirNames(path string) ([]string, error)
```

- 示例：

```go
func ExampleDirNames() {
      // init
      var (
          path = gfile.TempDir("gfile_example_basic_dir")
      )
      // Get sub-file names of given directory `path`.
      dirNames, _ := gfile.DirNames(path)

      fmt.Println(dirNames)

      // May Output:
      // [file1]
}
```

### `Glob`

- 说明：模糊搜索给定路径下的文件列表，支持正则，第二个参数控制返回的结果是否带上绝对路径。

- 格式:

```go
func Glob(pattern string, onlyNames ...bool) ([]string, error)
```

- 示例：

```go
func ExampleGlob() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "*_example_basic_test.go"
      )
      // Get sub-file names of given directory `path`.
      // Only show file name
      matchNames, _ := gfile.Glob(path, true)

      fmt.Println(matchNames)

      // Show full path of the file
      matchNames, _ = gfile.Glob(path, false)

      fmt.Println(matchNames)

      // May Output:
      // [gfile_z_example_basic_test.go]
      // [xxx/gf/os/gfile/gfile_z_example_basic_test.go]
}
```

### `MatchGlob`

:::tip
版本要求：`v2.10.0`
:::

- 说明：`MatchGlob` 方法用于判断给定的文件名是否匹配指定的`shell`模式。它扩展了标准库的 `filepath.Match` 功能，支持 `**`（`globstar`）通配符模式，类似于`bash`的`globstar`和 `gitignore`的模式规则。

- 格式：

```go
func MatchGlob(pattern, name string) (bool, error)
```

- 参数说明：
  - `pattern`：匹配模式字符串，支持通配符。
  - `name`：要匹配的文件名或路径。
  - 返回值：第一个返回值表示是否匹配，第二个返回值表示可能的错误（例如模式格式错误）。

- 模式语法：
  - `*` 匹配任意非分隔符字符序列
  - `**` 匹配任意字符序列，包括路径分隔符（`globstar`）
  - `?` 匹配任意单个非分隔符字符
  - `[abc]` 匹配括号内的任意一个字符
  - `[a-z]` 匹配指定范围内的任意字符
  - `[^abc]` 匹配不在括号内的任意字符（取反）
  - `[^a-z]` 匹配不在指定范围内的任意字符（取反）

- `Globstar`规则：
  - `**` 仅当作为完整路径组件出现时才具有 `globstar` 语义（例如：`a/**/b`、`**/a`、`a/**`、`**`）
  - 像 `a**b` 或 `**a` 这样的模式中，`**` 被视为两个普通的 `*` 通配符，只匹配单个路径组件内的字符
  - `/` 和 `\` 都被视为路径分隔符（支持跨平台）

- 错误处理：
  - 对于格式错误的模式（例如未闭合的括号 `[abc`）会返回错误
  - 来自 `filepath.Match` 的错误会被传播

- 示例：

```go
func ExampleMatchGlob() {
      var pattern, name string
      var matched bool
      var err error

      // 基本通配符匹配
      pattern = "*.go"
      name = "main.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // 使用 ? 通配符
      pattern = "test_?.go"
      name = "test_1.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // 使用 ** 匹配任意深度的目录
      pattern = "**/*.go"
      name = "src/foo/bar/main.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // 使用 ** 匹配所有内容
      pattern = "**"
      name = "any/path/to/file.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // 使用中间的 ** 通配符
      pattern = "src/**/test/*.go"
      name = "src/foo/bar/test/main.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // 字符范围匹配
      pattern = "[a-z].go"
      name = "x.go"
      matched, err = gfile.MatchGlob(pattern, name)
      fmt.Printf("Pattern: %s, Name: %s, Matched: %v, Error: %v\n", pattern, name, matched, err)

      // Output:
      // Pattern: *.go, Name: main.go, Matched: true, Error: <nil>
      // Pattern: test_?.go, Name: test_1.go, Matched: true, Error: <nil>
      // Pattern: **/*.go, Name: src/foo/bar/main.go, Matched: true, Error: <nil>
      // Pattern: **, Name: any/path/to/file.go, Matched: true, Error: <nil>
      // Pattern: src/**/test/*.go, Name: src/foo/bar/test/main.go, Matched: true, Error: <nil>
      // Pattern: [a-z].go, Name: x.go, Matched: true, Error: <nil>
}
```

:::tip
- `**` 通配符特别适合在构建工具、文件搜索等场景中使用，可以灵活匹配任意深度的目录结构。
- 该方法与 `.gitignore` 文件的模式规则兼容，便于实现文件过滤功能。
- 如果只需要标准的通配符匹配（不包含 `**`），可以直接使用标准库的 `filepath.Match`，性能更优。
:::

### `Exists`

- 说明：检查给定的路径是否存在 。
- 格式:

```go
func Exists(path string) bool
```

- 示例：

```go
func ExampleExists() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )
      // Checks whether given `path` exist.
      fmt.Println(gfile.Exists(path))

      // Output:
      // true
}
```

### `Chdir`

- 说明：使用给定的路径，更改当前的工作路径。
- 格式:

```go
func Chdir(dir string) error
```

- 示例：

```go
func ExampleChdir() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )
      // Get current working directory
      fmt.Println(gfile.Pwd())

      // Changes the current working directory to the named directory.
      gfile.Chdir(path)

      // Get current working directory
      fmt.Println(gfile.Pwd())

      // May Output:
      // xxx/gf/os/gfile
      // /tmp/gfile_example_basic_dir/file1
}
```

## 路径操作

### `Join`

- 说明：将多个字符串路径通过\`/\`进行连接。
- 格式:

```go
func Join(paths ...string) string
```

- 示例：

```go
func ExampleJoin() {
      // init
      var (
          dirPath  = gfile.TempDir("gfile_example_basic_dir")
          filePath = "file1"
      )

      // Joins string array paths with file separator of current system.
      joinString := gfile.Join(dirPath, filePath)

      fmt.Println(joinString)

      // Output:
      // /tmp/gfile_example_basic_dir/file1
}
```

### `Abs`

- 说明：返回路径的绝对路径。

- 格式:

```go
func Abs(path string) string
```

- 示例：

```go
func ExampleAbs() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Get an absolute representation of path.
      fmt.Println(gfile.Abs(path))

      // Output:
      // /tmp/gfile_example_basic_dir/file1
}
```

### `RealPath`

- 说明：获取给定路径的绝对路径地址。

- 注意：如果文件不存在则返回空。

- 格式:

```go
func RealPath(path string) string
```

- 示例：

```go
func ExampleRealPath() {
      // init
      var (
          realPath  = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
          worryPath = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "worryFile")
      )

      // fetch an absolute representation of path.
      fmt.Println(gfile.RealPath(realPath))
      fmt.Println(gfile.RealPath(worryPath))

      // Output:
      // /tmp/gfile_example_basic_dir/file1
      //
}
```

### `SelfName`

- 说明：获取当前运行程序的名称。

- 格式:

```go
func SelfName() string
```

- 示例：

```go
func ExampleSelfName() {

      // Get file name of current running process
      fmt.Println(gfile.SelfName())

      // May Output:
      // ___github_com_gogf_gf_v2_os_gfile__ExampleSelfName
}
```

### `Basename`

- 说明：获取给定路径中的最后一个元素，包含扩展名。

- 格式:

```go
func Basename(path string) string
```

- 示例：

```go
func ExampleBasename() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Get the last element of path, which contains file extension.
      fmt.Println(gfile.Basename(path))

      // Output:
      // file.log
}
```

### `Name`

- 说明：获取给定路径中的最后一个元素，不包含扩展名。

- 格式:

```go
func Name(path string) string
```

- 示例：

```go
func ExampleName() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Get the last element of path without file extension.
      fmt.Println(gfile.Name(path))

      // Output:
      // file
}
```

### `Dir`

- 说明：获取给定路径的目录部分，排除最后的元素。

- 格式:

```go
func Dir(path string) string
```

- 示例：

```go
func ExampleDir() {
      // init
      var (
          path = gfile.Join(gfile.TempDir("gfile_example_basic_dir"), "file1")
      )

      // Get all but the last element of path, typically the path's directory.
      fmt.Println(gfile.Dir(path))

      // Output:
      // /tmp/gfile_example_basic_dir
}
```

### `Ext`

- 说明：获取给定路径的扩展名，包含\`.\`。

- 格式:

```go
func Ext(path string) string
```

- 示例：

```go
func ExampleExt() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Get the file name extension used by path.
      fmt.Println(gfile.Ext(path))

      // Output:
      // .log
}
```

### `ExtName`

- 说明：获取给定路径的扩展名，不包含\`.\`。

- 格式:

```go
func ExtName(path string) string
```

- 示例：

```go
func ExampleExtName() {
      // init
      var (
          path = gfile.Pwd() + gfile.Separator + "testdata/readline/file.log"
      )

      // Get the file name extension used by path but the result does not contains symbol '.'.
      fmt.Println(gfile.ExtName(path))

      // Output:
      // log
}
```

### `MainPkgPath`

- 说明：获取main文件（主入口）所在的绝对路径，。

- 注意：
  - `该方法仅在开发环境中可用，同时仅在源代码开发环境中有效，build二进制后将显示源代码的路径地址。`
  - `第一次调用该方法时，如果处于异步的goroutine中，可能会无法获取主包的路径`
- 格式:

```go
func MainPkgPath() string
```

- 示例：

```go
func Test() {
      fmt.Println("main pkg path on main :", gfile.MainPkgPath())
      char := make(chan int, 1)
      go func() {
          fmt.Println("main pkg path on goroutine :", gfile.MainPkgPath())
          char <- 1
      }()
      select {
      case <-char:
      }
      // Output:
      // /xxx/xx/xxx/xx
      // /xxx/xx/xxx/xx
}
// 二进制包
$ ./testDemo
main pkg path on main : /xxx/xx/xxx/xx
main pkg path on goroutine : /xxx/xx/xxx/xx

```