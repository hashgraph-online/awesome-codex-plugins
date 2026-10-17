# BabelDOC PDF Translate — 通用 Agent 技能

[![HOL Guard verified badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dreliable-ly0411%252Fbabeldoc-pdf-translate%26metric%3Dtrust)](https://hol.org/registry/plugins/reliable-ly0411%2Fbabeldoc-pdf-translate)

Layout-preserving PDF translation skill for **Codex and DeepSeek Harness**, powered by a separately installed BabelDOC runtime. Supports bilingual output, page selection, custom glossaries and contextual terminology review. Local parsing/typesetting; translation uses the provider you configure. No telemetry or bundled cloud account.

## Codex plugin 安装

```sh
codex plugin marketplace add reliable-ly0411/babeldoc-pdf-translate
```

在支持仓库市场的 Codex 客户端选择 `BabelDOC PDF Translate` 安装。该仓库市场独立于 OpenAI 官方公共目录，不代表官方收录。插件只封装技能；Python/BabelDOC 按部署文档另行安装。

## DeepSeek Harness skill 安装

DSH 原生发现项目 `.dsh/skills/<name>/SKILL.md`。在目标项目根目录运行：

```sh
git clone --branch main --depth 1 https://github.com/reliable-ly0411/babeldoc-pdf-translate.git .dsh/skills/babeldoc-pdf-translate
```

这是文件系统技能，无需安装 Cordis 插件或运行 npm 安装脚本。也可从本仓库复制 `skills/babeldoc-pdf-translate` 到 `.dsh/skills/` 或配置的用户技能目录。需要 DSH 的文件/命令工具和独立 BabelDOC 运行时；未声称验证所有 DSH 版本。

See [DSH's filesystem skill discovery](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/skills.md). Root `SKILL.md` remains available for direct skill installers; the nested `skills/` copy is the Codex plugin payload. Maintainers edit the root skill resources, run `python scripts/sync_plugin_skill.py`, and check with `--check`.

## License / 许可

本仓库原创技能和适配脚本采用 MIT。`patches/babeldoc-0.6.4/` 中的上游衍生补丁采用 AGPL-3.0，见该目录的 LICENSE；嵌套技能内副本亦同。BabelDOC、PyMuPDF 及其他运行时依赖分别适用各自上游许可；完整依赖和二进制不包含在本仓库内。

入口：[SKILL.md](SKILL.md)。这是可分发的技能与脚本包，不是包含所有模型和依赖的独立翻译软件。

适用于支持文件访问和命令执行的 agent 平台；核心不依赖 Codex 工具。`agents/openai.yaml` 是可选界面元数据，其他平台可忽略。

## 快速使用

1. 将整个 `babeldoc-pdf-translate` 目录复制到目标平台支持的技能目录；若没有技能机制，让 agent 读取 SKILL.md。
2. 按 [部署说明](references/deployment.md) 配置 BabelDOC 运行时。
3. 告诉 agent PDF 路径、目标语言和偏好；服务未配置时也可先准备术语和作业草案。

示例请求：

> 使用这个技能把论文第 2–4 个物理页翻译为中文，输出交替页中英对照，只保留选中页。phase margin 固定翻译为相位裕度，其余术语结合控制领域上下文自动匹配。保留公式、图片和单位。云端接口稍后配置，先准备作业和术语表。

> 翻译整份 PDF，输出中文单语及左右对照两个版本。航空专有名词采用英文（中文），使用我提供的 CSV；先试译有公式和表格的两页。

## 本机聊天额度自动翻译

1.3.0 提供 Codex / DSH 原生客户端桥接：复制 `assets/job.codex.example.json` 或 `assets/job.dsh.example.json`，运行 `chat-doctor` 检查登录，再执行 `run --execute`。支持私有译文缓存、有限重试、中断清理和代码标识符保护；无需手动复制模型回复。Codex 使用 ChatGPT 登录额度；DSH 默认账户路由，也可在用户明确选择后复用已配置的官方 API 及余额。配置及边界见 [无人值守说明](references/unattended.md)，真实验收状态记录在 [Issue #8](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/8)。

## 包结构

```text
SKILL.md              agent 入口与工作流程
scripts/              参数校验、引擎探测、PDF 检查与执行
references/           参数、术语、质量、部署和来源
assets/               作业、术语表、提示词模板
agents/               可选的平台界面元数据
requirements.txt      已测运行时版本基线
patches/              带哈希保护的 BabelDOC 0.6.4 兼容补丁及上游许可
```

支持单双语、双语页顺序、页码、术语表、自动术语提取、风格提示、字体、扫描处理、并发和云端兼容接口。专业领域判断由 agent 结合上下文完成；本包不自带各行业权威词库，不保证复杂 PDF 完全免返工。

运行与测试边界见 [VALIDATION.md](VALIDATION.md)。不要在分发包中加入个人密钥、PDF、缓存或虚拟环境。

1.2.0 的修复需要按部署文档显式运行 `scripts/repair_runtime.py --apply`；更新技能文件不会自动修改引擎。补丁检查原始文件哈希并保留可验证回滚副本，未知版本或文件会拒绝修改。`doctor` 仅证明 CLI 可用，`needs-review` 表示结构校验通过，译文与版式仍需检查。
