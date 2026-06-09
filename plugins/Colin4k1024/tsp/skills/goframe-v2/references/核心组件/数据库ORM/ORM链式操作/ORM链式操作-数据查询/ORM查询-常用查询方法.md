## 基本介绍
数据查询比较常用的几个方法：

```go
func (m *Model) All(where ...interface{} (Result, error)
func (m *Model) One(where ...interface{}) (Record, error)
func (m *Model) Array(fieldsAndWhere ...interface{}) ([]Value, error)
func (m *Model) Value(fieldsAndWhere ...interface{}) (Value, error)
func (m *Model) Count(where ...interface{}) (int, error)
func (m *Model) CountColumn(column string) (int, error)
```

简要说明：

1. `All` 用于查询并返回多条记录的列表/数组。
2. `One` 用于查询并返回单条记录。
3. `Array` 用于查询指定字段列的数据，返回数组。
4. `Value` 用于查询并返回一个字段值，往往需要结合 `Fields` 方法使用。
5. `Count` 用于查询并返回记录数。

此外，也可以看得到这五个方法定义中也支持条件参数的直接输入，参数类型与 `Where` 方法一致。但需要注意，其中 `Array` 和 `Value` 方法的参数中至少应该输入字段参数。

## 使用示例

```go
// SELECT * FROM `user` WHERE `score`>60
Model("user").Where("score>?", 60).All()

// SELECT * FROM `user` WHERE `score`>60 LIMIT 1
Model("user").Where("score>?", 60).One()

// SELECT `name` FROM `user` WHERE `score`>60
Model("user").Fields("name").Where("score>?", 60).Array()

// SELECT `name` FROM `user` WHERE `uid`=1 LIMIT 1
Model("user").Fields("name").Where("uid", 1).Value()

// SELECT COUNT(1) FROM `user` WHERE `status` IN(1,2,3)
Model("user").Where("status", g.Slice{1,2,3}).Count()
```