#!/usr/bin/env python3
"""stage5_pipeline.py —— 阶段七流水线主入口（历史文件名 stage5 保留，避免破坏脚本约定）

按顺序执行:
  1. auto_correct.py     (自动修复时长问题)
  2. auto_header.py      (重写集头说明)
  3. run_all_checks.py   (最终复跑确认)

用法:
    python stage5_pipeline.py <02-jimeng-prompts.md路径> [--max-iter 3] [--script <剧本原文>]

退出码:
    0 = 全 PASS (含集头已重写)
    1 = 有问题(详见输出)

设计: 2026-08-15 stage5-pipeline-design
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run(script, args, env=None):
    cmd = [sys.executable, str(SCRIPT_DIR / script)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          env=env, timeout=300)
    return proc.returncode, proc.stdout, proc.stderr


def main():
    parser = argparse.ArgumentParser(description="阶段七流水线（correct → header → check）")
    parser.add_argument("storyboard", help="02-jimeng-prompts.md 路径")
    parser.add_argument("--max-iter", type=int, default=3, help="auto_correct 最大迭代轮数")
    parser.add_argument("--script", dest="original_script", default=None,
                        help="剧本原文路径（台词校验需要）")
    parser.add_argument("--skip-correct", action="store_true", help="跳过 auto_correct")
    parser.add_argument("--skip-header", action="store_true", help="跳过 auto_header")
    args = parser.parse_args()

    sb = Path(args.storyboard)
    if not sb.exists():
        print(f"错误: {sb} 不存在", file=sys.stderr)
        sys.exit(2)

    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    print(f"=== 阶段七流水线 ===")
    print(f"分镜文件: {sb}")
    print()

    overall_ok = True

    if not args.skip_correct:
        print("[1/3] auto_correct ...")
        rc, stdout, stderr = run(
            "auto_correct.py",
            [str(sb), "--max-iter", str(args.max_iter)] + (["--script", str(args.original_script)] if args.original_script else []),
            env=env,
        )
        print(stdout, end="" if stdout.endswith("\n") else "\n")
        if rc != 0:
            print(f"[1/3] FAIL (退出码 {rc})", file=sys.stderr)
            overall_ok = False
        else:
            print(f"[1/3] PASS")
        print()

    if not args.skip_header:
        print("[2/3] auto_header ...")
        rc, stdout, stderr = run("auto_header.py", [str(sb)], env=env)
        print(stdout, end="" if stdout.endswith("\n") else "\n")
        if rc == 0:
            print(f"[2/3] 已重写集头")
        elif rc == 1:
            print(f"[2/3] 集头无变化(已匹配)")
        else:
            print(f"[2/3] FAIL (退出码 {rc})", file=sys.stderr)
            overall_ok = False
        print()

    print("[3/3] run_all_checks ...")
    rc, stdout, stderr = run(
        "run_all_checks.py",
        [str(sb)] + (["--script", str(args.original_script)] if args.original_script else []),
        env=env,
    )
    print(stdout, end="" if stdout.endswith("\n") else "\n")
    if rc != 0:
        print(f"[3/3] FAIL (退出码 {rc})", file=sys.stderr)
        overall_ok = False
    else:
        print(f"[3/3] PASS")
    print()

    if overall_ok:
        print("=== 流水线全 PASS ===")
        sys.exit(0)
    else:
        print("=== 流水线有 FAIL ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
