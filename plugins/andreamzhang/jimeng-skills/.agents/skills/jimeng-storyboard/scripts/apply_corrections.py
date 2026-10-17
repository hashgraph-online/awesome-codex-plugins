#!/usr/bin/env python3
"""
apply_corrections.py —— 一次性写入所有时长修正+母镜头拆分+重新编号+语速修正

用法:
    python apply_corrections.py --storyboard <分镜文件路径> --corrections <修正JSON路径>

corrections.json 格式:
{
  "split": {
    "母镜头ID": {
      "new_id": "临时ID(如 1b)",
      "split_before_sub": 子镜头号,
      "new_header": {
        "total": 总时长,
        "title": "标题(不含P编号)",
        "scene_type": "场景类型",
        "transition": "分镜过渡",
        "style": "全局风格",
        "assets": "声明行"
      }
    }
  },
  "renumber": { "旧ID": 新ID, ... },
  "total_fixes": { "母镜头ID": 新总时长 },
  "duration_fixes": { "母镜头ID": {"子镜头ID": 新时长, ...} },
  "speed_fixes": { "母镜头ID": {"子镜头ID": "新语速"} }
}

处理顺序: split → renumber → total_fixes → duration_fixes → speed_fixes
特性:
- 幂等性: 如果当前值已等于目标值，跳过修改
- 拆分后子镜头自动重新编号
- renumber 后 P 编号自动重新分配（P01, P02, ...）
- 所有中文数据从 JSON 读取，不硬编码
"""

import re
import json
import sys
from pathlib import Path


def format_duration(val):
    """将数字格式化为子镜头时长字符串，如 3.0, 6.5, 10.5"""
    if isinstance(val, int):
        return f"{val}.0"
    elif isinstance(val, float):
        if val == int(val):
            return f"{int(val)}.0"
        else:
            return str(val)
    return str(val)


def format_total(val):
    """将数字格式化为母镜头总时长字符串，整数无小数，如 12, 9.5, 13.5"""
    if isinstance(val, int):
        return f"{val}"
    elif isinstance(val, float):
        if val == int(val):
            return f"{int(val)}"
        else:
            return str(val)
    return str(val)


def split_into_mother_shots(content):
    """
    将分镜文件内容拆分为: [前导部分, [(母镜头ID, 母镜头完整文本), ...]]
    """
    # 找到所有母镜头的起始位置（编号必须为纯数字或临时ID，禁止字母后缀，如 3A、4B）
    pattern = r'\n## 母镜头(\d+|[a-zA-Z0-9]+)'
    matches = list(re.finditer(pattern, content))

    if not matches:
        return content, []

    # 前导部分
    preamble = content[:matches[0].start()]

    shots = []
    for i, match in enumerate(matches):
        shot_id = match.group(1)
        start = match.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        section = content[start:end]
        shots.append((shot_id, section))

    return preamble, shots


def build_new_header(new_id, new_header):
    """构建新母镜头头部文本"""
    total = new_header.get('total', 0)
    title = new_header.get('title', '')
    scene_type = new_header.get('scene_type', '')
    transition = new_header.get('transition', '')
    style = new_header.get('style', '')
    assets = new_header.get('assets', '')

    total_str = format_total(total)

    header = f"## 母镜头{new_id}（总时长：{total_str}秒）—— [P00 {title}]\n\n"
    header += f"场景类型：{scene_type}\n\n"
    header += f"**分镜过渡**：{transition}\n\n"
    header += f"{style}\n\n"
    header += f"{assets}\n\n"
    return header


def renumber_subs(subs_text, start_num):
    """将子镜头重新编号，原 start_num 及之后的子镜头改为从 1 开始"""
    pattern = r'(### 子镜头)(\d+)(（时长：)'

    def repl(m):
        old_num = int(m.group(2))
        new_num = old_num - start_num + 1
        return f"{m.group(1)}{new_num}{m.group(3)}"

    return re.sub(pattern, repl, subs_text)


