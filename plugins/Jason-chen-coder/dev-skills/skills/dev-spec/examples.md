# dev-spec · Examples

具体反例集。SKILL.md 描述了规则,本文件给真实的 fuzzy request → ambiguity list → final spec,让实际输出对齐这里的笔法。

模式说明:

- 例 1–3 演示 `--quick` 模式行为(单轮列歧义)。
- 例 4 演示 `--default` 模式(多 wave + 打分,简单需求 wave 1–2 即达标)。
- 例 5 演示 `--deep` 模式(多 wave + Challenge modes + Ontology 跟踪)。

---

## 例 1 — 模糊需求 → 歧义清单(Step 1 输出)

**用户原始请求**

> 帮我做个用户导出。

**期望 Step 1 输出**

```
执行 dev-spec 之前,我对以下 5 点不确定,请确认:

1. 导出谁的数据?
   (a) 当前登录用户的自有数据(GDPR 自助导出)
   (b) 管理员导出任意用户(后台运营功能)
   (c) 其他:你说

2. 导出什么字段?
   (a) 全部字段(含敏感)
   (b) 一个白名单子集 —— 由我列默认清单等你审
   (c) 其他

3. 导出格式?
   (a) CSV  (b) JSON  (c) Excel  (d) 多选

4. 同步还是异步?
   (a) 同步(< 5s,直接返回文件)
   (b) 异步(任务排队 + 邮件/通知拿下载链接)

5. 量级预期?
   (a) 单用户 < 1000 行 —— 同步够用
   (b) 单用户可能数万 —— 必须异步
   (c) 不确定 —— 我先按 1000 行 / 同步设计,后续按量级加异步路径

回答后我会进入 spec 生成。
```

注意:**不要直接开始写 spec**。这一步必须先要用户回答。

---

## 例 2 — 用户回答后的 spec(Step 6 artifact)

延续例 1。用户回答:

> 1=a(自助导出),2=b(等你列白名单),3=a(CSV),4=b(异步),5=b(数万)

**期望生成的 artifact** `.claude/artifacts/designs/user-export.md`:

```markdown
# user-export Spec

> Status: DRAFT
> Author: gli
> Last updated: 2026-04-29

## Background
GDPR 合规要求用户能自助导出自有数据。当前需求方为合规团队,
预期 1.5 个月内上线 v1。

## In scope
- 当前登录用户对自有数据的导出请求
- 异步任务模型:用户触发 → 后台 worker 生成 → 邮件通知下载链接
- CSV 格式,固定字段白名单(见下)
- 下载链接 7 天有效,带 signed URL

## Out of scope
- 管理员代用户导出(后台运营功能,另起 spec)
- JSON / Excel 格式(v2 再说)
- 增量导出(v1 一律全量)
- 跨租户 / 多账号合并导出

## Assumptions
- 单用户数据量 ≤ 50 万行,worker 单任务可在 10 分钟内完成
- 邮件投递走现有 notification-service,不新建通道
- 下载存储复用现有 S3 bucket `user-exports/`,生命周期已配置

## Solution

**数据模型**(新增)
- `export_job` 表:id, user_id, status (queued|running|done|failed), created_at, completed_at, file_url, expires_at

**字段白名单(CSV 列)**
profile.id, profile.email, profile.created_at, profile.locale,
order.id, order.created_at, order.status, order.total

**流程**
1. POST /api/me/exports → 创建 export_job(status=queued),返回 job_id
2. worker 监听队列 → status=running → 拉数据 → 写 CSV → 上传 S3 → status=done
3. notification-service 监听 status=done 事件 → 发邮件含 signed URL
4. GET /api/me/exports/:id → 查询任务状态

**变更面**
- 新增表 export_job
- 新增 worker `services/export-worker/`
- 新增 2 个 API endpoint
- notification-service 新增 1 个 template

## Edge cases & risks

| 类目 | 内容 |
|---|---|
| 边界 | 用户无任何数据 → 仍生成空 CSV(只含 header),不报错 |
| 失败 | worker 拉数据中途失败 → status=failed,记录 error_msg,允许用户重试 |
| 重复 | 用户连点多次「导出」→ 同一用户 24h 内只允许 3 个并发任务,超过返回 429 |
| 风险 | 数据量超预期(> 50 万行)→ 任务超时,需要 monitoring 告警 + 后续支持分片 |
| 缓解 | 加 export_job.duration metric;> 10min 任务 PagerDuty 告警 |

## Acceptance criteria

- AC-1  用户在 UI 触发导出 → 1s 内返回 job_id 且 status=queued
- AC-2  job 完成后 → 用户在 60s 内收到邮件,邮件含可访问的 signed URL
- AC-3  下载的 CSV 行数 == 该用户实际记录数,字段顺序固定为白名单顺序
- AC-4  字段不包含白名单外的列(用 grep 校验 header)
- AC-5  signed URL 在 7 天后访问返回 403
- AC-6  同用户 24h 内第 4 次触发 → 返回 429,error code = `EXPORT_RATE_LIMIT`

## Open questions
- 邮件模板的 i18n 是否覆盖全部支持语言?(待 PM 确认)
- 失败任务是否自动重试一次?(暂定不自动,等用户手动)
```

