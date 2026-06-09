## 基本介绍

`Go` 语言中的 `goroutine` 虽然相对于系统线程来说比较轻量级（初始栈大小仅 `2KB`），（并且支持动态扩容），而正常采用 `Java`、 `C++` 等语言启用的线程一般都是内核态的占用的内存资源一般在 `4m` 左右，而假设我们的服务器 `CPU` 内存为 `4G`，那么很明显内核态线程的并发总数量也就 `1024` 个，相反 `Go` 语言的协程则可以达到 `4*1024*1024/2=200w`，这么一看就明白了为什么Go语言天生支持高并发。

## 痛点描述

### 协程执行的资源消耗大

但是在高并发量下的 `goroutine` 频繁创建和销毁对于性能损耗以及 `GC` 来说压力也不小。充分将 `goroutine` 复用，减少 `goroutine` 的创建/销毁的性能损耗，这便是 `grpool` 对 `goroutine` 进行池化封装的目的。例如，针对于 `100W` 个执行任务，使用 `goroutine` 的话需要不停创建并销毁 `100W` 个 `goroutine`，而使用 `grpool` 也许底层只需要几万个 `goroutine` 便能充分复用地执行完成所有任务。

经测试， `goroutine` 池对于业务逻辑的执行效率（降低执行时间/CPU使用率）提升不大，甚至没有原生的 `goroutine` 执行快速（池化 `goroutine` 执行调度并没有底层 `Go` 调度器高效，因为池化 `goroutine` 的执行调度也是基于底层 `Go` 调度器），但是由于采用了复用的设计，池化后对内存的使用率得到极大的降低。

### 大量协程影响全局协程调度

某些业务模块需要动态创建协程来执行，例如异步采集任务、指标计算任务等等。这些业务逻辑不是服务的核心逻辑，并且会产生协程。在极端情况下可能会引起协程大暴涨，影响底层 `Go` 引擎全局的写成调度，造成服务整体执行延迟较大。

拿异步采集任务来举个例子，每隔 `5` 秒执行一次，每次创建 `100` 个协程来采集不同的目标端。当采集出现网络延迟时，上一步的任务并未执行完，下一次的任务又新创建协程开始执行。当积累的任务越来越多，会造成协程的暴涨，影响全局的服务执行。针对这一类场景，我们可以通过池化的技术来将任务进行定量执行，当池中的任务堆积到达一定量时，后续的任务应当阻塞。例如，我们设定池中任务的最大数量为 `10000` 个，后续不停将任务丢到池中执行，当超过池的最大数量时，任务执行将会阻塞，但并不会影响全局的服务执行。

## 概念介绍

### `Pool`

`goroutine` 池，用于管理若干可复用的 `goroutine` 协程资源。

### `Job`

添加到池对象的任务队列中等待执行的任务，是一个 `Func` 的方法，一个 `Job` 同时只能被一个 `Worker` 获取并执行。 `Func` 的定义如下：

```go
type Func func(ctx context.Context)
```

### `Worker`

池对象中参与任务执行的 `goroutine`，一个 `Worker` 可以执行若干个 `Job`，直到队列中再无等待的 `Job`。

## 使用介绍

**使用方式**：

```go
import "github.com/gogf/gf/v2/os/grpool"

```

**使用场景**：

管理大量异步任务的场景、需要异步协程复用的场景、需要降低内存使用率的场景。

**接口文档**：

```go
func Add(ctx context.Context, f Func) error
func AddWithRecover(ctx context.Context, userFunc Func, recoverFunc RecoverFunc) error
func Jobs() int
func Size() int
func New(limit ...int) *Pool
    func (p *Pool) Add(ctx context.Context, f Func) error
    func (p *Pool) AddWithRecover(ctx context.Context, userFunc Func, recoverFunc RecoverFunc) error
    func (p *Pool) Cap() int
    func (p *Pool) Close()
    func (p *Pool) IsClosed() bool
    func (p *Pool) Jobs() int
    func (p *Pool) Size() int
```

