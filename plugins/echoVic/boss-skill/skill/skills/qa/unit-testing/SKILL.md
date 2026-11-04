---

name: qa/unit-testing
description: 单元测试方法论，覆盖 AAA 模式、Test Doubles、跨语言示例（JS/TS、Python、Go、Java）、前后端单元测试、边界与属性测试、变异测试
version: 1.0.0
agent: qa
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
- shared/tech-stack-detection
  triggers:
- 需要编写或审查单元测试时
- 需要测试纯函数、Service 层、组件、Hook 时
- 需要确定 Mock 边界时
  metadata:
  internal: true

---

# 单元测试方法论

## 单元测试的定义与原则

单元测试验证**最小可测试单元**（函数、方法、类、组件）的行为，隔离外部依赖。

### 核心原则

| 原则     | 说明                                             |
| -------- | ------------------------------------------------ |
| **隔离** | 一个测试只验证一个行为，不依赖其他测试或外部系统 |
| **快速** | 毫秒级执行，全部单元测试应在秒级完成             |
| **确定** | 相同输入多次运行结果一致，不依赖时间/网络/随机数 |
| **可读** | 测试代码即文档，命名清晰表达意图                 |
| **独立** | 测试顺序不影响结果，可任意顺序执行               |

### 什么该做单元测试

| 应该测                   | 不应该测                       |
| ------------------------ | ------------------------------ |
| 纯函数 / 工具函数        | 框架内部行为（React 渲染机制） |
| Service 层业务逻辑       | 第三方库本身                   |
| 组件渲染与交互（前端）   | 配置文件 / 常量                |
| Hook 状态逻辑            | 简单的 getter/setter           |
| 校验 / 转换 / 格式化逻辑 | 数据库查询（属于集成测试）     |
| 状态机 / 状态转换        | 网络请求（属于集成测试）       |

## AAA 模式（Arrange-Act-Assert）

每个单元测试遵循三段式结构：

```typescript
it('applies 10% discount when total > 100', () => {
  // Arrange — 准备测试数据和环境
  const items = [{ price: 60, quantity: 2 }]; // total = 120
  const discount = 0.1;

  // Act — 执行被测逻辑
  const result = calculateTotal(items, discount);

  // Assert — 验证结果
  expect(result).toBe(108); // 120 * 0.9
});
```

**命名规范**：`[期望行为] when [条件]` 或 `[动作] [结果]`

```typescript
// ✅ 好
it('returns error when email is invalid');
it('calculates total with discount applied');

// ❌ 差
it('should work');
it('test1');
```

## Test Doubles（测试替身）

根据用途选择不同的替身类型：

| 类型      | 用途                 | 示例                                    |
| --------- | -------------------- | --------------------------------------- |
| **Dummy** | 占位，不被调用       | 传一个空对象满足参数签名                |
| **Stub**  | 提供预设返回值       | `repo.findById.mockResolvedValue(user)` |
| **Spy**   | 记录调用信息         | `expect(fn).toHaveBeenCalledWith(arg)`  |
| **Mock**  | Stub + Spy，验证交互 | `mock.calledWith(...)`                  |
| **Fake**  | 简化的真实实现       | 内存数据库替代真实 DB                   |

### 何时使用哪种

```typescript
// Stub：被测代码需要依赖返回值，但不关心调用细节
jest.mock('../repo', () => ({
  findById: jest.fn().mockResolvedValue({ id: '1', name: 'Alice' }),
}));

// Spy：需要验证依赖是否被正确调用
const emailSpy = jest.spyOn(emailService, 'send');
await userService.register(user);
expect(emailSpy).toHaveBeenCalledWith(user.email, expect.any(String));

// Fake：需要一个可用但简化的实现
class FakeCache implements Cache {
  private store = new Map<string, string>();
  async get(k: string) {
    return this.store.get(k) ?? null;
  }
  async set(k: string, v: string) {
    this.store.set(k, v);
  }
}
```

## 前端单元测试

### 组件渲染测试

```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    await userEvent.click(screen.getByRole('button', { name: 'Click' }));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not call onClick when disabled', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick} disabled>Click</Button>);

    await userEvent.click(screen.getByRole('button', { name: 'Click' }));

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies variant styles', () => {
    const { container } = render(<Button variant="primary">Save</Button>);
    expect(container.firstChild).toHaveClass('btn-primary');
  });
});
```

### Hook 测试