def apply_split(content, split_spec):
    """拆分母镜头。split_spec: {"原ID": {"new_id":..., "split_before_sub":..., "new_header":...}}"""
    preamble, shots = split_into_mother_shots(content)

    existing_ids = {sid for sid, _ in shots}

    # 从后往前处理，避免位置偏移
    for shot_id in sorted(split_spec.keys(), key=lambda x: int(re.match(r'\d+', x).group()), reverse=True):
        spec = split_spec[shot_id]
        new_id = spec['new_id']
        split_before_sub = spec['split_before_sub']
        new_header = spec['new_header']

        # 幂等性：new_id 已存在则跳过
        if new_id in existing_ids:
            print(f"  母镜头{new_id}已存在，跳过拆分{shot_id}（幂等）")
            continue

        # 找到母镜头
        idx = None
        for i, (sid, section) in enumerate(shots):
            if sid == shot_id:
                idx = i
                break
        if idx is None:
            print(f"  警告: 母镜头{shot_id}不存在，跳过拆分")
            continue

        section = shots[idx][1]

        # 找到子镜头位置
        sub_pattern = r'(### 子镜头)(\d+)(（时长：)'
        sub_matches = list(re.finditer(sub_pattern, section))
        if not sub_matches:
            print(f"  警告: 母镜头{shot_id}无子镜头，跳过拆分")
            continue

        # 找到 split_before_sub 子镜头的位置
        split_pos = None
        for m in sub_matches:
            if int(m.group(2)) == split_before_sub:
                split_pos = m.start()
                break
        if split_pos is None:
            print(f"  警告: 母镜头{shot_id}未找到子镜头{split_before_sub}，跳过拆分")
            continue

        first_sub_pos = sub_matches[0].start()
        header = section[:first_sub_pos]
        subs = section[first_sub_pos:]

        # 第一部分：子1..(split_before_sub-1)
        part1_subs = subs[:split_pos - first_sub_pos]
        # 第二部分：子split_before_sub..end
        part2_subs = subs[split_pos - first_sub_pos:]

        # 第一部分母镜头
        part1 = header + part1_subs

        # 第二部分母镜头
        new_header_text = build_new_header(new_id, new_header)
        part2_subs_renumbered = renumber_subs(part2_subs, split_before_sub)
        part2 = new_header_text + part2_subs_renumbered

        # 更新 shots
        shots[idx] = (shot_id, part1)
        shots.insert(idx + 1, (new_id, part2))
        existing_ids.add(new_id)
        print(f"  母镜头{shot_id} 拆分为 {shot_id} + {new_id}（在子镜头{split_before_sub}前）")

    # 重组
    result = preamble
    for sid, section in shots:
        result += section
    return result


def apply_renumber(content, renumber_map):
    """重新编号母镜头ID，并按顺序重新分配 P 编号（P01, P02, ...）"""
    # 1. 一次性替换母镜头ID
    pattern = r'(## 母镜头)(\d+|[a-zA-Z0-9]+)(（)'

    def repl(m):
        old_id = m.group(2)
        new_id = renumber_map.get(old_id, old_id)
        return f"{m.group(1)}{new_id}{m.group(3)}"

    content = re.sub(pattern, repl, content)

    # 2. 重新分配P编号（按顺序）
    p_pattern = r'(## 母镜头\d+（总时长：[^\n]*）—— \[)P\d+([^\]]*\])'
    matches = list(re.finditer(p_pattern, content))
    for i, m in enumerate(reversed(matches)):
        new_p = f"P{len(matches) - i:02d}"
        content = content[:m.start()] + m.group(1) + new_p + m.group(2) + content[m.end():]

    if matches:
        print(f"  母镜头重新编号完成，P 编号重新分配为 P01–P{len(matches):02d}")
    return content


def apply_total_fix(section, shot_id, new_total):
    """修正母镜头总时长"""
    old_match = re.search(r'总时长：(\d+\.?\d*)秒', section)
    if not old_match:
        return section, False
    old_total = old_match.group(1)
    new_total_str = format_total(new_total)
    if old_total == new_total_str:
        return section, False  # 已是目标值，跳过
    section = section.replace(
        f'总时长：{old_total}秒',
        f'总时长：{new_total_str}秒',
        1
    )
    print(f"  母镜头{shot_id}: 总时长 {old_total}秒 → {new_total_str}秒")
    return section, True


def apply_duration_fix(section, shot_id, sub_id, new_dur):
    """修正子镜头时长"""
    new_val = format_duration(new_dur)
    pattern = rf'(### 子镜头{sub_id}（时长：⏱)\d+\.?\d*s( 秒）：)'
    match = re.search(pattern, section)
    if not match:
        return section, False
    old_val_match = re.search(r'⏱(\d+\.?\d*)s', match.group(0))
    old_val = old_val_match.group(1) if old_val_match else "?"
    # 检查是否已是目标值
    if old_val == new_val:
        return section, False
    section = re.sub(pattern, rf'\g<1>{new_val}s\g<2>', section, count=1)
    print(f"  母镜头{shot_id} 子镜头{sub_id}: 时长 {old_val}s → {new_val}s")
    return section, True