通过 `grpool.New` 方法创建一个 `goroutine池` 对象，参数 `limit` 为非必需参数，用于限定池中的工作 `goroutine` 数量，默认为不限制。需要注意的是，任务可以不停地往池中添加，没有限制，但是工作的 `goroutine` 是可以做限制的。我们可以通过 `Size()` 方法查询当前的工作 `goroutine` 数量，使用 `Jobs()` 方法查询当前池中待处理的任务数量。

同时，为便于使用， `grpool` 包提供了默认的 `goroutine` 池，默认的池对象不限制 `goroutine` 数量，直接通过 `grpool.Add` 即可往默认的池中添加任务，任务参数必须是一个 `func()` 类型的函数/方法。

这个模块大家问得最多的是外部如何给 `grpool` 里面的任务传递参数，具体请看示例2。

## 使用示例

### 使用默认的 `goroutine` 池，限制 `100` 个 `goroutine` 执行 `1000` 个任务

```go
package main

import (
     "context"
     "fmt"
     "github.com/gogf/gf/v2/os/gctx"
     "github.com/gogf/gf/v2/os/grpool"
     "github.com/gogf/gf/v2/os/gtimer"
     "time"
)

var (
    ctx = gctx.New()
)

func job(ctx context.Context) {
     time.Sleep(1*time.Second)
}

func main() {
     pool := grpool.New(100)
     for i := 0; i < 1000; i++ {
         pool.Add(ctx,job)
     }
     fmt.Println("worker:", pool.Size())
     fmt.Println(" jobs:", pool.Jobs())
     gtimer.SetInterval(ctx,time.Second, func(ctx context.Context) {
         fmt.Println("worker:", pool.Size())
         fmt.Println(" jobs:", pool.Jobs())
         fmt.Println()
     })

     select {}
}
```

这段程序中的任务函数的功能是 `sleep 1秒钟`，这样便能充分展示出goroutine数量限制功能。其中，我们使用了 `gtime.SetInterval` 定时器每隔1秒钟打印出当前默认池中的工作 `goroutine` 数量以及待处理的任务数量。

### 异步传参：来个新手容易出错的例子

> 这个例子在go版本≥1.22时不再生效，即go 1.22以后不再有循环变量陷阱。

```go
package main

import (
     "context"
     "fmt"
     "github.com/gogf/gf/v2/os/gctx"
     "github.com/gogf/gf/v2/os/grpool"
     "sync"
)

var (
    ctx = gctx.New()
)

func main() {
     wg := sync.WaitGroup{}
     for i := 0; i < 10; i++ {
        wg.Add(1)
        grpool.Add(ctx,func(ctx context.Context) {
               fmt.Println(i)
               wg.Done()
        })
     }
     wg.Wait()
}
```

我们这段代码的目的是要顺序地打印出0-9，然而运行后却输出：

```10
10
10
10
10
10
10
10
10
10
```

为什么呢？这里的执行结果无论是采用 `go` 关键字来执行还是 `grpool` 来执行都是如此。原因是，对于异步线程/协程来讲，函数进行异步执行注册时，该函数并未真正开始执行(注册时只在 `goroutine` 的栈中保存了变量 `i` 的内存地址)，而一旦开始执行时函数才会去读取变量 `i` 的值，而这个时候变量 `i` 的值已经自增到了 `10`。 清楚原因之后，改进方案也很简单了，就是在注册异步执行函数的时候，把当时变量 `i` 的值也一并传递获取；或者把当前变量i的值赋值给一个不会改变的临时变量，在函数中使用该临时变量而不是直接使用变量 `i`。

改进后的示例代码如下：

**1)、使用go关键字**

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    wg := sync.WaitGroup{}
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(v int){
            fmt.Println(v)
            wg.Done()
        }(i)
    }
    wg.Wait()
}

```

执行后，输出结果为：

```0
9
3
4
5
6
7
8
1
2
```

注意，异步执行时并不会保证按照函数注册时的顺序执行，以下同理。

**2)、使用临时变量**

```go
package main

