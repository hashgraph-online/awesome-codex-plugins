# Git Commit Details

本文件承载 `git-commit` 的按需细节。主 `SKILL.md` 保留高频运行时流程；只有在仓库没有明文规则、需要解释 emoji 取舍、需要类型表或需要校验默认值时读取这里。

## Conventional Commit 类型

| type | 用途 |
|------|------|
| `feat` | 新功能 / 新行为 |
| `fix` | 缺陷修复 |
| `docs` | 文档变更 |
| `style` | 仅格式调整，不改行为 |
| `refactor` | 结构重构，不改行为 |
| `perf` | 性能优化 |
| `test` | 测试 |
| `chore` | 工具 / 维护 |
| `ci` | 流水线 / 自动化 |

选择 type 时看 diff 的主要目的，而不是受影响文件夹。例如改 README 通常是 `docs`，改构建脚本通常是 `chore` 或 `ci`。

## Emoji 规则

默认不使用 emoji。只有用户传 `--emoji`，且仓库没有禁止 emoji 时才启用。

正确位置：

- 默认：`feat(api): 新增活动分页接口`
- `--emoji`：`feat(api): ✨ 新增活动分页接口`

不要写成：

- `✨ feat(api): 新增活动分页接口`

原因：release-please、semantic-release、commitlint 等工具通常从提交标题开头匹配 Conventional Commit type。emoji 前置会让 `feat` / `fix` 不再位于开头，导致自动发版、changelog 或 lint 误判。放在冒号之后时，emoji 只是描述的一部分，不影响机器解析。

常用配对：

| type | emoji |
|------|-------|
| `feat` | ✨ |
| `fix` | 🐛 |
| `docs` | 📝 |
| `style` | 💄 |
| `refactor` | ♻️ |
| `perf` | ⚡️ |
| `test` | ✅ |
| `chore` | 🔧 |
| `ci` | 🚀 |

更精确的 gitmoji 可以使用，但 Conventional Commit type 必须仍然准确。

## 校验默认值

原则：跑能给出有意义信心的最轻校验，不做无差别全量构建。

### Node / Frontend

存在 `package.json` 时：

- 先读 scripts，再决定是否跑 `lint`、`build` 或其他仓库声明命令
- 仓库声明包管理器时按仓库来
- 未声明时按 lockfile 推断：`pnpm-lock.yaml` 用 `pnpm`，`package-lock.json` 用 `npm`
- `generate:docs` 仅在脚本存在且属于仓库正常工作流时运行

### Java Maven

存在 `pom.xml` 时默认跑 `mvn compile`，除非仓库文档声明了更合适的轻量命令。

### 混合仓库

只跑与改动区域相关的校验。比如只改 README 或 Skill 文档时，优先做格式 / diff 检查；不要因为仓库有多种语言就全部构建。

### 跳过或失败

`--no-verify`、"跳过校验"、"别跑 lint"、"直接提交" 都视为跳过授权。

校验失败时可以给出提交消息或修复建议，但只有用户明确接受带失败继续时才提交，并且报告中必须说清失败。

## 示例

默认无 emoji：

- `feat(api): add campaign pagination endpoint`
- `fix(auth): handle empty token refresh response`
- `docs(readme): clarify local setup steps`
- `feat(api): 新增活动分页接口`

`--emoji`：

- `feat(api): ✨ add campaign pagination endpoint`
- `fix(auth): 🐛 handle empty token refresh response`
- `refactor(trigger): ♻️ extract retry policy builder`
- `feat(api): ✨ 新增活动分页接口`
