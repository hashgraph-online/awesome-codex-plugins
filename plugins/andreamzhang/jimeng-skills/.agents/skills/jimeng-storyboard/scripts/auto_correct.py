#!/usr/bin/env python3
"""auto_correct.py —— 自动修复分镜时长问题

按优先级尝试修复:
  1. 借时长 (同母镜头内无台词子镜头让渡)
  2. 调语速 (中等→快→极快)
  3. 拆母镜头 (角色切换/自然停顿)

循环最多 --max-iter 轮(默认 3),通过 run_all_checks 验证收敛。

用法:
    python auto_correct.py <02-jimeng-prompts.md路径> [--max-iter 3] [--script <剧本原文>]

退出码:
    0 = 收敛 (全部校验通过)
    1 = 未收敛 (达到 max_iter 仍有 issues)
    2 = 用法错误

设计: 2026-08-15 stage5-pipeline-design
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def setup_env():
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def run_all_checks(storyboard, original_script=None):
    """调用 run_all_checks.py,返回 (passed, issues_dict)"""
    args = [sys.executable, str(SCRIPT_DIR / "run_all_checks.py"), str(storyboard), "--json"]
    if original_script:
        args += ["--script", str(original_script)]
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          env=setup_env(), timeout=60)
    try:
        data = json.loads(proc.stdout)
    except Exception:
        return False, {"error": "parse failure", "raw": proc.stdout[:500]}
    return data.get("overall_passed", False), data


def extract_duration_issues(storyboard):
    """从 calc_duration.py 输出解析时长 issues(母镜头超时/单镜头时长不足)"""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "calc_duration.py"), "--from-storyboard", str(storyboard)],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=setup_env(), timeout=60,
    )
    issues = []
    for line in proc.stdout.splitlines():
        # "母镜头1 (声明8.0s, 子镜头和=8.0s) [✗ 2个问题]"
        m = re.search(r"\u6bcd\u955c\u5934(\d+).*?\u5b50\u955c\u5934\u548c=(\d+\.?\d*)s.*?\u3010\u95ee\u9898(\d+)\u4e2a\u3011", line)
        if m:
            issues.append({
                "mother_id": int(m.group(1)),
                "sum": float(m.group(2)),
                "issue_count": int(m.group(3)),
            })
    return issues


def generate_borrow_corrections(content, issues):
    """对每个有问题的母镜头,尝试借时长(从无台词子镜头让渡给超时子镜头)"""
    return {}


def generate_speed_corrections(content, issues):
    """对每个超时子镜头,尝试调语速为'快'"""
    return {}


def generate_split_corrections(content, issues):
    """对超 15s 的母镜头,尝试按自然停顿拆分为两个"""
    return {}


def main():
    parser = argparse.ArgumentParser(description="\u81ea\u52a8\u4fee\u590d\u5206\u955c\u65f6\u957f\u95ee\u9898")
    parser.add_argument("storyboard", help="02-jimeng-prompts.md \u8def\u5f84")
    parser.add_argument("--max-iter", type=int, default=3, help="\u6700\u5927\u8fed\u4ee3\u8f6e\u6570")
    parser.add_argument("--script", dest="original_script", default=None,
                        help="\u5267\u672c\u539f\u6587\u8def\u5f84\uff08\u53f0\u8bcd\u6821\u9a8c\u9700\u8981\uff09")
    args = parser.parse_args()
    storyboard = Path(args.storyboard)
    if not storyboard.exists():
        print(f"\u9519\u8bef: {storyboard} \u4e0d\u5b58\u5728", file=sys.stderr)
        sys.exit(2)

    print(f"\u5f00\u59cb\u81ea\u52a8\u4fee\u590d: {storyboard}")
    print(f"\u6700\u5927\u8f6e\u6570: {args.max_iter}")

    for iteration in range(1, args.max_iter + 1):
        print(f"\n--- \u8f6e {iteration}/{args.max_iter} ---")
        passed, data = run_all_checks(storyboard, args.original_script)
        if passed:
            print("[OK] 全部校验通过，收敛。")
            sys.exit(0)

        # 检查时长问题
        duration_issues = extract_duration_issues(storyboard)
        if not duration_issues:
            print(f"\u26a0 \u65e0\u53ef\u4fee\u590d\u7684\u65f6\u957f\u95ee\u9898:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            sys.exit(1)

        print(f"\u53d1\u73b0 {len(duration_issues)} \u4e2a\u6709\u95ee\u9898\u7684\u6bcd\u955c\u5934: {[i['mother_id'] for i in duration_issues]}")
        # TODO: 调用 generate_* 决定修复方案,然后写 corrections.json + apply
        print(f"\u26a0 \u672c\u7248\u4ec5\u68c0\u6d4b issues\uff0c\u4fee\u590d\u903b\u8f91\u5f85\u5b9e\u73b0\u3002\u8bf7\u624b\u52a8\u8fd0\u884c apply_corrections.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
