# 质量门禁

Boss Harness Gate Engine 提供三层程序化门禁，由 `boss runtime evaluate-gates` 统一调度。
所有门禁结果都会先追加到 `.meta/events.jsonl`，再物化到只读的 `.meta/execution.json` read model 中。

## Gate 0：代码质量（开发完成后，测试执行前）

入口：`boss runtime evaluate-gates <feature> gate0`

- [ ] TypeScript / 类型检查编译无错误
- [ ] Lint（ESLint / Biome / Ruff）检查通过，无 error 级别问题
- [ ] 无已知高危依赖漏洞

自动检测逻辑：
- 若存在 `tsconfig.json` → 执行 `tsc --noEmit`
- 若存在 Biome/ESLint/Ruff 配置 → 执行对应 lint
- 若存在 `package.json` → 执行 `npm audit` 检查高危漏洞

## Gate 1：测试（QA 执行后，部署前）

入口：`boss runtime evaluate-gates <feature> gate1`

阶段 3 完成后，必须全部通过才能进入阶段 4。

- [ ] 单元测试全部通过
- [ ] 测试覆盖率 ≥ 70%
- [ ] 无 P0/P1 级别 Bug
- [ ] E2E 测试已编写并通过
- [ ] 集成测试通过

自动检测逻辑：
- 自动识别测试框架：Vitest / Jest / pytest / cargo test / go test
- 自动解析覆盖率报告（coverage-summary.json / coverage.json / coverage.out）
- 自动识别 E2E 框架：Playwright / Cypress

## Gate 2：性能（部署前，仅适用于 Web 项目）

入口：`boss runtime evaluate-gates <feature> gate2`

- [ ] 前端：Lighthouse Performance Score ≥ 80
- [ ] 后端：API P99 响应时间 < 500ms
- [ ] 无内存泄漏（长时间运行稳定）

自动检测逻辑：
- 检测前端框架（React / Vue / Svelte / Angular / Next.js）→ 执行 Lighthouse
- 检测 API 框架（Express / Fastify / Koa / Hono / Go / Python）→ 测量 P99

## 插件门禁

通过 Harness 插件协议可注册自定义门禁（如安全审计、许可证检查）。
插件门禁通过 `.boss/plugins/<name>/plugin.json` 的 `hooks.gate` 指向一个可执行文件，由 `boss runtime evaluate-gates` 统一调度。

## 调用方式

```bash
boss runtime evaluate-gates <feature> gate0
boss runtime evaluate-gates <feature> gate1
boss runtime evaluate-gates <feature> gate2
boss runtime evaluate-gates <feature> <plugin-gate-name>
boss runtime evaluate-gates <feature> gate0 --dry-run
```

## 判断标准

问自己：
- **如果现在把这个代码交给用户，他能正常使用吗？**
- **核心流程有没有遗漏的测试？**
- **有没有明显的性能或安全问题？**

## 未通过处理

如果门禁未通过：
1. `boss runtime evaluate-gates` 自动追加门禁结果事件并物化 `execution.json` read model
2. Boss Agent 调用 `boss runtime update-stage <feature> 3 failed` 标记阶段为 `failed`
3. 尝试修复后通过 `boss runtime retry-stage` 重试
4. 重新执行对应门禁
5. 再次检查是否通过

不允许绕过门禁直接部署。
