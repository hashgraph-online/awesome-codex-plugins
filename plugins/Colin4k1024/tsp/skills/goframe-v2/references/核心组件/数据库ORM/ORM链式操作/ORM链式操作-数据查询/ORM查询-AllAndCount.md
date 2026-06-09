## 基本介绍
该方法从 `v2.5.0` 版本开始提供，用于同时查询数据记录列表及总数量，一般用于分页查询场景中，简化分页查询逻辑。

方法定义：

```go
// AllAndCount retrieves all records and the total count of records from the model.
// If useFieldForCount is true, it will use the fields specified in the model for counting;
// otherwise, it will use a constant value of 1 for counting.
// It returns the result as a slice of records, the total count of records, and an error if any.
// The where parameter is an optional list of conditions to use when retrieving records.
//
// Example:
//
//    var model Model
//    var result Result
//    var count int
//    where := []interface{}{"name = ?", "John"}
//    result, count, err := model.AllAndCount(true)
//    if err != nil {
//        // Handle error.
//    }
//    fmt.Println(result, count)
func (m *Model) AllAndCount(useFieldForCount bool) (result Result, totalCount int, err error)
```

在方法内部查询总数量时，将会忽略查询中的 `Limit/Page` 操作。

## 使用示例

```go
// SELECT `uid`,`name` FROM `user` WHERE `status`='deleted' LIMIT 0,10
// SELECT COUNT(`uid`,`name`) FROM `user` WHERE `status`='deleted'
all, count, err := Model("user").Fields("uid", "name").Where("status", "deleted").Limit(0, 10).AllAndCount(true)

// SELECT `uid`,`name` FROM `user` WHERE `status`='deleted' LIMIT 0,10
// SELECT COUNT(1) FROM `user` WHERE `status`='deleted'
all, count, err := Model("user").Fields("uid", "name").Where("status", "deleted").Limit(0, 10).AllAndCount(false)
```