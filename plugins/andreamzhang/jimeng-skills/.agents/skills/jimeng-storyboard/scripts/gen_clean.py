#!/usr/bin/env python3
"""从含格式版 Markdown 分镜文件生成纯文本版 clean.txt"""

import sys
import re
import os

def gen_clean(md_path: str):
    if not os.path.exists(md_path):
        print(f"错误: 文件不存在: {md_path}")
        sys.exit(1)

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    output = []
    in_asset_table = False

    for line in lines:
        # 跳过素材对应表（Markdown表格）及其表头
        if line.strip().startswith("| 引用名称"):
            in_asset_table = True
            continue
        if in_asset_table:
            if line.strip().startswith("|") and not line.strip().startswith("|---"):
                # 提取素材引用行，生成顶部注解
                parts = [p.strip() for p in line.strip().split("|") if p.strip()]
                if len(parts) >= 4:
                    ref_name = parts[0]
                    ref_type = parts[1]
                    file_name = parts[2]
                    note = parts[3] if len(parts) > 3 else ""
                    output.append(f"{ref_name}（{ref_type}，{file_name}，{note}）")
                continue
            elif line.strip() == "---":
                in_asset_table = False
                output.append("")
                continue
            elif not line.strip().startswith("|"):
                in_asset_table = False
            else:
                continue

        # 去掉 ## 和 ### 标记
        if line.startswith("## 母镜头"):
            line = line.replace("## ", "", 1)
        elif line.startswith("### 子镜头"):
            line = line.replace("### ", "", 1)

        # 去掉 ** 粗体标记（保留内容）
        line = line.replace("**", "")

        output.append(line)

    # 确定输出路径
    dir_path = os.path.dirname(md_path)
    base_name = os.path.splitext(os.path.basename(md_path))[0]
    clean_path = os.path.join(dir_path, base_name.replace("-jimeng-prompts", "-jimeng-prompts-clean") + ".txt")

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"已生成: {clean_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python gen_clean.py <02-jimeng-prompts.md>")
        sys.exit(1)
    gen_clean(sys.argv[1])
