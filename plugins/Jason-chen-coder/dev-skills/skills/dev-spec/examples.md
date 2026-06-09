# dev-spec · Compatibility Alias Examples

`dev-spec` 只保留旧提示兼容性。实际执行时加载 `../dev-grill-docs/SKILL.md`,并按 `dev-grill-docs --spec-only` 跑。

本文件只演示 alias 语义,不维护第二套访谈协议。完整规则以 `dev-grill-docs` 为准:

- 每轮只问一个问题。
- 不写 `CONTEXT.md`。
- 不写 `docs/adr/`。
- 仍然生成 `.claude/artifacts/designs/<feature>.md`。

---

## 例 1 — 旧入口触发,按 dev-grill-docs 单问题 wave 处理

**用户原始请求**

> 用 dev-spec 帮我做个用户导出。

**期望输出**

```text
我会把 dev-spec 当作 dev-grill-docs --spec-only 执行:
- 产物仍写到 .claude/artifacts/designs/<feature>.md
- 不更新 CONTEXT.md / ADR

Wave 1 | Focus: Goal | Ambiguity: not scored yet
Why this matters: "用户导出"可能是合规自助导出,也可能是后台运营代导,两者权限、字段和审计要求不同。
Recommended answer: 如果目标是合规/GDPR,建议选自助导出。

Question: 这次的用户导出指 (a) 当前登录用户导出自己的数据,还是 (b) 管理员在后台代用户导出?
```

注意:不要一次性把格式、字段、同步/异步、量级全部问完。继续按 `dev-grill-docs` 的 weakest-focus 规则逐轮推进。

---

## 例 2 — 用户回答后继续下一轮,仍然只问一个问题

**用户回答**

> 选 a,当前登录用户导出自己的数据。

**期望输出**

```text
Wave 2 | Focus: Scope | Ambiguity: 52%
Why this matters: 导出格式会决定 API 响应、worker、文件生成和前端下载体验。
Recommended answer: v1 先做 CSV,JSON / Excel 放到 out of scope。

Question: v1 只支持 CSV,还是同时支持 JSON / Excel?
```

---

## 例 3 — 信息足够后写 spec-only artifact

当用户逐轮确认:

- 当前登录用户自助导出。
- v1 只支持 CSV。
- 异步任务 + 邮件通知。
- 单用户可能数万行。
- 字段采用白名单。

期望写入 `.claude/artifacts/designs/user-export.md`:

```markdown
# user-export Spec

> Status: DRAFT
> Author: user
> Last updated: 2026-06-03

## Background
用户需要自助导出自己的数据,用于合规和数据可携带性场景。v1 仅覆盖当前登录用户的 CSV 异步导出。

## In scope
- 当前登录用户导出自己的数据。
- CSV 格式。
- 异步任务:用户触发 -> worker 生成文件 -> 邮件通知下载链接。
- 字段白名单。

## Out of scope
- 管理员后台代导。
- JSON / Excel。
- 增量导出。
- 跨账号合并导出。

## Assumptions
- 下载链接可使用现有 signed URL 机制。
- 邮件通知复用现有 notification service。
- 单用户数据量可能达到数万行,不走同步响应。

## Solution
新增导出任务模型和查询接口,由 worker 生成 CSV 并上传到对象存储。完成后发送邮件,用户通过 signed URL 下载。

## Edge cases & risks
| Category | Notes |
|---|---|
| Boundary conditions | 用户无数据时仍生成只有 header 的 CSV。 |
| Failure modes | worker 失败后任务进入 failed,用户可重新触发。 |
| Risks | 字段白名单不清可能导致敏感字段泄露。 |
| Mitigation | 将 CSV header 作为测试断言,禁止白名单外字段。 |

## Acceptance criteria
- AC-1 用户触发导出后,系统创建 queued export job。
- AC-2 job 完成后,用户收到包含 signed URL 的邮件。
- AC-3 CSV header 只包含字段白名单。
- AC-4 用户无数据时,下载文件仍包含 header 且无数据行。
- AC-5 JSON / Excel 请求不在 v1 暴露入口。

## Open questions
- 字段白名单最终列表待产品确认。

## Interview metadata
- Mode: --spec-only
- Waves: 4
- Final ambiguity: 28%
- Status: PASSED
```

Alias 路径到此结束:不写 `CONTEXT.md`,不写 ADR,也不主动进入 `dev-plan`。
