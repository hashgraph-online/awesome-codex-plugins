# dev-plan · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实 spec → plan 的样例,让实际输出对齐这里的笔法。

模式说明:

- 例 1 演示 `--quick` 模式(小改动单 pass,无 Architect/Critic)。
- 例 2 演示**默认模式**完整 Planner → Architect → Critic loop,1 次迭代后 APPROVED。
- 例 3 演示 `--deliberate` 模式 + 高风险信号触发 + 2 次迭代后 APPROVED + Pre-mortem + Expanded test plan。

---

## 例 1 — `--quick` 模式(小改动)

**用户原始请求**

> --quick 给后台加个清空 Redis 缓存的按钮,只有 superadmin 能看到。

**期望产出 `.claude/artifacts/plans/admin-flush-cache.md`**

```markdown
# admin-flush-cache Implementation Plan

> Status: APPROVED
> Source: user request(无 spec,改动 < 3 文件 / < 100 行)
> Mode: --quick
> Iterations: 1 / 1

## Requirements summary
后台 admin 控制台增加「清空 Redis 缓存」按钮,仅 superadmin 角色可见。

## Acceptance criteria
- AC-1  superadmin 登录 → 后台导航栏显示「Flush Cache」按钮
- AC-2  非 superadmin 角色登录 → 该按钮不渲染(后端也拒绝调用)
- AC-3  点击按钮 → 弹确认框,确认后调用 POST /admin/cache/flush,返回 200 + 清理 entry 数
- AC-4  audit_log 写入一条 (operator_id, action='cache_flush', ts)

## Implementation steps
1. 后端:`api/admin/cache.py:1-30` 新增 POST /admin/cache/flush handler,检查 role == superadmin
2. 后端:`services/audit.py:42` 复用现有 audit_log 写入接口,新增 action 类型 'cache_flush'
3. 前端:`web/admin/Sidebar.tsx:88` 在 superadmin 条件渲染区加按钮
4. 前端:`web/admin/CacheActions.tsx`(新文件)按钮 + 确认弹框 + API 调用

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| 误清生产缓存导致冷启动 | 必须二次确认弹框 + audit log 全量 |
| 权限绕过(前端隐藏按钮但 API 没拦) | AC-2 强制前后端双校验 |

## Verification steps
- AC-1/2: 手动以两个角色登录,看 UI
- AC-3: curl POST /admin/cache/flush 带 superadmin token,验证返回结构
- AC-4: 触发后查询 audit_log 表,确认有对应 entry

## Quick mode rationale
改动 < 100 行 / 4 个文件,无架构选型,无 ≥ 2 选项分歧。跳过 Architect/Critic loop,
直接出最小可行 plan。
```

---

## 例 2 — 默认模式(完整 1 次迭代)

**用户原始请求**

> 出个 plan,基于 dev-grill-docs 那个 user-export spec。

**Step 1**:加载 `.claude/artifacts/designs/user-export.md`,读取 In scope / Out of scope / AC / Core entities。

**Step 3 — Planner draft v1**

```
## Planner draft v1

### Principles
- 跟随 spec In scope:仅自助导出
- 异步任务 + 邮件通知,与现有 notification-service 保持一致
- 失败可重试,不引入新存储

### Decision drivers
- 上线时间(GDPR 合规截止 1.5 月内)
- 与现有 worker 框架一致(运维成本)
- 存储复用 S3 已有 bucket(无新基础设施)

### Viable options
**Option A: 复用现有 worker 框架(Sidekiq-style)**
- 实现思路:在 services/export-worker/ 加新 job 类型 'user_export'
- 改动文件:services/export-worker/jobs/user_export.rb (新), services/api/exports_controller.rb (新)
- Pros: 与团队栈一致;无新基础设施;监控复用
- Cons: 队列堆积可能延迟其他任务

**Option B: 单独起个 export-service**
- 实现思路:新建独立服务,只处理导出
- 改动文件:services/export-service/ (新目录)
- Pros: 隔离失败影响面;可独立扩缩容
- Cons: 新服务运维成本;1.5 月内可能赶不上

### Implementation steps (基于 Option A)
1. services/export-worker/jobs/user_export.rb 新增 job 类
2. services/api/controllers/exports_controller.rb 新增 POST /api/me/exports + GET /api/me/exports/:id
3. db/migrate/20260429_create_export_jobs.rb 新建 export_job 表
4. services/notification/templates/export_ready.erb 新邮件模板
5. config/sidekiq.yml 加新 queue 'exports',并发 2

### Open questions
- 是否需要为 export queue 单独配 worker pool?(Option A 默认共享)
```

**Step 4 — Architect challenge v1**

