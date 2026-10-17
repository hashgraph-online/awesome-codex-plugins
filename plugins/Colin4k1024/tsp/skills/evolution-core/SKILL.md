---
name: evolution-core
description: >
  统一进化资产模型与自进化闭环核心。定义 Gene（策略 DNA）、Capsule（已验证经验快照）、
  EvolutionEvent（追加式事件日志）三层资产模型，实现 Detect→Select→Replay→Validate→Solidify→Reuse
  闭环，使 agent 遇到已知问题时先复用已验证经验，跳过重新试错。
origin: inspired by Oris EvoKernel
version: 1.0.0
---

# Evolution Core — 自进化资产模型与闭环

## 用途

- **即时复用**：agent 遇到错误时，先从进化存储中查找匹配的已验证经验（Capsule），尝试重放，成功则跳过 LLM 推理
- **经验沉淀**：每次成功解决问题后，自动提取信号、生成策略 Gene 和执行快照 Capsule
- **跨 agent 共享**：不同 agent/项目的验证过经验可以发布到共享网络，其他 agent 直接复用
- **治理安全**：通过 Governor 控制进化速率、爆炸半径和回归检测，防止低质量策略扩散

## 核心概念

### Gene — 策略 DNA

Gene 是一条可复用的问题解决策略，从一次或多次成功经验中提取并泛化：

```json
{
  "gene_id": "g-a1b2c3d4",
  "signals": [
    {
      "signal_type": "compiler_error",
      "source": "compiler",
      "pattern": "Cannot find module '(.+)'",
      "context_hints": ["typescript", "import"]
    }
  ],
  "strategy": {
    "description": "检查 tsconfig.json paths 配置和 package.json dependencies，确认模块存在后重新安装",
    "steps": [
      "检查 tsconfig.json 中 paths 和 baseUrl 配置",
      "检查 package.json 中是否包含该依赖",
      "运行 npm install 或对应包管理器安装命令",
      "若为路径别名问题，更新 tsconfig paths"
    ],
    "constraints": ["不要直接删除 node_modules 重装，先定位根因"]
  },
  "validation_rules": {
    "success_indicator": "tsc 编译通过，无 Cannot find module 错误",
    "timeout_seconds": 120
  },
  "confidence": 0.75,
  "state": "promoted",
  "tags": ["typescript", "module-resolution", "build-error"],
  "env_fingerprint": {
    "languages": ["typescript"],
    "frameworks": ["next.js"],
    "tools": ["npm"]
  },
  "stats": {
    "total_uses": 12,
    "successes": 10,
    "failures": 2,
    "last_used": "2026-04-01T10:30:00Z"
  },
  "created_at": "2026-03-15T08:00:00Z",
  "updated_at": "2026-04-01T10:30:00Z"
}
```

**Gene 状态生命周期**：

```
candidate → promoted → archived
    ↓           ↓
  revoked    quarantined → (re-promoted | revoked)
```

| 状态 | 含义 |
|------|------|
| `candidate` | 新提取，尚未达到晋升门槛 |
| `promoted` | 经过多次验证，高置信度可用 |
| `quarantined` | 从外部导入或连续失败，需本地验证 |
| `revoked` | 多次失败或人工标记无效 |
| `archived` | 长期未使用，自动归档 |

### Capsule — 已验证经验快照

Capsule 是 Gene 的一次具体执行记录，包含完整的上下文和结果：

```json
{
  "capsule_id": "c-e5f6g7h8",
  "gene_ref": "g-a1b2c3d4",
  "execution_context": {
    "project_id": "proj-xyz",
    "agent_id": "agent-session-001",
    "trigger_signal": {
      "signal_type": "compiler_error",
      "source": "compiler",
      "raw_message": "Cannot find module '@/utils/helpers'",
      "file_path": "src/pages/index.tsx"
    }
  },
  "outcome": {
    "success": true,
    "changes_summary": "更新 tsconfig.json paths 配置，添加 @/ → src/ 映射",
    "diff_hash": "sha256:abc123...",
    "files_changed": ["tsconfig.json"],
    "lines_modified": 3,
    "duration_seconds": 15
  },
  "env_fingerprint": {
    "os": "darwin",
    "node_version": "20.x",
    "typescript_version": "5.4",
    "package_manager": "npm"
  },
  "confidence": 0.85,
  "created_at": "2026-04-01T10:30:00Z"
}
```

### EvolutionEvent — 追加式事件日志

EvolutionEvent 是不可变的事件记录，构成进化存储的唯一事实源（single source of truth）：

```json
{
  "event_id": "ev-20260401-001",
  "type": "capsule_reused",
  "timestamp": "2026-04-01T10:30:00Z",
  "agent_id": "agent-session-001",
  "payload": {
    "gene_id": "g-a1b2c3d4",
    "capsule_id": "c-e5f6g7h8",
    "success": true,
    "confidence_delta": 0.05
  }
}
```

**事件类型**：

| 类型 | 触发时机 |
|------|----------|
| `signal_detected` | 检测到错误/问题信号 |
| `gene_created` | 新 Gene 从成功经验中提取 |
| `gene_updated` | Gene 置信度、统计或状态更新 |
| `gene_promoted` | Gene 从 candidate 晋升为 promoted |
| `gene_revoked` | Gene 被标记为无效 |
| `gene_quarantined` | Gene 进入隔离区 |
| `capsule_created` | 新的执行快照产生 |
| `capsule_reused` | 已有 Capsule 被重放使用 |
| `replay_attempted` | 尝试重放但未成功 |
| `governor_blocked` | Governor 阻止了某个操作 |
| `network_published` | Gene/Capsule 发布到共享网络 |
| `network_fetched` | 从共享网络获取了资产 |