---

## 例 3 — 看似清晰、实际仍需 Step 1

**用户原始请求**

> 把搜索做快一点。

很多人看到这种请求会直接跳进方案。但 baseline「不假设」要求**仍走 Step 1**:

**期望输出**

```
「做快一点」可以指多件事,我对以下 3 点不确定:

1. 优化目标?
   (a) 降低 P95 响应时间(后端慢)
   (b) 改善前端感知(loading 闪烁、防抖)
   (c) 提升吞吐(QPS 撑得更高)

2. 现状基线是多少?
   (a) 我有现成 metrics,可以贴一下数字
   (b) 没有 metrics —— 那 spec 第一步是先加 metrics,再优化

3. 可以接受多大改动面?
   (a) 仅查询层加索引/缓存(改动小)
   (b) 重写检索引擎(例:换 Elasticsearch)
   (c) 用户体验层兜底(skeleton + optimistic UI)

回答后我会进入 spec 生成。
```

未回答前**不写 spec**,即使能猜出方向。

---

## 例 4 — `--default` 模式(简单需求 Wave 2 即达标)

**用户原始请求**

> --default 帮我写个 spec,要给后台加个「禁用用户账号」的按钮。

### Wave 1(初始,无打分)

```
Wave 1 | 初始访谈
ambiguity 暂未计算(还没有对话基础)。

问题: 「禁用账号」具体指什么状态?
   (a) 软禁用 —— 标记 disabled,数据保留,可恢复
   (b) 硬删除 —— 数据清理,不可恢复
   (c) 其他:你说
```

**用户答**:a,软禁用,可恢复。

### Wave 2(打分 + 选下一题)

```
Wave 2 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.8 | 0.43 | 0.344 | 「可恢复」由谁触发未明 |
| Scope | 0.5 | 0.28 | 0.140 | 是否要审计日志、是否要通知用户都未定 |
| AC | 0.6 | 0.29 | 0.174 | 缺数字目标 |
| **Ambiguity** | | | **34.2%** | (greenfield) |

Ontology: User, Account (Wave 1 没记 → Wave 2 全 new,stability N/A)

下一目标: Scope (0.5) — 因为 in/out 边界还没列出。
   具体瓶颈:本次是否要审计 + 是否要通知用户。

问题: 触发「禁用」时,是否要做以下两件事?
   - 写 audit log(谁禁用、什么时候、原因)
   - 给用户邮件 / 站内通知
   选项:(a) 都做  (b) 只做 audit  (c) 只做通知  (d) 都不做
```

**用户答**:a,都做。

### Wave 3(达标,退出)

```
Wave 3 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.9 | 0.43 | 0.387 | clear |
| Scope | 0.85 | 0.28 | 0.238 | clear |
| AC | 0.8 | 0.29 | 0.232 | clear |
| **Ambiguity** | | | **14.3%** | ≤ 30% 阈值 ✓ |

Ontology: User, Account, AuditLog (vs Wave 2: 2 stable, 1 new — stability 67%)

✓ Ambiguity 达标(14.3% ≤ 30%),进 Step 2。
```

**最终 spec 节选(.claude/artifacts/designs/disable-user.md)**

