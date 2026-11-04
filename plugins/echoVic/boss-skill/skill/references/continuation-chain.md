# 续跑链（Continuation Chain）

专家小队的默认行为：**从当前入口开始，自动跑完后续所有环节，除非用户主动叫停。**

## 环节顺序

```
pm → architect → ui → review → tasks → dev → qa → ship
```

## 续跑规则

| 当前环节  | 下一步    | 跳过条件                  |
| --------- | --------- | ------------------------- |
| pm        | architect | —                         |
| architect | ui        | `--skip-ui` → 跳到 review |
| ui        | review    | —                         |
| review    | tasks     | —                         |
| tasks     | dev       | —                         |
| dev       | qa        | —                         |
| qa        | ship      | —                         |
| ship      | （终点）  | —                         |

## 停调条件

遇到以下任一情况，停止续跑：
1. 用户在对话中明确说"停"、"先到这"、"只做这一步"、"到 X 为止"
2. 用户传入 `--stop-after <环节>` 参数
3. 当前环节产出失败且无法修复
4. 到达 `ship` 终点

## 续跑执行流程

每个环节完成后：
1. 检查是否命中停调条件 → 命中则停止，输出当前产物路径
2. 未命中 → 按上表找到下一步环节
3. 检查下一步的**输入前置条件**（见下节）是否满足
4. 满足 → 执行下一步；不满足 → 尝试补齐或向用户确认后跳过
5. 重复直到终点或停调

## 输入前置条件

每个环节执行前，检查其输入产物是否存在。不存在时的处理：

| 环节      | 必需输入                       | 缺失时处理                                                              |
| --------- | ------------------------------ | ----------------------------------------------------------------------- |
| pm        | 用户需求描述                   | 向用户追问                                                              |
| architect | `prd.md`                       | 可用用户直接描述的需求替代                                              |
| ui        | `prd.md`                       | 可用用户直接描述的需求替代                                              |
| review    | `architecture.md`              | 评审代码或向用户索要架构                                                |
| tasks     | `plan.md`                      | 回退到 `tech-review.md` + `architecture.md`，或用用户直接描述的需求替代 |
| dev       | `tasks.md` + `architecture.md` | 可用用户直接描述的需求替代                                              |
| qa        | 可运行代码 + `prd.md`          | 无代码则提示先开发                                                      |
| ship      | `qa-report.md`                 | 警告后可强制继续                                                        |

**原则**：上游产物缺失时，可以用用户直接提供的需求替代，但必须在产物中标注来源。

## 产物路径规范

所有产物写入 `.boss/<feature-slug>/` 目录：

| 产物         | 路径                         | 产出环节  |
| ------------ | ---------------------------- | --------- |
| PRD          | `.boss/<f>/prd.md`           | pm        |
| 架构         | `.boss/<f>/architecture.md`  | architect |
| UI 规范      | `.boss/<f>/ui-spec.md`       | ui        |
| UI 设计 JSON | `.boss/<f>/ui-design.json`   | ui        |
| 技术评审     | `.boss/<f>/tech-review.md`   | review    |
| 实施计划     | `.boss/<f>/plan.md`          | review    |
| 任务拆解     | `.boss/<f>/tasks.md`         | tasks     |
| QA 报告      | `.boss/<f>/qa-report.md`     | qa        |
| 部署报告     | `.boss/<f>/deploy-report.md` | ship      |

feature-slug 从用户输入归一化而来，简短英文 kebab-case。若用户直接指定 slug 则使用用户指定的。

## 轻量门禁

每个环节完成时，自检本环节的硬性要求是否满足（见各 Agent prompt 的"硬性要求"表）。不满足时：
1. 先尝试自行修复
2. 无法修复时向用户报告，不进入下一环节
3. 用户可选择强制跳过（跳过后续环节可能受影响）
