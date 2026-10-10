# 参数与用户偏好

本包采用 JSON 作业文件；以下映射以本机验证过的 BabelDOC 0.6.4 为基线。运行时检查 `--help`，不支持的参数报错。用户用自然语言表达即可，agent 负责转换。不要求用户理解命令行。

| JSON 字段 | 可选值/含义 | BabelDOC 映射 |
|---|---|---|
| input / output | 单个 PDF / 每次新的输出目录 | --files / --output |
| source_language | 如 en、zh-CN；不填则引擎默认，不代表自动识别 | --lang-in |
| target_language | 必填；如 zh-CN、en、ja | --lang-out |
| outputs | both 默认、mono、dual | 不加开关 / --no-dual / --no-mono |
| dual_layout | side-by-side 默认、alternating | 默认左右 / --use-alternating-pages-dual |
| translated_first | true/false，默认 false | --dual-translate-first |
| pages | 物理页码，从 1 开始，如 "1,3-5"；不是印刷页码 | --pages |
| selected_pages_only | true 仅保留选中页；默认不加，其他页按引擎行为保留 | --only-include-translated-page |
| glossaries | CSV 路径数组，见术语文档 | --glossary-files |
| auto_terms | true 默认，false 关闭自动术语提取 | false 时 --no-auto-extract-glossary |
| save_terms | true 保存自动提取术语；默认 false | --save-auto-extracted-glossary |
| prompt_file | UTF-8 提示文本路径 | --custom-system-prompt |
| font | serif、sans-serif、script；不填自动选择 | --primary-font-family |
| translate_tables | true/false；表格文字翻译为实验功能 | --translate-table-text |
| scan_mode | off 默认、auto、force | 不加 / --auto-enable-ocr-workaround / --ocr-workaround |
| qps | 正整数，每秒请求上限；模板为 2 | --qps |
| workers / term_workers | 正整数，普通/术语并行任务数 | --pool-max-workers / --term-pool-max-workers |
| max_pages_per_part | 正整数，长文分块；未指定由引擎决定 | --max-pages-per-part |
| ignore_cache | true/false；术语/提示修改后可开启，增加调用成本 | --ignore-cache |
| watermark | watermarked、no_watermark、both | --watermark-output-mode |
| provider.base_url | 实际 OpenAI-compatible（兼容接口）地址 | --openai-base-url |
| provider.model | 实际服务提供的模型标识 | --openai-model |
| provider.api_key_env | 存放密钥的环境变量名 | 临时 TOML 注入，不放命令参数 |

未指定选项保持引擎默认；模板显式提供常用值。不要把模板默认误称为所有引擎版本的默认。语言代号的语法验证不能证明引擎支持该语言，必须查上游支持列表。源语言由 agent 根据样本判断并写入，无 `auto` 魔法值。

## 由 agent 处理的偏好（不能直接作为 JSON 字段）

| 用户要求 | 实现与限制 |
|---|---|
| 自动匹配航空、控制、医学等领域术语 | 判断领域 → 结合上下文生成候选 → 合并用户术语 → CSV → 抽查；不是一个 domain 开关 |
| 英文专有名词（中文） | 将确定术语写入 CSV，其他词通过 prompt_file 指导；输出必须核对，提示不是硬保证 |
| 首次双语，后续仅中文 | 跨片段首次出现需要全文位置追踪；原生分段翻译不保证，不冒充已有参数 |
| 学术/通俗/忠实原文 | prompt_file；技术论文默认忠实、不过度改写 |
| 不翻作者、参考文献、代码 | 提示只能尽力遵守；严格区域排除需另行实现，不能捏造 CLI 开关 |
| 图中文字也翻译 | 可提取文字与图片像素文字区分；嵌入图片需另行 OCR/图像排版，默认保留图片 |
| 批量翻译 | 每个输入独立 job 和输出目录，避免同名文件冲突；不要无约束并发 |

## 高级选项

这些不在便携脚本的稳定配置接口中；确有问题才查当前引擎帮助，构建单独实验命令并记录理由：
`--disable-rich-text-translate`、`--skip-clean`、`--split-short-lines`、`--formular-font-pattern`、`--formular-char-pattern`、`--skip-formula-offset-calculation`。
`--enhance-compatibility` 还可能改变双语页顺序，不能当作无副作用的通用修复。关闭曲线、表单、图形渲染可能丢失内容，不能默认启用。
扫描 workaround 是实验路径，不是完整 OCR 软件替代；off 不等于强制关闭引擎扫描检测。不将扫描文档的图像直接提交模型，除非相应流程与用户范围一致。
