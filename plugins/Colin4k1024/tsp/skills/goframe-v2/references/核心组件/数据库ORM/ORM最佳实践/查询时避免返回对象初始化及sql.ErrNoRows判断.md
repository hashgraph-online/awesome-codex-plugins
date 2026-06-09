## 查询时避免返回对象初始化及 `sql.ErrNoRows` 判断

执行`SQL`查询时，请避免提前将查询结果初始化，以避免结构对象默认值的影响，避免创建不必要的对象内存。通过返回对象指针 `nil` 判断避免 `sql.ErrNoRows` 使用，降低代码对 `error` 处理的复杂度、统一项目中对空查询结果处理逻辑。

一个反面例子：

```go
func (s *Service) GetOne(ctx context.Context, id uint64) (out *entity.ResourceTask, err error) {
    out = new(model.TaskDetail)
    err = dao.ResourceTask.Ctx(ctx).WherePri(id).Scan(out)
    if err != nil {
        if err == sql.ErrNoRows {
            err = gerror.Newf(`record not found for "%d"`, id)
        }
        return
    }
    return
}
```

在该例子中，实际返回的 `out` 对象由于对象初始化的缘故有了默认值（无论SQL是否查询到数据），并且 `sql.ErrNoRows` 的判断增加了代码逻辑中对 `error` 处理的复杂度。

建议改进如下：

```go
func (s *Service) GetOne(ctx context.Context, id uint64) (out *entity.ResourceTask, err error) {
    err = dao.ResourceTask.Ctx(ctx).WherePri(id).Scan(&out)
    if err != nil {
        return
    }
    if out == nil {
        err = gerror.Newf(`record not found for "%d"`, id)
    }
    return
}
```
:::warning
注意代码中 `&out` 的使用。
:::
更多的介绍请参考： [ORM结果处理-为空判断](../ORM结果处理/ORM结果处理-为空判断.md)