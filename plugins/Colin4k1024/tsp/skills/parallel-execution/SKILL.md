---
name: parallel-execution
description: >
  并行执行框架：基于 Git worktree 的多实例并行、任务分发与动态扩展。
  当任务可拆分、需要加速执行、或需要多分支并行开发时使用。
---

# Parallel Execution Framework

## 用途

- 任务并行：拆分可独立执行的任务并并行处理
- 分支隔离：使用 Git worktree 实现多分支并行开发
- 资源扩展：根据任务复杂度动态扩展执行实例
- 级联执行：串联依赖任务，并行独立任务

## 核心概念

### 1. 任务类型

| 类型 | 说明 | 并行策略 |
|------|------|---------|
| `independent` | 无依赖，可立即执行 | 并行 |
| `sequential` | 依赖前一任务输出 | 串行 |
| `parallel` | 多个独立任务 | 并行 |
| `cascade` | 主任务触发子任务 | 级联 |

### 2. Git Worktree 并行

```
worktree add <path> <branch>  # 创建新 worktree
worktree list                  # 列出所有 worktree
worktree prune                 # 清理无效 worktree
```

### 3. 扩展策略

- **Scale Out**：增加并行实例数（横向扩展）
- **Scale Up**：提升实例规格（纵向扩展）
- **Cascade**：主任务完成后触发子任务

## 触发信号

- 任务可明确拆分为多个独立子任务
- 需要在多个分支上并行开发
- 任务耗时超过 10 分钟且可拆分
- 需要同时验证多个方案

## 使用约束

1. 任务拆分后，每个子任务必须有明确的输入输出
2. 并行任务之间不能有写冲突
3. 需要共享的状态通过文件或消息传递
4. 主任务负责汇总子任务结果
5. 失败处理：部分失败时，主任务决定是重试、跳过还是中止

## 配套工具

- `scripts/lib/parallel_execution.py` - 底层并行执行接口
- `GitWorktreeManager` - worktree 管理
- `TaskDistributor` - 任务分发
- `ResultAggregator` - 结果汇总

## 命令接入

- `/parallel <task描述>` - 分解并并行执行任务
- `/worktree-create <branch>` - 创建 worktree 分支
- `/worktree-list` - 列出所有 worktree
- `/scale-out <num>` - 扩展到 N 个并行实例