def apply_speed_fix(section, shot_id, sub_id, new_speed):
    """修正子镜头台词语速"""
    # 将母镜头section按子镜头拆分
    sub_pattern = r'(### 子镜头\d+（时长：[^\n]*）：)'
    sub_parts = re.split(sub_pattern, section)

    # sub_parts[0] = 母镜头头部（标题、过渡、风格等）
    # sub_parts[1] = 子镜头1的标题
    # sub_parts[2] = 子镜头1的内容
    # sub_parts[3] = 子镜头2的标题
    # sub_parts[4] = 子镜头2的内容
    # ...

    changed = False
    for j in range(1, len(sub_parts), 2):
        sub_header = sub_parts[j]
        sub_body = sub_parts[j + 1] if j + 1 < len(sub_parts) else ""
        sub_num_match = re.search(r'### 子镜头(\d+)', sub_header)
        if sub_num_match and sub_num_match.group(1) == sub_id:
            # 只匹配【台词】字段中的语速，避免误改【画面】字段
            dialogue_match = re.search(r'【台词】[^\n]*', sub_body)
            if dialogue_match:
                dialogue_line = dialogue_match.group(0)
                speed_match = re.search(r'语速([^,）\)、]+)', dialogue_line)
                if speed_match:
                    old_speed = speed_match.group(1).strip()
                    if old_speed == new_speed:
                        return section, False  # 已是目标值
                    sub_body = sub_body.replace(
                        f'语速{old_speed}',
                        f'语速{new_speed}',
                        1
                    )
                    sub_parts[j + 1] = sub_body
                    changed = True
                    print(f"  母镜头{shot_id} 子镜头{sub_id}: 语速 {old_speed} → {new_speed}")
                    break

    if changed:
        return ''.join(sub_parts), True
    return section, False


def apply_corrections(storyboard_path, corrections_path):
    """主函数：读取修正方案并一次性应用"""
    with open(storyboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(corrections_path, 'r', encoding='utf-8') as f:
        corrections = json.load(f)

    # 0. 处理拆分
    if 'split' in corrections and corrections['split']:
        content = apply_split(content, corrections['split'])

    # 0.5 处理重新编号
    if 'renumber' in corrections and corrections['renumber']:
        content = apply_renumber(content, corrections['renumber'])

    # 重新解析母镜头
    preamble, shots = split_into_mother_shots(content)

    if not shots:
        print("错误: 未找到母镜头！")
        return False

    total_changes = 0
    new_shots = []

    for shot_id, section in shots:
        changed = False

        # 1. 应用总时长修正
        if 'total_fixes' in corrections and shot_id in corrections['total_fixes']:
            section, did_change = apply_total_fix(
                section, shot_id, corrections['total_fixes'][shot_id]
            )
            if did_change:
                total_changes += 1
                changed = True

        # 2. 应用子镜头时长修正
        if 'duration_fixes' in corrections and shot_id in corrections['duration_fixes']:
            for sub_id, new_dur in corrections['duration_fixes'][shot_id].items():
                section, did_change = apply_duration_fix(
                    section, shot_id, sub_id, new_dur
                )
                if did_change:
                    total_changes += 1
                    changed = True

        # 3. 应用语速修正
        if 'speed_fixes' in corrections and shot_id in corrections['speed_fixes']:
            for sub_id, new_speed in corrections['speed_fixes'][shot_id].items():
                section, did_change = apply_speed_fix(
                    section, shot_id, sub_id, new_speed
                )
                if did_change:
                    total_changes += 1
                    changed = True

        new_shots.append((shot_id, section))

    # 重组文件
    result = preamble
    for shot_id, section in new_shots:
        result += section

    # 写回文件
    with open(storyboard_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\n总修改数: {total_changes}")
    if total_changes == 0:
        print("提示: 未发现需要修改的内容，可能已经应用过修正（幂等性跳过）。")

    return True


def main():
    args = sys.argv[1:]
    storyboard_path = None
    corrections_path = None

    i = 0
    while i < len(args):
        if args[i] == '--storyboard' and i + 1 < len(args):
            storyboard_path = args[i + 1]
            i += 2
        elif args[i] == '--corrections' and i + 1 < len(args):
            corrections_path = args[i + 1]
            i += 2
        else:
            i += 1

    if not storyboard_path or not corrections_path:
        print("用法: python apply_corrections.py --storyboard <分镜文件路径> --corrections <修正JSON路径>")
        sys.exit(1)

    print(f"分镜文件: {storyboard_path}")
    print(f"修正方案: {corrections_path}")
    print()

    apply_corrections(storyboard_path, corrections_path)


if __name__ == '__main__':
    main()
