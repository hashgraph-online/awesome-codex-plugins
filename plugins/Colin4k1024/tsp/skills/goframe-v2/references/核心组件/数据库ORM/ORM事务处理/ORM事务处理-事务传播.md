事务传播（`Transaction Propagation`）是`GoFrame ORM`框架提供的一种高级事务管理机制，用于控制嵌套事务的行为。在复杂的业务场景中，一个事务方法可能会调用其他事务方法，此时需要明确定义事务的传播行为，以确保数据的一致性和完整性。

## 基本介绍

事务传播定义了事务方法被另一个事务方法调用时应该如何表现。`GoFrame ORM`支持多种事务传播行为，开发者可以根据业务需求选择合适的传播类型。

`GoFrame ORM`支持以下事务传播类型：

- `PropagationNested` (默认)：如果当前存在事务，则创建嵌套事务（使用保存点）；如果不存在事务，则创建新事务。
- `PropagationRequired`：如果当前存在事务，则加入该事务；如果不存在事务，则创建新事务。
- `PropagationSupports`：如果当前存在事务，则加入该事务；如果不存在事务，则以非事务方式执行。
- `PropagationRequiresNew`：创建新事务，如果当前存在事务，则挂起当前事务。
- `PropagationNotSupported`：以非事务方式执行，如果当前存在事务，则挂起当前事务。
- `PropagationMandatory`：如果当前存在事务，则加入该事务；如果不存在事务，则抛出异常。
- `PropagationNever`：以非事务方式执行，如果当前存在事务，则抛出异常。

:::info
注意事项：为保证和旧版本事务处理的兼容性，`GoFrame ORM`默认的事务传播类型为`PropagationNested`，而不是`PropagationRequired`。
:::

## 使用优势

1. **灵活的事务管理**：根据业务需求选择不同的事务传播行为，实现更精细的事务控制。
2. **提高代码复用性**：服务层方法可以独立定义事务行为，无需关心调用环境是否已有事务。
3. **降低事务冲突**：通过适当的传播行为，减少长事务导致的锁定和冲突问题。
4. **增强错误隔离**：使用独立事务（如`PropagationRequiresNew`）可以隔离错误影响，避免整体事务回滚。
5. **简化复杂业务逻辑**：在复杂业务流程中，不同步骤可以使用不同的事务传播策略，使代码更清晰。

## 应用场景

1. **服务组合**：当一个服务方法调用多个其他服务方法时，可以根据业务需求选择是共享同一事务还是使用独立事务。
2. **日志记录**：业务操作需要记录日志，但日志写入失败不应影响主要业务逻辑，可以使用`PropagationRequiresNew`。
3. **批量处理**：在批量处理中，可能希望每个项目使用独立事务，以便某个项目失败不影响其他项目。
4. **事务补偿**：在分布式系统中，可以使用不同的传播行为实现事务补偿机制。
5. **嵌套业务逻辑**：复杂业务逻辑中的某些步骤可能需要作为一个独立的事务单元，可以使用`PropagationNested`。

## 使用示例

在开始示例之前，我们先创建一个用于测试的数据表：

```sql
CREATE TABLE IF NOT EXISTS `user` (
    id INT PRIMARY KEY,
    username VARCHAR(50)
);
```

:::tip
如果您想逐步运行以下示例，您需要在每次运行新示例之前清空一下`user`表数据。
:::

### PropagationNested (嵌套事务，默认)

