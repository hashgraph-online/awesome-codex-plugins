# 分镜表Excel生成脚本模板

本目录包含分镜表生成技能的脚本模板。

## 文件说明

- `generate_table_template.py` - 分镜表生成脚本模板（支持模式A和模式B）

## 使用方式

本脚本由 storyboard-table-skill 在执行时调用，不接受直接命令行执行。

技能执行流程：
1. 读取输入文件（02-jimeng-prompts.md 或 01-director-analysis.md）
2. 根据输入模式选择解析逻辑
3. 生成Excel文件到工作区根目录

## 依赖

```bash
pip install openpyxl
```