```typescript
// useCounter.test.ts
import { renderHook, act } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('initializes with default value 0', () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });

  it('initializes with provided value', () => {
    const { result } = renderHook(() => useCounter(10));
    expect(result.current.count).toBe(10);
  });

  it('increments count', () => {
    const { result } = renderHook(() => useCounter());
    act(() => result.current.increment());
    expect(result.current.count).toBe(1);
  });

  it('decrements count but not below 0', () => {
    const { result } = renderHook(() => useCounter(0));
    act(() => result.current.decrement());
    expect(result.current.count).toBe(0); // 边界：不低于 0
  });

  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(5));
    act(() => result.current.increment());
    act(() => result.current.reset());
    expect(result.current.count).toBe(5);
  });
});
```

### 工具函数测试

```typescript
// formatDate.test.ts
import { formatDate, formatCurrency, maskEmail } from './format';

describe('formatDate', () => {
  it('formats ISO date to YYYY-MM-DD', () => {
    expect(formatDate('2024-01-15T10:30:00Z')).toBe('2024-01-15');
  });

  it('handles invalid date gracefully', () => {
    expect(formatDate('invalid')).toBe('');
  });
});

describe('maskEmail', () => {
  it('masks local part of email', () => {
    expect(maskEmail('alice@example.com')).toBe('a***@example.com');
  });

  it('handles short local part', () => {
    expect(maskEmail('ab@example.com')).toBe('a*@example.com');
  });

  it('returns empty for invalid email', () => {
    expect(maskEmail('not-an-email')).toBe('');
  });
});
```

## 后端单元测试

### Service 层测试（Mock Repository）

```typescript
// userService.test.ts
import { UserService } from './userService';

// Mock 整个 Repository 模块
const mockFindById = jest.fn();
const mockCreate = jest.fn();
jest.mock('../repositories/userRepository', () => ({
  UserRepository: jest.fn().mockImplementation(() => ({
    findById: mockFindById,
    create: mockCreate,
  })),
}));

describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    jest.clearAllMocks();
    service = new UserService();
  });

  describe('getById', () => {
    it('returns user when found', async () => {
      const user = { id: '1', name: 'Alice', email: 'alice@example.com' };
      mockFindById.mockResolvedValue(user);

      const result = await service.getById('1');

      expect(result).toEqual(user);
      expect(mockFindById).toHaveBeenCalledWith('1');
    });

    it('throws NotFoundError when user does not exist', async () => {
      mockFindById.mockResolvedValue(null);

      await expect(service.getById('999')).rejects.toThrow('User not found');
    });
  });

  describe('create', () => {
    it('creates user when email is unique', async () => {
      const data = { name: 'Bob', email: 'bob@example.com' };
      mockFindById.mockResolvedValue(null); // 邮箱不存在
      mockCreate.mockResolvedValue({ id: '2', ...data });

      const result = await service.create(data);

      expect(result).toEqual({ id: '2', ...data });
      expect(mockCreate).toHaveBeenCalledWith(data);
    });

    it('throws ConflictError when email exists', async () => {
      mockFindById.mockResolvedValue({ id: '1', email: 'exists@example.com' });

      await expect(service.create({ name: 'X', email: 'exists@example.com' })).rejects.toThrow(
        'Email already exists',
      );

      expect(mockCreate).not.toHaveBeenCalled(); // 不应调用创建
    });
  });
});
```

### 纯业务逻辑测试

```typescript
// pricing.test.ts
import { calculatePrice, applyCoupon } from './pricing';

describe('calculatePrice', () => {
  it('sums item prices', () => {
    const items = [
      { price: 100, quantity: 2 },
      { price: 50, quantity: 1 },
    ];
    expect(calculatePrice(items)).toBe(250);
  });

  it('returns 0 for empty items', () => {
    expect(calculatePrice([])).toBe(0);
  });

  it('throws on negative quantity', () => {
    expect(() => calculatePrice([{ price: 10, quantity: -1 }])).toThrow(
      'Quantity must be positive',
    );
  });
});

describe('applyCoupon', () => {
  const basePrice = 100;

  it('applies percentage discount', () => {
    expect(applyCoupon(basePrice, { type: 'percent', value: 20 })).toBe(80);
  });

  it('applies fixed amount discount', () => {
    expect(applyCoupon(basePrice, { type: 'fixed', value: 30 })).toBe(70);
  });

  it('does not go below 0', () => {
    expect(applyCoupon(10, { type: 'fixed', value: 100 })).toBe(0);
  });

  it('caps percentage at 100', () => {
    expect(applyCoupon(basePrice, { type: 'percent', value: 150 })).toBe(0);
  });
});
```

## Python 单元测试

