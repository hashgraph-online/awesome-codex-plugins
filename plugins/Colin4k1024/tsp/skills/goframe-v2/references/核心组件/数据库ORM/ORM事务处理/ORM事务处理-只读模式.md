## 基本介绍

事务只读模式（`ReadOnly`）是`GoFrame ORM`提供的一种事务处理特性，它允许开发者将事务标记为只读状态。
在只读事务中，数据库会禁止任何修改操作（如`INSERT`、`UPDATE`、`DELETE`等），只允许执行查询操作。
`GoFrame ORM`通过`TxOptions`结构体的`ReadOnly`字段支持此功能。

## 只读模式的优点

1. **提高安全性**：防止意外的数据修改操作，确保事务中只能进行读取操作
2. **优化性能**：数据库可以针对只读事务进行特定优化，如避免获取写锁，减少锁竞争
3. **减少资源消耗**：只读事务通常消耗更少的数据库资源，特别是在高并发场景下
4. **提高并发度**：多个只读事务可以并行执行而不会相互阻塞
5. **支持负载均衡**：只读事务可以被路由到只读副本，减轻主库压力

## 应用场景

1. **数据报表生成**：生成复杂报表时需要查询大量数据但不需要修改数据
2. **数据导出功能**：导出数据时确保数据一致性，同时防止意外修改
3. **复杂数据查询**：需要在事务中执行多个相关查询以确保数据一致性
4. **只读API接口**：为只提供数据查询的API接口提供事务保障
5. **数据分析操作**：执行复杂的数据分析查询时确保不会修改数据
6. **审计和日志查询**：查看历史记录和审计日志时防止意外修改

## 基本使用

`GoFrame ORM`提供了简单易用的API来创建只读事务，通过`BeginWithOptions`或`TransactionWithOptions`方法并设置`ReadOnly: true`即可启用只读模式。

### 使用`BeginWithOptions`

```go
// 开始一个只读事务
tx, err := db.BeginWithOptions(ctx, gdb.TxOptions{
    ReadOnly: true,
})
// SQL: BEGIN

if err != nil {
    // 处理错误
    return
}

// 确保事务最终会提交或回滚
defer func() {
    if err := recover(); err != nil {
        tx.Rollback()
        panic(err)
    }
}()

// 执行查询操作
users, err := tx.Model("user").All()
// SQL: SELECT * FROM user

// 尝试执行修改操作会失败
_, err = tx.Update("user", g.Map{"status": "active"}, "id=1")
// 在只读事务中，这将返回错误

// 提交事务
if err = tx.Commit(); err != nil {
    tx.Rollback()
    return
}
```

### 使用`TransactionWithOptions`

```go
// 使用事务闭包函数
err := db.TransactionWithOptions(ctx, gdb.TxOptions{
    ReadOnly: true,
}, func(ctx context.Context, tx gdb.TX) error {
    // 执行查询操作
    users, err := tx.Model("user").Where("status", "active").All()
    // SQL: SELECT * FROM user WHERE status='active'
    
    if err != nil {
        return err
    }
    
    // 处理查询结果
    fmt.Println("Active users count:", len(users))
    
    // 尝试执行修改操作会失败并自动回滚事务
    _, err = tx.Model("user").Data(g.Map{"login_time": gtime.Now()}).Where("id", 1).Update()
    // 在只读事务中，这将返回错误
    
    return err // 返回nil会自动提交事务，返回错误会自动回滚
})
```

## MySQL中的只读事务

在`MySQL`中，只读事务通过以下`SQL`语句实现：

```sql
-- 开始一个只读事务
SET TRANSACTION READ ONLY;
START TRANSACTION;

-- 执行查询操作
SELECT * FROM user;

-- 尝试执行修改操作会失败
UPDATE user SET status = 'active' WHERE id = 1;
-- 错误: ERROR 1792 (25006): Cannot execute statement in a READ ONLY transaction.

-- 提交事务
COMMIT;
```

## 注意事项

1. 只读事务中尝试执行数据修改操作会导致错误，事务将被回滚
2. 不同数据库对只读事务的支持和实现可能有所不同
3. 只读事务主要用于提高安全性和性能，而不是强制的访问控制机制
4. 在高并发系统中，合理使用只读事务可以显著提高性能
5. 只读事务通常可以被路由到数据库的只读副本上执行

## 实际应用示例

### 报表生成

```go
// 使用只读事务生成销售报表
err := db.TransactionWithOptions(ctx, gdb.TxOptions{
    ReadOnly: true,
}, func(ctx context.Context, tx gdb.TX) error {
    // 1. 查询总销售额
    totalSales, err := tx.Model("order").Where("status", "completed").Sum("amount")
    // SQL: SELECT SUM(amount) FROM order WHERE status='completed'
    
    if err != nil {
        return err
    }
    
    // 2. 查询各产品销售情况
    productSales, err := tx.Model("order_item")
        .Fields("product_id, SUM(quantity) as total_quantity, SUM(amount) as total_amount")
        .Group("product_id")
        .Order("total_amount DESC")
        .All()
    // SQL: SELECT product_id, SUM(quantity) as total_quantity, SUM(amount) as total_amount 
    //      FROM order_item GROUP BY product_id ORDER BY total_amount DESC
    
    if err != nil {
        return err
    }
    
    // 3. 查询热门客户
    topCustomers, err := tx.Model("order")
        .Fields("customer_id, COUNT(*) as order_count, SUM(amount) as total_spent")
        .Group("customer_id")
        .Order("total_spent DESC")
        .Limit(10)
        .All()
    // SQL: SELECT customer_id, COUNT(*) as order_count, SUM(amount) as total_spent 
    //      FROM order GROUP BY customer_id ORDER BY total_spent DESC LIMIT 10
    
    // 生成报表逻辑...
    
    return nil // 返回nil自动提交事务
})
```

