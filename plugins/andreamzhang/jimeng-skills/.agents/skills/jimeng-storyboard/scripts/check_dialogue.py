#!/usr/bin/env python3
"""
check_dialogue.py —— 台词对照校验脚本

校验分镜文件（02-jimeng-prompts.md）中的【台词】字段是否与剧本原文逐字一致，
防止台词在分镜写作时丢失或改写（回忆式复述是台词丢失的头号原因）。

用法:
    python check_dialogue.py --script <剧本原文路径> --storyboard <02-jimeng-prompts.md路径>

检测项:
1. 缺失台词：剧本原文中的台词在分镜中找不到对应（支持拆句拼接匹配）
2. 改写/偏离台词：分镜中的台词与剧本原文任何一句都不一致（非逐字、非子串、相似度低于阈值）

退出码: 0 = 通过, 1 = 存在缺失或改写问题
"""
import re
import sys
import difflib
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免 ✓/✗/⚠ 触发 UnicodeEncodeError 崩溃
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# 相似度阈值（归一化文本）
SIMILARITY_THRESHOLD = 0.85

# 冗余检测的最小归一化字数：更短的短语气词（嗯/好/行）在剧本与分镜中自然反复出现，不判冗余
REDUNDANT_MIN_CHARS = 6


def norm(text: str) -> str:
    """归一化：去所有非汉字/韩文音节/字母/数字字符（韩剧双语台词）"""
    return re.sub('[^一-鿿A-Za-z0-9가-힣]', '', text)


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def extract_script_dialogues(script_path: str):
    """
    从剧本原文提取台词 [(角色, 台词原文)]
    剧本台词行格式：`角色名（动作描述）：台词` 或 `角色名：台词`
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    dialogues = []
    pattern = re.compile(r'^([\u4e00-\u9fffA-Za-z0-9·．.]{1,20})(?:（[^）]*）)?[:：](.+)$')
    # 嵌在动作行（△/▲）内的对话模式：…人物名（情绪）：台词… —— ep62 等集把真台词写进 △ 动作行
    inline_start_pattern = re.compile(r'([\u4e00-\u9fffA-Za-z0-9]{1,12})(（[^）]*）)?[:：]')

    def _append_inline(line: str):
        """从 △ 动作行提取所有「人物（情绪）：台词」片段；台词止于下一个说话人标记或行内新 △ 动作"""
        starts = [mm for mm in inline_start_pattern.finditer(line)]
        for k, mm in enumerate(starts):
            end = starts[k + 1].start() if k + 1 < len(starts) else len(line)
            text = line[mm.end():end]
            if text.startswith('△'):
                continue  # 说话人标记后接的是新动作而非台词
            if '△' in text:
                text = text.split('△')[0]
            text = re.sub(r'（[^）]*）', '', text).strip().strip('。').strip()
            if text:
                dialogues.append((mm.group(1), text))
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 跳过动作描述行（△/▲ 两种三角符均可能）、标题行、人物表行、字幕行
        if line.startswith(('△', '▲')) or line.startswith('#') or line.startswith('【'):
            # △ 动作行可能把真台词嵌在行内（如「△高振华上台。高振华（郑重）：省里批准，…」），
            # 取行内「人物（情绪）：台词」片段，与讲戏本台词清单一致
            if line.startswith(('△', '▲')):
                _append_inline(line)
            continue
        if line.startswith('人物') or line.startswith('第') or line.startswith('时间'):
            continue
        m = pattern.match(line)
        if m:
            char, text = m.group(1), m.group(2).strip()
            text = re.sub(r'^[:：]', '', text).strip()
            # 剥离台词正文中间的全角括号动作/情绪说明（如「（话说到一半，他猛地反应过来）」），
            # 括号内容为动作说明不是台词正文；与台词清单拆句规则一致
            text = re.sub(r'（[^）]*）', '', text).strip()
            if text:
                dialogues.append((char, text))
        elif dialogues:
            # 跨行续行：不以角色名/动作符开头且已有未闭合台词时，合并到上一条
            # （剧本原文长台词被物理换行截断，合并保持整句完整）
            # 跳过场景标题行（如 "53-2 国营饭店办公室 日 内"）、标题行（"第五十三集"）
            if re.match(r'^\d+\s*[-\u2013]', line) or line.startswith('第') or line.startswith(('△', '▲')):
                continue
            prev_char, prev_text = dialogues[-1]
            cleaned = re.sub(r'（[^）]*）', '', line).strip()
            if cleaned:
                dialogues[-1] = (prev_char, prev_text + cleaned)
    return dialogues


def extract_storyboard_dialogues(prompts_path: str):
    """
    从分镜文件提取台词 [(母镜头ID, 角色, 台词)]
    分镜台词格式：【台词】@角色 说：「台词内容」
    支持同一【台词】字段内多位角色台词（换行或同行）
    """
    with open(prompts_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按母镜头分组
    parts = re.split(r'\n## 母镜头(\d+)', content)
    dialogues = []
    pattern = re.compile(r'【台词】@?([\u4e00-\u9fffA-Za-z0-9]+?)\s*(?:说)?[:：]?\s*「([^」\n]+)」[^\n]*?（原文：([^）]+)）')
    pattern_plain = re.compile(r'@?([\u4e00-\u9fffA-Za-z0-9]+?)\s*说：「(.+?)」')
    for i in range(1, len(parts), 2):
        shot_id = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ''
        # ① 韩剧双语台词：同一行内「…」（OS,…）（原文：中文原句）——校验统一取（原文：）括注里的中文
        consumed = []
        for m in pattern.finditer(body):
            consumed.append((m.start(), m.end()))
            dialogues.append((shot_id, m.group(1), m.group(3)))
        # ② 普通中文台词：跳过已被双语匹配覆盖的区间
        for m in pattern_plain.finditer(body):
            if any(s <= m.start() < e for s, e in consumed):
                continue
            dialogues.append((shot_id, m.group(1), m.group(2)))
    return dialogues


def find_missing(script_dlgs, story_dlgs):
    """
    找出剧本中有、分镜中缺失的台词。
    匹配策略：分镜按母镜头拼接归一化文本，剧本台词是其子串即视为命中（支持拆句）。
    """
    story_groups = {}
    for sid, char, text in story_dlgs:
        story_groups.setdefault(sid, '')
        story_groups[sid] += norm(text)
    all_story_norm = ''.join(story_groups.values())

    missing = []
    for idx, (char, text) in enumerate(script_dlgs, 1):
        n = norm(text)
        if not n:
            continue
        matched = any(n in g for g in story_groups.values())
        if not matched and n in all_story_norm:
            matched = True
        if not matched:
            missing.append((idx, char, text))
    return missing


def find_rewrites(script_dlgs, story_dlgs):
    """
    找出分镜中与剧本不一致（改写/偏离）的台词。
    分镜台词必须满足以下任一条件才算一致：
    - 是某句剧本台词的子串（拆句）
    - 包含某句剧本台词（合并）
    - 与某句剧本台词相似度 >= 阈值
    """
    script_norms = [norm(t) for _, t in script_dlgs]
    rewrites = []
    for sid, char, text in story_dlgs:
        n = norm(text)
        if not n:
            continue
        matched = False
        for sn in script_norms:
            if not sn:
                continue
            if n in sn or sn in n:
                matched = True
                break
        if not matched:
            for sn in script_norms:
                if not sn:
                    continue
                if similarity(n, sn) >= SIMILARITY_THRESHOLD:
                    matched = True
                    break
        if not matched:
            rewrites.append((sid, char, text))
    return rewrites


def find_redundant(script_dlgs, story_dlgs):
    """
    找出在分镜中重复出现的剧本台词（冗余）。
    正常：一句剧本台词只在一个母镜头内出现（可拆多句，同母镜头拼接匹配）。
    冗余：同一句剧本台词出现在 >=2 个不同母镜头（如 ep53 M4/M5 各用一次同句台词）。
    只对 >= REDUNDANT_MIN_CHARS 的实义句判冗余，避免短语气词自然复现误报。
    """
    story_groups = {}
    for sid, char, text in story_dlgs:
        story_groups.setdefault(sid, '')
        story_groups[sid] += norm(text)

    redundant = []
    for idx, (char, text) in enumerate(script_dlgs, 1):
        n = norm(text)
        if len(n) < REDUNDANT_MIN_CHARS:
            continue
        matched_mothers = [sid for sid, g in story_groups.items() if n in g]
        if len(matched_mothers) >= 2:
            redundant.append((idx, char, text, matched_mothers))
    return redundant


def main():
    args = sys.argv[1:]
    script_path = None
    prompts_path = None
    i = 0
    while i < len(args):
        if args[i] == '--script' and i + 1 < len(args):
            script_path = args[i + 1]
            i += 2
        elif args[i] == '--storyboard' and i + 1 < len(args):
            prompts_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not script_path or not prompts_path:
        print("用法: python check_dialogue.py --script <剧本原文> --storyboard <02-jimeng-prompts.md>")
        sys.exit(2)

    if not Path(script_path).exists():
        print(f"错误: 剧本文件不存在: {script_path}")
        sys.exit(2)
    if not Path(prompts_path).exists():
        print(f"错误: 分镜文件不存在: {prompts_path}")
        sys.exit(2)

    script_dlgs = extract_script_dialogues(script_path)
    story_dlgs = extract_storyboard_dialogues(prompts_path)

    missing = find_missing(script_dlgs, story_dlgs)
    rewrites = find_rewrites(script_dlgs, story_dlgs)
    redundant = find_redundant(script_dlgs, story_dlgs)

    print("=" * 70)
    print("台词对照校验报告")
    print("=" * 70)
    print(f"剧本文件: {script_path}")
    print(f"分镜文件: {prompts_path}")
    print(f"剧本台词数: {len(script_dlgs)} | 分镜台词数: {len(story_dlgs)}")
    print()

    total_problems = 0

    if missing:
        print(f"[缺失台词] ({len(missing)}处)")
        for idx, char, text in missing:
            print(f"  #{idx} [{char}]：{text}")
        print()
        total_problems += len(missing)

    if rewrites:
        print(f"[改写/偏离台词] ({len(rewrites)}处)")
        for sid, char, text in rewrites:
            print(f"  母镜头{sid} [{char}]：{text}")
        print()
        total_problems += len(rewrites)

    if redundant:
        print(f"[冗余台词（同一句剧本台词出现在 >=2 个母镜头）] ({len(redundant)}处)")
        for idx, char, text, mothers in redundant:
            print(f"  #{idx} [{char}]：{text}   → 母镜头{','.join(mothers)} 重复出现，应只保留 1 处（如为场景内拆分请合并回同一母镜头）")
        print(f"  注：{REDUNDANT_MIN_CHARS} 字以下的短语气词不计冗余（自然复现）")
        print()
        total_problems += len(redundant)

    if total_problems == 0:
        print("✓ 所有台词与剧本原文逐字一致，无缺失、无改写、无冗余！")
        sys.exit(0)
    else:
        print(f"⚠ 共发现 {total_problems} 个台词问题，请对照剧本原文逐条修正后重新校验。")
        print("  修正要求：分镜【台词】字段必须逐字复制剧本原文，禁止凭记忆复述。")
        sys.exit(1)


if __name__ == '__main__':
    main()
