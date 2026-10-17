#!/usr/bin/env python3
"""
check_budget.py —— 讲戏本预算自检脚本

在导演阶段（阶段二产出后）校验导演讲戏本的时间预算是否自洽，从源头拦截
"预算只算台词、没算视觉动作预算"的系统性问题（如 ep53 讲戏本累加 53s vs 分镜实际 68s 差 15s）。

校验项：
1. 硬错误：讲戏本各 P 预算之和 < 台词本全片台词合计 → 台词塞不下（余量为负，必返工）。
2. 硬错误：某个 P 预算 > 15s → 违反母镜头 4-15s 硬约束。
3. 软提示：余量（预算之和 - 台词合计）异常偏高（> 高余量阈值）→ 可能为凑时长加戏，需人工确认。
4. 信息：输出 预算之和 / 台词合计 / 余量 / 头声明的总预算（可选）对照。

用法:
    python check_budget.py --director <01-director-analysis.md> --dialogue <epXX-dialogue-list.md>

退出码: 0 = 通过, 1 = 存在硬错误, 2 = 用法错误/文件缺失
"""
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免 ✓/✗/⚠ 触发 UnicodeEncodeError 崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 母镜头总时长硬上限（秒）
MOTHER_MAX = 15.0
# 余量偏高阈值（秒）：预算之和 - 台词合计 超过此值视为"可能为凑时长加戏"
HIGH_MARGIN = 20.0


def main():
    args = sys.argv[1:]
    director_path = None
    dialogue_path = None
    i = 0
    while i < len(args):
        if args[i] == '--director' and i + 1 < len(args):
            director_path = args[i + 1]
            i += 2
        elif args[i] == '--dialogue' and i + 1 < len(args):
            dialogue_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not director_path or not dialogue_path:
        print("用法: python check_budget.py --director <01-director-analysis.md> --dialogue <epXX-dialogue-list.md>")
        sys.exit(2)
    if not Path(director_path).exists():
        print(f"错误: 讲戏本不存在: {director_path}")
        sys.exit(2)
    if not Path(dialogue_path).exists():
        print(f"错误: 台词本不存在: {dialogue_path}")
        sys.exit(2)

    # ── 1. 讲戏本：提取各 P 的时长 ──
    with open(director_path, encoding='utf-8') as f:
        director = f.read()

    p_budgets = []
    # 兼容两种讲戏本格式：
    #   旧格式：块内有 "- 时长: X秒"（deepseek 版 ep54）
    #   v2 精简格式：时长写进标题尾部 "## Pxx ...（Xs秒）"，body 无"时长:"键（Codex 版 ep55）
    for pm in re.finditer(r'^##\s*(P\d+)([^\n]*)\n(.*?)(?=^##\s*P\d+\b|^##\s+人物清单|^##\s+场景清单|^##\s+关键问题点汇总|\Z)', director, re.M | re.S):
        pid, title_rest, body = pm.group(1), pm.group(2), pm.group(3)
        tm = (re.search(r'时长\*\*[:：]?\s*([\d.]+)\s*秒', body)
              or re.search(r'时长[:：]\s*([\d.]+)\s*秒', body)
              or re.search(r'（\s*([\d.]+)\s*秒\s*）', title_rest))
        if tm:
            p_budgets.append((pid, float(tm.group(1))))

    # 头部声明的总预算（可选信息）
    header_total = None
    htm = re.search(r'总时长\s*[|~:：]\s*([\d.]+)\s*秒', director)
    if htm:
        header_total = float(htm.group(1))

    # ── 2. 台词本：全片台词合计 ──
    with open(dialogue_path, encoding='utf-8') as f:
        dialogue = f.read()
    dtm = re.search(r'全片台词合计约\s*([\d.]+)\s*秒', dialogue)
    dialogue_total = float(dtm.group(1)) if dtm else None
    if dialogue_total is None:
        # 退回：汇总每个场景的 **合计** / 约Xs秒
        scene_sum = re.findall(r'\*\*约\s*([\d.]+)\s*秒\*\*', dialogue)
        if scene_sum:
            dialogue_total = round(sum(float(x) for x in scene_sum), 1)

    print("=" * 76)
    print("导演讲戏本预算自检报告")
    print("=" * 76)
    print(f"讲戏本: {director_path}")
    print(f"台词本: {dialogue_path}")
    print()

    budget_sum = round(sum(b for _, b in p_budgets), 1)
    print(f"讲戏本剧情点: {len(p_budgets)} 个（{', '.join(p for p, _ in p_budgets) if p_budgets else '未解析到'}）")
    print(f"各 P 预算之和: {budget_sum} 秒")
    if header_total is not None:
        flag = "（一致）" if abs(budget_sum - header_total) < 0.5 else "（⚠ 与头部声明不一致）"
        print(f"头部声明总预算: {header_total} 秒 {flag}")
    print(f"台词本全片台词合计: {dialogue_total if dialogue_total is not None else '未解析到'} 秒")
    print()

    hard_errors = 0
    soft_warnings = 0

    # 硬错误 1：预算略小于台词
    if dialogue_total is not None and budget_sum + 1e-9 < dialogue_total:
        diff = round(dialogue_total - budget_sum, 1)
        print(f"✗ [硬错误] 各 P 预算之和 {budget_sum}s < 台词合计 {dialogue_total}s，差 {diff}s：台词塞不下，动作/反应余量为负，分镜阶段必然返工。")
        print(f"    请为相关 P 增加动作/反应预算（'时长'字段应按 台词参考时长 + 视觉动作预算 填写）。")
        hard_errors += 1
    elif dialogue_total is not None:
        margin = round(budget_sum - dialogue_total, 1)
        print(f"✓ 预算之和 {budget_sum}s >= 台词合计 {dialogue_total}s，动作/反应余量 {margin}s")
        if margin > HIGH_MARGIN:
            print(f"  ⚠ [软提示] 余量 {margin}s 偏高（>{HIGH_MARGIN}s），可能为凑时长加戏，请人工确认是否合理。")
            soft_warnings += 1
        if margin < 0.5:
            print(f"  ⚠ [软提示] 余量仅 {margin}s，几乎无动作/反应空间；若含无台词表演点可能偏紧。")
            soft_warnings += 1

    # 硬错误 2：单 P 超 15s
    over = [(p, b) for p, b in p_budgets if b > MOTHER_MAX]
    if over:
        print(f"✗ [硬错误] 以下剧情点预算超过母镜头 {MOTHER_MAX}s 硬上限：{', '.join(f'{p}={b}s' for p, b in over)}")
        print("    需拆分或重新分配，否则分镜母镜头超 15s。")
        hard_errors += 1

    print()
    print("=" * 76)
    if hard_errors == 0 and soft_warnings == 0:
        print("✓ 讲戏本预算自洽，可进入下一阶段。")
        sys.exit(0)
    elif hard_errors == 0:
        print(f"✓ 预算自洽（{soft_warnings} 个软提示，请人工参考）。")
        sys.exit(0)
    else:
        print(f"✗ 发现 {hard_errors} 个硬错误（必须修复）。")
        sys.exit(1)


if __name__ == '__main__':
    main()
