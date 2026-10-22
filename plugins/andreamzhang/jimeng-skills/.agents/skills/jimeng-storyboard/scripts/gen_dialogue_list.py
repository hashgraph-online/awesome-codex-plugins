"""
台词本生成器 v1.0
从剧本原文提取台词 + 按中等语速计算参考时长，输出台词本（md）+ 结构化（json）。

用法：
  python gen_dialogue_list.py scripts/[剧本名]/script/epXX.txt
输出：
  scripts/[剧本名]/outputs/epXX/epXX-dialogue-list.md
  scripts/[剧本名]/outputs/epXX/epXX-dialogue-list.json
"""
import json
import re
import sys
import os

# 复用 calc_duration.py 的时长计算（同目录，无 import 副作用，main 有 __main__ 保护）
from calc_duration import count_chars, compute_duration as calc_compute_duration

# ── 复用时长规则 ──
RULES_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'duration-rules.json')
with open(RULES_PATH, 'r', encoding='utf-8') as f:
    rules = json.load(f)

BASE_SPEED = rules['base_speed']['chars_per_second']  # 5字/秒


# 与 check_dialogue.py 口径一致：剥离台词正文中的嵌入式全角括号动作说明（仅用于时长/字数计算）
ACTION_NOTE_RE = re.compile(r'（[^）]*）')


def strip_action_notes(text: str) -> str:
    """剥离台词正文中的嵌入式全角括号动作说明，如（转头冲着手下大吼）"""
    return ACTION_NOTE_RE.sub('', text)


def compute_duration(text: str) -> dict:
    """按中等语速计算单条台词参考时长（复用 calc_duration.py，剥离括号动作说明后计算）"""
    stripped = strip_action_notes(text)
    return {
        "char_count": count_chars(stripped),
        "duration": calc_compute_duration(stripped, '中等')['rounded_duration'],
    }


# ── 剧本解析 ──
# 场景标题：行首数字编号（1 或 1-1）+ 空格 + 内容；内容含时间/内外标记或非台词
SCENE_RE = re.compile(r'^\s*(\d+(?:-\d+)?)\s+(.+)$')
SCENE_MARKER_RE = re.compile(r'[日夜晚晨昏上中下傍晚内外]')
CHARACTER_LINE_RE = re.compile(r'^\s*人物[:：]\s*(.+)$')
DIALOGUE_RE = re.compile(r'^\s*([^△（(【\s][^：:]{0,20}?)[（(]([^）)]*)[）)]\s*[:：]\s*(.+)$')
DIALOGUE_SIMPLE_RE = re.compile(r'^\s*([^△（(【\s][^：:]{0,20}?)\s*[:：]\s*(.+)$')
ACTION_RE = re.compile(r'^\s*△')
BRACKET_RE = re.compile(r'^\s*【[^】]+】\s*$')

# 中文数字 → 阿拉伯数字（支持一~九十九、一百以内常见写法）
CN_NUM = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
CN_UNIT = {'十': 10, '百': 100}


def cn_to_int(s: str) -> int:
    """中文数字转阿拉伯数字，如 一→1、十一→11、二十→20、一百零一→101"""
    total = 0
    current = 0
    for ch in s:
        if ch in CN_NUM:
            current = CN_NUM[ch]
        elif ch in CN_UNIT:
            unit = CN_UNIT[ch]
            if current == 0:
                current = 1
            total += current * unit
            current = 0
    return total + current


def is_scene_title(stripped: str) -> bool:
    """判断是否为场景标题行：数字编号开头，内容含时间/内外标记或非台词内容"""
    m = SCENE_RE.match(stripped)
    if not m:
        return False
    rest = m.group(2)
    if SCENE_MARKER_RE.search(rest):
        return True
    # 无时间/内外标记时：排除台词行后视为场景标题
    if DIALOGUE_RE.match(rest) or DIALOGUE_SIMPLE_RE.match(rest):
        return False
    return True