```markdown
## In scope
- 后台用户列表新增「禁用」操作按钮
- 软禁用:标记 user.status = 'disabled',登录时拒绝并显示已禁用
- 写 audit_log(operator_id, target_user_id, action, reason, timestamp)
- 给被禁用用户发邮件 + 站内通知

## Out of scope
- 硬删除用户数据
- 批量禁用
- 自动解禁(必须手动操作)

## Acceptance criteria
- AC-1  管理员点禁用 → 1s 内 user.status 变 disabled,目标用户当前 session 失效
- AC-2  被禁用用户尝试登录 → 返回 403,error_code = ACCOUNT_DISABLED
- AC-3  禁用操作必产生 audit_log 行,字段齐全
- AC-4  被禁用用户 60s 内收到邮件 + 站内通知

## Interview metadata
- Mode: --default
- Waves: 3
- Final ambiguity: 14.3%
- Status: PASSED

### Clarity breakdown
| 维度 | 分数 | 权重 | 加权 |
|---|---|---|---|
| Goal | 0.9 | 0.43 | 0.387 |
| Scope | 0.85 | 0.28 | 0.238 |
| AC | 0.8 | 0.29 | 0.232 |

## Core entities
| Entity | 类型 | 关键字段 | 关系 |
|---|---|---|---|
| User | core | id, email, status | has many AuditLog |
| AuditLog | supporting | operator_id, target_user_id, action, reason, ts | references User |
```

注意:`--default` 模式 spec 包含 `Interview metadata` 但**省略 Ontology convergence 表**(那是 deep 模式才有)。

---

## 例 5 — `--deep` 模式(复杂需求 + Challenge modes + Ontology 漂移)

**用户原始请求**

> --deep 我们想做个「智能任务系统」,帮员工自动安排日程。

### Wave 1

```
Wave 1 | 初始

问题: 「智能任务系统」核心做什么?
   (a) 把已有 todo 重新排序 / 提醒
   (b) 把会议、邮件、任务跨源聚合 + 排程
   (c) 类似 AI agent,主动建议下一步该做什么
   (d) 其他
```

**用户答**:b + c 混合,要聚合 + 主动建议。

### Wave 2(打分,Goal 仍弱)

```
Wave 2 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.4 | 0.40 | 0.160 | 「主动建议」边界不明,是 push 还是 pull |
| Scope | 0.3 | 0.25 | 0.075 | 数据源未列 |
| AC | 0.2 | 0.25 | 0.050 | 完全没定 |
| Context | 0.5 | 0.10 | 0.050 | 未确认是新建还是接现有日历 |
| **Ambiguity** | | | **66.5%** | (brownfield) |

Ontology: Task, Schedule (Wave 1 是 Task → 此轮加 Schedule,1 new)

下一目标: AC (0.2) — 因为「主动建议」如果没有验证条件,后续没法判定是否成功。

问题: 「主动建议」对用户的可见形式是什么?
   (a) 早上推送一份「今天建议日程」,用户接受/拒绝
   (b) 实时弹窗,用户接到新事件时立刻提示
   (c) 仪表盘上显示一个「下一步」推荐区域,被动查看
```

**用户答**:a。

### Wave 3 — Contrarian mode 激活

```
Wave 3 | 瞄准: Goal | 激活 Contrarian | Ambiguity: 52%

Contrarian rationale: 主目标仍模糊(0.5)。我先挑战核心假设而不是补细节,
看看「主动建议」是不是必须的。

问题: 你说「智能 + 自动安排」,但如果只做(b)聚合 + 显式排序、不做(c)主动建议,
团队是否仍然受益?如果是,(c) 是不是 v1 必需?
```

**用户答**:对,聚合本身就够价值,主动建议可以延后到 v2。

### Wave 4(scope 大幅收窄,ambiguity 显著下降)

```
Wave 4 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.85 | 0.40 | 0.340 | clear |
| Scope | 0.7 | 0.25 | 0.175 | 数据源数量未定 |
| AC | 0.6 | 0.25 | 0.150 | 接收冲突 detection 的判定标准未列 |
| Context | 0.6 | 0.10 | 0.060 | 待确认是否接现有日历 |
| **Ambiguity** | | | **27.5%** | (brownfield) |

Ontology: Task, Event, ScheduleSlot, ConflictHint (vs Wave 3 的 Task, Schedule, Suggestion:
   - Schedule renamed → ScheduleSlot (语义相同)
   - Suggestion removed (主动建议被砍)
   - Event, ConflictHint new
   stability ratio: 50% — 概念正在重构,不要急着结束)

下一目标: AC (0.6) — 冲突检测的判定标准未列。

问题: 系统检测到日程冲突时,「冲突」的判定标准是什么?
   (a) 时间重叠(任意分钟数)
   (b) 时间重叠 ≥ 5 分钟
   (c) 跨地点 + 时间重叠
   (d) 其他
```

