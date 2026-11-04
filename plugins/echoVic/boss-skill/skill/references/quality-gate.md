# 质量门禁

质量门禁是各环节完成时的自检清单。**未通过的门禁必须修复后才能进入下一环节**，用户强制跳过除外。

## Gate 0：代码质量（开发环节自检）

- [ ] TypeScript / 类型检查编译无错误
- [ ] Lint（ESLint / Biome / Ruff）检查通过，无 error 级别问题
- [ ] 无已知高危依赖漏洞

检测逻辑：
- 若存在 `tsconfig.json` → 执行 `tsc --noEmit`
- 若存在 Biome/ESLint/Ruff 配置 → 执行对应 lint
- 若存在 `package.json` → 执行 `npm audit` 检查高危漏洞

## Gate 1：测试（QA 环节自检）

- [ ] 单元测试全部通过
- [ ] 测试覆盖率 ≥ 70%
- [ ] 无 P0/P1 级别 Bug
- [ ] E2E 测试已编写并通过
- [ ] 集成测试通过

检测逻辑：
- 自动识别测试框架：Vitest / Jest / pytest / cargo test / go test
- 自动解析覆盖率报告（coverage-summary.json / coverage.json / coverage.out）
- 自动识别 E2E 框架：Playwright / Cypress

## Gate 2：性能（部署环节自检，仅适用于 Web 项目）

- [ ] 前端：Lighthouse Performance Score ≥ 80
- [ ] 后端：API P99 响应时间 < 500ms
- [ ] 无内存泄漏（长时间运行稳定）

检测逻辑：
- 检测前端框架（React / Vue / Svelte / Angular / Next.js）→ 执行 Lighthouse
- 检测 API 框架（Express / Fastify / Koa / Hono / Go / Python）→ 测量 P99

## 判断标准

问自己：
- **如果现在把这个代码交给用户，他能正常使用吗？**
- **核心流程有没有遗漏的测试？**
- **有没有明显的性能或安全问题？**

## 未通过处理

如果门禁未通过：
1. 尝试修复问题
2. 重新执行对应检查
3. 再次确认是否通过
4. 无法修复时向用户报告，不进入下一环节

**原则**：不允许绕过门禁直接宣布交付完成，除非用户明确要求强制跳过。