```python
# tests/unit/test_pricing.py
import pytest
from app.pricing import calculate_price, apply_coupon

class TestCalculatePrice:
    def test_sums_item_prices(self):
        items = [{"price": 100, "quantity": 2}, {"price": 50, "quantity": 1}]
        assert calculate_price(items) == 250

    def test_empty_items_returns_zero(self):
        assert calculate_price([]) == 0

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="Quantity must be positive"):
            calculate_price([{"price": 10, "quantity": -1}])


class TestApplyCoupon:
    @pytest.mark.parametrize("coupon_type,value,expected", [
        ("percent", 20, 80),
        ("fixed", 30, 70),
        ("percent", 100, 0),
        ("percent", 150, 0),  # cap at 0
    ])
    def test_applies_discount(self, coupon_type, value, expected):
        coupon = {"type": coupon_type, "value": value}
        assert apply_coupon(100, coupon) == expected

    def test_does_not_go_below_zero(self):
        assert apply_coupon(10, {"type": "fixed", "value": 100}) == 0
```

### Python Mock 示例

```python
# tests/unit/test_user_service.py
from unittest.mock import Mock, patch
from app.services.user_service import UserService

class TestUserService:
    def test_get_by_id_returns_user(self):
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = {"id": "1", "name": "Alice"}
        service = UserService(mock_repo)

        result = service.get_by_id("1")

        assert result["name"] == "Alice"
        mock_repo.find_by_id.assert_called_once_with("1")

    def test_get_by_id_raises_when_not_found(self):
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = None
        service = UserService(mock_repo)

        with pytest.raises(ValueError, match="User not found"):
            service.get_by_id("999")
```

## Go 单元测试

```go
// pricing_test.go
package pricing

import "testing"

func TestCalculatePrice(t *testing.T) {
	tests := []struct {
		name  string
		items []Item
		want  int
	}{
		{"sums prices", []Item{{Price: 100, Qty: 2}, {Price: 50, Qty: 1}}, 250},
		{"empty items", []Item{}, 0},
		{"single item", []Item{{Price: 10, Qty: 3}}, 30},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculatePrice(tt.items)
			if got != tt.want {
				t.Errorf("CalculatePrice() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestCalculatePriceNegativeQty(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for negative quantity")
		}
	}()
	CalculatePrice([]Item{{Price: 10, Qty: -1}})
}
```

### Go 接口 Mock

```go
// user_service_test.go
package service

import (
	"testing"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mock Repository
type MockUserRepo struct {
	mock.Mock
}

func (m *MockUserRepo) FindByID(id string) (*User, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*User), args.Error(1)
}

func TestUserService_GetByID(t *testing.T) {
	mockRepo := new(MockUserRepo)
	mockRepo.On("FindByID", "1").Return(&User{ID: "1", Name: "Alice"}, nil)

	service := NewUserService(mockRepo)
	user, err := service.GetByID("1")

	assert.NoError(t, err)
	assert.Equal(t, "Alice", user.Name)
	mockRepo.AssertExpectations(t)
}
```

## Java 单元测试

```java
// PricingTest.java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import static org.junit.jupiter.api.Assertions.*;

class PricingTest {

    @Test
    void sumsItemPrices() {
        var items = List.of(
            new Item(100, 2),
            new Item(50, 1)
        );
        assertEquals(250, Pricing.calculatePrice(items));
    }

    @ParameterizedTest
    @CsvSource({
        "percent, 20, 80",
        "fixed, 30, 70",
        "percent, 100, 0",
    })
    void appliesDiscount(String type, int value, int expected) {
        var coupon = new Coupon(type, value);
        assertEquals(expected, Pricing.applyCoupon(100, coupon));
    }

    @Test
    void throwsOnNegativeQuantity() {
        var items = List.of(new Item(10, -1));
        assertThrows(IllegalArgumentException.class,
            () -> Pricing.calculatePrice(items));
    }
}
```

### Java Mockito 示例

```java
// UserServiceTest.java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void getByIdReturnsUser() {
        var user = new User("1", "Alice");
        when(userRepository.findById("1")).thenReturn(Optional.of(user));

        var result = userService.getById("1");

        assertEquals("Alice", result.getName());
        verify(userRepository).findById("1");
    }

    @Test
    void getByIdThrowsWhenNotFound() {
        when(userRepository.findById("999")).thenReturn(Optional.empty());

        assertThrows(UserNotFoundException.class,
            () -> userService.getById("999"));
    }
}
```

## 边界值与特殊情况

单元测试必须覆盖边界：

| 边界类型          | 示例                              |
| ----------------- | --------------------------------- |
| **空值**          | 空字符串、空数组、null、undefined |
| **零值**          | 数量为 0、金额为 0                |
| **最小值/最大值** | 字符串最大长度、数值上下限        |
| **负数**          | 负数数量、负数金额                |
| **类型边界**      | 整数溢出、浮点数精度              |
| **日期时间**      | 闰年、时区、夏令时、跨年          |
| **集合边界**      | 单元素、刚好达到上限、超过上限    |