import (
     "context"
     "fmt"
     "github.com/gogf/gf/v2/os/gctx"
     "github.com/gogf/gf/v2/os/grpool"
     "sync"
)

var (
   ctx = gctx.New()
)

func main() {
     wg := sync.WaitGroup{}
     for i := 0; i < 10; i++ {
        wg.Add(1)
        v := i
        grpool.Add(ctx, func(ctx context.Context) {
               fmt.Println(v)
               wg.Done()
        })
     }
     wg.Wait()
}
```

执行后，输出结果为：

```9
0
1
2
3
4
5
6
7
8
```

这里可以看到，使用 `grpool` 进行任务注册时，注册方法为 `func(ctx context.Context)`，因此无法在任务注册时把变量 `i` 的值注册进去（请尽量不要通过 `ctx` 传递业务参数），因此只能采用临时变量的形式来传递当前变量 `i` 的值。

### 自动捕获 `goroutine` 错误： `AddWithRecover`

`AddWithRecover` 将新作业推送到具有指定恢复功能的池中。当 `userFunc` 执行过程中出现 `panic` 时，会调用可选的 `Recovery Func`。如果没有传入 `Recovery Func` 或赋空，则忽略 `userFunc` 引发的 `panic`。该作业将异步执行。

```go
package main

import (
    "context"
    "fmt"
    "github.com/gogf/gf/v2/container/garray"
    "github.com/gogf/gf/v2/os/gctx"
    "github.com/gogf/gf/v2/os/grpool"
    "time"
)

var (
    ctx = gctx.New()
)
func main() {
    array := garray.NewArray(true)
    grpool.AddWithRecover(ctx, func(ctx context.Context) {
        array.Append(1)
        array.Append(2)
        panic(1)
    }, func(err error) {
        array.Append(1)
    })
    grpool.AddWithRecover(ctx, func(ctx context.Context) {
        panic(1)
        array.Append(1)
    })
    time.Sleep(500 * time.Millisecond)
    fmt.Print(array.Len())
}
```

### 测试一下 `grpool` 和原生的 `goroutine` 之间的性能

**1)、 `grpool`**

```go
package main

import (
     "context"
     "fmt"
     "github.com/gogf/gf/v2/os/gctx"
     "github.com/gogf/gf/v2/os/grpool"
     "github.com/gogf/gf/v2/os/gtime"
     "sync"
     "time"
)

var (
   ctx = gctx.New()
)

func main() {
     start := gtime.TimestampMilli()
     wg := sync.WaitGroup{}
     for i := 0; i < 10000000; i++ {
        wg.Add(1)
        grpool.Add(ctx,func(ctx context.Context) {
               time.Sleep(time.Millisecond)
               wg.Done()
        })
     }
     wg.Wait()
     fmt.Println(grpool.Size())
     fmt.Println("time spent:", gtime.TimestampMilli() - start)
}
```

**2)、 `goroutine`**

```go
package main

import (
     "fmt"
     "github.com/gogf/gf/v2/os/gtime"
     "sync"
     "time"
)

func main() {
     start := gtime.TimestampMilli()
     wg := sync.WaitGroup{}
     for i := 0; i < 10000000; i++ {
        wg.Add(1)
        go func() {
               time.Sleep(time.Millisecond)
               wg.Done()
        }()
     }
     wg.Wait()
     fmt.Println("time spent:", gtime.TimestampMilli() - start)
}
```

**3)、运行结果比较**

测试结果为两个程序各运行 `3` 次取平均值。

```shell
grpool:
    goroutine count: 847313
     memory   spent: ~2.1 G
     time     spent: 37792 ms

goroutine:
    goroutine count: 1000W
    memory    spent: ~4.8 GB
    time      spent: 27085 ms

```

可以看到池化过后，执行相同数量的任务， `goroutine` 数量减少很多，相对的内存也降低了一倍以上，CPU时间耗时也勉强可以接受。