### 数据导出

```go
// 使用只读事务导出用户数据
err := db.TransactionWithOptions(ctx, gdb.TxOptions{
    ReadOnly: true,
}, func(ctx context.Context, tx gdb.TX) error {
    // 查询用户基本信息
    users, err := tx.Model("user").All()
    // SQL: SELECT * FROM user
    
    if err != nil {
        return err
    }
    
    // 对每个用户查询其详细信息
    for _, user := range users {
        userId := user["id"]
        
        // 查询用户地址
        address, err := tx.Model("user_address").Where("user_id", userId).One()
        // SQL: SELECT * FROM user_address WHERE user_id=?
        
        if err != nil {
            return err
        }
        
        // 查询用户订单
        orders, err := tx.Model("order").Where("user_id", userId).All()
        // SQL: SELECT * FROM order WHERE user_id=?
        
        if err != nil {
            return err
        }
        
        // 导出数据处理逻辑...
    }
    
    return nil
})
```

## 事务只读模式与`DryRun`特性的区别

`GoFrame ORM`除了提供事务的只读模式外，还提供了`DryRun`特性（相关章节 [ORM高级特性-空跑特性](../ORM高级特性/ORM高级特性-空跑特性.md)）。
虽然这两个特性都能防止数据修改，但它们在实现机制、应用场景和影响范围上有明显区别：

### 实现机制

1. **只读事务（ReadOnly）**：
   - 在数据库层面实现，通过设置事务的只读属性
   - 由数据库引擎强制执行，尝试修改操作会返回数据库错误
   - 通过`TxOptions`结构体的`ReadOnly`字段启用，仅影响当前事务

2. **DryRun特性**：
   - 在`ORM`层面实现，是一种模拟执行机制
   - 由`GoFrame`框架拦截并忽略写操作，不会实际发送到数据库
   - 通过配置文件、命令行参数或环境变量全局启用，影响所有数据库操作

### 应用场景

1. **只读事务适用于**：
   - 生产环境中需要保证数据一致性的只读操作
   - 需要利用数据库只读副本的场景
   - 需要在事务中执行多个查询以保证数据一致性
   - 对性能有较高要求的高并发只读操作

2. **DryRun特性适用于**：
   - 开发和测试环境中验证SQL语句的正确性
   - 调试程序逻辑而不想实际修改数据库
   - 演示系统功能而不改变数据状态
   - 批处理脚本的预检查

### 影响范围

1. **只读事务**：
   - 仅影响特定的事务实例
   - 可以与普通事务并存于同一应用中
   - 需要显式地在每个事务中启用

2. **DryRun特性**：
   - 全局影响所有数据库操作（包括非事务操作）
   - 通常作为应用级别的配置选项
   - 一旦启用，所有写操作都将被忽略

### 错误处理

1. **只读事务**：
   - 尝试执行写操作会立即返回数据库错误
   - 错误会导致事务回滚
   - 可以在代码中捕获和处理这些错误

2. **DryRun特性**：
   - 写操作不会返回错误，而是被静默忽略
   - 应用程序会认为写操作成功执行
   - 通常与日志和调试模式配合使用以查看SQL语句

### 配置方式

1. **只读事务**：
   ```go
   // 通过代码配置，仅影响当前事务
   tx, err := db.BeginWithOptions(ctx, gdb.TxOptions{
       ReadOnly: true,
   })
   ```

2. **DryRun特性**：
   ```yaml
   # 通过配置文件启用
   database:
     default:
       - link: "mysql:root:password@tcp(127.0.0.1:3306)/db"
         debug: true
         dryRun: true
   ```
   
   ```bash
   # 或通过命令行参数启用
   $ ./app --gf.gdb.dryrun=true
   
   # 或通过环境变量启用
   $ export GF_GDB_DRYRUN=true
   $ ./app
   ```

### 如何选择

- 如果需要在**生产环境**中保证数据一致性并提高性能，选择**只读事务**
- 如果是在**开发/测试环境**中调试SQL语句或验证程序逻辑，选择`DryRun`特性
- 如果需要**细粒度控制**哪些操作是只读的，选择**只读事务**
- 如果需要**全局禁止**所有写操作（如演示环境），选择`DryRun`特性

两者可以结合使用，例如在开发环境中使用`DryRun`进行全局调试，同时在特定场景中使用只读事务来测试事务隔离和错误处理逻辑。

## 总结

事务只读模式是`GoFrame ORM`提供的一种重要特性，通过将事务标记为只读状态，可以提高数据库操作的安全性和性能。在只读事务中，数据库会禁止任何修改操作，只允许执行查询操作，这对于需要确保数据一致性但不需要修改数据的场景非常有用。

在实际应用中，建议在以下情况下考虑使用只读事务：
- 需要在事务中执行多个查询以确保数据一致性
- 需要防止意外的数据修改操作
- 高并发系统中的只读操作
- 需要利用数据库只读副本的场景

合理使用只读事务可以显著提高系统的安全性、性能和可扩展性。与`DryRun`特性相比，只读事务更适合生产环境中的实际业务需求，而`DryRun`则更适合开发和测试阶段的调试工作。