def parse_script(script_path: str) -> dict:
    """解析剧本原文，返回 {ep_num, scenes: [{scene_id, title, dialogues: [{seq, character, emotion, text}]}]}
    台词逐字提取：跨物理行的台词自动合并；场景标题解析失败或缺失时优雅降级，绝不崩溃。"""
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    ep_m = re.search(r'第([\d一二三四五六七八九十百]+)集', '\n'.join(lines[:20]))
    ep_num = ep_m.group(1) if ep_m else 'XX'
    if ep_num != 'XX' and not ep_num.isdigit():
        ep_num = str(cn_to_int(ep_num))

    scenes = []
    current_scene = None
    seq = 0
    pending = None  # 当前台词缓冲 {seq, character, emotion, text}

    def ensure_scene():
        """台词出现在场景标题之前时，归入「未命名场景」，绝不崩溃"""
        nonlocal current_scene
        if current_scene is None:
            current_scene = {
                "scene_id": "?",
                "title": "未命名场景（场景标题缺失）",
                "dialogues": [],
            }
            scenes.append(current_scene)

    def commit_pending():
        """提交当前台词缓冲（若存在）"""
        nonlocal pending
        if pending is None:
            return
        ensure_scene()
        current_scene["dialogues"].append(pending)
        pending = None

    for raw in lines:
        line = raw.rstrip('\n').rstrip('\r')
        stripped = line.strip()

        # 场景标题（台词折行终止条件）
        if is_scene_title(stripped):
            commit_pending()
            current_scene = {
                "scene_id": SCENE_RE.match(stripped).group(1),
                "title": stripped,
                "dialogues": [],
            }
            scenes.append(current_scene)
            seq = 0
            continue

        # 空行：台词折行终止条件
        if not stripped:
            commit_pending()
            continue

        # 括号标记行（如【闪回开始】【闪回结束】）：终止台词折行，跳过
        if BRACKET_RE.match(stripped):
            commit_pending()
            continue

        # 人物行
        if CHARACTER_LINE_RE.match(line):
            commit_pending()
            continue

        # 动作行
        if ACTION_RE.match(line):
            commit_pending()
            continue

        # 台词行（带情绪标注）
        d_match = DIALOGUE_RE.match(line)
        if d_match:
            commit_pending()
            seq += 1
            pending = {
                "seq": seq,
                "character": d_match.group(1).strip(),
                "emotion": d_match.group(2).strip(),
                "text": d_match.group(3).strip(),
            }
            continue

        # 台词行（无情绪标注）
        d_simple = DIALOGUE_SIMPLE_RE.match(line)
        if d_simple:
            commit_pending()
            seq += 1
            pending = {
                "seq": seq,
                "character": d_simple.group(1).strip(),
                "emotion": "",
                "text": d_simple.group(2).strip(),
            }
            continue

        # 普通文本行：续接当前台词（多行台词折行合并，逐字保留）
        if pending is not None:
            pending["text"] += stripped
            continue

        # 无法识别的行：跳过，不崩溃

    commit_pending()
    return {"ep_num": ep_num, "scenes": scenes}


def render_markdown(data: dict) -> str:
    """渲染台词本 md"""
    lines = []
    lines.append(f"# 第{data['ep_num']}集 台词本与时长清单")
    lines.append("")
    lines.append("> 台词逐字引用剧本原文；参考时长按中等语速（5字/秒）计算，向上取整到0.5秒。")
    lines.append("")
    lines.append("> 字面唯一权威是剧本原文（script/epXX.txt），本清单为提取的工作副本。")
    lines.append("")

    total_all = 0.0
    for scene in data['scenes']:
        lines.append(f"## 场景 {scene['title']}")
        lines.append("")
        lines.append("| 序号 | 角色 | 台词（剧本原文） | 参考时长 |")
        lines.append("|------|------|------------------|----------|")
        scene_total = 0.0
        for d in scene['dialogues']:
            dur = compute_duration(d['text'])
            scene_total += dur['duration']
            lines.append(f"| {d['seq']} | {d['character']} | {d['text']} | 约{dur['duration']}秒 |")
        total_all += scene_total
        lines.append(f"| **合计** | | | **约{round(scene_total, 1)}秒** |")
        lines.append("")

    lines.append(f"**全片台词合计约 {round(total_all, 1)} 秒**")
    lines.append("")
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python gen_dialogue_list.py scripts/[剧本名]/script/epXX.txt")
        sys.exit(1)

    script_path = sys.argv[1]
    if not os.path.exists(script_path):
        print(f"错误：剧本文件不存在 {script_path}")
        sys.exit(1)

    data = parse_script(script_path)

    # 输出目录 = 剧本目录同级 outputs/epXX（集号从剧本文件名提取，如 ep56.txt → ep56）
    script_dir = os.path.dirname(script_path)
    ep_match = re.search(r'(ep\d+)', os.path.basename(script_path))
    ep_dir = ep_match.group(1) if ep_match else 'epXX'
    output_dir = os.path.join(os.path.dirname(script_dir), 'outputs', ep_dir)
    os.makedirs(output_dir, exist_ok=True)

    md_path = os.path.join(output_dir, f'{ep_dir}-dialogue-list.md')
    json_path = os.path.join(output_dir, f'{ep_dir}-dialogue-list.json')

    # md
    md_content = render_markdown(data)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # json
    json_data = {
        "meta": {
            "ep": ep_dir,
            "source": os.path.basename(script_path),
            "rules_version": rules['version'],
            "base_speed": f"{BASE_SPEED}字/秒",
            "note": "参考时长按中等语速计算",
        },
        "scenes": [
            {
                "scene_id": s['scene_id'],
                "title": s['title'],
                "dialogues": [
                    {
                        "seq": d['seq'],
                        "character": d['character'],
                        "emotion": d['emotion'],
                        "text": d['text'],
                        "char_count": compute_duration(d['text'])['char_count'],
                        "duration": compute_duration(d['text'])['duration'],
                    }
                    for d in s['dialogues']
                ],
            }
            for s in data['scenes']
        ],
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    total_dialogues = sum(len(s['dialogues']) for s in data['scenes'])
    total_duration = sum(compute_duration(d['text'])['duration'] for s in data['scenes'] for d in s['dialogues'])
    print(f"台词本生成完成：{total_dialogues} 条台词，全片参考时长约 {round(total_duration, 1)} 秒")
    print(f"台词本：{md_path}")
    print(f"结构化：{json_path}")


if __name__ == '__main__':
    main()