```
## Architect challenge v1

### Steelman against favored option (A)
最强反方:1.5 月窗口内上线 OK,但 Option A 把导出和其他业务任务塞同一个 Sidekiq 进程。
**最坏情况**:某个用户有 50 万订单,导出任务跑 10 分钟,期间其他重要任务(订单确认邮件、
支付回调)都被压在队列后面。这是隐性的可用性风险。

如果反驳成立,plan 应改为:
- 即使用 Option A 框架,**必须为 'exports' queue 起独立 worker pool**(不共享其他 queue 的 worker)
- 给单任务超时熔断:超过 10 分钟自动 fail + 标记重试

### Tradeoff tensions
- **速度上线 vs 隔离性**:1.5 月赶上线倾向 Option A,但隔离性弱;Option B 隔离好但赶不上
- **运维简单 vs 队列治理**:Option A 复用现有 Sidekiq 简单,但需要额外队列治理(独立 worker pool / 超时 / 限流)

### Synthesis path
Option A + 强约束:**独立 worker pool + 单任务超时 + 限流(单用户 24h 内 ≤ 3 任务)**
这些约束基本消除 Option A 的核心 con,同时保留上线速度。

### Principle violations
无明显违反。
```

**Step 5 — Critic verdict v1**

```
## Critic verdict v1

| 维度 | 状态 | 备注 |
|---|---|---|
| Principle consistency | ✓ | favored option 与 principles 对齐 |
| Alternative exploration | ✓ | A/B 真候选,各有 pros/cons |
| Risk mitigation clarity | ✗ | Architect 提出的「队列堵塞」风险未在 risks 表 |
| AC testability | ✓ | spec 继承的 AC 全部可验证 |
| Verification concreteness | ⚠ | AC-2(下载链接 60s 内收到)缺验证步骤 |
| File/line coverage | ✓ | 5 步实施全 cite 文件 |

### Verdict: REVISE

待改项:
1. Risks 表加一条「export queue 堵塞影响其他业务任务」+ 对应 mitigation(独立 worker pool / 超时 / 限流)
2. Verification 段补 AC-2 的具体验证方法(模拟用户触发 → 监听邮件队列 → 测时延)
3. Implementation steps 加入 Architect 提出的 synthesis 约束(独立 worker pool + 超时 + 限流)
```

**Step 6 — 回到 Planner v2,合入 Critic 反馈**(略,迭代 1 次后达 APPROVED)

**最终 plan 节选**

```markdown
# user-export Implementation Plan

> Status: APPROVED
> Source: .claude/artifacts/designs/user-export.md
> Mode: (default)
> Iterations: 2 / 3

## Acceptance criteria
(从 spec 继承 AC-1 ~ AC-6)

## Implementation steps
1. config/sidekiq.yml — 新建独立 queue 'exports' + 独立 worker pool(并发 2)
2. services/export-worker/jobs/user_export.rb — 新 job + 10 分钟超时 + 单用户限流
3. services/api/controllers/exports_controller.rb — 新增 endpoints + 限流校验
4. db/migrate/20260429_create_export_jobs.rb — 新表
5. services/notification/templates/export_ready.erb — 新邮件模板
6. monitoring/sidekiq.yml — exports queue 添加堵塞告警(等待时间 > 30s 报警)

## Risks & mitigations
| Risk | Mitigation |
|---|---|
| Export 任务长时间运行堵塞其他业务 | 独立 worker pool;单任务 10 分钟硬超时 |
| 用户连点导致队列爆 | 单用户 24h 内 ≤ 3 任务,超过返回 429 |
| S3 上传失败 | job 重试 3 次;持续失败标记 status=failed + 通知 |
| 邮件投递失败 | notification-service 自动重试;UI 仍可查询 status 拿 URL |

## Verification steps
- AC-1: curl POST /api/me/exports → 验证 1s 内返回 job_id
- AC-2: 模拟触发 + 监听邮件 queue + 测时延(应 < 60s 投递)
- AC-3/4: pytest 测 CSV 行数 + 列名 + 不含白名单外字段
- AC-5: 启动 export → 等 7 天后(测试可改 expires_at)→ curl signed URL → 验证 403
- AC-6: 同用户 4 次连发 → 第 4 次返回 429 + ECODE='EXPORT_RATE_LIMIT'

## ADR

- **Decision**: 复用现有 Sidekiq 框架 + 独立 worker pool + 单任务超时 + 单用户限流
- **Drivers**: 上线时间(GDPR 合规)/ 与现有栈一致 / 存储复用
- **Alternatives considered**:
   - Option A(原版,共享 worker pool)— rejected,Critic 认为隔离性不够
   - Option B(独立服务)— rejected,1.5 月窗口赶不上
- **Why chosen**: 在保留上线速度的前提下,通过 Architect 提出的 synthesis 约束(独立 pool + 超时 + 限流)消除了 Option A 的核心 con
- **Consequences**:
   + 上线速度有保障
   + 与现有运维体系一致
   - 增加 1 个 queue 治理成本(监控告警新规则)
   - 未来若导出体量爆增,可能仍需要拆为独立服务(届时再 ADR)
- **Follow-ups**:
   - export queue P95 等待时间监控(grafana 面板)
   - v2 评估:是否需要拆为独立 service(基于 v1 实际负载数据)

## Review trail
- Planner draft v1: 复用 Sidekiq + 共享 worker
- Architect challenge v1: 队列隔离性不够,可能堵塞其他业务
- Critic verdict v1: REVISE — 缺 risk + 缺验证步骤 + 未吸收 synthesis
- Planner draft v2: 加独立 worker pool + 超时 + 限流 + 监控
- Architect challenge v2: tradeoff 已平衡,无新意见
- Critic verdict v2: APPROVED with 2 improvements applied
- Final iterations: 2 / 3
```

