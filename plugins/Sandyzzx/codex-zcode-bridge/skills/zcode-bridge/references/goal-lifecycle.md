# Goal 与持续目标

> Status: AUTHORITATIVE
> Last updated: 2026-11-11
> Last verified: 2026-11-11，核对入口授权边界与当前线程 Goal 语义；真实跨轮模型行为 NOT RUN。
> Verified against: 372e90622772b070357a278f1da3dea58fa42dee（基线；本候选离线证据见 docs/research/master-skill-simplification-20261111.md）

本文件只处理已由入口确认的持续 Bridge 授权。已有 Goal 或普通持续开发请求本身不授权调用 Bridge；当前线程已有覆盖同一目标的活动 Goal 时核对沿用，不重复创建。

- 用户明确要求跨轮持续推进当前目标时，在首个 ZCode 任务派发前调用 `create_goal`。Goal 写明授权最终结果、独立验收、改动接收条件和停止条件；不扩大授权，除非用户明确要求不设置 token budget。
- 单次有边界委派或一次性问答不创建 Goal。当前环境没有 Goal 工具时如实说明无法启用持久续行。
- Goal 属于当前线程并保持活动，直到最终目标经证据核验完成：必要任务终态、改动独立审查、适用验证和授权范围内接收均完成。Bridge `completed` 或 Worker 报告不是完成条件。
- 当前轮结束时任务仍运行则保留 Goal 并说明状态；用户要求停止时遵从。不要把中间状态写成最终结论或自行暂停 Goal。
