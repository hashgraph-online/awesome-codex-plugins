---
name: tech-lead/technical-standards
description: 技术规范和最佳实践，确保代码质量和一致性
version: 1.0.0
agent: tech-lead
type: guideline
user-invocable: false
agent-invocable: true
dependencies:
  - shared/tech-stack-detection
triggers:
  - 需要定义技术规范时
  - 需要统一代码风格时
---

# 技术规范与最佳实践

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量 | camelCase | `userName`, `isActive` |
| 常量 | UPPER_SNAKE_CASE | `MAX_COUNT`, `API_URL` |
| 函数 | camelCase | `getUserById`, `calculateTotal` |
| 类 | PascalCase | `UserService`, `OrderController` |
| 文件 | kebab-case | `user-service.ts`, `order-controller.ts` |

## 代码组织

- **单一职责**：每个函数/类只做一件事
- **DRY原则**：不要重复代码
- **KISS原则**：保持简单
- **YAGNI原则**：不要过度设计

## 错误处理

- 使用try-catch捕获异常
- 提供有意义的错误信息
- 记录错误日志
- 优雅降级

## 测试要求

- 单元测试覆盖率 ≥ 70%
- 关键路径必须有测试
- 测试要独立、可重复
