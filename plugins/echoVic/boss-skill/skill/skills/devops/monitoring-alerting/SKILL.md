---
name: devops/monitoring-alerting
description: 监控告警配置，确保系统稳定运行
version: 1.0.0
agent: devops
type: guideline
user-invocable: false
agent-invocable: true
dependencies: []
triggers:
  - 需要配置监控时
  - 需要设置告警时
---

# 监控告警

## 监控指标

| 类型 | 指标 | 阈值 |
|------|------|------|
| 应用 | 错误率 | < 1% |
| 应用 | 响应时间 | P99 < 500ms |
| 系统 | CPU使用率 | < 80% |
| 系统 | 内存使用率 | < 85% |
| 系统 | 磁盘使用率 | < 90% |

## 告警规则

| 级别 | 条件 | 通知方式 |
|------|------|----------|
| P0 | 服务不可用 | 电话 + 短信 + 邮件 |
| P1 | 错误率 > 5% | 短信 + 邮件 |
| P2 | 响应时间 > 1s | 邮件 |
| P3 | 资源使用率 > 80% | 邮件 |

## 日志管理

- 集中式日志收集
- 日志分级（ERROR, WARN, INFO, DEBUG）
- 日志保留策略（30天）
- 敏感信息脱敏