**用户答**:b。

### Wave 5 — Simplifier mode 激活

```
Wave 5 | 瞄准: Scope | 激活 Simplifier | Ambiguity: 18%

Simplifier rationale: ambiguity 已接近阈值,但 Scope 仍有「数据源数量未定」一项。
v1 用最少数据源能跑就好,不要一上来覆盖所有源。

问题: v1 接哪些数据源?
   (a) 只接 Google Calendar
   (b) Google Calendar + Outlook
   (c) GCal + Outlook + Slack 提到的事件
   (d) 全部 + 自定义任务
```

**用户答**:a,v1 只接 GCal,验证价值后再扩。

### Wave 6(达标退出)

```
Wave 6 完成。

| 维度 | 分数 | 权重 | 加权 | gap |
|---|---|---|---|---|
| Goal | 0.9 | 0.40 | 0.360 | clear |
| Scope | 0.9 | 0.25 | 0.225 | clear |
| AC | 0.85 | 0.25 | 0.213 | clear |
| Context | 0.7 | 0.10 | 0.070 | clear |
| **Ambiguity** | | | **13.2%** | ≤ 20% ✓ |

Ontology: Task, Event, ScheduleSlot, ConflictHint (vs Wave 4: 4 stable, 0 new — stability 100%)

✓ Ambiguity 达标 + Ontology 连续稳定 → 进 Step 2。
```

### Spec metadata 节选

```markdown
## Interview metadata
- Mode: --deep
- Waves: 6
- Final ambiguity: 13.2%
- Status: PASSED
- Challenges used: Contrarian (Wave 3), Simplifier (Wave 5)

### Ontology convergence
| Wave | Entities | New | Renamed | Stable | Stability% |
|---|---|---|---|---|---|
| 1 | 1 (Task) | 1 | - | - | N/A |
| 2 | 2 (+ Schedule) | 1 | 0 | 1 | 50% |
| 3 | 3 (+ Suggestion) | 1 | 0 | 2 | 67% |
| 4 | 4 (Task, Event, ScheduleSlot, ConflictHint) | 2 | 1 | 1 | 50% |
| 5 | 4 | 0 | 0 | 4 | 100% |
| 6 | 4 | 0 | 0 | 4 | 100% |

## Open questions
- 是否接现有 GCal API quota?(Wave 4 Context 仍 0.7,留待 Step 2 之外讨论)
```

注意 Wave 3 的 Contrarian 是这次访谈最关键的一步 —— 它让原本要做「智能 agent」的需求收窄到「日程聚合」,直接砍掉了 v1 的最大复杂度。**这正是 challenge mode 的产品价值**:不是问更多细节,而是质疑大方向。

---

## 反模式备忘(不要这样写 spec / 跑 interview)

- ❌ Step 1 跳过 —— 任何模式都不能跳列歧义。
- ❌ default / deep 模式批量提问 —— 一次只能问一个,等回答后再选下一题。
- ❌ 不输出 round report —— 用户必须看见每轮的分数表 + 下一目标 + rationale。
- ❌ ambiguity 仍 > 阈值时强行进 Step 2(除非用户明确说「够了」并接受 warning)。
- ❌ Acceptance criteria 写「performs well」「user-friendly」 —— 不可验证。
- ❌ Solution 段画大饼 —— 「未来可扩展为分布式」属于 out-of-scope,删。
- ❌ Out of scope 留空 —— 总有不做的东西,写出来。空白意味着没认真想。
- ❌ 替用户选了技术栈 —— 「我决定用 Redis 做缓存」要列成选项让用户选,除非用户原话指定。
- ❌ Spec 超过两屏 —— 超长 spec 通常是把 v2/v3 也塞进来了,删到只剩本次 delivery。
- ❌ Brownfield 不做 pre-flight 就问代码自答的事(「你用什么数据库?」)。
- ❌ Challenge mode 用了不止一次 —— 每个 mode 一轮就该用完。