```typescript
describe('pagination', () => {
  it('returns first page when page is 1', () => {
    expect(paginate(items, 1, 10)).toEqual(items.slice(0, 10));
  });

  it('returns empty array when page exceeds total', () => {
    expect(paginate([1, 2, 3], 10, 10)).toEqual([]);
  });

  it('clamps pageSize to max', () => {
    expect(paginate(items, 1, 1000).length).toBeLessThanOrEqual(100);
  });

  it('handles page 0 as page 1', () => {
    expect(paginate(items, 0, 10)).toEqual(paginate(items, 1, 10));
  });
});
```

## 错误与异常测试

```typescript
describe('error handling', () => {
  it('throws custom error with code', () => {
    expect(() => validateEmail('invalid')).toThrow(
      expect.objectContaining({ code: 'INVALID_EMAIL' }),
    );
  });

  it('rejects promise with typed error', async () => {
    await expect(service.delete('not-owner-id')).rejects.toMatchObject({
      code: 'FORBIDDEN',
      status: 403,
    });
  });

  it('does not throw for valid input', () => {
    expect(() => validateEmail('a@b.com')).not.toThrow();
  });
});
```

## 属性测试（Property-Based Testing）

对纯函数，用随机生成的输入验证不变量：

```typescript
// 使用 fast-check
import fc from 'fast-check';

describe('reverse function (property test)', () => {
  it('reverse of reverse equals original', () => {
    fc.assert(
      fc.property(fc.array(fc.integer()), (arr) => {
        expect(reverse(reverse(arr))).toEqual(arr);
      }),
    );
  });

  it('reverse preserves length', () => {
    fc.assert(
      fc.property(fc.array(fc.integer()), (arr) => {
        expect(reverse(arr)).toHaveLength(arr.length);
      }),
    );
  });
});
```

## 变异测试（Mutation Testing）

变异测试验证测试的有效性：故意修改源代码（变异），检查测试是否能捕获。

```bash
# Node.js (Stryker)
npx stryker run

# Python (mutmut)
mutmut run

# Go
go test -run TestMutate -v
```

**变异算子**：
- `a + b` → `a - b`
- `a > b` → `a >= b`
- `&&` → `||`
- `return x` → `return 0` / `return null`

**变异得分** = 被杀变异数 / 总变异数，目标 ≥ 80%。

## Mock 边界（单元测试）

### 单元测试中应该 Mock 的

| 依赖                | 原因                                |
| ------------------- | ----------------------------------- |
| 数据库              | 单元测试不碰真实 DB（那是集成测试） |
| 网络请求 / 外部 API | 不可控、慢                          |
| 文件系统            | 速度和隔离                          |
| 时间                | 保证确定性                          |

### 不应该 Mock 的

| 依赖                         | 原因            |
| ---------------------------- | --------------- |
| 被测函数内部调用的同模块函数 | 要验证真实协作  |
| 纯函数 / 工具函数            | Mock 它们无意义 |
| 数据结构 / 常量              | 不是行为依赖    |

**判断标准**：如果一个依赖的行为会被测试直接验证，就不要 Mock 它。

## 测试反模式（禁止）

| 反模式                       | 问题                 | 正确做法            |
| ---------------------------- | -------------------- | ------------------- |
| **一个测试多个断言无关行为** | 失败时不知道哪里坏了 | 拆分多个测试        |
| **测试实现细节而非行为**     | 重构就全挂           | 测输入输出          |
| **Mock 一切**                | 测的是 Mock 不是代码 | 只 Mock 外部依赖    |
| **测试间共享状态**           | 顺序依赖、flaky      | beforeEach 重建     |
| **try-catch 吞异常**         | 测试永远通过         | 让断言抛错          |
| **用随机数据不固定种子**     | 不可重复             | 固定种子或用固定值  |
| **只测 happy path**          | 边界没覆盖           | 必须有边界/异常用例 |

## 检查清单

- [ ] 每个被测单元有对应测试文件
- [ ] 测试遵循 AAA 模式
- [ ] 测试命名表达行为意图
- [ ] 覆盖 happy path + 边界值 + 异常情况
- [ ] 只 Mock 外部依赖，不 Mock 被测逻辑
- [ ] 测试间无共享状态，可独立运行
- [ ] 测试快速执行（毫秒级）
- [ ] 无 try-catch 吞异常
- [ ] 无测试实现细节（只测行为）
