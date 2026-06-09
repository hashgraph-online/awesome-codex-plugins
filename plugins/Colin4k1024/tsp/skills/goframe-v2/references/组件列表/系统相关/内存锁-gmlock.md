内存锁模块，也称之为 `动态互斥锁` 模块，支持按照 `给定键名动态生成互斥锁`，并发安全并支持 `Try*Lock` 特性。

> 当维护大量动态互斥锁的场景时，如果不再使用的互斥锁对象，请手动调用 `Remove` 方法删除掉。

**使用方式**：

```go
import "github.com/gogf/gf/v2/os/gmlock"
```

**使用场景**： 需要 `动态创建互斥锁`，或者需要 `维护大量动态锁` 的场景；

**接口文档**：

[https://pkg.go.dev/github.com/gogf/gf/v2/os/gmlock](https://pkg.go.dev/github.com/gogf/gf/v2/os/gmlock)

```go
func Lock(key string)
func LockFunc(key string, f func())
func RLock(key string)
func RLockFunc(key string, f func())
func RUnlock(key string)
func Remove(key string)
func TryLock(key string) bool
func TryLockFunc(key string, f func()) bool
func TryRLock(key string) bool
func TryRLockFunc(key string, f func()) bool
func Unlock(key string)
type Locker
    func New() *Locker
    func (l *Locker) Clear()
    func (l *Locker) Lock(key string)
    func (l *Locker) LockFunc(key string, f func())
    func (l *Locker) RLock(key string)
    func (l *Locker) RLockFunc(key string, f func())
    func (l *Locker) RUnlock(key string)
    func (l *Locker) Remove(key string)
    func (l *Locker) TryLock(key string) bool
    func (l *Locker) TryLockFunc(key string, f func()) bool
    func (l *Locker) TryRLock(key string) bool
    func (l *Locker) TryRLockFunc(key string, f func()) bool
    func (l *Locker) Unlock(key string)
```

### 示例1，基本使用

```go
package main

import (
    "time"
    "sync"
    "github.com/gogf/gf/v2/os/glog"
    "github.com/gogf/gf/v2/os/gmlock"
)

func main() {
    key := "lock"
    wg  := sync.WaitGroup{}
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(i int) {
            gmlock.Lock(key)
            glog.Println(i)
            time.Sleep(time.Second)
            gmlock.Unlock(key)
            wg.Done()
        }(i)
    }
    wg.Wait()
}
```

该示例中，模拟了同时开启 `10` 个 `goroutine`，但同一时刻只能有一个 `goroutine` 获得锁，获得锁的 `goroutine` 执行 `1` 秒后退出，其他 `goroutine` 才能获得锁。

执行后，输出结果为：

```html
2018-10-15 23:57:28.295 9
2018-10-15 23:57:29.296 0
2018-10-15 23:57:30.296 1
2018-10-15 23:57:31.296 2
2018-10-15 23:57:32.296 3
2018-10-15 23:57:33.297 4
2018-10-15 23:57:34.297 5
2018-10-15 23:57:35.297 6
2018-10-15 23:57:36.298 7
2018-10-15 23:57:37.298 8
```

### 示例2，TryLock非阻塞锁

`TryLock` 方法是有返回值的，它表示用来尝试获取锁，如果获取成功，则返回 `true`；如果获取失败（即互斥锁已被其他 `goroutine` 获取），则返回 `false`。

```go
package main

import (
    "sync"
    "github.com/gogf/gf/v2/os/glog"
    "time"
    "github.com/gogf/gf/v2/os/gmlock"
)

func main() {
    key := "lock"
    wg  := sync.WaitGroup{}
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(i int) {
            if gmlock.TryLock(key) {
                glog.Println(i)
                time.Sleep(time.Second)
                gmlock.Unlock(key)
            } else {
                glog.Println(false)
            }
            wg.Done()
        }(i)
    }
    wg.Wait()
}
```

同理，在该示例中，同时也只有 `1` 个 `goroutine` 能获得锁，其他 `goroutine` 在 `TryLock` 失败便直接退出了。

执行后，输出结果为：

```html
2018-10-16 00:01:59.172 9
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.172 false
2018-10-16 00:01:59.176 false
```