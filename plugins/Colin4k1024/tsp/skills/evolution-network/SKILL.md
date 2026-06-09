---
name: evolution-network
description: Cross-agent gene sharing protocol for exchanging validated evolution patterns between Claude sessions with trust downgrades and local revalidation.
---

# Evolution Network

> 跨 Agent 基因共享协议，允许不同 agent 实例发现、请求和接收来自其他 agent 的验证过的经验基因。

## 触发条件

- 当 `evolution-core` 查询未命中本地基因时
- 当用户执行 `/evolve share` 或 `/evolve pull` 时
- 当 session-end hook 检测到可共享的高置信度基因时

## 核心概念

### Gene Sharing Protocol

基因共享遵循 **请求-响应** 模型：

1. **Discovery**：Agent A 广播信号特征，网络中的 agent 匹配本地基因
2. **Request**：Agent A 获取候选列表后请求完整基因数据
3. **Receive**：接收基因以 `received` 状态进入本地 store（confidence 降级为 0.30）
4. **Validate**：本地至少成功执行 1 次后才提升为 `candidate`

### Shared Gene Registry

共享注册表存储在 `~/.claude/evolution/network/registry.json`：

```json
{
  "version": 1,
  "agents": {
    "agent-abc123": {
      "last_seen": "2025-01-15T10:00:00Z",
      "gene_count": 42,
      "promoted_count": 15,
      "capabilities": ["python", "typescript", "docker"]
    }
  },
  "shared_genes": [
    {
      "gene_id": "gene_xxx",
      "owner_agent": "agent-abc123",
      "signals_summary": ["npm test failure", "jest config"],
      "confidence": 0.85,
      "tags": ["testing", "jest", "node"],
      "shared_at": "2025-01-15T10:00:00Z"
    }
  ]
}
```

### Trust Model

| 来源 | 初始 Confidence | 提升条件 |
|------|----------------|---------|
| 本地创建 | 0.40 | 正常流程 |
| 网络接收 | 0.30 | 本地执行成功 1 次 → 0.40，之后正常流程 |
| 导入 (migrate) | 基于原始数据 | 正常流程 |

### Share Policy

默认共享策略：
- 只共享 `promoted` 状态的基因（confidence ≥ 0.60，至少 3 次成功）
- 不共享包含路径、密钥或环境特有配置的基因
- 共享前自动脱敏信号中的绝对路径和用户名

## 传输格式

Gene 共享使用 JSON 行格式（`.jsonl`），每行一个基因：

```json
{
  "gene_id": "gene_xxx",
  "signals": [...],
  "strategy": {...},
  "confidence": 0.85,
  "tags": [...],
  "stats": {"successes": 5, "failures": 0},
  "exported_at": "2025-01-15T10:00:00Z",
  "source_agent": "agent-abc123"
}
```

导出文件存储在 `~/.claude/evolution/network/exports/`，导入文件从 `~/.claude/evolution/network/imports/` 读取。

## 命令接口

```
/evolve share              # 导出 promoted 基因到 exports/
/evolve share --tags test  # 只导出特定 tag 的基因
/evolve pull               # 从 imports/ 导入其他 agent 的基因
/evolve pull --dry-run     # 预览将导入的基因
/evolve network status     # 查看网络注册表状态
```

## 隐私与安全

- 基因共享默认 **opt-in**，需要设置 `EVOLUTION_NETWORK_ENABLED=1`
- 导出前自动执行信号脱敏（路径、用户名、主机名）
- 不传输 `capsule` 中的原始 `outcome` 数据（可能包含敏感输出）
- 支持 `~/.claude/evolution/network/deny-list.json` 手动排除特定基因或 tag

## 参考

- [evolution-core SKILL.md](../evolution-core/SKILL.md) — 基因模型定义
- [store.py](../../../scripts/evolution/store.py) — 存储层
- [governor.py](../../../scripts/evolution/governor.py) — 安全控制层
