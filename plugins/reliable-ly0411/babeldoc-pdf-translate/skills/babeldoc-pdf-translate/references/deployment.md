# 部署与跨平台分发

## 三层架构

1. 指令层：SKILL.md + references，平台无关的工作流程。
2. 执行层：标准 Python 脚本，将经验证的 JSON 转为 BabelDOC CLI 参数，不调用私有 Python API。
3. 运行时层：BabelDOC、PDF 检查库、字体/版面模型、用户选择的翻译服务。运行时单独安装，不塞进技能 ZIP。

无需特定 agent SDK。支持 SKILL.md 的平台将整个目录放到其技能搜索路径；只支持规则/提示文件的平台，在其入口写明读取本目录 SKILL.md 并按需读取 references。不要把所有参考资料重复注入上下文。无 shell/文件能力的聊天平台只能参考指导，不能独立执行本包。

## 安装示例

在解压目录打开终端。需要真实的 Python 3.10+（建议 3.12），不要调用 Windows Store 占位 python。可用 uv 创建独立环境：

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/babeldoc --warmup
.venv/bin/python scripts/pdf_translate.py doctor --engine .venv/bin/babeldoc
```

Windows PowerShell 对应路径：

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
& ./.venv/Scripts/babeldoc.exe --warmup
& ./.venv/Scripts/python.exe scripts/pdf_translate.py doctor --engine .venv/Scripts/babeldoc.exe
```

没有 uv 时，用已验证的 Python 绝对路径执行 `-m venv .venv`，再用环境内 Python 执行 `-m pip install -r requirements.txt`。requirements 是已测版本基线，不是跨操作系统完整锁文件；正式交付可在目标系统生成依赖锁与 wheelhouse。虚拟环境通常不可跨机器直接搬运。

仓库根目录 `requirements.lock` 记录 Windows/Python 3.12 的已测环境快照（含检查工具），供该环境复现；它不是所有平台的通用依赖解。其他平台从 requirements.txt 解析并单独验证。

复制 assets/job.example.json 为自己的 job.json；相对路径基于 job.json 所在目录，需自行放好 document.pdf 或改成实际路径。仅当希望采用相应示例术语和提示时才复制并引用它们。密钥通过本机环境配置提供，不写进 job.json 或聊天。

```sh
.venv/bin/python scripts/pdf_translate.py run /path/to/job.json --engine .venv/bin/babeldoc
.venv/bin/python scripts/pdf_translate.py run /path/to/job.json --engine .venv/bin/babeldoc --execute
```

Windows 将上述 Python/引擎改为 `.venv/Scripts/python.exe`、`.venv/Scripts/babeldoc.exe`。脚本不会自动安装依赖、创建付费账号或选择服务。

## 本地与离线

解析、排版本地进行，云端接口可能收到文本、上下文、术语和提示；本地部署不等于全文不出机。用户选择云端翻译时按该范围使用，勿额外上传完整 PDF。完全离线需要本地兼容翻译服务及预先准备的权重。无鉴权的本地服务也须提供其接受的非空占位 key 环境值。

`babeldoc --generate-offline-assets DIR` 导出字体/模型资源包；`babeldoc --restore-offline-assets PACKAGE` 恢复。该包不含通用 LLM 权重，也不替代 Python 依赖包。不要重命名上游带哈希的资源包。

技能目录可直接复制，但 BabelDOC 缓存/字体可能仍写入用户目录。未验证所有缓存和运行时路径前，不宣称整套运行时是零痕迹便携版。运行时缓存、作业输出和临时文件可包含文档内容，按用户保留策略处理；不要打入公开分发包。

## PDFMathTranslate 参考路线

需要更多翻译服务或 WebUI 时可使用 PDFMathTranslate-next（底层仍为 BabelDOC）。它的 CLI 采用 `pdf2zh_next INPUT.pdf ...`，参数和安装包版本应以其 `--help` 为准。不能将它的可执行文件传入本包的 --engine：本脚本仅适配 BabelDOC CLI。若扩展该后端，增加独立映射与测试，不改写现有 job 语义。

上游建议嵌入式 Python 开发通过 pdf2zh_next 的公开接口；本包为减少运行时依赖采用 BabelDOC CLI。BabelDOC 将其 CLI 定位为调试用途，升级须重新验证兼容性；不承诺上游技术支持。

## 分发

分发整个技能目录及 SHA256，排除 .venv、缓存、密钥、用户 PDF、输出和临时日志。本包未捆绑上游源码或二进制；若另外分发引擎/修改版，应保留对应上游许可证和声明。不要将第三方组件的许可证替换为技能文档许可。
