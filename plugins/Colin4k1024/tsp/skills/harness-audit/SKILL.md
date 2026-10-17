---
name: harness-audit
description: Harness 能力面审计（7 维度评分 + 改进建议）。对角色覆盖、技能完整性、Hook 有效性、规则执行、命令覆盖、文档质量、集成深度进行全面评估，输出 Overall Score、Dimension Scores 和 Top Actions。适用于平台健康检查、季度能力审查、新增能力后的回归验证。关键词：harness-audit、平台审计、技能完整性、Agent 覆盖、命令覆盖、文档质量。
---

# Harness 能力面审计

对当前平台配置进行 **7 维度评分**，定位能力短板并给出优先改进建议。

---

## 触发方式

```
/harness-audit
```

或由 `harness-optimizer` specialist 直接调用。

---

## 7 个评估维度

### 1. Agent Coverage（代理覆盖）

检查所有角色是否有对应的 `agents/roles/*.md` 生成文件，specialist agents 是否与 `commands/` 命令一一对应。

**评分标准**：
- 90–100：所有角色 + 全部 specialist 覆盖完整
- 70–89：≥ 2 个角色或 specialist 缺失
- < 70：核心角色缺失 agent 文件

### 2. Skill Completeness（技能完整性）

检查 `skills/`、`skills/`、`skills/` 中所有技能是否有有效 `SKILL.md`，role.yaml 中引用的技能是否实际存在。

**评分标准**：
- 90–100：无悬空引用，所有 SKILL.md 齐备
- 70–89：1–3 处悬空引用
- < 70：多处悬空引用或 SKILL.md 缺失

### 3. Hook Effectiveness（Hook 有效性）

检查 `hooks/hooks.json` 配置是否启用关键 hook，`session_start.py`/`session_end.py` 是否能实际运行。

**评分标准**：
- 90–100：hooks 配置完整，smoke 验证通过
- 70–89：hooks 存在但未启用
- < 70：hooks 缺失或运行报错

### 4. Rule Enforcement（规则执行）

检查 `rules/` 中所有规则文件是否被 CLAUDE.md/AGENTS.md 或角色的 `governance_rules` 字段引用。

**评分标准**：
- 90–100：无孤立规则，所有规则有引用入口
- 70–89：≤ 3 个孤立规则
- < 70：> 3 个孤立规则或核心规则未引用

### 5. Command Coverage（命令覆盖）

检查 `commands/` 中每个命令是否在 CLAUDE.md/AGENTS.md 的命令面中列出，specialist 与命令是否匹配。

**评分标准**：
- 90–100：命令与 AGENTS.md 门面一致
- 70–89：1–2 个命令缺少文档入口
- < 70：> 2 个命令游离于门面之外

### 6. Documentation Quality（文档质量）

检查 `docs/runbooks/`、`docs/memory/`（若存在）中关键手册是否存在，AGENTS.md 中链接的文件是否实际可访问。

**评分标准**：
- 90–100：所有 AGENTS.md 链接文件存在，docs/memory/ 已初始化
- 70–89：≤ 5 个链接失效
- < 70：> 5 个链接失效或 docs/memory/ 不存在

### 7. Integration Depth（集成深度）

评估 role.yaml 中 `recommended_ecc_skills` / `recommended_domain_skills` 覆盖情况，以及各角色能力与其职责的匹配度。

**评分标准**：
- 90–100：所有角色至少有 3 个 ecc + 2 个 domain skills（适用角色）
- 70–89：部分角色 skills 配置稀疏
- < 70：多个角色零 skills 配置

---

## 标准输出格式

```markdown
## Harness Audit Report — {date}

### Overall Score: {score}/100

| 维度 | 得分 | 状态 | 主要问题 |
|------|------|------|---------|
| Agent Coverage | XX | ✅/⚠️/❌ | ... |
| Skill Completeness | XX | ✅/⚠️/❌ | ... |
| Hook Effectiveness | XX | ✅/⚠️/❌ | ... |
| Rule Enforcement | XX | ✅/⚠️/❌ | ... |
| Command Coverage | XX | ✅/⚠️/❌ | ... |
| Documentation Quality | XX | ✅/⚠️/❌ | ... |
| Integration Depth | XX | ✅/⚠️/❌ | ... |

### Top Actions（优先级排序）

1. **[优先级:高]** {具体行动} — 影响维度：{维度名}
2. ...

### Recommendations

- {建议1}
- {建议2}
```

---

## 执行步骤

1. `ls agents/roles/ | wc -l` 与 `roles/` 数量对比 → Agent Coverage
2. `node scripts/validate-library.js` → Skill Completeness（利用已有验证工具）
3. 检查 `hooks/hooks.json` enabled 字段 + `python3 scripts/hooks/session_end.py --dry-run`（若支持）→ Hook Effectiveness
4. `grep -r "governance_rules" roles/` 与 `ls rules/` 对比 → Rule Enforcement
5. 比对 `AGENTS.md` 命令表与 `ls commands/` → Command Coverage
6. 遍历 AGENTS.md 中所有 Markdown 链接，验证目标文件存在 → Documentation Quality
7. 遍历所有 role.yaml 的 `recommended_ecc_skills` + `recommended_domain_skills` 字段 → Integration Depth
8. 汇总得分，输出报告

---

## 配合规则

- 执行后按 `artifact-standards.md` 写入 `docs/artifacts/{slug}/harness-audit-report.md`
- 发现 skill 悬空引用时，联动触发修复建议（可对接 `/build-fix`）
