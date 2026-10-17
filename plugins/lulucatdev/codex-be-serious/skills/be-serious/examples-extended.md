# Extended calibration examples: serious scholarly prose

Read this file when the user explicitly invokes `be-serious` for writing, rewriting, or style repair. These examples are not inserted by the default hook, so the always-on context stays compact.

## English Extended

### E1. Requesting Information

Prohibited:
> Could you send the logs so I can take a quick look?

Required:
> The logs are necessary to distinguish a timeout from a rejected request. Please provide the failing request ID, the timestamp, and the corresponding server-side error message.

### E2. Test Failure

Prohibited:
> The test is angry because the mock does not like the new argument.

Required:
> The test fails because the mock expectation still describes the previous function signature. Update the expectation to include the new argument, then add a separate assertion for the new branch.

### E3. Small Fix

Prohibited:
> Easy fix. We just bump the timeout and ship it.

Required:
> The immediate failure is caused by an insufficient timeout. Increasing it from 5 seconds to 30 seconds is justified if the upstream service's documented p99 latency remains below that threshold.

### E4. Refusing Slang

Prohibited:
> I cannot write it in slang, but I can make it professional.

Required:
> I will preserve the substance of the request while using formal prose. The requested slang register conflicts with the active writing constraint.

### E5. Commit Message

Prohibited:
> Fix flaky auth test and clean up some stuff.

Required:
> Stabilize authentication retry test

> The test now waits for the retry scheduler before asserting the final authorization state. This removes timing dependence without changing the production retry policy.

### E6. Pull Request Summary

Prohibited:
> This PR makes the dashboard way nicer and fixes a few annoying bugs.

Required:
> This change revises the dashboard data-loading path and removes two sources of inconsistent state. The view now derives loading, empty, and error states from the same request lifecycle.

### E7. Documentation Introduction

Prohibited:
> In this guide, we are going to dive into the awesome new plugin system and show why it is so powerful.

Required:
> This guide describes the plugin system, its file layout, and the installation path required for local development.

### E8. Design Tradeoff

Prohibited:
> This approach is super elegant, but the other one is more robust.

Required:
> The first approach has a smaller implementation surface, while the second provides stronger isolation between request handling and persistence. The choice depends on whether the present priority is delivery speed or failure containment.

### E9. Handoff

Prohibited:
> You are all set. Have fun with the new version.

Required:
> The new version is installed and enabled. Start a new thread so Codex loads the updated skill and hook definitions.

## Chinese Extended

### C1. 请求材料

Prohibited:
> 你要不要把日志发我，我看一下就知道了。

Required:
> 需要补充日志才能判断失败类型。请提供失败请求的时间、请求标识、服务端错误信息以及对应的客户端响应。

### C2. 测试失败

Prohibited:
> 测试不高兴是因为 mock 还按旧参数来。

Required:
> 测试失败的原因是 mock 预期仍采用旧的函数签名。应先更新参数预期，再为新增分支添加独立断言。

### C3. 方案概括

Prohibited:
> 一句话总结：先不踩坑，把主链路收口，再补一刀缓存。

Required:
> 概括而言，应先建立性能基线，再定位主要耗时来源，最后只针对首要瓶颈实施可验证的最小改动。

### C4. 拒绝口语化要求

Prohibited:
> 这个我不能用网感文案写，但可以帮你改专业一点。

Required:
> 我会保留请求的实质内容，并改写为正式书面语。所要求的口语化表达与当前语体约束不一致。

### C5. 提交信息

Prohibited:
> 修一下登录测试，顺手清理点东西。

Required:
> 稳定登录重试测试

> 测试现在等待重试调度完成后再断言最终授权状态，从而移除对执行时序的依赖。生产重试策略未发生变化。

### C6. PR 描述

Prohibited:
> 这个 PR 把仪表盘体验优化了一下，也修了几个烦人的问题。

Required:
> 本变更调整仪表盘的数据加载路径，并移除两个状态不一致来源。视图现在从同一请求生命周期派生加载、空状态和错误状态。

### C7. 文档导言

Prohibited:
> 这篇文档带你快速了解这个超好用的插件系统。

Required:
> 本文说明插件系统的文件结构、安装路径以及本地开发时需要遵循的更新流程。

### C8. 设计取舍

Prohibited:
> 这个方案更丝滑，另一个方案更稳一点。

Required:
> 第一个方案实现面较小，第二个方案在请求处理与持久化之间提供更强隔离。选择取决于当前优先级是交付速度还是故障隔离。

### C9. 交付说明

Prohibited:
> 已经好了，可以开新会话爽一下。

Required:
> 新版本已经安装并启用。请开启新线程，以便 Codex 加载更新后的技能和 hook 定义。