如果当前存在事务，则创建嵌套事务（使用保存点）；如果不存在事务，则创建新事务。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 执行事务
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在外层事务中插入数据
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "outer_user",
		})
		if err != nil {
			return err
		}

		// 嵌套事务 - 使用PropagationNested创建嵌套事务（使用保存点）
		err = tx.Transaction(ctx, func(ctx context.Context, tx2 gdb.TX) error {
			// 在嵌套事务中插入数据
			_, err = tx2.Insert("user", g.Map{
				"id":       2,
				"username": "nested_user",
			})
			if err != nil {
				return err
			}

			// 模拟错误，导致嵌套事务回滚到保存点
			return fmt.Errorf("嵌套事务故意失败")
		})

		// 嵌套事务失败，但外层事务可以继续
		fmt.Println("嵌套事务错误:", err)

		// 继续在外层事务中插入数据
		_, err = tx.Insert("user", g.Map{
			"id":       3,
			"username": "outer_after_nested",
		})
		// 外层事务正常提交
		return nil
	})

	if err != nil {
		fmt.Println("事务执行失败:", err)
		return
	}

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	// 数据中只有id为1和3的数据，没有2
	fmt.Println("查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');

-- 创建保存点
SAVEPOINT sp1;
-- 插入嵌套事务数据
INSERT INTO user(id,username) VALUES(2,'nested_user');
-- 嵌套事务失败，回滚到保存点
ROLLBACK TO SAVEPOINT sp1;

-- 继续外层事务
INSERT INTO user(id,username) VALUES(3,'outer_after_nested');
-- 提交外层事务
COMMIT;
```

### PropagationRequired (保证事务)

事务传播类型`PropagationRequired`与`PropagationNested`的主要区别在于，`PropagationRequired`在当前存在事务时加入该事务，
而在没有事务时创建新事务，**并不会创建嵌套事务**。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 执行事务
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在外层事务中插入数据
		// 在事务闭包中使用tx对象或者db对象来操作数据表都是等价的
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "outer_user",
		})
		if err != nil {
			return err
		}

		// 嵌套事务 - 默认使用PropagationRequired
		err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
			Propagation: gdb.PropagationRequired,
		}, func(ctx context.Context, tx2 gdb.TX) error {
			// 在嵌套事务中插入数据（使用相同的事务）
			// 在事务闭包中使用tx2对象或者db对象来操作数据表都是等价的
			_, err = tx2.Insert("user", g.Map{
				"id":       2,
				"username": "inner_user",
			})
			return err
		})

		return err
	})
	if err != nil {
		fmt.Println("事务执行失败:", err)
		return
	}

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	fmt.Println("查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');
-- 插入内层数据（使用相同事务）
INSERT INTO user(id,username) VALUES(2,'inner_user');
-- 提交事务
COMMIT;
```

### PropagationRequiresNew (创建新事务)

创建新事务，如果当前存在事务，则挂起当前事务。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 执行事务
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在外层事务中插入数据
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "outer_user",
		})
		if err != nil {
			return err
		}

		// 嵌套事务 - 使用PropagationRequiresNew创建新事务
		err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
			Propagation: gdb.PropagationRequiresNew,
		}, func(ctx context.Context, tx2 gdb.TX) error {
			// 在新事务中插入数据
			_, err = tx2.Insert("user", g.Map{
				"id":       2,
				"username": "new_tx_user",
			})
			// 模拟错误，导致内层事务回滚
			return fmt.Errorf("内层事务故意失败")
		})

		// 内层事务失败不影响外层事务
		fmt.Println("内层事务错误:", err)

		// 继续在外层事务中插入数据
		_, err = tx.Insert("user", g.Map{
			"id":       3,
			"username": "outer_after_error",
		})
		// 外层事务正常提交
		return nil
	})

	if err != nil {
		fmt.Println("事务执行失败:", err)
		return
	}

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	fmt.Println("查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');

-- 开始新的独立事务
BEGIN;
-- 插入内层数据（使用新事务）
INSERT INTO user(id,username) VALUES(2,'new_tx_user');
-- 内层事务回滚
ROLLBACK;

-- 继续外层事务
INSERT INTO user(id,username) VALUES(3,'outer_after_error');
-- 提交外层事务
COMMIT;
```

### PropagationSupports (支持当前事务)

如果当前存在事务，则加入该事务；如果不存在事务，则以非事务方式执行。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 场景1: 有外部事务时，加入外部事务
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在外层事务中插入数据
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "outer_user",
		})
		if err != nil {
			return err
		}

		// 嵌套事务 - 使用PropagationSupports
		err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
			Propagation: gdb.PropagationSupports,
		}, func(ctx context.Context, tx2 gdb.TX) error {
			// 在支持当前事务的方式下插入数据（使用外层事务）
			_, err = tx2.Insert("user", g.Map{
				"id":       2,
				"username": "supports_user",
			})
			return err
		})

		return err
	})
	if err != nil {
		fmt.Println("场景1执行失败:", err)
		return
	}

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	fmt.Println("场景1查询结果:", result)

	// 清空数据表
	_, err = db.Exec(ctx, `TRUNCATE TABLE user`)
	if err != nil {
		fmt.Println("执行失败:", err)
		return
	}

	// 场景2: 没有外部事务时，非事务方式执行
	err = db.TransactionWithOptions(ctx, gdb.TxOptions{
		Propagation: gdb.PropagationSupports,
	}, func(ctx context.Context, tx gdb.TX) error {
		// 以非事务方式插入数据
		_, err = tx.Insert("user", g.Map{
			"id":       3,
			"username": "non_tx_user",
		})
		return err
	})
	if err != nil {
		fmt.Println("场景2执行失败:", err)
		return
	}

	// 查询结果
	result, err = db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	fmt.Println("场景2查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 场景1: 有外部事务
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');
-- 插入内层数据（使用外层事务）
INSERT INTO user(id,username) VALUES(2,'supports_user');
-- 提交事务
COMMIT;

-- 场景2: 没有外部事务
-- 非事务方式直接插入数据
INSERT INTO user(id,username) VALUES(3,'non_tx_user');
```

### PropagationMandatory (强制使用事务)

如果当前存在事务，则加入该事务；如果不存在事务，则抛出异常。

```go
package main

import (
    _ "github.com/gogf/gf/contrib/drivers/mysql/v2"

    "context"
    "fmt"

    "github.com/gogf/gf/v2/database/gdb"
    "github.com/gogf/gf/v2/frame/g"
)

func main() {
    var (
        ctx = context.Background()
        db  = g.DB()
    )
    db.SetDebug(true)

    // 场景1: 有外部事务时，加入外部事务
    err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
        // 在外层事务中插入数据
        _, err := tx.Insert("user", g.Map{
            "id":       1,
            "username": "outer_user",
        })
        if err != nil {
            return err
        }

        // 嵌套事务 - 使用PropagationMandatory
        err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
            Propagation: gdb.PropagationMandatory,
        }, func(ctx context.Context, tx2 gdb.TX) error {
            // 在强制使用当前事务的方式下插入数据（使用外层事务）
            _, err = tx2.Insert("user", g.Map{
                "id":       2,
                "username": "mandatory_user",
            })
            return err
        })

        return err
    })

    if err != nil {
        fmt.Println("场景1执行失败:", err)
        return
    }

    // 查询结果
    result, err := db.Model("user").All()
    if err != nil {
        fmt.Println("查询失败:", err)
        return
    }

    fmt.Println("场景1查询结果:", result)

    // 清空数据表
    _, err = db.Exec(ctx, `TRUNCATE TABLE user`)
    if err != nil {
        fmt.Println("执行失败:", err)
        return
    }

    // 场景2: 没有外部事务时，将抛出异常
    fmt.Println("场景2: 没有外部事务时使用PropagationMandatory")
    err = db.TransactionWithOptions(ctx, gdb.TxOptions{
        Propagation: gdb.PropagationMandatory,
    }, func(ctx context.Context, tx gdb.TX) error {
        // 这里的代码不会执行，因为没有外部事务时会抛出异常
        _, err = tx.Insert("user", g.Map{
            "id":       3,
            "username": "will_not_insert",
        })
        return err
    })

    // 应该有错误，因为没有外部事务
    fmt.Println("场景2错误:", err)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 场景1: 有外部事务
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');
-- 插入内层数据（使用外层事务）
INSERT INTO user(id,username) VALUES(2,'mandatory_user');
-- 提交事务
COMMIT;

-- 场景2: 没有外部事务
-- 抛出异常: "mandatory transaction is required, but none exists"
```

### PropagationNever (不允许在事务中执行)

以非事务方式执行，如果当前存在事务，则抛出异常。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 场景1: 有外部事务时，将抛出异常
	fmt.Println("场景1: 有外部事务时使用PropagationNever")
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在外层事务中插入数据
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "outer_user",
		})
		if err != nil {
			return err
		}

		// 嵌套事务 - 使用PropagationNever
		err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
			Propagation: gdb.PropagationNever,
		}, func(ctx context.Context, tx2 gdb.TX) error {
			// 这里的代码不会执行，因为在外部事务中使用PropagationNever会抛出异常
			_, err := tx2.Insert("user", g.Map{
				"id":       2,
				"username": "will_not_insert",
			})
			return err
		})

		// 应该有错误
		fmt.Println("嵌套事务错误:", err)

		// 继续外层事务
		return nil
	})
	if err != nil {
		fmt.Println("场景1执行失败:", err)
		return
	}

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}
	// 应该只有id=1的记录
	fmt.Println("场景1查询结果:", result)

	// 清空数据表
	_, err = db.Exec(ctx, `TRUNCATE TABLE user`)
	if err != nil {
		fmt.Println("执行失败:", err)
		return
	}

	// 场景2: 没有外部事务时，非事务方式执行
	err = db.TransactionWithOptions(ctx, gdb.TxOptions{
		Propagation: gdb.PropagationNever,
	}, func(ctx context.Context, tx gdb.TX) error {
		// 以非事务方式插入数据
		_, err = tx.Insert("user", g.Map{
			"id":       3,
			"username": "non_tx_user",
		})
		return err
	})
	if err != nil {
		fmt.Println("场景2执行失败:", err)
		return
	}

	// 查询结果
	result, err = db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}
	// 应该有id=3的记录
	fmt.Println("场景2查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 场景1: 有外部事务
-- 开始外层事务
BEGIN;
-- 插入外层数据
INSERT INTO user(id,username) VALUES(1,'outer_user');
-- 抛出异常: "transaction is existing, but never transaction is required"
-- 提交外层事务
COMMIT;

-- 场景2: 没有外部事务
-- 非事务方式直接插入数据
INSERT INTO user(id,username) VALUES(3,'non_tx_user');
```

### PropagationNotSupported (非事务方式执行)

以非事务方式执行，如果当前存在事务，则挂起当前事务。

```go
package main

import (
	_ "github.com/gogf/gf/contrib/drivers/mysql/v2"

	"context"
	"fmt"

	"github.com/gogf/gf/v2/database/gdb"
	"github.com/gogf/gf/v2/frame/g"
)

func main() {
	var (
		ctx = context.Background()
		db  = g.DB()
	)
	db.SetDebug(true)

	// 执行事务
	err := db.Transaction(ctx, func(ctx context.Context, tx gdb.TX) error {
		// 在事务中插入数据
		_, err := tx.Insert("user", g.Map{
			"id":       1,
			"username": "tx_user",
		})
		if err != nil {
			return err
		}

		// 使用PropagationNotSupported挂起当前事务
		err = tx.TransactionWithOptions(ctx, gdb.TxOptions{
			Propagation: gdb.PropagationNotSupported,
		}, func(ctx context.Context, tx2 gdb.TX) error {
			// 非事务方式写入数据
			_, err = tx2.Insert("user", g.Map{
				"id":       2,
				"username": "non_tx_user",
			})
			return err
		})
		if err != nil {
			return err
		}

		// 模拟错误，导致外层事务回滚
		return fmt.Errorf("外层事务故意失败")
	})

	fmt.Println("事务执行结果:", err)

	// 查询结果
	result, err := db.Model("user").All()
	if err != nil {
		fmt.Println("查询失败:", err)
		return
	}

	// 应该只看到id=2的记录，因为id=1的记录在事务回滚时被撤销
	fmt.Println("查询结果:", result)
}
```

上述代码执行的`SQL`语句类似于：

```sql
-- 开始事务
BEGIN;
-- 插入事务内数据
INSERT INTO user(id,username) VALUES(1,'tx_user');

-- 非事务方式执行（直接提交）
INSERT INTO user(id,username) VALUES(2,'non_tx_user');

-- 外层事务回滚
ROLLBACK;
```

## 总结

`GoFrame ORM`的事务传播功能为开发者提供了灵活的事务管理机制，能够满足复杂业务场景下的事务处理需求。通过合理选择事务传播行为，可以实现更精细的事务控制，提高系统的可靠性和性能。

在实际应用中，建议根据业务特点选择合适的传播行为：

1. 对于大多数场景，默认的`PropagationRequired`已经能够满足需求。
2. 当需要独立事务以隔离错误影响时，可以使用`PropagationRequiresNew`。
3. 对于需要保存点功能的场景，可以使用`PropagationNested`。
4. 当某些操作不需要事务保护时，可以使用`PropagationNotSupported`。

通过合理使用事务传播机制，可以构建更加健壮和可维护的应用程序。