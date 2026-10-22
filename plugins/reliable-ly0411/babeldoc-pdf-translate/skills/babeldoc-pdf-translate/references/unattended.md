# 本机聊天额度与无人值守翻译

`run --execute` 自动启动桥接、翻译并关闭本次创建的进程和端口，无需在聊天框中复制回复。开发和真实实验记录见 [Issue #8](https://github.com/reliable-ly0411/babeldoc-pdf-translate/issues/8)。原有兼容 API 的作业格式保持可用。

## 前置条件

- Python / BabelDOC 按 [部署说明](deployment.md) 安装并应用兼容补丁。
- Codex：CLI 须支持 `exec --ignore-user-config --ephemeral --output-schema`；`codex login status` 必须显示 `Logged in using ChatGPT`。桥接拒绝 API Key 登录。模型省略时使用 CLI 默认模型，也可指定账户可用的 `provider.model`。
- DSH：已安装含构建产物的 CLI、base、账户和 LLM 组件，并在 DSH 登录 **DeepSeek 模型账户**。Web 界面的本机登录不等于模型账户登录。默认使用 `deepseek-account`；只有用户明确选择复用现有 API 接口及余额时，才将 `route` 设为 `deepseek-official`。后一方式由 DSH 原生凭据服务解析 `DEEPSEEK_API_KEY`，不会要求在作业或聊天中提供密钥，也不在账户失败时自动回退。`dsh_package` 指向 CLI 的 `package.json`；源码构建为 `apps/cli/package.json`。`node_bin` 指向兼容该安装的 Node。
- 套餐必须允许相应模型调用；额度耗尽、退出登录或服务限流会失败，不绕过账户限制。

原生桥接的进程组清理在 Linux/POSIX 实验；其他系统需独立验收。DSH 使用已安装的组件接口，其升级可能导致接口变化，需重新探测和试译。已测版本与真实验收状态以 Issue #8 / VALIDATION.md 为准；模块导入成功不代表模型验收通过。

## 作业与运行

复制 `assets/job.codex.example.json` 或 `assets/job.dsh.example.json` 到工作目录，设置 PDF 与输出路径。相对路径基于作业文件目录；勿在只读插件缓存中保存作业输出。原生后端的 `workers`、`term_workers`、`qps` 固定为 1，填写其他值会拒绝。

```sh
python scripts/pdf_translate.py chat-doctor /path/to/job.json
python scripts/pdf_translate.py run /path/to/job.json --engine /path/to/babeldoc
python scripts/pdf_translate.py run /path/to/job.json --engine /path/to/babeldoc --execute
```

`chat-doctor` 只检查原生登录/组件，不翻译 PDF，也不证明远端推理成功。普通 `run` 是参数计划，不启动桥接。只有 `--execute` 调用已登录模型。已授权的多份文件可顺序运行独立作业；每份使用新输出目录，任一退出码非零时停止并检查清单。

### Windows 执行身份与登录诊断

`chat-doctor` 报告所选 CLI 路径、操作系统实际执行身份及继承的用户目录，
不读取 `auth.json`、令牌或系统凭据存储。Windows 受限命令可能以
`CodexSandboxOffline` 执行，却继承桌面用户的 `USERNAME` 和 `USERPROFILE`；
这时 CLI 的 `Not logged in` 只表示该进程上下文无法使用登录，不能推断桌面、
其他 CLI 或云任务未登录。先对照实际身份和所选可执行文件，使用已经授权的
正常用户终端；在需要按次批准的工具中由操作者选择正确上下文。

`CODEX_EXECUTION_CONTEXT_MISMATCH`、`CODEX_AUTH_UNAVAILABLE_IN_CONTEXT`、
`CODEX_AUTH_METHOD_MISMATCH`、`CODEX_LOGIN_STATUS_FAILED` 和
`CODEX_LOGIN_STATUS_UNRECOGNIZED` 分别保留这些失败边界。诊断不会自动重登、
切换账号、复制认证、提升自身权限或修改认证设置。当前 `codex` 后端仍明确使用
已有 ChatGPT 通道；每次调用的 `forced_login_method="chatgpt"` 和
`--ignore-user-config` 防止非预期的 API 计费/提供商回退，不修改全局配置。
云任务读取拒绝、执行服务断连、DNS 或代理故障须分别定位。

| 原生 provider 字段 | 含义 |
|---|---|
| type | `codex` 或 `dsh` |
| model | Codex 可省略；DSH 默认 `deepseek-flash` |
| codex_bin | 仅 Codex；默认 `codex`，支持绝对路径 |
| route | 仅 DSH；默认 `deepseek-account`；明确选择 `deepseek-official` 会使用已配置官方 API 的余额 |
| dsh_package / node_bin | 仅 DSH；CLI 的 package.json 必填，Node 默认 `node` |
| timeout_seconds | 每次调用 5–1800 秒，默认 180 |
| retries | 可恢复传输/超时/限流及受限格式修正重试 0–2 次，默认 1；鉴权、额度错误不重试 |
| cache_dir | 可选私有译文缓存；不填仅在本次进程中去重 |
| reasoning_effort | 仅 Codex；可选 `low`、`medium`、`high`、`max`，必须由所选模型支持；省略则沿用 CLI 默认值；进入缓存键；不改变调用预算或重试次数 |
| diagnostics_dir | 可选失败请求/回复诊断目录，必须私有（0700/0600）；包含文档内容，禁止上传或提交 |

原生 provider 不接受端点、密钥正文或密钥环境字段。DSH 当前仅适配官方端点与标准凭据引用，不自动读取其他 profile 的自定义网关。顶层 `timeout_seconds` 限制整个引擎执行（5–86400 秒，默认 7200），独立于每次模型调用。原生后端强制关闭 BabelDOC 翻译缓存，由桥接分别记录成功模型请求和缓存命中；普通 API 后端继续尊重 `ignore_cache`。

## 失败与恢复

账户未登录、超时、空答案、截断、无效 JSON、意外工具事件不能计为成功。只接受完整最终回答，不将中间思考当译文。原生请求最终失败会终止引擎，避免 BabelDOC 回退原文后仍生成貌似成功的 PDF。退出码 1 为任务失败，2 为配置/启动错误，正常中断为 130。检查 `run-manifest.json` 的 `status`、`error`、`bridge.errors`、`live_requests`、`cache_hits`。

本机 HTTP 桥接对有效 Content-Length（至多 512 KiB）的 POST 先完整读取有界请求体，再返回路径 404 或鉴权 401，避免 Windows 在请求体未读时关闭连接而中止响应。读取采用 10 秒绝对截止时间，响应明确 `Connection: close`；拒绝重复长度字段、Transfer-Encoding、不完整或超限请求。路径或鉴权不通过时不解析翻译内容、不调用模型，也不污染后续已授权翻译的失败状态。此传输修复不改变翻译缓存身份，不重试 HTTP 错误，不修改系统代理或安全设置。

成功回复立即原子写入配置的缓存，文件权限 0600、目录 0700；仅保存请求哈希与回复，不保存请求原文。缓存键包含后端、模型、原生版本与完整翻译上下文，改变术语或提示会产生不同键。损坏或开放权限的缓存会拒绝。

BabelDOC 批量回复必须逐项返回完整、唯一的输入 ID。桥接版本 3 将批量及已识别的单段翻译拆成独立文本槽；Codex 原生输出 schema 为每个槽声明必填字段，公式、样式和代码标记由程序保留并按原位恢复。空槽、合并、漏项、重复项或新增标记拒绝；受限格式修正最多使用 `retries` 次追加请求，不能无限重试。ASCII 赋值代码及被 `{vN}` 公式占位符拆开的标识符在请求前保护、回复后原样恢复，并核对标记的完整计数。此规则覆盖受测代码形式，不是通用代码解析器；逐槽翻译也可能影响跨公式的中文语序，仍需视觉与语义核验。

清单额外记录 `native_inference_calls` 及脱敏 `native_call_records`（请求哈希、耗时、原生客户端返回的 usage）。缓存命中不算新的模型调用。异常强杀可能来不及记录最后一次调用，缺失 usage 不等于零消费。模型别名的冷启动回复可以有措辞差异；缓存恢复的逐页文字/像素一致性应单独验证。

重试时保留 `cache_dir`，将 `output` 改为新目录再运行；已成功片段复用缓存，其余重新请求。缓存含译文，按用户保留要求管理，勿提交到 Git。旧输出不覆盖，中断清单和部分 PDF 保留诊断，不能当成成品。

Ctrl-C / SIGTERM 关闭本次桥接和子进程；SIGKILL、断电、系统崩溃不能运行清理。此类异常后应先确认旧进程已结束，避免同一作业并行运行。

## 范围与数据

桥接只监听随机 `127.0.0.1` 端口，采用单任务随机令牌，通过临时私有文件交给 BabelDOC。Codex 使用独立空目录和只读沙箱，关闭 shell/apps/web/多代理/钩子/图像工具；DSH 只加载原生账户与 LLM 组件，没有 Agent、工具或会话持久化组件。不会从浏览器、日志或认证文件复制令牌，不导出个人提示词，不修改现有 Web 配置。原生客户端仍可进行正常认证状态维护；本包不保证客户端没有本机日志。

仅支持 BabelDOC 使用的非流式文本 Chat Completions 与文本/JSON 对象回复，不是通用 OpenAI API 替代品。解析排版本地执行，抽取文本仍发送给所选账户的云端模型。`needs-review` 表示调用及 PDF 结构检查通过，译文、数字和排版仍按 [quality.md](quality.md) 验收。不得把缓存回放或模拟客户端测试称为新的真实模型实测。

接口依据：[Codex 非交互调用](https://learn.chatgpt.com/docs/non-interactive-mode)、[Codex 登录](https://learn.chatgpt.com/docs/auth)、[DSH 账户模型组件](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/llm/llm-deepseek-account)、[DSH LLM](https://github.com/deepseek-ai/deepseek-harness/tree/master/packages/llm/llm)。

## Paired code tags split by PDF formula markers

The rc.24 bridge protects literal opening/closing tag names before inference when both names are evidenced. PDF-split tags additionally require an explicit tag/markup cue in the source. Adjacent tags may share a formula marker; each visible name remains separately bound to its original anchors. Unpaired prose, math variables and unknown hidden formula contents are not inferred to be code. Standalone requests receive the fidelity check, while automatic token masking currently applies to batch requests.

Affected legacy cache replies must pass the new guard before reuse. Correct replies are reused without another model call; a reply that changed the tag name is left untouched and excluded from recovery. Existing request, time and retry limits still apply. This closes one lexical preservation gap, not general semantic or visual acceptance.
