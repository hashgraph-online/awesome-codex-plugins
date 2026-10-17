#!/usr/bin/env python3
"""run_all_checks.py —— 统一校验入口

一键跑完四道脚本校验（时长/画面字段/台词对照/母镜头编号）并输出统一 JSON 报告。

用法:
    python run_all_checks.py <02-jimeng-prompts.md路径> [--script-dir DIR] [--quiet]

输出:
    - 控制台: 一行摘要 + 每个 check 的简要状态
    - JSON 格式结果可通过 --json 输出到 stdout

退出码:
    0 = 全部 PASS
    1 = 至少一项 FAIL
    2 = 用法错误/文件不存在

设计: 2026-08-15 stage5-pipeline-design
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_SCRIPT_DIR = Path(__file__).parent  # 同目录即为 jimeng-storyboard/scripts

# 四道校验脚本 + 它们对应的参数
CHECKS = [
    {
        "name": "duration",
        "script": "calc_duration.py",
        "args": ["--from-storyboard"],
        "label": "时长校验",
    },
    {
        "name": "picture",
        "script": "check_picture_field.py",
        "args": [],
        "label": "画面字段校验",
    },
    {
        "name": "dialogue",
        "script": "check_dialogue.py",
        "args": ["--script", "--storyboard"],
        "label": "台词对照校验",
        "requires_script_pair": True,  # 需要 --script + --storyboard 两个文件
    },
    {
        "name": "mother_id",
        "script": "check_mother_id.py",
        "args": [],
        "label": "母镜头编号校验",
    },
]


def setup_python_env():
    """设置 Python 子进程环境变量以避免 Windows GBK 编码问题"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def find_script_path(script_dir: Path, script_name: str) -> Path:
    """查找脚本路径,支持 .agents/skills/jimeng-storyboard/scripts 目录"""
    candidate = script_dir / script_name
    if candidate.exists():
        return candidate
    # 备用路径
    alt = script_dir.parent / "scripts" / script_name
    if alt.exists():
        return alt
    raise FileNotFoundError(f"找不到校验脚本: {script_name} (在 {script_dir})")


def run_single_check(check: dict, storyboard: Path, script_dir: Path,
                     original_script: Path = None, quiet: bool = False) -> dict:
    """运行单个校验脚本,返回结果字典"""
    script_path = find_script_path(script_dir, check["script"])
    # Windows 上必须用 sys.executable 显式调用 Python 解释器
    # 构造参数
    args = [sys.executable, str(script_path)] + check["args"] + [str(storyboard)]
    if check.get("requires_script_pair") and original_script:
        # dialogue 校验需要 --script + --storyboard
        args = [sys.executable, str(script_path), "--script", str(original_script),
                "--storyboard", str(storyboard)]

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=setup_python_env(),
            timeout=60,
        )
        passed = (proc.returncode == 0)
        stdout = proc.stdout
        stderr = proc.stderr
        # 提取关键信息
        issues = []
        for line in stdout.splitlines():
            if "发现问题数" in line:
                m = re.search(r"发现问题数:\s*(\d+)", line)
                if m:
                    issues.append(int(m.group(1)))
                    break
            if "台词与剧本原文逐字一致" in line or "所有画面字段通过检查" in line or "全部通过" in line:
                passed = True
                break
        # dialogue / mother_id 通常无 "发现问题数" 行, 退码 0 即 PASS
        result = {
            "name": check["name"],
            "label": check["label"],
            "passed": passed,
            "returncode": proc.returncode,
            "stdout_tail": stdout[-500:] if not quiet else "",
            "issues_count": issues[0] if issues else (0 if passed else None),
        }
        return result
    except subprocess.TimeoutExpired:
        return {
            "name": check["name"],
            "label": check["label"],
            "passed": False,
            "returncode": -1,
            "error": "TIMEOUT",
        }
    except Exception as e:
        return {
            "name": check["name"],
            "label": check["label"],
            "passed": False,
            "returncode": -1,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="统一校验入口")
    parser.add_argument("storyboard", help="02-jimeng-prompts.md 路径")
    parser.add_argument("--script", dest="original_script", default=None,
                        help="剧本原文路径（台词对照校验需要）")
    parser.add_argument("--script-dir", default=str(DEFAULT_SCRIPT_DIR),
                        help="校验脚本目录（默认同目录）")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 结果到 stdout")
    parser.add_argument("--quiet", action="store_true", help="压缩 stdout_tail 输出")
    args = parser.parse_args()

    storyboard = Path(args.storyboard)
    if not storyboard.exists():
        print(f"错误: 分镜文件不存在: {storyboard}", file=sys.stderr)
        sys.exit(2)

    # 台词对照校验需要剧本原文路径
    original_script = None
    if args.original_script:
        original_script = Path(args.original_script)
    else:
        # 启发式推断:scripts/<剧名>/script/epXX.txt (从 storyboard 路径向上找)
        # storyboard 形如 .../outputs/ep53/02-jimeng-prompts.md
        match = re.search(r"(.*outputs\\ep\d+)\\02-jimeng-prompts\.md$", str(storyboard))
        if match:
            ep_dir = Path(match.group(1))
            project_root = ep_dir.parent.parent
            ep_num = ep_dir.name.replace("ep", "")
            candidate = project_root / "script" / f"ep{ep_num}.txt"
            if candidate.exists():
                original_script = candidate

    script_dir = Path(args.script_dir)

    # 跑四道校验
    results = []
    for check in CHECKS:
        result = run_single_check(check, storyboard, script_dir,
                                  original_script=original_script, quiet=args.quiet)
        results.append(result)

    # 汇总
    overall_passed = all(r["passed"] for r in results)
    summary = {
        "storyboard": str(storyboard),
        "overall_passed": overall_passed,
        "checks": results,
        "pass_count": sum(1 for r in results if r["passed"]),
        "fail_count": sum(1 for r in results if not r["passed"]),
    }

    if args.json:
        # 把 stdout_tail 里的 emoji 替换为 ASCII 字符,避免 GBK 编码错误
        # 覆盖 calc_duration / check_* 等子脚本的常见输出
        safe = dict(summary)
        safe["checks"] = []
        for c in summary["checks"]:
            cc = dict(c)
            tail = (cc.get("stdout_tail") or "")
            for old, new in [("✗", "X"), ("✓", "OK"), ("⚠", "[!]"),
                              ("→", "->"), ("─", "-")]:
                tail = tail.replace(old, new)
            cc["stdout_tail"] = tail
            safe["checks"].append(cc)
        print(json.dumps(safe, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if overall_passed else "FAIL"
        one_line = f"{status} | 4道脚本: {summary['pass_count']}/4 PASS"
        print(one_line)
        for r in results:
            mark = "[OK]" if r["passed"] else "[FAIL]"
            ic = r.get("issues_count", "?")
            print(f"  {mark} {r['label']}: passed={r['passed']}, issues={ic}")

    sys.exit(0 if overall_passed else 1)


if __name__ == "__main__":
    main()
