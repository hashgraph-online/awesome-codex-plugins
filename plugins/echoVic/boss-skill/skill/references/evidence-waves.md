# Evidence Waves And Code Dispatch Safety

本文件保存 code 阶段派发前的证据门禁、写集冲突和风险确认规则。只有处理 `code` 产物或 QA/门禁风险时才需要读取。

## Repo Preflight

code 阶段规划前必须探测项目事实；在 `tasks.md` 存在前将摘要注入 Tech Lead、Scrum Master、Frontend、Backend、QA 上下文，Scrum Master 必须把摘要写入 `.boss/<feature>/tasks.md`。

必须检查：
- Git：默认分支、当前分支、是否存在未提交变更。
- CI：`.github/workflows/`、`.gitlab-ci.yml`、`.circleci/config.yml`、`vercel.json`、`netlify.toml`，以及 CI 实际执行的 lint/test/build 命令。
- 包管理与测试脚本：package manager、install 命令、test/build/lint/typecheck 脚本，确认 `npm test` 或等价命令是否包含 integration/E2E。
- 测试工具：单元、集成、E2E、浏览器自动化工具。
- 契约来源：真实 schema enum、OpenAPI/JSON Schema、Zod/Yup/Pydantic、Prisma/Drizzle、共享类型、API 路由。
- 业务常量：用户可见数值、阈值、限制、状态流转、访问策略、内容/资源策略。
- 路由与迁移：框架路由约定、destructive migrations、silent pagination/row limits、irreversible backfills。

未知事实必须写 `unknown`，并列出已检查命令或文件；不得猜测，不得用模板默认值代替。缺失 Repo Preflight 时不得派发 code Agent。

## Evidence Wave

每个 code 产物至少有一个 Evidence Wave；高 Blast Radius 功能必须拆成多个更小 Evidence Wave。每个 Wave 必须包含：
- 红测
- 绿门禁
- Contract Matrix
- Stop Condition
- 下一 Wave 依赖关系

缺任一项不得派发 code Agent。

## 任务写集冲突检测

仅 code 产物派发前执行：
- 从 `tasks.md` 解析每个 Task 的“文件输出列表 / 写集”表，提取计划创建、修改、删除的文件路径、写集风险和 owner。
- 构建任务冲突图：任意两个任务写同一文件、中央索引、依赖清单、锁文件、全局配置、`i18n.ts`、`store.ts` 等共享文件时，视为写集重叠。
- 根据显式依赖边和冲突图生成并行安全组；同一并行安全组内任务写集必须互斥，写集重叠的任务不得并行。
- Evidence Wave 是验收检查点，不等同于并行派发批次；同一 Evidence Wave 内可包含多个按依赖顺序执行的并行安全组。
- 共享文件必须指定 owner；非 owner 任务只能读取或等待 owner 完成后的后续 Wave 集成，不得同时落盘。
- 若任务缺少文件输出列表、路径仍为 `待确认`、或共享文件 owner 不明确，暂停并回派 Scrum Master 修订 `tasks.md`。

## 风险等级感知确认

仅 code 产物派发前执行：
- 从 `tasks.md` 摘要读取 `Blast Radius` 与 `风险确认触发项`；若缺失，暂停并回派 Scrum Master 补齐，不得派发 code Agent。
- 命中任一强制确认 trigger 时，在 `auto` / `interactive` 模式下必须向用户展示即将写入的文件数量、核心模块、依赖变更、安装命令和不可逆操作，并等待确认。
- 强制确认 trigger 包括：计划写入文件数达到项目阈值（默认 ≥ 10 个；项目可在 `tech-review.md` 降低阈值）、修改 `package.json`/锁文件/构建或部署配置、需要运行依赖安装命令、修改认证/支付/数据模型/迁移/权限/全局状态等核心模块、删除文件或执行不可逆操作。
- `--quick` / `--hitl-level off` 只跳过常规确认；命中强制确认 trigger 仍需显式授权。
- 未命中触发项时，记录“风险确认：未触发”并继续 D.4c。

## Wave 边界校验

同一 Wave 的并行 Agent 全部返回 `DONE` / `DONE_WITH_CONCERNS` 后，orchestrator 必须按项目技术栈选择适用校验，不能只信子代理自报：
- 运行适用的类型检查、编译检查、测试套件、lint/格式检查。
- 检查依赖清单、锁文件、构建配置等关键工程文件的 diff 摘要；不限于 Node.js，其他生态使用等价文件。
- 若项目没有可运行的自动化校验，记录原因，并至少执行文件 diff 与产物一致性检查。
- 任一适用校验失败：暂停推进，将失败摘要交给对应 Agent 修复，修复后重跑。
- 依赖清单、锁文件或构建配置出现意外 diff：orchestrator 必须确认变动是否与本 Wave 任务、Agent 报告一致。
- 只有通过 Wave 边界校验后，才允许进入后续派发、标记阶段 completed、或回到 DAG 循环。

## 术语边界

- 写集冲突检测决定能否并行派发。
- 风险等级感知确认决定是否需要用户授权。
- Evidence Wave 决定阶段性验收证据。
- 未通过任一项时不得派发 code Agent。