## 进化闭环流程

```
┌──────────────────────────────────────────────────────┐
│                  Evolution Loop                       │
│                                                       │
│  ① Detect  ──→  ② Select  ──→  ③ Replay             │
│     │              │              │                   │
│     │              │              ├─ 成功 → ⑥ Reuse  │
│     │              │              │                   │
│     │              │              └─ 失败 ↓           │
│     │              │                                  │
│     │              └──→  ④ Execute (LLM)              │
│     │                       │                         │
│     │                       ↓                         │
│     │               ⑤ Validate                        │
│     │                  │                              │
│     │                  ├─ 通过 → Solidify → Gene+     │
│     │                  │              Capsule          │
│     │                  └─ 失败 → 记录失败事件          │
│     │                                                 │
│     └─── Governor 全程监控速率/半径/回归 ──────────────│
└──────────────────────────────────────────────────────┘
```

1. **Detect**: 从工具调用结果（编译错误、测试失败、运行时异常）中提取结构化信号
2. **Select**: 用信号在 Evolution Store 中查询匹配的 Gene 候选
3. **Replay**: 取置信度最高的 Capsule 尝试重放其策略
4. **Execute**: 若无匹配或重放失败，走正常 LLM 推理解决问题
5. **Validate**: 验证解决方案的正确性（编译通过、测试通过等）
6. **Solidify**: 验证通过后提取 Gene + Capsule 写入进化存储
7. **Reuse**: 成功重放时记录复用事件，提升 Gene 置信度

## 存储布局

```
~/.claude/evolution/
├── events.jsonl          # 追加式事件日志（唯一事实源）
├── genes.json            # Gene 投影缓存（从 events 重建）
├── capsules.json         # Capsule 投影缓存（从 events 重建）
├── LOCK                  # 并发写入保护
├── config.json           # 本地配置（Governor 参数等）
└── shared/               # 跨 agent 共享区
    ├── published/        # 本地发布的资产
    └── quarantine/       # 外部导入的待验证资产
```

## 置信度模型

### 初始置信度

| 来源 | 初始值 |
|------|--------|
| 首次成功解决 | 0.40 |
| 从 error-experience 迁移 | 根据 success_rate 映射 |
| 从 instinct 迁移 | 保留原有 confidence |
| 从外部网络导入 | 0.30（进入 quarantine） |

### 置信度变更

```
成功复用: confidence = min(0.95, confidence + 0.05)
失败复用: confidence = max(0.10, confidence - 0.10)
时间衰减: confidence = confidence × e^(-0.001 × days_since_last_use)
手动标记: confidence = 指定值
```

### 状态晋升门槛

| 转换 | 条件 |
|------|------|
| candidate → promoted | confidence ≥ 0.60 且 successes ≥ 3 |
| promoted → quarantined | 连续失败 ≥ 3 次 |
| quarantined → promoted | 本地验证通过 2 次以上 |
| * → revoked | confidence < 0.15 或手动标记 |
| promoted → archived | 90 天未使用 |

## 信号匹配算法

信号匹配分三级：

1. **精确匹配** (score=1.0): signal_type + source + pattern 完全匹配
2. **模糊匹配** (score=0.7): signal_type + source 匹配，pattern 相似度 > 0.8
3. **上下文匹配** (score=0.4): 仅 tags 和 env_fingerprint 部分重叠

最终匹配分 = match_score × gene_confidence × env_similarity

## 命令接入

| 命令 | 用途 |
|------|------|
| `/replay <error>` | 手动查询匹配的 Gene 并尝试重放 |
| `/evolution-status` | 查看进化存储状态面板 |
| `/evolve` | 将 instinct 聚类为 Gene（升级版） |
| `/instinct-export` | 导出进化资产（升级版） |
| `/instinct-import` | 导入进化资产（升级版） |

## 与现有系统的关系

| 现有系统 | 关系 |
|----------|------|
| error-experience-library | Gene 的数据来源之一；迁移后 `/error-lookup` 仍可用，底层查询 Evolution Store |
| continuous-learning | Instinct 可晋升为 Gene；观察流程继续保留 |
| instinct-export/import | 升级为 Evolution Asset 导入导出 |
| session-end hook | 增加 solidify 调用，自动从 git diff 提取 Gene |
| session-start hook | 增加进化上下文注入 |

## 相关工具

- `scripts/evolution/store.py` — Evolution Store 读写接口
- `scripts/evolution/replay.py` — Replay-First 执行器
- `scripts/evolution/governor.py` — Governor 治理层
- `scripts/evolution/network.py` — 跨 agent 共享网络
- `scripts/evolution/migrate.py` — 从旧系统迁移数据

## 配合约束

1. 所有进化操作必须产生 EvolutionEvent，事件日志是唯一事实源
2. Gene/Capsule JSON 缓存可随时从 events.jsonl 重建
3. 外部导入的资产必须先进 quarantine，本地验证通过后才能 promote
4. Governor 可全局禁用（用于调试），但生产环境必须启用
5. 进化能力默认 opt-in，通过 hooks.json 的 enabled flag 控制
