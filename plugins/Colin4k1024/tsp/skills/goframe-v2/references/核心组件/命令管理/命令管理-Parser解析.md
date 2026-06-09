## 基本介绍

命令行解析最主要的是针对于选项的解析， `gcmd` 组件提供了 `Parse` 方法，用于自定义解析选项，包括有哪些选项名称，每个选项是否带有数值。根据这一配置便可将所有的参数和选项进行解析归类。
:::tip
大部分场景下，我们并不需要显式创建 `Parser` 对象，因为我们有层级管理以及对象管理方式来管理多命令。但底层仍然是采用 `Parser` 方式实现，因此本章节大家了解原理即可。
:::
相关方法：

更多 `Parser` 方法请参考接口文档： [https://pkg.go.dev/github.com/gogf/gf/v2/os/gcmd#Parser](https://pkg.go.dev/github.com/gogf/gf/v2/os/gcmd#Parser)

```go
func Parse(supportedOptions map[string]bool, option ...ParserOption) (*Parser, error)
func ParseWithArgs(args []string, supportedOptions map[string]bool, option ...ParserOption) (*Parser, error)
func ParserFromCtx(ctx context.Context) *Parser
func (p *Parser) GetArg(index int, def ...string) *gvar.Var
func (p *Parser) GetArgAll() []string
func (p *Parser) GetOpt(name string, def ...interface{}) *gvar.Var
func (p *Parser) GetOptAll() map[string]string
```

其中， `ParserOption` 如下：

```go
// ParserOption manages the parsing options.
type ParserOption struct {
    CaseSensitive bool // Marks options parsing in case-sensitive way.
    Strict        bool // Whether stops parsing and returns error if invalid option passed.
}
```

解析示例：

```go
parser, err := gcmd.Parse(g.MapStrBool{
    "n,name":    true,
    "v,version": true,
    "a,arch":    true,
    "o,os":      true,
    "p,path":    true,
})
```

可以看到，选项输入参数其实是一个 `map` 类型。其中键值为选项名称，同一个选项的不同名称可以通过 `,` 符号进行分隔。比如，该示例中 `n` 和 `name` 选项是同一个选项，当用户输入 `-n john` 的时候， `n` 和 `name` 选项都会获得到数据 `john`。

而键值是一个布尔类型，标识该选项是否需要解析参数。这一选项配置是非常重要的，因为有的选项是不需要获得数据的，仅仅作为一个标识。例如， `-f force` 这个输入，在需要解析数据的情况下，选项 `f` 的值为 `force`；而在不需要解析选项数据的情况下，其中的 `force` 便是命令行的一个参数，而不是选项。

## 使用示例

```go
func ExampleParse() {
    os.Args = []string{"gf", "build", "main.go", "-o=gf.exe", "-y"}
    p, err := gcmd.Parse(g.MapStrBool{
        "o,output": true,
        "y,yes":    false,
    })
    if err != nil {
        panic(err)
    }
    fmt.Println(p.GetOpt("o"))
    fmt.Println(p.GetOpt("output"))
    fmt.Println(p.GetOpt("y") != nil)
    fmt.Println(p.GetOpt("yes") != nil)
    fmt.Println(p.GetOpt("none") != nil)

    // Output:
    // gf.exe
    // gf.exe
    // true
    // true
    // false
}
```