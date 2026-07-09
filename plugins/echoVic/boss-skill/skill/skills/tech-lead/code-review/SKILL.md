---
name: tech-lead/code-review
description: 代码审查方法，包含审查清单、常见问题、最佳实践
version: 1.0.0
agent: tech-lead
type: methodology
user-invocable: false
agent-invocable: true
dependencies:
  - shared/tech-stack-detection
triggers:
  - 需要审查代码时
  - 需要评估代码质量时
---

# 代码审查方法

## 审查清单

### 功能正确性
- [ ] 代码实现符合需求
- [ ] 边界情况处理正确
- [ ] 错误处理完善

### 代码质量
- [ ] 命名清晰易懂
- [ ] 函数职责单一
- [ ] 避免重复代码
- [ ] 注释必要且准确

### 安全性
- [ ] 输入验证
- [ ] SQL注入防护
- [ ] XSS防护
- [ ] 认证授权正确

### 性能
- [ ] 无明显性能问题
- [ ] 数据库查询优化
- [ ] 避免N+1查询

### 可维护性
- [ ] 代码结构清晰
- [ ] 易于测试
- [ ] 遵循项目规范