---

## 例 3 — `--deliberate` 模式(高风险触发)

**用户原始请求**

> --deliberate 给现有 user 表加 phone_number 列,要做迁移,影响 5000 万行。

**自动检测**:数据迁移 + 大表 → 高风险信号 → 即使用户没显式 deliberate 也应升模式。本例用户已加 `--deliberate`,跳过自动判断。

**Step 3 — Planner draft v1(节选)**

```
### Viable options

**Option A: 在线迁移(零停机)**
- 实现:add column → 后台 backfill → 加 NOT NULL constraint
- Pros: 零停机
- Cons: 多步骤,中间状态复杂

**Option B: 维护窗口迁移(短停机)**
- 实现:停 write → ALTER TABLE → 重启
- Pros: 简单,一步到位
- Cons: 需要维护窗口(对 5000w 行表 ALTER 可能 30 分钟)
```

**Step 5 — Critic verdict v1**

```
### Verdict: REJECT (deliberate mode 缺关键内容)

待改项:
1. **缺 Pre-mortem** —— deliberate 模式必填 3 个 failure scenarios
2. **缺 Expanded test plan** —— deliberate 模式必填 unit/integration/e2e/observability
3. AC 没明确「迁移完成」的判定(行数核对?spot check?)
```

**Step 6 → Planner v2 补全 → Critic v2 APPROVED**

**最终 plan 包含**(deliberate 特有):

```markdown
## Pre-mortem

1. **Scenario**: 在线 backfill 跑了 6 小时,中途因 DB 主备切换中断,部分行留有 NULL phone_number
   **Trigger**: backfill 脚本无幂等性,重跑会重复处理
   **Mitigation**: backfill 脚本必须**幂等**(WHERE phone_number IS NULL);加 checkpoint 表记录进度

2. **Scenario**: 加 NOT NULL constraint 时发现仍有 N 行未 backfill,DDL 失败回滚
   **Trigger**: backfill 漏行(可能新写入的行)
   **Mitigation**: 加 constraint 前**强制全表扫描** SELECT COUNT(*) WHERE phone_number IS NULL;若 > 0 不允许 DDL

3. **Scenario**: 应用代码读 phone_number 时假设非空,但迁移期间仍有 NULL,导致 NPE
   **Trigger**: 应用代码 deploy 时机早于 backfill 完成
   **Mitigation**: 应用代码 v1 必须 nullable-safe;backfill 完成后再 deploy v2(假设非空)

## Expanded test plan

- **Unit**:
  - backfill 脚本的幂等性单测(重跑 N 次结果一致)
  - 数据生成函数的边界(空字符串 / 国际格式 / 特殊字符)

- **Integration**:
  - 迁移脚本在 staging 环境对 1000 万行子集跑通
  - 检查迁移前后 row count 一致 + spot check 100 行 phone_number 字段值

- **E2E**:
  - 应用 v1(nullable-safe)在 staging 跑全链路,验证读 / 写 phone_number 正常
  - 应用 v2(假设非空)在 staging 跑全链路,验证迁移完成后无 NULL 错误

- **Observability**:
  - backfill 进度 metric:已处理行数 / 总行数,Grafana 面板
  - DB 慢查询监控:迁移期间长 SQL 阈值降到 500ms
  - 应用错误率告警:迁移窗口内 NPE / NullPointerException 率 > baseline 2x 报警
```

注意 **Critic 在 deliberate 模式下的强约束** —— 没有 pre-mortem 和 expanded test plan 直接 REJECT。这就是 deliberate 模式存在的意义。

---

## 反模式备忘(不要这样跑 dev-plan)

- ❌ **请求模糊就硬上** —— 应停下提示用户先 `dev-grill-docs`,不要拼凑 spec 替用户做需求决策。
- ❌ **只列 1 个 option 而无 invalidation rationale** —— 违反 baseline「不假设」,RALPLAN-DR 强制 ≥ 2 或显式说明为什么砍。
- ❌ **Planner / Architect / Critic 写在一起** —— 三个 pass 必须**单独成节**,不能让用户分不清谁说了什么。
- ❌ **Architect 走形式** —— 没有 steelman、没有 tension 就是没干活,Planner 该回去重写。
- ❌ **Critic 软通过** —— 看见明显 vague 的 risks / verification 还说 APPROVED,Critic 失职。
- ❌ **3 次迭代后还硬循环** —— 达上限就 BELOW_CONSENSUS_THRESHOLD 收手,不要无限磨。
- ❌ **deliberate 模式漏 pre-mortem / expanded test plan** —— Critic 必须 REJECT,这是 deliberate 模式的最小定义。
- ❌ **Implementation steps 写「重构 X 模块」** —— 必须 cite 具体文件 / 行号,80% 起。
- ❌ **替用户调起其他 skill** —— plan 完成就停,不要 invoke `dev-code-review` 或别的。dev-skills 松耦合。
