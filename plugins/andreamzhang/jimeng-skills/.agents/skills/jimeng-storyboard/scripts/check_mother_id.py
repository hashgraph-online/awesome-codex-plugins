#!/usr/bin/env python3
"""
check_mother_id.py —— 母镜头编号 / 剧情点编号 纯数字校验脚本

校验分镜文件（02-jimeng-prompts.md）中：
1. 母镜头编号必须为纯数字（1、2、3……），禁止字母后缀（如 1A、3A2、9B）；
2. 母镜头标题里的剧情点编号 [Pxx …] 必须为纯数字且全局连续（P01、P02……），
   禁止任何字母后缀（如 P09b、P03A、P1C）；
3. 母镜头编号必须连续且从 1 开始（1、2、3、4……，不允许跳号或字母）。

用法:
    python check_mother_id.py <02-jimeng-prompts.md路径>

退出码: 0 = 通过, 1 = 发现字母/非连续编号, 2 = 用法错误/文件不存在
"""
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免 ✓/✗/⚠ 触发 UnicodeEncodeError 崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def main():
    args = [a for a in sys.argv[1:] if a]
    if not args:
        print("用法: python check_mother_id.py <02-jimeng-prompts.md路径>")
        sys.exit(2)
    path = args[0]
    if not Path(path).exists():
        print(f"错误: 文件不存在: {path}")
        sys.exit(2)

    with open(path, encoding="utf-8") as f:
        content = f.read()

    problems = []

    # 1) 母镜头编号：## 母镜头N（总时长：X秒）
    mother_ids = []
    for m in re.finditer(r'^##\s*母镜头([^\s（(]+)', content, re.M):
        sid = m.group(1)
        if not re.fullmatch(r'\d+', sid):
            problems.append(f"母镜头编号含字母/非纯数字: 「母镜头{sid}」")
        else:
            mother_ids.append(int(sid))
    # 3) 连续且从1开始
    if mother_ids:
        expect = list(range(1, len(mother_ids) + 1))
        if mother_ids != expect:
            problems.append(
                f"母镜头编号不连续/非从1开始: 实际 {mother_ids}，应为 {expect}"
            )

    # 2) 标题剧情点编号 [Pxx …]：P 后必须紧跟纯数字，禁止字母后缀（如 P09b、P1C、P03A）
    p_ids = []
    for m in re.finditer(r'\[(P[^\]]*?)\]', content):
        token = m.group(1).strip()
        pm = re.match(r'P\s*(\d+)(.*)$', token, re.S)
        if not pm:
            problems.append(f"标题剧情点编号异常（非 P+数字 开头）: 「[{token}]」")
            continue
        num, rest = pm.group(1), pm.group(2)
        if rest.strip() and re.match(r'^[a-zA-Z]', rest.strip()):
            problems.append(f"标题剧情点编号含字母后缀: 「[{token}]」")
            continue
        p_ids.append(int(num))
    if p_ids:
        expect_p = list(range(1, len(p_ids) + 1))
        if p_ids != expect_p:
            problems.append(
                f"剧情点编号不连续/非从1开始: 实际 P{','.join(map(str, p_ids))}，应为 {expect_p}"
            )

    print("=" * 70)
    print("母镜头/剧情点编号纯数字校验报告")
    print("=" * 70)
    print(f"文件: {path}")
    print(f"母镜头数: {len(mother_ids)} | 标题剧情点编号数: {len(p_ids)}")
    print()

    if problems:
        print(f"[编号问题] ({len(problems)}处)")
        for p in problems:
            print(f"  ⚠ {p}")
        print()
        print(f"✗ 发现 {len(problems)} 个编号问题，母镜头号与标题 P 编号必须为纯数字且连续。")
        sys.exit(1)
    else:
        print(f"✓ 全部通过：母镜头编号 {mother_ids}、剧情点编号 P01–P{len(p_ids)} 均为纯数字且连续。")
        sys.exit(0)


if __name__ == "__main__":
    main()